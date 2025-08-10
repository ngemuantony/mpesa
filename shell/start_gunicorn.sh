#!/bin/bash
# Quick Gunicorn startup script (no migrations/static collection)

echo "🚀 Starting M-Pesa with Gunicorn on port 5000"

# Set environment variables
export DEBUG=False
export CLOUDFLARE_TUNNEL=True
export DJANGO_SETTINGS_MODULE=config.settings

# Ensure logs directory exists
mkdir -p logs

cd /home/devops/MPESA/mpesa

# Start Gunicorn
exec /home/devops/MPESA/mpesa/venv/bin/gunicorn \
    --config gunicorn.conf.py \
    config.wsgi:application
