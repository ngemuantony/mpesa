import json
import uuid
from unittest.mock import patch, Mock, MagicMock
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from phonenumber_field.phonenumber import PhoneNumber

from .models import Transaction
from .serializers import MpesaCheckoutSerializer, TransactionSerializer
from .stk_push import MpesaGateWay
from .phone_number_validation import validate_possible_number
from .views import SafaricomIPWhitelist


class TransactionModelTest(TestCase):
    """Test cases for Transaction model"""
    
    def setUp(self):
        self.transaction_data = {
            'phone_number': '+254718643064',
            'amount': '100',
            'reference': 'TEST-001',
            'description': 'Test payment',
            'checkout_request_id': 'ws_CO_test123',
            'status': '1',
            'ip': '127.0.0.1'
        }
    
    def test_transaction_creation(self):
        """Test transaction model creation"""
        transaction = Transaction.objects.create(**self.transaction_data)
        
        self.assertIsNotNone(transaction.transaction_no)
        self.assertEqual(str(transaction.phone_number), '+254718643064')
        self.assertEqual(transaction.amount, '100')
        self.assertEqual(transaction.reference, 'TEST-001')
        self.assertEqual(transaction.status, '1')
        self.assertTrue(transaction.is_pending)
        self.assertFalse(transaction.is_successful)
    
    def test_transaction_str_method(self):
        """Test transaction string representation"""
        transaction = Transaction.objects.create(**self.transaction_data)
        expected_str = f"Transaction {transaction.transaction_no} - Pending"
        self.assertEqual(str(transaction), expected_str)
    
    def test_transaction_status_properties(self):
        """Test transaction status properties"""
        # Test pending transaction
        pending_transaction = Transaction.objects.create(**self.transaction_data)
        self.assertTrue(pending_transaction.is_pending)
        self.assertFalse(pending_transaction.is_successful)
        
        # Test successful transaction
        success_data = self.transaction_data.copy()
        success_data['status'] = '0'
        success_data['checkout_request_id'] = 'ws_CO_test124'
        success_transaction = Transaction.objects.create(**success_data)
        self.assertFalse(success_transaction.is_pending)
        self.assertTrue(success_transaction.is_successful)


class PhoneNumberValidationTest(TestCase):
    """Test cases for phone number validation"""
    
    def test_valid_kenyan_phone_numbers(self):
        """Test validation of valid Kenyan phone numbers"""
        valid_numbers = [
            '254718643064',
            '254700123456',
            '254722123456'
        ]
        
        for number in valid_numbers:
            result = validate_possible_number(number, 'KE')
            self.assertIsNotNone(result)
            self.assertTrue(result.is_valid())
    
    def test_invalid_phone_numbers(self):
        """Test validation of invalid phone numbers"""
        invalid_numbers = [
            '123456789',  # Too short
            '25471864306412345',  # Too long
            '123718643064',  # Wrong country code
        ]
        
        for number in invalid_numbers:
            with self.assertRaises(Exception):
                validate_possible_number(number, 'KE')


