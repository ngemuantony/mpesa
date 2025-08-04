"""
Django App Configuration for M-Pesa Module

This module contains the Django app configuration for the M-Pesa payment
integration system. It defines app-specific settings and initialization
parameters for the payment processing functionality.

Components:
    - MpesaConfig: Main app configuration class
    - Auto field configuration for model primary keys
    - App name and metadata settings

App Features:
    - M-Pesa STK Push payment processing
    - Transaction management and tracking
    - Callback handling for payment confirmations
    - Security features with IP whitelisting
    - Comprehensive admin interface

Dependencies:
    - Django framework
    - Django REST Framework for API functionality
    - Phone number validation libraries
    - Environment variable management

Author: M-Pesa Integration Team
Date: 2024
"""

from django.apps import AppConfig


class MpesaConfig(AppConfig):
    """
    Django app configuration for the M-Pesa payment system.
    
    This configuration class defines essential settings for the M-Pesa
    app including field types, app name, and initialization parameters.
    
    Attributes:
        default_auto_field (str): Default field type for model primary keys
        name (str): The app name used by Django for identification
        
    Configuration:
        - Uses BigAutoField for primary keys to support large-scale deployments
        - App name 'mpesa' for URL routing and template organization
    """
    
    # Use BigAutoField for primary keys (supports larger ID ranges)
    default_auto_field = 'django.db.models.BigAutoField'
    
    # App name for Django registration and routing
    name = 'mpesa'
