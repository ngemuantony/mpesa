import logging
from rest_framework.permissions import BasePermission


class SafaricomIPWhitelist(BasePermission):
    """
    Custom permission to only allow requests from Safaricom's official IP addresses
    """
    SAFARICOM_IPS = [
        '196.201.214.200',
        '196.201.214.206', 
        '196.201.213.114',
        '196.201.214.207',
        '196.201.214.208',
        '196.201.213.44',
        '196.201.212.127',
        '196.201.212.138',
        '196.201.212.129',
        '196.201.212.136',
        '196.201.212.74',
        '196.201.212.69'
    ]

    def has_permission(self, request, view):
        client_ip = self.get_client_ip(request)
        logging.info(f"M-Pesa callback request from IP: {client_ip}")
        
        if client_ip in self.SAFARICOM_IPS:
            return True
        
        logging.warning(f"Unauthorized M-Pesa callback attempt from IP: {client_ip}")
        return False
    
    def get_client_ip(self, request):
        """Extract the real client IP address from the request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in case of multiple forwarded IPs
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip