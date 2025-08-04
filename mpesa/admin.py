from django.contrib import admin
from .models import Transaction

# Register your models here.

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_no',
        'phone_number', 
        'amount',
        'status',
        'reference',
        'receipt_no',
        'created'
    ]
    list_filter = ['status', 'created']
    search_fields = ['transaction_no', 'phone_number', 'reference', 'receipt_no']
    readonly_fields = ['transaction_no', 'checkout_request_id', 'created', 'ip']
    list_per_page = 25
    ordering = ['-created']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_no', 'checkout_request_id', 'amount', 'status', 'receipt_no')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'reference', 'description')
        }),
        ('Metadata', {
            'fields': ('created', 'ip'),
            'classes': ('collapse',)
        }),
    )
