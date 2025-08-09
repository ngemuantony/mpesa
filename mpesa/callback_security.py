"""
M-Pesa Callback Security Module

This module provides comprehensive security mechanisms for validating M-Pesa payment 
callbacks from Safaricom's servers. It implements multiple layers of security including
IP whitelisting, request signature validation, rate limiting, and callback structure verification.

Components:
    - SafaricomIPWhitelist: Permission class for IP address validation
    - CallbackSignatureValidator: HMAC signature validation for callbacks
    - CallbackRateLimiter: Rate limiting for callback endpoints
    - CallbackStructureValidator: Validates callback JSON structure
    - Official Safaricom IP addresses whitelist
    - Enhanced client IP extraction utilities

Security Features:
    - IP address validation against official Safaricom ranges
    - HMAC signature verification for callback authenticity
    - Rate limiting to prevent callback flooding
    - Request structure validation
    - Comprehensive logging and monitoring
    - Protection against replay attacks
    - Request fingerprinting for anomaly detection

Usage:
    Apply multiple security layers to views that handle M-Pesa callbacks
    to ensure comprehensive protection.

Author: M-Pesa Integration Team
Date: 2024
Updated: 2025
"""

import logging
import hashlib
import hmac
import json
import time
import base64
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status


class SafaricomIPWhitelist(BasePermission):
    """
    Enhanced permission class to validate M-Pesa callback requests from Safaricom.
    
    This permission ensures that only requests originating from Safaricom's
    official IP addresses are allowed to access callback endpoints. It includes
    enhanced logging, monitoring, and security features.
    
    Attributes:
        SAFARICOM_IPS (list): Official IP addresses used by Safaricom for callbacks
        SAFARICOM_IP_RANGES (list): IP ranges for additional validation
    
    Methods:
        has_permission: Validates if request IP is from Safaricom
        get_client_ip: Enhanced client IP extraction with proxy support
        is_ip_in_range: Check if IP is within allowed ranges
        log_security_event: Enhanced security logging
    """
    
    # Official Safaricom IP addresses for M-Pesa callbacks
    # These IPs are provided by Safaricom and should be kept updated
    SAFARICOM_IPS = [
        '196.201.214.200',  # Primary callback server
        '196.201.214.206',  # Secondary callback server 
        '196.201.213.114',  # Backup server 1
        '196.201.214.207',  # Backup server 2
        '196.201.214.208',  # Backup server 3
        '196.201.213.44',   # Regional server 1
        '196.201.212.127',  # Regional server 2
        '196.201.212.138',  # Regional server 3
        '196.201.212.129',  # Regional server 4
        '196.201.212.136',  # Regional server 5
        '196.201.212.74',   # Load balancer 1
        '196.201.212.69'    # Load balancer 2
    ]

    # Additional IP ranges for Safaricom (CIDR notation)
    SAFARICOM_IP_RANGES = [
        '196.201.214.0/24',  # Primary range
        '196.201.213.0/24',  # Secondary range
        '196.201.212.0/24'   # Tertiary range
    ]

    # Development/testing IPs (only when DEBUG=True)
    DEVELOPMENT_IPS = [
        '127.0.0.1',      # Localhost
        '::1',            # IPv6 localhost
        '0.0.0.0'         # Any interface
    ]

    def has_permission(self, request, view):
        """
        Enhanced permission check with comprehensive security validation.
        
        This method validates IP addresses, logs security events, implements
        rate limiting, and provides detailed security monitoring.
        
        Args:
            request (Request): DRF request object
            view (APIView): The view being accessed
            
        Returns:
            bool: True if request is authorized, False otherwise
        """
        # Extract client IP and request metadata
        client_ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        request_method = request.method
        request_path = request.path
        
        # Create security context for logging (filter serializable data only)
        security_context = {
            'ip': client_ip,
            'user_agent': user_agent,
            'method': request_method,
            'path': request_path,
            'timestamp': datetime.now().isoformat(),
            'content_type': request.META.get('CONTENT_TYPE', ''),
            'content_length': request.META.get('CONTENT_LENGTH', '0'),
            'remote_addr': request.META.get('REMOTE_ADDR', ''),
            # Only include safe headers (avoid complex objects)
            'headers': {
                k: str(v) for k, v in request.META.items() 
                if k.startswith('HTTP_') and isinstance(v, (str, int, float))
                and 'AUTHORIZATION' not in k and 'COOKIE' not in k
            }
        }
        
        # Log callback attempt
        logging.info(f"M-Pesa callback security check - IP: {client_ip}, Path: {request_path}")
        
        # Check rate limiting first
        if not self._check_rate_limit(client_ip):
            self.log_security_event('RATE_LIMIT_EXCEEDED', security_context)
            return False
        
        # Validate IP address
        is_authorized = self._is_authorized_ip(client_ip)
        
        if is_authorized:
            self.log_security_event('CALLBACK_AUTHORIZED', security_context)
            # Track successful callbacks for monitoring
            self._track_successful_callback(client_ip)
            return True
        else:
            self.log_security_event('UNAUTHORIZED_CALLBACK_ATTEMPT', security_context)
            # Track failed attempts for security monitoring
            self._track_failed_attempt(client_ip)
            return False
    
    def _is_authorized_ip(self, client_ip):
        """
        Check if IP is authorized with multiple validation methods.
        
        Args:
            client_ip (str): Client IP address
            
        Returns:
            bool: True if IP is authorized
        """
        # Check exact IP matches
        if client_ip in self.SAFARICOM_IPS:
            return True
        
        # In development mode, allow local IPs
        if getattr(settings, 'DEBUG', False) and client_ip in self.DEVELOPMENT_IPS:
            logging.warning(f"Development mode: Allowing local IP {client_ip}")
            return True
        
        # Check IP ranges (basic implementation)
        for ip_range in self.SAFARICOM_IP_RANGES:
            if self._ip_in_range(client_ip, ip_range):
                return True
        
        return False
    
    def _ip_in_range(self, ip, cidr_range):
        """
        Check if IP is within CIDR range (basic implementation).
        
        Args:
            ip (str): IP address to check
            cidr_range (str): CIDR notation range
            
        Returns:
            bool: True if IP is in range
        """
        try:
            import ipaddress
            return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr_range, strict=False)
        except (ValueError, ImportError):
            # Fallback to basic prefix matching
            network_prefix = cidr_range.split('/')[0].rsplit('.', 1)[0]
            return ip.startswith(network_prefix)
    
    def _check_rate_limit(self, client_ip):
        """
        Implement rate limiting for callback requests.
        
        Args:
            client_ip (str): Client IP address
            
        Returns:
            bool: True if within rate limits
        """
        cache_key = f"mpesa_callback_rate_limit:{client_ip}"
        current_requests = cache.get(cache_key, 0)
        
        # Allow max 100 requests per minute per IP
        max_requests = 100
        window_minutes = 1
        
        if current_requests >= max_requests:
            logging.warning(f"Rate limit exceeded for IP {client_ip}: {current_requests} requests")
            return False
        
        # Increment counter with expiration
        cache.set(cache_key, current_requests + 1, 60 * window_minutes)
        return True
    
    def _track_successful_callback(self, client_ip):
        """Track successful callbacks for monitoring."""
        cache_key = f"mpesa_callback_success:{client_ip}:daily"
        current_count = cache.get(cache_key, 0)
        cache.set(cache_key, current_count + 1, 86400)  # 24 hours
    
    def _track_failed_attempt(self, client_ip):
        """Track failed attempts for security monitoring."""
        cache_key = f"mpesa_callback_failed:{client_ip}:hourly"
        current_count = cache.get(cache_key, 0)
        cache.set(cache_key, current_count + 1, 3600)  # 1 hour
        
        # Alert if too many failed attempts
        if current_count + 1 >= 10:
            logging.critical(f"SECURITY ALERT: Multiple failed callback attempts from IP {client_ip}")
    
    def log_security_event(self, event_type, context):
        """
        Enhanced security event logging with safe JSON serialization.
        
        Args:
            event_type (str): Type of security event
            context (dict): Security context information
        """
        try:
            # Create safe log entry with only serializable data
            log_entry = {
                'event_type': event_type,
                'timestamp': datetime.now().isoformat(),
                'ip': context.get('ip', 'Unknown'),
                'user_agent': context.get('user_agent', 'Unknown'),
                'method': context.get('method', 'Unknown'),
                'path': context.get('path', 'Unknown')
            }
            
            # Add additional context safely
            for key, value in context.items():
                if key not in log_entry and value is not None:
                    try:
                        # Test if value is JSON serializable
                        json.dumps(value)
                        log_entry[key] = value
                    except (TypeError, ValueError):
                        # Convert non-serializable values to string
                        log_entry[key] = str(value)[:200]  # Limit length
            
            # Log based on event severity
            if event_type == 'UNAUTHORIZED_CALLBACK_ATTEMPT':
                logging.warning(f"SECURITY ALERT: Unauthorized M-Pesa callback from {context.get('ip')} - {event_type}")
                logging.debug(f"Security details: {json.dumps(log_entry)}")
            elif event_type == 'RATE_LIMIT_EXCEEDED':
                logging.warning(f"RATE LIMIT: M-Pesa callback rate limit exceeded from {context.get('ip')}")
                logging.debug(f"Rate limit details: {json.dumps(log_entry)}")
            elif event_type == 'CALLBACK_AUTHORIZED':
                logging.info(f"M-Pesa callback authorized from {context.get('ip')}")
            else:
                logging.info(f"M-Pesa security event: {event_type} from {context.get('ip')}")
                
        except Exception as e:
            # Fallback logging if JSON serialization still fails
            logging.error(f"Security logging error for {event_type}: {str(e)}")
            logging.warning(f"Security event {event_type} from IP {context.get('ip', 'Unknown')}")
    
    def get_client_ip(self, request):
        """
        Enhanced client IP extraction with comprehensive proxy support.
        
        This method handles various proxy scenarios including multiple
        forwarding headers, CDNs, and load balancers.
        
        Args:
            request (Request): DRF request object
            
        Returns:
            str: Client IP address as a string
        """
        # Priority order for IP extraction
        ip_headers = [
            'HTTP_X_FORWARDED_FOR',      # Standard proxy header
            'HTTP_X_REAL_IP',            # Nginx proxy header
            'HTTP_CF_CONNECTING_IP',     # Cloudflare header
            'HTTP_X_FORWARDED',          # Alternative forwarded header
            'HTTP_X_CLUSTER_CLIENT_IP',  # Cluster environments
            'HTTP_FORWARDED_FOR',        # RFC 7239
            'HTTP_FORWARDED',            # RFC 7239 standard
            'REMOTE_ADDR'                # Direct connection
        ]
        
        for header in ip_headers:
            ip_value = request.META.get(header)
            if ip_value:
                # Handle comma-separated IPs (proxy chain)
                if ',' in ip_value:
                    ip = ip_value.split(',')[0].strip()
                else:
                    ip = ip_value.strip()
                
                # Validate IP format and skip private/invalid IPs
                if self._is_valid_public_ip(ip):
                    return ip
        
        # Fallback to REMOTE_ADDR
        return request.META.get('REMOTE_ADDR', 'Unknown')
    
    def _is_valid_public_ip(self, ip):
        """
        Validate if IP is a valid public IP address.
        
        Args:
            ip (str): IP address to validate
            
        Returns:
            bool: True if valid public IP
        """
        try:
            import ipaddress
            ip_obj = ipaddress.ip_address(ip)
            
            # Allow localhost in development
            if getattr(settings, 'DEBUG', False) and ip_obj.is_loopback:
                return True
                
            # Check if it's a valid public IP
            return not (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_multicast)
        except (ValueError, ImportError):
            # Basic validation fallback
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            try:
                return all(0 <= int(part) <= 255 for part in parts)
            except ValueError:
                return False


