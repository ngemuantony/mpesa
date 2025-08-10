# Import phone number validation utilities
from .phone_number_validation import validate_possible_number
from rest_framework import serializers
from django.core.exceptions import ValidationError
import re
import html
import bleach
from decimal import Decimal, InvalidOperation

from . import models


class MpesaCheckoutSerializer(serializers.ModelSerializer):
    """
    Serializer for M-Pesa checkout requests.
    
    This serializer validates and processes payment request data including
    phone number formatting, amount validation, and optional reference/description fields.
    """
    
    # Override PhoneNumberField to use custom validation
    phone_number = serializers.CharField()
    
    class Meta:
        model = models.Transaction
        fields = (
            "phone_number",  # Customer's phone number
            "amount",        # Payment amount in KES
            "reference",     # Optional payment reference
            "description",   # Optional payment description
        )

    def validate_phone_number(self, phone_number):
        """
        Validate and normalize phone number for M-Pesa compatibility with security checks.
        
        Args:
            phone_number (str): Raw phone number input
            
        Returns:
            str: Normalized phone number in 254XXXXXXXXX format
            
        Raises:
            serializers.ValidationError: If phone number is invalid
        """
        # Input sanitization
        phone_number = str(phone_number).strip()
        
        # Security: Prevent injection attacks by limiting input length
        if len(phone_number) > 20:
            raise serializers.ValidationError("Phone number too long")
        
        # Security: Only allow digits, +, spaces, hyphens, and parentheses
        if not re.match(r'^[\d\s\-\(\)\+]+$', phone_number):
            raise serializers.ValidationError("Phone number contains invalid characters")
        
        # Remove any non-digit characters except + symbol
        phone_number = re.sub(r'[^\d+]', '', phone_number)
        
        # Handle international format (+254...)
        if phone_number.startswith("+"):
            phone_number = phone_number[1:]  # Remove '+' prefix
            
        # Convert local format (0XXX) to international (254XXX)
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
            
        try:
            # Validate using phonenumbers library with Kenya region
            result = validate_possible_number(phone_number, "KE")
            return phone_number  # Return the processed phone number
        except ValidationError as e:
            raise serializers.ValidationError("Invalid phone number format")
        except Exception as e:
            raise serializers.ValidationError("Phone number validation failed")

    def validate_amount(self, amount):
        """
        Validate payment amount with security checks.
        
        Args:
            amount (str/float): Payment amount to validate
            
        Returns:
            Decimal: Validated amount
            
        Raises:
            serializers.ValidationError: If amount is invalid or out of range
        """
        try:
            # Convert to Decimal for precise financial calculations
            amount_decimal = Decimal(str(amount))
            
            # Security: Check for negative amounts
            if amount_decimal <= 0:
                raise serializers.ValidationError("Amount must be greater than zero")
                
            # Security: Check for unreasonably large amounts (prevent overflow)
            if amount_decimal > Decimal('999999.99'):
                raise serializers.ValidationError("Amount exceeds maximum limit")
                
            # M-Pesa specific validation (KES 300,000 limit)
            if amount_decimal > Decimal('300000.00'):
                raise serializers.ValidationError("Amount exceeds M-Pesa transaction limit")
                
            # Check minimum amount (KES 1)
            if amount_decimal < Decimal('1.00'):
                raise serializers.ValidationError("Minimum amount is KES 1")
                
            # Check decimal places (max 2 for currency)
            if amount_decimal.as_tuple().exponent < -2:
                raise serializers.ValidationError("Amount cannot have more than 2 decimal places")
                
            return amount_decimal
            
        except (InvalidOperation, ValueError):
            raise serializers.ValidationError("Invalid amount format")
        except Exception:
            raise serializers.ValidationError("Amount validation failed")

    def validate_reference(self, reference):
        """
        Validate and sanitize payment reference with security checks.
        
        Args:
            reference (str): Optional payment reference
            
        Returns:
            str: Validated and sanitized reference
        """
        if not reference:
            return "Payment"  # Default reference
        
        # Convert to string and sanitize
        reference = str(reference).strip()
        
        # Security: Limit length to prevent abuse
        if len(reference) > 50:
            raise serializers.ValidationError("Reference too long (max 50 characters)")
        
        # Security: Remove HTML and script tags
        reference = bleach.clean(reference, tags=[], attributes={}, strip=True)
        
        # Security: Escape HTML entities
        reference = html.escape(reference)
        
        # Security: Only allow alphanumeric, spaces, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', reference):
            raise serializers.ValidationError("Reference contains invalid characters")
            
        return reference

    def validate_description(self, description):
        """
        Validate and sanitize payment description with security checks.
        
        Args:
            description (str): Optional payment description
            
        Returns:
            str: Validated and sanitized description
        """
        if not description:
            return "Payment"  # Default description
        
        # Convert to string and sanitize
        description = str(description).strip()
        
        # Security: Limit length to prevent abuse
        if len(description) > 100:
            raise serializers.ValidationError("Description too long (max 100 characters)")
        
        # Security: Remove HTML and script tags
        description = bleach.clean(description, tags=[], attributes={}, strip=True)
        
        # Security: Escape HTML entities
        description = html.escape(description)
        
        # Security: Only allow alphanumeric, spaces, and basic punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-_\.\,\!\?]+$', description):
            raise serializers.ValidationError("Description contains invalid characters")
            
        return description


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Transaction model data.
    
    This serializer is used to convert Transaction model instances
    to JSON format for API responses. Includes all transaction fields
    and computed properties.
    """
    
    # Include computed properties for convenience
    is_successful = serializers.ReadOnlyField()
    is_pending = serializers.ReadOnlyField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Transaction
        # Include all model fields in serialization
        fields = "__all__"
        
    def get_status_display(self, obj):
        """
        Get human-readable status display.
        
        Args:
            obj (Transaction): Transaction model instance
            
        Returns:
            str: Human-readable status (e.g., "Complete", "Pending")
        """
        return obj.get_status_display()