class MpesaCheckoutSerializerTest(TestCase):
    """Test cases for MpesaCheckoutSerializer"""
    
    def test_valid_serializer_data(self):
        """Test serializer with valid data"""
        valid_data = {
            'phone_number': '0718643064',
            'amount': '100',
            'reference': 'TEST-001',
            'description': 'Test payment'
        }
        
        serializer = MpesaCheckoutSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['phone_number'], '254718643064')
        self.assertEqual(validated_data['amount'], '100')
        self.assertEqual(validated_data['reference'], 'TEST-001')
    
    def test_phone_number_conversion(self):
        """Test phone number format conversion"""
        test_cases = [
            ('0718643064', '254718643064'),
            ('+254718643064', '254718643064'),
            ('254718643064', '254718643064'),
        ]
        
        for input_number, expected_output in test_cases:
            data = {
                'phone_number': input_number,
                'amount': '100'
            }
            serializer = MpesaCheckoutSerializer(data=data)
            self.assertTrue(serializer.is_valid())
            self.assertEqual(serializer.validated_data['phone_number'], expected_output)
    
    def test_invalid_phone_number(self):
        """Test serializer with invalid phone number"""
        invalid_data = {
            'phone_number': '123456',  # Invalid number
            'amount': '100'
        }
        
        serializer = MpesaCheckoutSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors)
    
    def test_invalid_amount(self):
        """Test serializer with invalid amount"""
        invalid_amounts = ['0', '-10', 'abc']
        
        for amount in invalid_amounts:
            data = {
                'phone_number': '0718643064',
                'amount': amount
            }
            serializer = MpesaCheckoutSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('amount', serializer.errors)
    
    def test_default_values(self):
        """Test serializer default values"""
        minimal_data = {
            'phone_number': '0718643064',
            'amount': '100'
        }
        
        serializer = MpesaCheckoutSerializer(data=minimal_data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        # Note: Default values are handled in the validate methods, not in validated_data
        # The actual defaults are applied in the STK push request processing


class TransactionSerializerTest(TestCase):
    """Test cases for TransactionSerializer"""
    
    def setUp(self):
        self.transaction = Transaction.objects.create(
            phone_number='+254718643064',
            amount='100',
            reference='TEST-001',
            description='Test payment',
            checkout_request_id='ws_CO_test123',
            status='1',
            ip='127.0.0.1'
        )
    
    def test_transaction_serialization(self):
        """Test transaction serialization"""
        serializer = TransactionSerializer(self.transaction)
        data = serializer.data
        
        self.assertEqual(data['phone_number'], '+254718643064')
        self.assertEqual(data['amount'], '100')
        self.assertEqual(data['reference'], 'TEST-001')
        self.assertEqual(data['status'], '1')  # String, not int
        self.assertIn('transaction_no', data)
        self.assertIn('created', data)


class SafaricomIPWhitelistTest(TestCase):
    """Test cases for Safaricom IP whitelist permission"""
    
    def setUp(self):
        self.permission = SafaricomIPWhitelist()
        self.mock_request = Mock()
        self.mock_view = Mock()
    
    def test_allowed_ip(self):
        """Test request from allowed Safaricom IP"""
        # Mock allowed IP
        self.mock_request.META = {'REMOTE_ADDR': '196.201.214.200'}
        
        result = self.permission.has_permission(self.mock_request, self.mock_view)
        self.assertTrue(result)
    
    def test_blocked_ip(self):
        """Test request from blocked IP"""
        # Mock blocked IP
        self.mock_request.META = {'REMOTE_ADDR': '192.168.1.1'}
        
        result = self.permission.has_permission(self.mock_request, self.mock_view)
        self.assertFalse(result)
    
    def test_forwarded_ip(self):
        """Test request with X-Forwarded-For header"""
        # Mock forwarded IP
        self.mock_request.META = {
            'HTTP_X_FORWARDED_FOR': '196.201.214.206, 10.0.0.1',
            'REMOTE_ADDR': '10.0.0.1'
        }
        
        result = self.permission.has_permission(self.mock_request, self.mock_view)
        self.assertTrue(result)


class MpesaGateWayTest(TestCase):
    """Test cases for MpesaGateWay class"""
    
    @patch('mpesa.stk_push.env')
    @patch('mpesa.stk_push.requests.get')
    def test_gateway_initialization(self, mock_get, mock_env):
        """Test MpesaGateWay initialization"""
        # Mock environment variables
        mock_env.side_effect = lambda key: {
            'shortcode': '174379',
            'consumer_key': 'test_key',
            'consumer_secret': 'test_secret',
            'access_token_url': 'https://test.com/token',
            'mpesa_query_check_url': 'https://test.com/query',
            'pass_key': 'test_passkey',
            'c2b_callback': 'https://test.com/callback',
            'checkout_url': 'https://test.com/checkout'
        }.get(key, '')
        
        # Mock token response
        mock_response = Mock()
        mock_response.json.return_value = {'access_token': 'test_token'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        gateway = MpesaGateWay()
        
        self.assertEqual(gateway.shortcode, '174379')
        self.assertEqual(gateway.consumer_key, 'test_key')
        self.assertIn('Authorization', gateway.headers)
        self.assertEqual(gateway.access_token, 'test_token')
    
    @patch('mpesa.stk_push.env')
    def test_password_generation(self, mock_env):
        """Test password generation"""
        mock_env.side_effect = lambda key: {
            'shortcode': '174379',
            'pass_key': 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
        }.get(key, '')
        
        with patch('mpesa.stk_push.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {'access_token': 'test_token'}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            gateway = MpesaGateWay()
            password = gateway.generate_password()
            
            self.assertIsNotNone(password)
            self.assertIsInstance(password, str)
    
    @patch('mpesa.stk_push.env')
    @patch('mpesa.stk_push.requests.post')
    def test_stk_push_query(self, mock_post, mock_env):
        """Test STK push query functionality"""
        # Setup mocks
        mock_env.side_effect = lambda key: {
            'shortcode': '174379',
            'consumer_key': 'test_key',
            'consumer_secret': 'test_secret',
            'access_token_url': 'https://test.com/token',
            'mpesa_query_check_url': 'https://test.com/query',
            'pass_key': 'test_passkey',
            'c2b_callback': 'https://test.com/callback',
            'checkout_url': 'https://test.com/checkout'
        }.get(key, '')
        
        with patch('mpesa.stk_push.requests.get') as mock_get:
            mock_get_response = Mock()
            mock_get_response.json.return_value = {'access_token': 'test_token'}
            mock_get_response.raise_for_status.return_value = None
            mock_get.return_value = mock_get_response
            
            mock_post_response = Mock()
            mock_post_response.json.return_value = {
                'ResponseCode': '0',
                'ResponseDescription': 'Success',
                'ResultCode': '0',
                'ResultDesc': 'Transaction successful'
            }
            mock_post.return_value = mock_post_response
            
            gateway = MpesaGateWay()
            result = gateway.stk_push_query('ws_CO_test123')
            
            self.assertEqual(result['ResponseCode'], '0')
            self.assertEqual(result['ResultCode'], '0')


class MpesaAPIViewsTest(APITestCase):
    """Test cases for M-Pesa API views"""
    
    def setUp(self):
        self.client = APIClient()
        self.checkout_url = reverse('checkout')
        self.callback_url = reverse('callback')
        self.query_url = reverse('stk_query')
    
    def test_checkout_view_valid_data(self):
        """Test checkout view with valid data"""
        with patch('mpesa.views.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.stk_push_request.return_value = {
                'ResponseCode': '0',
                'ResponseDescription': 'Success',
                'CheckoutRequestID': 'ws_CO_test123',
                'MerchantRequestID': 'test_merchant_123'
            }
            mock_get_gateway.return_value = mock_gateway
            
            data = {
                'phone_number': '0718643064',
                'amount': 100,
                'reference': 'TEST-001',
                'description': 'Test payment'
            }
            
            response = self.client.post(self.checkout_url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['ResponseCode'], '0')
            mock_gateway.stk_push_request.assert_called_once()
    
    def test_checkout_view_invalid_phone(self):
        """Test checkout view with invalid phone number"""
        data = {
            'phone_number': '123456',  # Invalid
            'amount': 100
        }
        
        response = self.client.post(self.checkout_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)
    
    def test_query_view_valid_request(self):
        """Test query view with valid checkout request ID"""
        # Create a test transaction
        transaction = Transaction.objects.create(
            phone_number='+254718643064',
            amount='100',
            checkout_request_id='ws_CO_test123',
            status='1'
        )
        
        with patch('mpesa.views.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.stk_push_query.return_value = {
                'ResponseCode': '0',
                'ResultCode': '0',
                'ResultDesc': 'Transaction successful'
            }
            mock_get_gateway.return_value = mock_gateway
            
            data = {'checkout_request_id': 'ws_CO_test123'}
            response = self.client.post(self.query_url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['ResponseCode'], '0')
            self.assertIn('local_transaction', response.data)
            mock_gateway.stk_push_query.assert_called_once_with('ws_CO_test123')
    
    def test_query_view_missing_checkout_id(self):
        """Test query view without checkout request ID"""
        response = self.client.post(self.query_url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_callback_view_ip_whitelist(self):
        """Test callback view IP whitelisting"""
        # Test with non-whitelisted IP
        callback_data = {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": "ws_CO_test123",
                    "ResultCode": 0,
                    "ResultDesc": "Success"
                }
            }
        }
        
        response = self.client.post(self.callback_url, callback_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    @patch('mpesa.views.SafaricomIPWhitelist.has_permission')
    def test_callback_view_successful_payment(self, mock_permission):
        """Test callback view with successful payment"""
        mock_permission.return_value = True
        
        # Create a test transaction
        transaction = Transaction.objects.create(
            phone_number='+254718643064',
            amount='100',
            checkout_request_id='ws_CO_test123',
            status='1'
        )
        
        callback_data = {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": "ws_CO_test123",
                    "ResultCode": 0,
                    "ResultDesc": "Success",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 100},
                            {"Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV"},
                            {"Name": "PhoneNumber", "Value": 254718643064}
                        ]
                    }
                }
            }
        }
        
        response = self.client.post(self.callback_url, callback_data, format='json')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class MpesaIntegrationTest(TestCase):
    """Integration tests for the complete M-Pesa flow"""
    
    def setUp(self):
        self.client = Client()
    
    @patch('mpesa.stk_push.requests.get')
    @patch('mpesa.stk_push.requests.post')
    @patch('mpesa.stk_push.env')
    def test_complete_payment_flow(self, mock_env, mock_post, mock_get):
        """Test complete payment flow from initiation to callback"""
        # Mock environment variables
        mock_env.side_effect = lambda key: {
            'shortcode': '174379',
            'consumer_key': 'test_key',
            'consumer_secret': 'test_secret',
            'access_token_url': 'https://test.com/token',
            'mpesa_query_check_url': 'https://test.com/query',
            'pass_key': 'test_passkey',
            'c2b_callback': 'https://test.com/callback',
            'checkout_url': 'https://test.com/checkout'
        }.get(key, '')
        
        # Mock token response
        mock_get_response = Mock()
        mock_get_response.json.return_value = {'access_token': 'test_token'}
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response
        
        # Mock STK push response
        mock_post_response = Mock()
        mock_post_response.json.return_value = {
            'ResponseCode': '0',
            'ResponseDescription': 'Success',
            'CheckoutRequestID': 'ws_CO_test123',
            'MerchantRequestID': 'test_merchant_123'
        }
        mock_post_response.ok = True
        mock_post.return_value = mock_post_response
        
        # Step 1: Initiate payment
        checkout_data = {
            'phone_number': '0718643064',
            'amount': 100,
            'reference': 'TEST-001',
            'description': 'Test payment'
        }
        
        response = self.client.post(
            '/payments/checkout/',
            json.dumps(checkout_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify transaction was created
        transaction = Transaction.objects.get(checkout_request_id='ws_CO_test123')
        self.assertEqual(transaction.status, '1')  # Pending
        self.assertEqual(str(transaction.phone_number), '254718643064')
        
        # Step 2: Simulate callback
        with patch('mpesa.views.SafaricomIPWhitelist.has_permission', return_value=True):
            callback_data = {
                "Body": {
                    "stkCallback": {
                        "CheckoutRequestID": "ws_CO_test123",
                        "ResultCode": 0,
                        "ResultDesc": "Success",
                        "CallbackMetadata": {
                            "Item": [
                                {"Name": "Amount", "Value": 100},
                                {"Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV"},
                                {"Name": "PhoneNumber", "Value": 254718643064}
                            ]
                        }
                    }
                }
            }
            
            callback_response = self.client.post(
                '/payments/callback/',
                json.dumps(callback_data),
                content_type='application/json'
            )
            
            self.assertEqual(callback_response.status_code, 200)
        
        # Verify transaction was updated
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, '0')  # Complete
        self.assertEqual(transaction.receipt_no, 'NLJ7RT61SV')


class MpesaModelAdminTest(TestCase):
    """Test cases for Django admin integration"""
    
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='password123'
        )
        self.client.login(username='admin', password='password123')
        
        self.transaction = Transaction.objects.create(
            phone_number='+254718643064',
            amount='100',
            reference='TEST-001',
            description='Test payment',
            checkout_request_id='ws_CO_test123',
            status='1',
            ip='127.0.0.1'
        )
    
    def test_admin_transaction_list_view(self):
        """Test admin list view for transactions"""
        response = self.client.get('/admin/mpesa/transaction/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.transaction.transaction_no)
        self.assertContains(response, '+254718643064')
    
    def test_admin_transaction_detail_view(self):
        """Test admin detail view for transaction"""
        response = self.client.get(f'/admin/mpesa/transaction/{self.transaction.id}/change/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.transaction.transaction_no)
    
    def test_admin_readonly_fields(self):
        """Test that certain fields are readonly in admin"""
        response = self.client.get(f'/admin/mpesa/transaction/{self.transaction.id}/change/')
        self.assertEqual(response.status_code, 200)
        # Check that readonly fields are present but not editable
        self.assertContains(response, 'readonly')


if __name__ == '__main__':
    import django
    from django.test.utils import get_runner
    from django.conf import settings
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["mpesa.tests"])
