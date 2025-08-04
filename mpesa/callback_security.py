"""
M-Pesa Callback Security Module

This module provides security mechanisms for validating M-Pesa payment callbacks
from Safaricom's servers. It implements IP whitelisting to ensure that only
legitimate callback requests are processed.

Components:
    - SafaricomIPWhitelist: Permission class for IP address validation
    - Official Safaricom IP addresses whitelist
    - Client IP extraction utilities

Security Features:
    - IP address validation against official Safaricom ranges
    - Request filtering for callback endpoints
    - Logging of callback attempts for monitoring
    - Protection against unauthorized callback submissions

Usage:
    Apply the SafaricomIPWhitelist permission class to views that handle
    M-Pesa callbacks to ensure security.

Author: M-Pesa Integration Team
Date: 2024
"""

import logging
from rest_framework.permissions import BasePermission


class SafaricomIPWhitelist(BasePermission):
    """
    Custom permission class to validate M-Pesa callback requests from Safaricom.
    
    This permission ensures that only requests originating from Safaricom's
    official IP addresses are allowed to access callback endpoints. This
    prevents unauthorized parties from sending fake callback data.
    
    Attributes:
        SAFARICOM_IPS (list): Official IP addresses used by Safaricom for callbacks
    
    Methods:
        has_permission: Validates if request IP is from Safaricom
        get_client_ip: Extracts client IP from request headers
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

    def has_permission(self, request, view):
        """
        Check if the request originates from a whitelisted Safaricom IP.
        
        This method extracts the client IP address and validates it against
        the official Safaricom IP whitelist. All callback attempts are logged
        for security monitoring.
        
        Args:
            request (Request): DRF request object
            view (APIView): The view being accessed
            
        Returns:
            bool: True if IP is whitelisted, False otherwise
        """
        # Extract client IP address from request
        client_ip = self.get_client_ip(request)
        
        # Log callback attempt for security monitoring
        logging.info(f"M-Pesa callback request from IP: {client_ip}")
        
        # Validate IP against Safaricom whitelist
        if client_ip in self.SAFARICOM_IPS:
            logging.info(f"Callback authorized from whitelisted IP: {client_ip}")
            return True
        
        # Log security warning for unauthorized attempts
        logging.warning(f"Unauthorized M-Pesa callback attempt from IP: {client_ip}")
        return False
    
    def get_client_ip(self, request):
        """
        Extract the real client IP address from the request.
        
        This method handles various scenarios including requests that come
        through proxies, load balancers, or CDNs. It prioritizes the
        X-Forwarded-For header which contains the original client IP.
        
        Args:
            request (Request): DRF request object
            
        Returns:
            str: Client IP address as a string
            
        Note:
            When multiple IPs are present in X-Forwarded-For (proxy chain),
            the first IP is considered the original client IP.
        """
        # Check for forwarded IP (proxy/load balancer scenarios)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in case of multiple forwarded IPs
            # Format: "client_ip, proxy1_ip, proxy2_ip"
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            # Direct connection - use remote address
            ip = request.META.get('REMOTE_ADDR')
        return ip