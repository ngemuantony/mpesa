from .phone_number_validation import validate_possible_number
from rest_framework import serializers
from django.core.exceptions import ValidationError

from . import models


class MpesaCheckoutSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField()  # Override the PhoneNumberField
    
    class Meta:
        model = models.Transaction
        fields = (
            "phone_number",
            "amount",
            "reference",
            "description",
        )

    def validate_phone_number(self, phone_number):
        """A very Basic validation to remove the preceding + or replace the 0 with 254"""
        import re
        
        # Convert to string if not already
        phone_number = str(phone_number).strip()
        
        # Remove any non-digit characters except +
        phone_number = re.sub(r'[^\d+]', '', phone_number)
        
        if phone_number.startswith("+"):
            phone_number = phone_number[1:]
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
            
        try:
            result = validate_possible_number(phone_number, "KE")
            return phone_number  # Return the processed phone number
        except ValidationError as e:
            raise serializers.ValidationError("Phone number is not valid")
        except Exception as e:
            raise serializers.ValidationError(f"Phone number validation error: {str(e)}")

        return phone_number

    def validate_amount(self, amount):
        """this methods validates the amount"""
        try:
            amount_float = float(amount)
            if amount_float <= 0:
                raise serializers.ValidationError(
                    "Amount must be greater than Zero"
                )
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                "Amount must be a valid number"
            )
        return amount

    def validate_reference(self, reference):
        """Write your validation logic here"""
        if reference:
            return reference
        return "Test"

    def validate_description(self, description):
        """Write your validation logic here"""
        if description:
            return description
        return "Test"


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Transaction
        fields = "__all__"