"""
M-Pesa STK Push Integration Module

This module provides the core functionality for integrating with Safaricom's M-Pesa
STK Push API. It handles authentication, payment requests, status queries, and
callback processing.

Key Features:
- Automatic access token management with refresh
- STK Push payment initiation
- Payment status queries
- Callback handling from Safaricom
- Transaction database management
"""

import logging
import time
import math
import base64
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
from rest_framework.response import Response
from phonenumber_field.phonenumber import PhoneNumber

from config.settings import env
from .models import Transaction
from .serializers import TransactionSerializer

# Initialize logger for this module
logging = logging.getLogger("default")

class MpesaGateWay:
    """
    Main M-Pesa Gateway class for handling all M-Pesa API interactions.
    
    This class manages:
    - Authentication with Safaricom API
    - STK Push payment requests
    - Payment status queries
    - Callback processing
    - Transaction record management
    """
    
    # Class-level attributes for API configuration
    shortcode = None          # Business short code
    consumer_key = None       # API consumer key
    consumer_secret = None    # API consumer secret
    access_token_url = None   # Token endpoint URL
    access_token = None       # Current access token
    access_token_expiration = None  # Token expiration timestamp
    checkout_url = None       # STK Push endpoint URL
    timestamp = None          # Current timestamp for requests


    def __init__(self):
        """
        Initialize the M-Pesa Gateway with configuration and authentication.
        
        Loads configuration from environment variables and attempts to
        obtain an access token for API authentication.
        """
        now = datetime.now()
        
        # Load configuration from environment variables
        self.shortcode = env("shortcode")
        self.consumer_key = env("consumer_key")
        self.consumer_secret = env("consumer_secret")
        self.access_token_url = env("access_token_url")
        self.stk_query_url = env("mpesa_query_check_url")  # STK query endpoint
        self.headers = {}  # Initialize request headers

        # Generate password for API authentication
        self.password = self.generate_password()
        
        # Load callback URL and checkout endpoint
        self.c2b_callback = env("c2b_callback")
        self.checkout_url = env("checkout_url")

        try:
            # Attempt to get access token
            self.access_token = self.getAccessToken()
            if self.access_token is None:
                raise Exception("Request for access token failed.")
        except Exception as e:
            logging.error("Error {}".format(e))
            # Set default headers even if token fails to prevent crashes
            self.headers = {"Authorization": "Bearer "}
        else:
            # Set token expiration time (3400 seconds = ~57 minutes, slightly less than 1 hour)
            self.access_token_expiration = time.time() + 3400

    def getAccessToken(self):
        """
        Obtain access token from Safaricom OAuth API.
        
        Uses Basic Authentication with consumer key and secret to get
        an OAuth access token for subsequent API calls.
        
        Returns:
            str: Access token string
            
        Raises:
            Exception: If token request fails or response is invalid
        """
        try:
            # Make OAuth request using Basic Authentication
            res = requests.get(
                self.access_token_url,
                auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
            )
            res.raise_for_status()  # Raise exception for HTTP error status codes
            
            # Parse JSON response
            token_data = res.json()
            token = token_data.get("access_token")
            
            if not token:
                raise Exception("No access token in response")
                
            # Set authorization header for future requests
            self.headers = {"Authorization": "Bearer %s" % token}
            return token
            
        except Exception as err:
            logging.error("Error getting access token: {}".format(err))
            # Set empty bearer token to prevent None errors
            self.headers = {"Authorization": "Bearer "}
            raise err

    class Decorators:
        """
        Utility decorators for the MpesaGateWay class.
        """
        
        @staticmethod
        def refreshToken(decorated):
            """
            Decorator to automatically refresh expired access tokens.
            
            Checks if the current access token has expired and refreshes it
            before executing the decorated method.
            
            Args:
                decorated: The method to be decorated
                
            Returns:
                function: Wrapped function with token refresh logic
            """
            def wrapper(gateway, *args, **kwargs):
                # Check if token has expired
                if (
                    gateway.access_token_expiration
                    and time.time() > gateway.access_token_expiration
                ):
                    try:
                        # Refresh the access token
                        token = gateway.getAccessToken()
                        gateway.access_token = token
                    except Exception as e:
                        logging.error("Failed to refresh token: {}".format(e))
                        # Continue with existing token (may fail, but worth trying)
                        
                # Execute the original method
                return decorated(gateway, *args, **kwargs)

            return wrapper


    def generate_password(self):
        """
        Generate M-Pesa API password using business shortcode and passkey.
        
        The password is created by concatenating:
        - Business shortcode
        - Passkey (from Safaricom)
        - Current timestamp
        
        This string is then base64 encoded.
        
        Returns:
            str: Base64 encoded password string
        """
        now = datetime.now()
        # Generate timestamp in required format (YYYYMMDDHHMMSS)
        self.timestamp = now.strftime("%Y%m%d%H%M%S")
        
        # Concatenate shortcode + passkey + timestamp
        password_str = env("shortcode") + env("pass_key") + self.timestamp
        
        # Encode as base64
        password_bytes = password_str.encode("ascii")
        return base64.b64encode(password_bytes).decode("utf-8")

    @Decorators.refreshToken
    def stk_push_request(self, payload):
        """
        Initiate an STK Push payment request to customer's phone.
        
        This method sends a payment request to the customer's phone via M-Pesa.
        The customer will receive a prompt to enter their M-Pesa PIN.
        
        Args:
            payload (dict): Contains 'request' (Django request) and 'data' (validated form data)
                - request: Django HTTP request object
                - data: Dictionary with phone_number, amount, reference, description
                
        Returns:
            dict: M-Pesa API response containing CheckoutRequestID and status
        """
        # Extract request and data from payload
        request = payload["request"]
        data = payload["data"]
        
        # Get payment details from validated data
        amount = data["amount"]
        phone_number = data["phone_number"]
        reference = data.get("reference", "Test")  # Default reference if not provided
        description = data.get("description", "Test")  # Default description if not provided
        
        # Prepare STK Push request data according to Safaricom API specification
        req_data = {
            "BusinessShortCode": self.shortcode,      # Business number (paybill/till)
            "Password": self.password,                # Base64 encoded password
            "Timestamp": self.timestamp,              # Request timestamp
            "TransactionType": "CustomerPayBillOnline",  # Transaction type
            "Amount": math.ceil(float(amount)),       # Round up amount to nearest integer
            "PartyA": phone_number,                   # Customer phone number
            "PartyB": self.shortcode,                 # Business number (same as BusinessShortCode)
            "PhoneNumber": phone_number,              # Phone number to receive STK push
            "CallBackURL": self.c2b_callback,         # URL for payment confirmation
            "AccountReference": reference,            # Payment reference
            "TransactionDesc": description,           # Payment description
        }

        # Send STK Push request to Safaricom API
        res = requests.post(
            self.checkout_url, json=req_data, headers=self.headers, timeout=30
        )
        res_data = res.json()
        
        # Log request and response for debugging
        logging.info("Mpesa request data {}".format(req_data))
        logging.info("Mpesa response info {}".format(res_data))

        # Check if request was successful
        if res.ok and res_data.get("ResponseCode") == "0":
            # Create transaction record with all available data
            transaction_data = {
                "phone_number": phone_number,
                "amount": str(amount),
                "reference": reference,
                "description": description,
                "checkout_request_id": res_data["CheckoutRequestID"],  # Unique M-Pesa request ID
                "ip": request.META.get("REMOTE_ADDR"),  # Customer's IP address
                "status": "1"  # Set as Pending initially
            }
            
            # Save transaction to database
            Transaction.objects.create(**transaction_data)
            logging.info("Transaction record created successfully")
        else:
            # Log error if STK push failed
            logging.error("STK push failed: {}".format(res_data))
            
        return res_data

    @Decorators.refreshToken
    def stk_push_query(self, checkout_request_id):
        """
        Query the status of an STK push transaction.
        
        This method checks the current status of a payment request using
        the CheckoutRequestID returned from the initial STK push.
        
        Args:
            checkout_request_id (str): Unique identifier from STK push response
            
        Returns:
            dict: M-Pesa API response with transaction status information
        """
        # Prepare query request data
        req_data = {
            "BusinessShortCode": self.shortcode,
            "Password": self.password,
            "Timestamp": self.timestamp,
            "CheckoutRequestID": checkout_request_id
        }

        try:
            # Send query request to Safaricom API
            res = requests.post(
                self.stk_query_url, json=req_data, headers=self.headers, timeout=30
            )
            res_data = res.json()
            
            # Log query request and response
            logging.info("STK Query request data {}".format(req_data))
            logging.info("STK Query response info {}".format(res_data))
            
            return res_data
        except Exception as e:
            logging.error("STK Query error: {}".format(e))
            # Return error response if query fails
            return {"ResultCode": "1", "ResultDesc": "Query failed", "error": str(e)}

    def check_status(self, data):
        """
        Extract status code from M-Pesa callback data.
        
        Args:
            data (dict): Callback data from Safaricom
            
        Returns:
            str: Status code ("0" = success, "1" = failed/pending)
        """
        try:
            # Navigate through callback data structure to get status
            status = str(data["Body"]["stkCallback"]["ResultCode"])
        except Exception as e:
            logging.error(f"Error extracting status: {e}")
            status = "1"  # Default to failed/pending if structure is unexpected
        return status

    def get_transaction_object(self, data):
        """
        Retrieve or create transaction record from callback data.
        
        Args:
            data (dict): Callback data containing CheckoutRequestID
            
        Returns:
            Transaction: Database transaction object
        """
        # Extract checkout request ID from callback
        checkout_request_id = data["Body"]["stkCallback"]["CheckoutRequestID"]
        
        # Get or create transaction record (should already exist from STK push)
        transaction, _ = Transaction.objects.get_or_create(
            checkout_request_id=checkout_request_id
        )

        return transaction

    def handle_successful_pay(self, data, transaction):
        """
        Process successful payment callback and update transaction record.
        
        Extracts payment details from Safaricom callback and updates the
        transaction record with receipt number and confirmation details.
        
        Args:
            data (dict): Callback data from Safaricom containing payment details
            transaction (Transaction): Database transaction object to update
            
        Returns:
            Transaction: Updated transaction object
        """
        # Extract callback metadata containing payment details
        items = data["Body"]["stkCallback"]["CallbackMetadata"]["Item"]
        
        # Initialize variables for payment details
        amount = None
        receipt_no = None
        phone_number = None
        transaction_date = None
        
        # Parse callback items to extract payment information
        for item in items:
            if item["Name"] == "Amount":
                amount = item["Value"]
            elif item["Name"] == "MpesaReceiptNumber":
                receipt_no = item["Value"]  # M-Pesa transaction receipt
            elif item["Name"] == "PhoneNumber":
                phone_number = item["Value"]
            elif item["Name"] == "TransactionDate":
                transaction_date = item["Value"]

        # Update transaction with callback data
        if amount:
            transaction.amount = str(amount)
        if phone_number:
            # Convert phone number to PhoneNumber object
            transaction.phone_number = PhoneNumber(raw_input=str(phone_number))
        if receipt_no:
            transaction.receipt_no = receipt_no  # Store M-Pesa receipt number
            
        # Mark transaction as complete
        transaction.status = "0"  # "0" = Complete status
        
        return transaction

    def callback_handler(self, data):
        """
        Main callback handler for processing M-Pesa payment confirmations.
        
        This method is called when Safaricom sends payment status updates.
        It processes the callback data and updates transaction records accordingly.
        
        Args:
            data (dict): JSON callback data from Safaricom
            
        Returns:
            Response: HTTP response to acknowledge callback receipt
        """
        # Extract status from callback data
        status = self.check_status(data)
        
        # Get the associated transaction record
        transaction = self.get_transaction_object(data)
        
        if status == "0":
            # Payment was successful - process confirmation
            self.handle_successful_pay(data, transaction)
            logging.info("Payment successful for CheckoutRequestID: {}".format(
                data["Body"]["stkCallback"]["CheckoutRequestID"]
            ))
        else:
            # Payment failed or was cancelled
            transaction.status = "1"  # Keep as pending/failed
            logging.warning("Payment failed for CheckoutRequestID: {} with status: {}".format(
                data["Body"]["stkCallback"]["CheckoutRequestID"], status
            ))

        # Save the updated transaction to database
        transaction.save()

        # Serialize transaction data for logging
        transaction_data = TransactionSerializer(transaction).data
        logging.info("Transaction completed info {}".format(transaction_data))

        # Return success response to Safaricom (required to acknowledge callback)
        return Response({"status": "ok", "code": 0}, status=200)