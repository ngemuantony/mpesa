import uuid
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

# Status choices for transaction - using string values for consistency
STATUS = (("1", "Pending"), ("0", "Complete"))

class Transaction(models.Model):
    """
    Model to store M-Pesa transaction records.
    
    This model tracks all payment transactions including their status,
    phone numbers, amounts, and M-Pesa specific identifiers.
    """
    
    # Unique transaction identifier generated automatically
    transaction_no = models.CharField(default=uuid.uuid4, max_length=50, unique=True)
    
    # Customer phone number (validated using phonenumbers library)
    phone_number = PhoneNumberField(null=False, blank=False)
    
    # M-Pesa checkout request ID from Safaricom API
    checkout_request_id = models.CharField(max_length=200)
    
    # Optional payment reference for customer identification
    reference = models.CharField(max_length=40, blank=True)
    
    # Optional description of what the payment is for
    description = models.TextField(null=True, blank=True)
    
    # Transaction amount stored as string to maintain precision
    amount = models.CharField(max_length=10)
    
    # Transaction status: "1" = Pending, "0" = Complete
    status = models.CharField(max_length=15, choices=STATUS, default=1)
    
    # M-Pesa receipt number (only available after successful payment)
    receipt_no = models.CharField(max_length=200, blank=True, null=True)
    
    # Timestamp when transaction was created
    created = models.DateTimeField(auto_now_add=True)
    
    # Timestamp when transaction was last updated
    updated_at = models.DateTimeField(auto_now=True)
    
    # IP address of the customer who initiated the transaction
    ip = models.CharField(max_length=200, blank=True, null=True)

    def __unicode__(self):
        """Unicode representation for Python 2 compatibility."""
        return f"{self.transaction_no}"
    
    def __str__(self):
        """String representation showing transaction number and status."""
        return f"Transaction {self.transaction_no} - {self.get_status_display()}"
    
    @property
    def is_successful(self):
        """
        Check if the transaction was completed successfully.
        
        Returns:
            bool: True if transaction is complete (status "0"), False otherwise
        """
        return self.status == "0"
    
    @property
    def is_pending(self):
        """
        Check if the transaction is still pending.
        
        Returns:
            bool: True if transaction is pending (status "1"), False otherwise
        """
        return self.status == "1"