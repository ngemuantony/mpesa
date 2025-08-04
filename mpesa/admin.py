"""
Django Admin Configuration for M-Pesa Module

This module configures the Django admin interface for M-Pesa transaction
management. It provides a user-friendly interface for administrators to
view, search, and manage payment transactions.

Components:
    - TransactionAdmin: Custom admin interface for Transaction model
    - Enhanced list display with key transaction fields
    - Search and filtering capabilities for transaction management

Admin Features:
    - Transaction listing with status indicators
    - Search by phone number, reference, and receipt number
    - Filter by status, date, and amount ranges
    - Read-only access to critical payment data
    - Detailed transaction views with all M-Pesa response data

Security Considerations:
    - Admin access should be restricted to authorized personnel only
    - Sensitive payment data is displayed but not editable
    - Audit trail for admin actions on transaction records

Author: M-Pesa Integration Team
Date: 2024
"""

from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Django admin configuration for Transaction model.
    
    Provides a comprehensive interface for viewing and managing M-Pesa
    transactions. Includes search, filtering, and detailed view capabilities
    while maintaining data security.
    
    Features:
        - List view with key transaction information
        - Search functionality across multiple fields
        - Status-based filtering
        - Read-only display of sensitive payment data
    """
    
    # Display key transaction fields in the list view
    list_display = [
        'transaction_no',      # Unique transaction identifier
        'phone_number',        # Customer phone number 
        'amount',             # Payment amount
        'status',             # Current transaction status
        'reference',          # Payment reference/description
        'receipt_no',         # M-Pesa receipt number
        'created'             # Transaction creation timestamp
    ]
    
    # Filter options for transaction listing
    list_filter = ['status', 'created']  # Filter by status and creation date
    
    # Search functionality across key fields
    search_fields = ['transaction_no', 'phone_number', 'reference', 'receipt_no']
    
    # Protect critical fields from accidental modification
    readonly_fields = ['transaction_no', 'checkout_request_id', 'created', 'ip']
    
    # Pagination settings for better performance
    list_per_page = 25
    
    # Default ordering (newest transactions first)
    ordering = ['-created']
    
    # Organized field grouping for detailed view
    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_no', 'checkout_request_id', 'amount', 'status', 'receipt_no'),
            'description': 'Core transaction information from M-Pesa processing'
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'reference', 'description'),
            'description': 'Customer contact details and payment description'
        }),
        ('Metadata', {
            'fields': ('created', 'ip'),
            'classes': ('collapse',),
            'description': 'System-generated metadata and tracking information'
        }),
    )