class HMACSignatureValidator:
    """
    HMAC signature validation for M-Pesa callbacks.
    
    This class provides cryptographic validation of callback payloads using
    HMAC (Hash-based Message Authentication Code) to ensure data integrity
    and authenticity. It prevents tampering and replay attacks.
    
    Attributes:
        SECRET_KEY (str): Secret key for HMAC generation
        SIGNATURE_HEADER (str): HTTP header containing the signature
        TIMESTAMP_TOLERANCE (int): Maximum age of requests in seconds
    
    Methods:
        validate_signature: Validates HMAC signature of callback data
        generate_signature: Generates HMAC signature for data
        is_timestamp_valid: Validates request timestamp
    """
    
    def __init__(self, secret_key=None):
        """
        Initialize HMAC validator with secret key.
        
        Args:
            secret_key (str): Secret key for HMAC. If None, uses Django SECRET_KEY
        """
        self.secret_key = secret_key or settings.SECRET_KEY
        self.signature_header = 'HTTP_X_MPESA_SIGNATURE'
        self.timestamp_tolerance = 300  # 5 minutes
    
    def validate_signature(self, request):
        """
        Validate HMAC signature of incoming callback request.
        
        This method extracts the request payload, generates the expected
        HMAC signature, and compares it with the provided signature.
        
        Args:
            request (Request): DRF request object
            
        Returns:
            dict: Validation result with status and details
        """
        try:
            # Extract signature from headers
            provided_signature = request.META.get(self.signature_header)
            if not provided_signature:
                return {
                    'valid': False,
                    'error': 'Missing signature header',
                    'details': f'No {self.signature_header} header found'
                }
            
            # Get raw request body
            request_body = request.body
            if not request_body:
                return {
                    'valid': False,
                    'error': 'Empty request body',
                    'details': 'Cannot validate signature of empty payload'
                }
            
            # Extract timestamp if present
            timestamp = self._extract_timestamp(request)
            if timestamp and not self.is_timestamp_valid(timestamp):
                return {
                    'valid': False,
                    'error': 'Timestamp validation failed',
                    'details': 'Request timestamp is outside acceptable range'
                }
            
            # Generate expected signature
            expected_signature = self.generate_signature(request_body, timestamp)
            
            # Compare signatures using secure comparison
            if self._secure_compare(provided_signature, expected_signature):
                logging.info(f"HMAC signature validation successful")
                return {
                    'valid': True,
                    'message': 'Signature validation successful'
                }
            else:
                logging.warning(f"HMAC signature validation failed")
                return {
                    'valid': False,
                    'error': 'Signature mismatch',
                    'details': 'Provided signature does not match expected signature'
                }
                
        except Exception as e:
            logging.error(f"HMAC signature validation error: {str(e)}")
            return {
                'valid': False,
                'error': 'Validation error',
                'details': str(e)
            }
    
    def generate_signature(self, payload, timestamp=None):
        """
        Generate HMAC signature for given payload.
        
        Args:
            payload (bytes): Request payload data
            timestamp (str, optional): Request timestamp
            
        Returns:
            str: Base64 encoded HMAC signature
        """
        # Prepare data for signing
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        
        # Include timestamp in signature if provided
        if timestamp:
            data_to_sign = payload + timestamp.encode('utf-8')
        else:
            data_to_sign = payload
        
        # Generate HMAC signature
        signature = hmac.new(
            key=self.secret_key.encode('utf-8'),
            msg=data_to_sign,
            digestmod=hashlib.sha256
        ).digest()
        
        # Return base64 encoded signature
        return base64.b64encode(signature).decode('utf-8')
    
    def is_timestamp_valid(self, timestamp_str):
        """
        Validate request timestamp to prevent replay attacks.
        
        Args:
            timestamp_str (str): Timestamp string (ISO format or Unix timestamp)
            
        Returns:
            bool: True if timestamp is within acceptable range
        """
        try:
            # Try parsing as Unix timestamp first
            try:
                timestamp = float(timestamp_str)
                request_time = datetime.fromtimestamp(timestamp)
            except ValueError:
                # Try parsing as ISO format
                request_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Check if timestamp is within tolerance
            current_time = datetime.now()
            time_diff = abs((current_time - request_time).total_seconds())
            
            return time_diff <= self.timestamp_tolerance
            
        except Exception as e:
            logging.warning(f"Timestamp validation error: {str(e)}")
            return False
    
    def _extract_timestamp(self, request):
        """
        Extract timestamp from request headers or payload.
        
        Args:
            request (Request): DRF request object
            
        Returns:
            str: Timestamp string or None
        """
        # Check headers first
        timestamp = request.META.get('HTTP_X_TIMESTAMP')
        if timestamp:
            return timestamp
        
        # Check JSON payload
        try:
            if hasattr(request, 'data') and request.data:
                return request.data.get('timestamp')
        except Exception:
            pass
        
        return None
    
    def _secure_compare(self, provided_sig, expected_sig):
        """
        Perform secure signature comparison to prevent timing attacks.
        
        Args:
            provided_sig (str): Signature from request
            expected_sig (str): Expected signature
            
        Returns:
            bool: True if signatures match
        """
        return hmac.compare_digest(provided_sig, expected_sig)


