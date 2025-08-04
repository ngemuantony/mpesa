# Import phone number validation utilities
from .phone_number_validation import validate_possible_number
from rest_framework import serializers
from django.core.exceptions import ValidationError

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
        Validate and normalize phone number for M-Pesa compatibility.
        
        Performs the following transformations:
        - Removes non-digit characters (except +)
        - Converts local format (07XX) to international (254XX)
        - Validates using Kenya phone number rules
        
        Args:
            phone_number (str): Raw phone number input
            
        Returns:
            str: Normalized phone number in 254XXXXXXXXX format
            
        Raises:
            serializers.ValidationError: If phone number is invalid
        """
        import re
        
        # Convert to string and remove whitespace
        phone_number = str(phone_number).strip()
        
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
            raise serializers.ValidationError("Phone number is not valid")
        except Exception as e:
            raise serializers.ValidationError(f"Phone number validation error: {str(e)}")

    def validate_amount(self, amount):
        """
        Validate payment amount is within acceptable range.
        
        M-Pesa has specific limits on transaction amounts. This method ensures
        the amount is positive and within reasonable bounds.
        
        Args:
            amount (str/float): Payment amount to validate
            
        Returns:
            str/float: Validated amount
            
        Raises:
            serializers.ValidationError: If amount is invalid or out of range
        """
        try:
            # Convert to float for validation
            amount_float = float(amount)
            
            # Check minimum amount (must be greater than 0)
            if amount_float <= 0:
                raise serializers.ValidationError(
                    "Amount must be greater than Zero"
                )
                
            # Optional: Add maximum amount check for M-Pesa limits
            if amount_float > 300000:  # KES 300,000 M-Pesa limit
                raise serializers.ValidationError(
                    "Amount cannot exceed KES 300,000"
                )
                
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                "Amount must be a valid number"
            )
        return amount

    def validate_reference(self, reference):
        """
        Validate and provide default value for payment reference.
        
        The reference field helps customers and merchants track payments.
        If no reference is provided, a default "Test" value is used.
        
        Args:
            reference (str): Optional payment reference
            
        Returns:
            str: Validated reference or default value
        """
        if reference and reference.strip():
            # Return trimmed reference if provided
            return reference.strip()
        # Return default reference for testing
        return "Test"

    def validate_description(self, description):
        """
        Validate and provide default value for payment description.
        
        The description helps identify what the payment is for.
        If no description is provided, a default "Test" value is used.
        
        Args:
            description (str): Optional payment description
            
        Returns:
            str: Validated description or default value
        """
        if description and description.strip():
            # Return trimmed description if provided
            return description.strip()
        # Return default description for testing
        return "Test"


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