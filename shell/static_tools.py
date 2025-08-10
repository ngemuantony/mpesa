#!/usr/bin/env python
"""
Django management script for static files operations.

This script provides shortcuts for common static file operations:
- Collecting static files
- Compressing static files  
- Clearing static file cache
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.conf import settings

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'collect':
            # Collect static files
            execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
            print("✅ Static files collected successfully!")
            
        elif command == 'clear':
            # Clear static files
            import shutil
            if os.path.exists(settings.STATIC_ROOT):
                shutil.rmtree(settings.STATIC_ROOT)
                print("🗑️  Static files cleared!")
            else:
                print("ℹ️  No static files to clear.")
                
        elif command == 'serve':
            # Run development server with static files
            execute_from_command_line(['manage.py', 'runserver'])
            
        else:
            print("Usage:")
            print("  python static_tools.py collect  - Collect static files")
            print("  python static_tools.py clear    - Clear static files")
            print("  python static_tools.py serve    - Run development server")
    else:
        print("Usage:")
        print("  python static_tools.py collect  - Collect static files")
        print("  python static_tools.py clear    - Clear static files") 
        print("  python static_tools.py serve    - Run development server")
