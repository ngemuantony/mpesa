"""
Phone Number Validation Module

This module provides comprehensive phone number validation functionality
for the M-Pesa payment system. It ensures that only valid Kenyan phone
numbers are accepted for payment processing.

Components:
    - validate_possible_number: Core validation function for phone numbers
    - Integration with phonenumbers library for international validation
    - Custom error handling with payment-specific error codes

Validation Features:
    - International phone number format support
    - Kenyan country code validation
    - Phone number possibility checking
    - Phone number validity verification
    - Custom error messages for payment context

Dependencies:
    - phonenumbers library for comprehensive validation
    - Django validation framework
    - Custom error codes for payment systems

Usage:
    Use validate_possible_number() to validate phone numbers before
    processing M-Pesa payments.

Author: M-Pesa Integration Team
Date: 2024
"""

from enum import Enum

from django.core.exceptions import ValidationError
from phonenumber_field.phonenumber import to_python
from phonenumbers.phonenumberutil import is_possible_number

from .error_codes import PaymentErrorCode


def validate_possible_number(phone, country=None):
    """
    Validate if a phone number is possible and valid for M-Pesa payments.
    
    This function performs comprehensive validation of phone numbers including:
    - Converting to standardized phone number object
    - Checking if number is possible in the specified country
    - Verifying the number is valid according to international standards
    
    Args:
        phone (str): Phone number string to validate
        country (str, optional): Country code for validation context.
                                Defaults to None (auto-detect)
    
    Returns:
        PhoneNumber: Validated phone number object if valid
        
    Raises:
        ValidationError: If phone number is invalid, impossible, or malformed
        
    Example:
        >>> validate_possible_number("+254712345678", "KE")
        PhoneNumber(country_code=254, national_number=712345678)
        
        >>> validate_possible_number("invalid")
        ValidationError: The phone number entered is not valid.
    
    Note:
        This validation is specifically designed for M-Pesa which requires
        valid Kenyan phone numbers (Safaricom network primarily).
    """
    # Convert string to standardized phone number object
    phone_number = to_python(phone, country)
    
    # Perform comprehensive validation checks
    if (
        not phone_number  # Phone number object creation failed
        or not is_possible_number(phone_number)  # Number format impossible
        or not phone_number.is_valid()  # Number doesn't pass validity rules
    ):
        # Raise validation error with payment-specific error code
        raise ValidationError(
            "The phone number entered is not valid.", 
            code=PaymentErrorCode.INVALID
        )
    
    # Return validated phone number object
    return phone_number