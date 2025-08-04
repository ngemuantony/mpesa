import json
import logging

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import MpesaCheckoutSerializer, TransactionSerializer
from .stk_push import MpesaGateWay
from .callback_security import SafaricomIPWhitelist


def get_gateway():
    """Lazy initialization of MpesaGateWay to avoid startup issues"""
    if not hasattr(get_gateway, '_gateway'):
        get_gateway._gateway = MpesaGateWay()
    return get_gateway._gateway


@authentication_classes([])
@permission_classes((AllowAny,))
class MpesaCheckout(APIView):
    serializer = MpesaCheckoutSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            payload = {"data":serializer.validated_data, "request":request}
            res = get_gateway().stk_push_request(payload)
            return Response(res, status=200)

@authentication_classes([])
@permission_classes((AllowAny,))
class MpesaStkQuery(APIView):
    def post(self, request, *args, **kwargs):
        checkout_request_id = request.data.get('checkout_request_id')
        if not checkout_request_id:
            return Response(
                {"error": "checkout_request_id is required"}, 
                status=400
            )
        
        # Query M-Pesa API
        res = get_gateway().stk_push_query(checkout_request_id)
        
        # Also return local transaction data if available
        try:
            from .models import Transaction
            transaction = Transaction.objects.get(checkout_request_id=checkout_request_id)
            transaction_data = TransactionSerializer(transaction).data
            res['local_transaction'] = transaction_data
        except Transaction.DoesNotExist:
            res['local_transaction'] = None
        
        return Response(res, status=200)

@authentication_classes([])
@permission_classes((SafaricomIPWhitelist,))
@method_decorator(csrf_exempt, name='dispatch')
class MpesaCallBack(APIView):
    def get(self, request):
        return Response({"status": "OK"}, status=200)

    def post(self, request, *args, **kwargs):
        logging.info("{}".format("Callback from MPESA"))
        data = request.body
        return get_gateway().callback_handler(json.loads(data))