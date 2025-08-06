"""
M-Pesa Views Module

This module contains all the views for the M-Pesa payment integration system.
It provides both frontend views for the payment form and API endpoints for
M-Pesa payment processing.

Components:
    Frontend Views:
        - payment_form: Renders the payment initiation form
        - transaction_status: Displays transaction status details
    
    API Views:
        - MpesaCheckout: Initiates STK push payments
        - MpesaStkQuery: Queries payment status
        - MpesaCallBack: Handles Safaricom payment callbacks

Security Features:
    - IP whitelisting for callback endpoints
    - CSRF exemption for external callbacks
    - Authentication controls for public APIs

Dependencies:
    - Django REST Framework for API functionality
    - Custom serializers for data validation
    - M-Pesa gateway for payment processing
    - Callback security for IP whitelisting

Author: M-Pesa Integration Team
Date: 2024
"""

import json
import logging

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import MpesaCheckoutSerializer, TransactionSerializer
from .stk_push import MpesaGateWay
from .callback_security import SafaricomIPWhitelist

# Initialize logger for this module
logging = logging.getLogger("default")


def get_gateway():
    """
    Lazy initialization of MpesaGateWay to avoid startup issues.
    
    This function ensures the gateway is only initialized when needed,
    preventing issues during application startup, testing, or when
    environment variables might not be available.
    
    Uses function attributes to store the singleton instance.
    
    Returns:
        MpesaGateWay: Singleton instance of the M-Pesa gateway
    """
    if not hasattr(get_gateway, '_gateway'):
        get_gateway._gateway = MpesaGateWay()
    return get_gateway._gateway


def payment_form(request):
    """
    Render the payment form template for frontend interface.
    
    This view serves the main payment form where users can enter
    their phone number, amount, and payment details.
    
    Args:
        request (HttpRequest): Django HTTP request object
        
    Returns:
        HttpResponse: Rendered payment form template
    """
    return render(request, 'payment_form.html')


def transaction_status(request, checkout_request_id):
    """
    Display transaction status page for a specific payment.
    
    Shows detailed information about a transaction including status,
    amount, phone number, and timestamps.
    
    Args:
        request (HttpRequest): Django HTTP request object
        checkout_request_id (str): M-Pesa checkout request identifier
        
    Returns:
        HttpResponse: Rendered transaction status page or error page
    """
    try:
        from .models import Transaction
        # Retrieve transaction by checkout request ID
        transaction = Transaction.objects.get(checkout_request_id=checkout_request_id)
        return render(request, 'transaction_status.html', {'transaction': transaction})
    except Transaction.DoesNotExist:
        # Handle case where transaction is not found
        return render(request, 'payment_form.html', {
            'error': 'Transaction not found'
        })


@authentication_classes([])  # Disable authentication for public API
@permission_classes((AllowAny,))  # Allow access without authentication
class MpesaCheckout(APIView):
    """
    API view for initiating M-Pesa STK Push payments.
    
    This endpoint accepts payment requests from the frontend and
    initiates STK push to the customer's phone.
    
    Methods:
        POST: Initiate payment request
    """
    
    # Specify the serializer for request validation
    serializer = MpesaCheckoutSerializer

    def post(self, request, *args, **kwargs):
        """
        Handle POST request to initiate M-Pesa payment.
        
        Validates the request data and sends STK push to customer's phone.
        
        Args:
            request (Request): DRF request object containing payment data
            
        Returns:
            Response: JSON response with STK push result
        """
        # Validate request data using serializer
        serializer = self.serializer(data=request.data)
        
        if serializer.is_valid(raise_exception=True):
            # Prepare payload for gateway
            payload = {
                "data": serializer.validated_data,  # Validated payment data
                "request": request  # Original request for IP tracking
            }
            
            # Send STK push request through gateway
            res = get_gateway().stk_push_request(payload)
            
            # Return M-Pesa API response to frontend
            return Response(res, status=200)


