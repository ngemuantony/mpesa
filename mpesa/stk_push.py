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

logging = logging.getLogger("default")

class MpesaGateWay:
    shortcode = None
    consumer_key = None
    consumer_secret = None
    access_token_url = None
    access_token = None
    access_token_expiration = None
    checkout_url = None
    timestamp = None


    def __init__(self):
        now = datetime.now()
        self.shortcode = env("shortcode")
        self.consumer_key = env("consumer_key")
        self.consumer_secret = env("consumer_secret")
        self.access_token_url = env("access_token_url")
        self.stk_query_url = env("mpesa_query_check_url")  # Add STK query URL
        self.headers = {}  # Initialize headers

        self.password = self.generate_password()
        self.c2b_callback = env("c2b_callback")
        self.checkout_url = env("checkout_url")

        try:
            self.access_token = self.getAccessToken()
            if self.access_token is None:
                raise Exception("Request for access token failed.")
        except Exception as e:
            logging.error("Error {}".format(e))
            # Set default headers even if token fails
            self.headers = {"Authorization": "Bearer "}
        else:
            self.access_token_expiration = time.time() + 3400

    def getAccessToken(self):
        try:
            res = requests.get(
                self.access_token_url,
                auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
            )
            res.raise_for_status()  # Raise an exception for bad status codes
            token_data = res.json()
            token = token_data.get("access_token")
            if not token:
                raise Exception("No access token in response")
            self.headers = {"Authorization": "Bearer %s" % token}
            return token
        except Exception as err:
            logging.error("Error getting access token: {}".format(err))
            self.headers = {"Authorization": "Bearer "}  # Set empty bearer token
            raise err

    class Decorators:
        @staticmethod
        def refreshToken(decorated):
            def wrapper(gateway, *args, **kwargs):
                if (
                    gateway.access_token_expiration
                    and time.time() > gateway.access_token_expiration
                ):
                    try:
                        token = gateway.getAccessToken()
                        gateway.access_token = token
                    except Exception as e:
                        logging.error("Failed to refresh token: {}".format(e))
                        # Continue with existing token
                return decorated(gateway, *args, **kwargs)

            return wrapper


    def generate_password(self):
        """Generates mpesa api password using the provided shortcode and passkey"""
        now = datetime.now()
        self.timestamp = now.strftime("%Y%m%d%H%M%S")
        password_str = env("shortcode") + env("pass_key") + self.timestamp
        password_bytes = password_str.encode("ascii")
        return base64.b64encode(password_bytes).decode("utf-8")

    @Decorators.refreshToken
    def stk_push_request(self, payload):
        request = payload["request"]
        data = payload["data"]
        amount = data["amount"]
        phone_number = data["phone_number"]
        reference = data.get("reference", "Test")
        description = data.get("description", "Test")
        
        req_data = {
            "BusinessShortCode": self.shortcode,
            "Password": self.password,
            "Timestamp": self.timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": math.ceil(float(amount)),
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self.c2b_callback,
            "AccountReference": reference,
            "TransactionDesc": description,
        }

        res = requests.post(
            self.checkout_url, json=req_data, headers=self.headers, timeout=30
        )
        res_data = res.json()
        logging.info("Mpesa request data {}".format(req_data))
        logging.info("Mpesa response info {}".format(res_data))

        if res.ok and res_data.get("ResponseCode") == "0":
            # Create transaction record with all available data
            transaction_data = {
                "phone_number": phone_number,
                "amount": str(amount),
                "reference": reference,
                "description": description,
                "checkout_request_id": res_data["CheckoutRequestID"],
                "ip": request.META.get("REMOTE_ADDR"),
                "status": "1"  # Pending
            }
            
            Transaction.objects.create(**transaction_data)
            logging.info("Transaction record created successfully")
        else:
            logging.error("STK push failed: {}".format(res_data))
            
        return res_data

    @Decorators.refreshToken
    def stk_push_query(self, checkout_request_id):
        """Query the status of an STK push transaction"""
        req_data = {
            "BusinessShortCode": self.shortcode,
            "Password": self.password,
            "Timestamp": self.timestamp,
            "CheckoutRequestID": checkout_request_id
        }

        try:
            res = requests.post(
                self.stk_query_url, json=req_data, headers=self.headers, timeout=30
            )
            res_data = res.json()
            logging.info("STK Query request data {}".format(req_data))
            logging.info("STK Query response info {}".format(res_data))
            return res_data
        except Exception as e:
            logging.error("STK Query error: {}".format(e))
            return {"ResultCode": "1", "ResultDesc": "Query failed", "error": str(e)}

    def check_status(self, data):
        try:
            status = str(data["Body"]["stkCallback"]["ResultCode"])
        except Exception as e:
            logging.error(f"Error: {e}")
            status = "1"  # Return string instead of int
        return status

    def get_transaction_object(self, data):
        checkout_request_id = data["Body"]["stkCallback"]["CheckoutRequestID"]
        transaction, _ = Transaction.objects.get_or_create(
            checkout_request_id=checkout_request_id
        )

        return transaction

    def handle_successful_pay(self, data, transaction):
        items = data["Body"]["stkCallback"]["CallbackMetadata"]["Item"]
        amount = None
        receipt_no = None
        phone_number = None
        transaction_date = None
        
        for item in items:
            if item["Name"] == "Amount":
                amount = item["Value"]
            elif item["Name"] == "MpesaReceiptNumber":
                receipt_no = item["Value"]
            elif item["Name"] == "PhoneNumber":
                phone_number = item["Value"]
            elif item["Name"] == "TransactionDate":
                transaction_date = item["Value"]

        # Update transaction with callback data
        if amount:
            transaction.amount = str(amount)
        if phone_number:
            transaction.phone_number = PhoneNumber(raw_input=str(phone_number))
        if receipt_no:
            transaction.receipt_no = receipt_no
            
        transaction.status = "0"  # Set to complete (string)
        
        return transaction

    def callback_handler(self, data):
        status = self.check_status(data)
        transaction = self.get_transaction_object(data)
        
        if status == "0":
            # Successful payment
            self.handle_successful_pay(data, transaction)
            logging.info("Payment successful for CheckoutRequestID: {}".format(
                data["Body"]["stkCallback"]["CheckoutRequestID"]
            ))
        else:
            # Failed payment
            transaction.status = "1"
            logging.warning("Payment failed for CheckoutRequestID: {} with status: {}".format(
                data["Body"]["stkCallback"]["CheckoutRequestID"], status
            ))

        # Save the transaction
        transaction.save()

        transaction_data = TransactionSerializer(transaction).data
        logging.info("Transaction completed info {}".format(transaction_data))

        return Response({"status": "ok", "code": 0}, status=200)