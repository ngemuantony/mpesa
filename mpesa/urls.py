"""
URL Configuration for M-Pesa Module

This module defines the URL routing patterns for the M-Pesa payment system.
It maps URLs to their corresponding views for both frontend interfaces
and API endpoints.

URL Patterns:
    Frontend URLs:
        - / : Payment form interface
        - status/<id>/ : Transaction status page
    
    API Endpoints:
        - checkout/ : STK push initiation
        - callback/ : Payment callback handling
        - stk-query/ : Payment status queries

Security Features:
    - Callback URLs are protected with IP whitelisting
    - CSRF protection disabled for external callbacks
    - Public access for payment form and status pages

Integration Points:
    - Frontend JavaScript calls API endpoints
    - Safaricom calls callback URL for payment updates
    - Status URLs provide transaction result pages

Author: M-Pesa Integration Team
Date: 2024
"""

from django.urls import path
from . import views

urlpatterns = [
    # Frontend interface URLs
    path("", views.payment_form, name="payment_form"),
    # Main payment form where users initiate payments
    
    path("status/<str:checkout_request_id>/", views.transaction_status, name="transaction_status"),
    # Transaction status page showing payment results
    
    # API endpoint URLs for M-Pesa integration
    path("checkout/", views.MpesaCheckout.as_view(), name="checkout"),
    # STK push initiation endpoint (called by frontend JavaScript)
    
    path("callback/", views.MpesaCallBack.as_view(), name="callback"),  
    # Payment callback endpoint (called by Safaricom servers)
    
    path("stk-query/", views.MpesaStkQuery.as_view(), name="stk_query"),
    # Payment status query endpoint (called by frontend for status updates)
]