@authentication_classes([])  # Disable authentication for public API
@permission_classes((AllowAny,))  # Allow access without authentication
class MpesaStkQuery(APIView):
    """
    API view for querying M-Pesa payment status.
    
    This endpoint allows checking the current status of a payment
    using the checkout request ID.
    
    Methods:
        POST: Query payment status
    """
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to query payment status.
        
        Args:
            request (Request): DRF request object containing checkout_request_id
            
        Returns:
            Response: JSON response with payment status and local transaction data
        """
        # Extract checkout request ID from request data
        checkout_request_id = request.data.get('checkout_request_id')
        
        if not checkout_request_id:
            return Response(
                {"error": "checkout_request_id is required"}, 
                status=400
            )
        
        # Query M-Pesa API for payment status
        res = get_gateway().stk_push_query(checkout_request_id)
        
        # Update local transaction status based on M-Pesa response
        try:
            from .models import Transaction
            transaction = Transaction.objects.get(checkout_request_id=checkout_request_id)
            
                        # Map M-Pesa ResultCode to our local status codes
            if 'ResultCode' in res:
                result_code = str(res['ResultCode'])
                old_status = transaction.status
                
                # Update status based on M-Pesa ResultCode
                if result_code == "0":
                    # Payment successful
                    transaction.status = "0"  # Complete
                elif result_code == "1032":
                    # User cancelled
                    transaction.status = "3"  # Cancelled
                elif result_code == "1037":
                    # Request timeout (no response from user)
                    transaction.status = "4"  # Timeout
                elif result_code in ["1", "17"]:
                    # Insufficient funds or other payment failures
                    transaction.status = "2"  # Failed
                elif result_code in ["1001", "4999"]:
                    # Still pending (4999 = transaction still under processing)
                    transaction.status = "1"  # Pending
                else:
                    # Other error codes - mark as failed
                    transaction.status = "2"  # Failed
                
                # Save only if status changed
                if transaction.status != old_status:
                    transaction.save()
                    print(f"Transaction {checkout_request_id} status updated from {old_status} to {transaction.status}")
                else:
                    print(f"Transaction {checkout_request_id} status unchanged: {transaction.status}")
            
            # Get updated transaction data
            transaction.refresh_from_db()
            transaction_data = TransactionSerializer(transaction).data
            res['local_transaction'] = transaction_data
            
        except Transaction.DoesNotExist:
            # No local transaction found
            res['local_transaction'] = None
        except Exception as e:
            print(f"Error updating transaction status: {e}")
            # Still return the transaction data even if update failed
            try:
                transaction = Transaction.objects.get(checkout_request_id=checkout_request_id)
                transaction_data = TransactionSerializer(transaction).data
                res['local_transaction'] = transaction_data
            except:
                res['local_transaction'] = None
        
        return Response(res, status=200)


@authentication_classes([])  # Disable authentication for callback
@permission_classes((SafaricomIPWhitelist,))  # Only allow Safaricom IPs
@method_decorator(csrf_exempt, name='dispatch')  # Disable CSRF for callback
class MpesaCallBack(APIView):
    """
    API view for handling M-Pesa payment callbacks from Safaricom.
    
    This endpoint receives payment confirmations and updates from
    Safaricom's servers. It's secured with IP whitelisting to ensure
    only legitimate callbacks are processed.
    
    Methods:
        GET: Health check endpoint
        POST: Process payment callback
    """
    
    def get(self, request):
        """
        Handle GET request for callback health check.
        
        Safaricom may send GET requests to verify the callback URL is active.
        
        Args:
            request (Request): DRF request object
            
        Returns:
            Response: Simple OK response
        """
        return Response({"status": "OK"}, status=200)

    def post(self, request, *args, **kwargs):
        """
        Handle POST request containing payment callback data.
        
        Processes payment confirmations from Safaricom and updates
        transaction records accordingly.
        
        Args:
            request (Request): DRF request object with callback data
            
        Returns:
            Response: Acknowledgment response for Safaricom
        """
        logging.info("{}".format("Callback from MPESA"))
        
        # Get raw callback data from request body
        data = request.body
        
        # Process callback through gateway handler
        return get_gateway().callback_handler(json.loads(data))