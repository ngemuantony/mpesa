#!/bin/bash
# Production server startup script for Cloudflare tunnels with Gunicorn

echo "☁️  Starting M-Pesa Production Server (Cloudflare Tunnel + Gunicorn)"
echo "� Running on port 5000 with Gunicorn WSGI server"

# Set production environment variables
export DEBUG=False
export CLOUDFLARE_TUNNEL=True
export DJANGO_SETTINGS_MODULE=config.settings

# Ensure logs directory exists
mkdir -p logs

# Collect static files for production
echo "📦 Collecting static files..."
/home/devops/MPESA/mpesa/venv/bin/python manage.py collectstatic --noinput

# Run database migrations
echo "🗃️  Applying database migrations..."
/home/devops/MPESA/mpesa/venv/bin/python manage.py migrate --noinput

# Start the production server with Gunicorn
echo "🚀 Starting Gunicorn server on port 5000..."
cd /home/devops/MPESA/mpesa

# Start Gunicorn with configuration file
exec /home/devops/MPESA/mpesa/venv/bin/gunicorn \
    --config gunicorn.conf.py \
    config.wsgi:application
