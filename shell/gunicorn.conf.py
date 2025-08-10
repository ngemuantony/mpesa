# Gunicorn configuration file for M-Pesa Django application
# Place this file as gunicorn.conf.py in your project root

import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Recommended: (2 x CPU cores) + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 60
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "mpesa_django"

# Server mechanics
daemon = False
pidfile = "logs/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if needed - usually handled by Cloudflare)
# keyfile = None
# certfile = None

# Environment
raw_env = [
    'DJANGO_SETTINGS_MODULE=config.settings',
    'CLOUDFLARE_TUNNEL=True',
    'DEBUG=False'
]

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
