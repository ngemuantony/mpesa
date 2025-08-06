"""
Utility functions for the M-Pesa application.

This module contains helper functions that are used across different
parts of the M-Pesa integration system.
"""

import logging

# Initialize logger for this module
logger = logging.getLogger("default")


def get_client_ip(request):
    """
    Get the real client IP address from a Django request, handling proxy scenarios.
    
    This function checks various HTTP headers to find the actual client IP address
    when the application is running behind proxies, load balancers, or CDNs.
    
    Args:
        request (HttpRequest): Django HTTP request object
        
    Returns:
        str: Client's real IP address
        
    Example:
        >>> from mpesa.utils import get_client_ip
        >>> ip = get_client_ip(request)
        >>> print(ip)  # e.g., "192.168.1.100"
    """
    # Dictionary to store found IPs for logging
    found_ips = {}
    
    # Check for X-Forwarded-For header (most common proxy header)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2, ...)
        # Format: "client_ip, proxy1_ip, proxy2_ip"
        ip_list = [ip.strip() for ip in x_forwarded_for.split(',')]
        client_ip = ip_list[0]  # First IP is the original client
        found_ips['X-Forwarded-For'] = f"{client_ip} (from: {x_forwarded_for})"
        
        # Validate that it's not a local/private IP if we have multiple IPs
        if len(ip_list) > 1 and not _is_private_ip(client_ip):
            logger.info("Client IP from X-Forwarded-For: {}".format(client_ip))
            return client_ip
        elif len(ip_list) == 1:
            logger.info("Client IP from X-Forwarded-For: {}".format(client_ip))
            return client_ip
    
    # Check for X-Real-IP header (common with nginx)
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        ip = x_real_ip.strip()
        found_ips['X-Real-IP'] = ip
        if not _is_private_ip(ip):
            logger.info("Client IP from X-Real-IP: {}".format(ip))
            return ip
    
    # Check for Cloudflare's connecting IP
    cf_connecting_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_connecting_ip:
        ip = cf_connecting_ip.strip()
        found_ips['CF-Connecting-IP'] = ip
        logger.info("Client IP from CF-Connecting-IP: {}".format(ip))
        return ip
    
    # Check for other common headers
    headers_to_check = [
        'HTTP_X_FORWARDED',
        'HTTP_X_CLUSTER_CLIENT_IP',
        'HTTP_FORWARDED_FOR',
        'HTTP_FORWARDED',
        'HTTP_CLIENT_IP',
    ]
    
    for header in headers_to_check:
        value = request.META.get(header)
        if value:
            ip = value.split(',')[0].strip()
            found_ips[header] = ip
            if not _is_private_ip(ip):
                logger.info("Client IP from {}: {}".format(header, ip))
                return ip
    
    # Fall back to REMOTE_ADDR
    remote_addr = request.META.get('REMOTE_ADDR', 'Unknown')
    found_ips['REMOTE_ADDR'] = remote_addr
    
    # Log all found IPs for debugging
    if found_ips:
        logger.info("IP detection results: {}".format(found_ips))
    else:
        logger.warning("No IP address found in request headers")
    
    logger.info("Using REMOTE_ADDR as client IP: {}".format(remote_addr))
    return remote_addr


def _is_private_ip(ip):
    """
    Check if an IP address is private/local.
    
    Args:
        ip (str): IP address to check
        
    Returns:
        bool: True if the IP is private/local, False otherwise
    """
    if not ip or ip == 'Unknown':
        return True
    
    # Common private/local IP ranges and addresses
    private_patterns = [
        '127.',          # Loopback
        '10.',           # Private Class A
        '172.16.',       # Private Class B (simplified check)
        '172.17.',       # Docker default
        '192.168.',      # Private Class C
        'localhost',     # Localhost
        '::1',           # IPv6 localhost
        '0.0.0.0',       # Unspecified
    ]
    
    return any(ip.startswith(pattern) for pattern in private_patterns)


def log_request_headers(request, prefix="Request"):
    """
    Log all relevant HTTP headers for debugging purposes.
    
    Args:
        request (HttpRequest): Django HTTP request object
        prefix (str): Prefix for the log message
    """
    relevant_headers = {
        key: value for key, value in request.META.items() 
        if key.startswith('HTTP_') or key in ['REMOTE_ADDR', 'REMOTE_HOST', 'SERVER_NAME']
    }
    
    logger.info("{} headers: {}".format(prefix, relevant_headers))