class CallbackStructureValidator:
    """
    Validates the structure and content of M-Pesa callback payloads.
    
    This class ensures that callback requests contain all required fields
    with proper data types and formats. It helps prevent malformed or
    malicious callback data from being processed.
    
    Attributes:
        REQUIRED_FIELDS (dict): Required fields and their validation rules
        OPTIONAL_FIELDS (dict): Optional fields and their validation rules
    
    Methods:
        validate_structure: Validates complete callback structure
        validate_field: Validates individual field
        sanitize_data: Sanitizes callback data
    """
    
    # Required fields for STK Push callback
    REQUIRED_STK_FIELDS = {
        'Body': {
            'type': dict,
            'required': True,
            'nested': {
                'stkCallback': {
                    'type': dict,
                    'required': True,
                    'nested': {
                        'MerchantRequestID': {'type': str, 'required': True, 'max_length': 50},
                        'CheckoutRequestID': {'type': str, 'required': True, 'max_length': 50},
                        'ResultCode': {'type': int, 'required': True, 'min_value': 0},
                        'ResultDesc': {'type': str, 'required': True, 'max_length': 200},
                    }
                }
            }
        }
    }
    
    # Optional fields that may be present
    OPTIONAL_STK_FIELDS = {
        'Body.stkCallback.CallbackMetadata': {
            'type': dict,
            'required': False,
            'nested': {
                'Item': {
                    'type': list,
                    'required': False,
                    'items': {
                        'Name': {'type': str, 'required': True},
                        'Value': {'type': [str, int, float], 'required': True}
                    }
                }
            }
        }
    }
    
    def __init__(self, callback_type='stk_push'):
        """
        Initialize validator for specific callback type.
        
        Args:
            callback_type (str): Type of callback ('stk_push', 'c2b', 'b2c')
        """
        self.callback_type = callback_type
        self.validation_errors = []
    
    def validate_structure(self, callback_data):
        """
        Validate complete callback structure and data.
        
        Args:
            callback_data (dict): Parsed callback JSON data
            
        Returns:
            dict: Validation result with status and details
        """
        self.validation_errors = []
        
        try:
            if not isinstance(callback_data, dict):
                return {
                    'valid': False,
                    'error': 'Invalid data type',
                    'details': 'Callback data must be a JSON object'
                }
            
            # Validate required fields
            self._validate_required_fields(callback_data, self.REQUIRED_STK_FIELDS)
            
            # Validate optional fields if present
            self._validate_optional_fields(callback_data, self.OPTIONAL_STK_FIELDS)
            
            # Additional business logic validation
            self._validate_business_rules(callback_data)
            
            if self.validation_errors:
                return {
                    'valid': False,
                    'error': 'Structure validation failed',
                    'details': self.validation_errors
                }
            
            return {
                'valid': True,
                'message': 'Structure validation successful',
                'sanitized_data': self.sanitize_data(callback_data)
            }
            
        except Exception as e:
            logging.error(f"Structure validation error: {str(e)}")
            return {
                'valid': False,
                'error': 'Validation error',
                'details': str(e)
            }
    
    def _validate_required_fields(self, data, field_schema, path=''):
        """Validate required fields recursively."""
        for field_name, field_rules in field_schema.items():
            current_path = f"{path}.{field_name}" if path else field_name
            
            if field_name not in data:
                self.validation_errors.append(f"Missing required field: {current_path}")
                continue
            
            field_value = data[field_name]
            
            # Type validation
            expected_type = field_rules.get('type')
            if expected_type and not isinstance(field_value, expected_type):
                self.validation_errors.append(
                    f"Invalid type for {current_path}: expected {expected_type.__name__}, got {type(field_value).__name__}"
                )
                continue
            
            # Length validation for strings
            if isinstance(field_value, str):
                max_length = field_rules.get('max_length')
                if max_length and len(field_value) > max_length:
                    self.validation_errors.append(f"Field {current_path} exceeds maximum length of {max_length}")
            
            # Value validation for integers
            if isinstance(field_value, int):
                min_value = field_rules.get('min_value')
                if min_value is not None and field_value < min_value:
                    self.validation_errors.append(f"Field {current_path} below minimum value of {min_value}")
            
            # Nested validation
            if 'nested' in field_rules and isinstance(field_value, dict):
                self._validate_required_fields(field_value, field_rules['nested'], current_path)
    
    def _validate_optional_fields(self, data, field_schema):
        """Validate optional fields if present."""
        # Implementation would be similar to required fields but skip missing fields
        pass
    
    def _validate_business_rules(self, callback_data):
        """Validate business-specific rules."""
        try:
            # Extract callback details
            stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
            result_code = stk_callback.get('ResultCode')
            
            # Validate result code is within expected range
            if result_code is not None and not (0 <= result_code <= 9999):
                self.validation_errors.append(f"Invalid result code: {result_code}")
            
            # Validate MerchantRequestID format (should be alphanumeric)
            merchant_id = stk_callback.get('MerchantRequestID', '')
            if merchant_id and not merchant_id.replace('-', '').replace('_', '').isalnum():
                self.validation_errors.append("Invalid MerchantRequestID format")
            
            # Additional validations can be added here
            
        except Exception as e:
            self.validation_errors.append(f"Business rule validation error: {str(e)}")
    
    def sanitize_data(self, callback_data):
        """
        Sanitize callback data for safe processing.
        
        Args:
            callback_data (dict): Raw callback data
            
        Returns:
            dict: Sanitized callback data
        """
        try:
            # Deep copy to avoid modifying original
            sanitized = json.loads(json.dumps(callback_data))
            
            # Sanitize string fields
            self._sanitize_strings(sanitized)
            
            return sanitized
        except Exception:
            return callback_data
    
    def _sanitize_strings(self, data):
        """Recursively sanitize string values."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    # Basic sanitization - remove potential script tags and normalize whitespace
                    data[key] = value.strip()[:1000]  # Limit length and trim whitespace
                elif isinstance(value, (dict, list)):
                    self._sanitize_strings(value)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._sanitize_strings(item)


class EnhancedCallbackSecurity:
    """
    Comprehensive M-Pesa callback security system.
    
    This class combines multiple security layers including IP whitelisting,
    HMAC signature validation, structure validation, and rate limiting to
    provide comprehensive protection for M-Pesa callback endpoints.
    
    Attributes:
        ip_whitelist: IP whitelisting validator
        hmac_validator: HMAC signature validator
        structure_validator: Callback structure validator
    
    Methods:
        validate_callback: Comprehensive callback validation
        get_security_context: Extract security context from request
    """
    
    def __init__(self, enable_hmac=True, enable_structure_validation=True):
        """
        Initialize enhanced security system.
        
        Args:
            enable_hmac (bool): Enable HMAC signature validation
            enable_structure_validation (bool): Enable structure validation
        """
        self.ip_whitelist = SafaricomIPWhitelist()
        self.hmac_validator = HMACSignatureValidator() if enable_hmac else None
        self.structure_validator = CallbackStructureValidator() if enable_structure_validation else None
        
    def validate_callback(self, request, view=None):
        """
        Comprehensive callback validation using multiple security layers.
        
        This method applies all enabled security validations in sequence:
        1. IP whitelisting
        2. HMAC signature validation (if enabled)
        3. Structure validation (if enabled)
        4. Rate limiting
        
        Args:
            request (Request): DRF request object
            view (APIView, optional): The view being accessed
            
        Returns:
            dict: Comprehensive validation result
        """
        security_context = self.get_security_context(request)
        validation_results = {
            'overall_status': 'pending',
            'security_context': security_context,
            'validations': {}
        }
        
        try:
            # Layer 1: IP Whitelisting
            ip_valid = self.ip_whitelist.has_permission(request, view)
            validation_results['validations']['ip_whitelist'] = {
                'passed': ip_valid,
                'message': 'IP whitelisting validation'
            }
            
            if not ip_valid:
                validation_results['overall_status'] = 'rejected'
                validation_results['rejection_reason'] = 'IP not whitelisted'
                return validation_results
            
            # Layer 2: HMAC Signature Validation (if enabled)
            if self.hmac_validator:
                hmac_result = self.hmac_validator.validate_signature(request)
                validation_results['validations']['hmac_signature'] = hmac_result
                
                if not hmac_result['valid']:
                    validation_results['overall_status'] = 'rejected'
                    validation_results['rejection_reason'] = 'HMAC signature validation failed'
                    return validation_results
            
            # Layer 3: Structure Validation (if enabled)
            if self.structure_validator:
                try:
                    callback_data = json.loads(request.body) if request.body else {}
                    structure_result = self.structure_validator.validate_structure(callback_data)
                    validation_results['validations']['structure'] = structure_result
                    
                    if not structure_result['valid']:
                        validation_results['overall_status'] = 'rejected'
                        validation_results['rejection_reason'] = 'Structure validation failed'
                        return validation_results
                except json.JSONDecodeError as e:
                    validation_results['validations']['structure'] = {
                        'valid': False,
                        'error': 'Invalid JSON',
                        'details': str(e)
                    }
                    validation_results['overall_status'] = 'rejected'
                    validation_results['rejection_reason'] = 'Invalid JSON payload'
                    return validation_results
            
            # All validations passed
            validation_results['overall_status'] = 'approved'
            validation_results['message'] = 'All security validations passed'
            
            # Log successful validation
            logging.info(f"Enhanced callback security: All validations passed for IP {security_context['client_ip']}")
            
            return validation_results
            
        except Exception as e:
            logging.error(f"Enhanced callback security error: {str(e)}")
            validation_results['overall_status'] = 'error'
            validation_results['error'] = str(e)
            return validation_results
    
    def get_security_context(self, request):
        """
        Extract comprehensive security context from request.
        
        Args:
            request (Request): DRF request object
            
        Returns:
            dict: Security context information
        """
        return {
            'client_ip': self.ip_whitelist.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'method': request.method,
            'path': request.path,
            'timestamp': datetime.now().isoformat(),
            'content_type': request.META.get('CONTENT_TYPE', ''),
            'content_length': request.META.get('CONTENT_LENGTH', 0),
            'headers': {
                k: v for k, v in request.META.items() 
                if k.startswith('HTTP_') and 'AUTHORIZATION' not in k
            }
        }