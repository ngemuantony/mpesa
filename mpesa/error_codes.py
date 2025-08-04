"""
Payment Error Codes Module

This module defines standardized error codes for the M-Pesa payment system.
These codes provide consistent error identification across the application
and help with debugging, logging, and user experience.

Components:
    - PaymentErrorCode: Enumeration of all payment-related error codes
    - Standardized error identifiers for validation and processing

Error Categories:
    - Validation Errors: Invalid input data (phone numbers, amounts, etc.)
    - Payment Processing Errors: M-Pesa API communication failures
    - System Errors: Internal application errors

Usage:
    Import PaymentErrorCode and use the enum values when raising
    ValidationError or handling payment processing exceptions.

Benefits:
    - Consistent error handling across the application
    - Easy error code lookup and debugging
    - Internationalization support for error messages
    - Structured error reporting for monitoring

Author: M-Pesa Integration Team
Date: 2024
"""

from enum import Enum


class PaymentErrorCode(Enum):
    """
    Enumeration of standardized error codes for M-Pesa payment processing.
    
    This enum provides consistent error identification throughout the payment
    system, making it easier to handle, log, and display appropriate error
    messages to users.
    
    Attributes:
        INVALID (str): Code for invalid input validation errors
        PAYMENT_ERROR (str): Code for M-Pesa payment processing errors
    
    Usage:
        >>> from .error_codes import PaymentErrorCode
        >>> raise ValidationError("Invalid phone", code=PaymentErrorCode.INVALID)
    """
    
    # Validation error codes
    INVALID = "invalid_phone"  # Invalid phone number format or validation failure
    
    # Payment processing error codes  
    PAYMENT_ERROR = "payment_error"  # M-Pesa API communication or processing error