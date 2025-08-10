# Gunicorn Setup Complete - M-Pesa Django Application

## 🎉 Successfully Configured!

Your M-Pesa Django application is now running with Gunicorn on **port 5000** instead of the development server.

## 📋 What Was Set Up

### 1. **Gunicorn Configuration** (`gunicorn.conf.py`)
- **Port**: 5000 (bound to 0.0.0.0:5000)
- **Workers**: Auto-calculated based on CPU cores (2 × CPU + 1)
- **Logging**: Separate access and error logs
- **Process Management**: PID file, process naming
- **Security**: Request size limits, timeout settings

### 2. **Startup Scripts**
- `start_prod.sh` - Full production startup (migrations + static files + Gunicorn)
- `start_gunicorn.sh` - Quick Gunicorn startup
- `manage_gunicorn.sh` - Process management (start/stop/restart/reload/status/logs)

### 3. **Systemd Service** (Optional)
- `mpesa-gunicorn.service` - For running as system service
- Auto-restart on failure, proper user/group settings

### 4. **Testing Tools**
- `test_gunicorn.py` - Comprehensive Gunicorn configuration and startup testing

## 🚀 How to Start Your Application

### **Recommended (Production):**
```bash
./start_prod.sh
```
This runs migrations, collects static files, then starts Gunicorn.

### **Quick Start (If already set up):**
```bash
./start_gunicorn.sh
```
Just starts Gunicorn without migrations/static collection.

### **Process Management:**
```bash
./manage_gunicorn.sh start     # Start server
./manage_gunicorn.sh stop      # Stop server  
./manage_gunicorn.sh restart   # Restart server
./manage_gunicorn.sh reload    # Graceful reload (no downtime)
./manage_gunicorn.sh status    # Check status
./manage_gunicorn.sh logs      # View recent logs
```

### **Manual Start:**
```bash
cd /home/devops/MPESA/mpesa
/home/devops/MPESA/mpesa/venv/bin/gunicorn --config gunicorn.conf.py config.wsgi:application
```

## 🌐 Access URLs

- **Local**: http://localhost:5000
- **Production**: https://www.digilaboratory.org (via Cloudflare tunnel)

## 📡 Cloudflare Tunnel Update Required

Update your `cloudflared` configuration to use the new port:

```yaml
tunnel: your-tunnel-id
credentials-file: /path/to/credentials.json

ingress:
  - hostname: www.digilaboratory.org
    service: http://localhost:5000  # ← Changed from 8000 to 5000
  - hostname: digilaboratory.org
    service: http://localhost:5000  # ← Changed from 8000 to 5000
  - service: http_status:404
```

Then restart your cloudflared tunnel:
```bash
cloudflared tunnel restart your-tunnel-name
```

## 📊 Current Status

✅ **Gunicorn Configuration**: Valid and optimized  
✅ **Server Startup**: Successfully tested  
✅ **HTTP Responses**: Working (200 OK for /payments/, 302 redirect for /)  
✅ **Django Integration**: Fully compatible  
✅ **Cloudflare Ready**: Port 5000 configured  
✅ **Production Ready**: Security headers, logging, error handling  

## 📈 Performance Benefits

### **Gunicorn vs Django Dev Server:**
- **Concurrent Requests**: Multiple workers handle simultaneous requests
- **Process Management**: Auto-restart on crashes, graceful reloads
- **Resource Efficiency**: Better memory and CPU usage
- **Production Features**: Proper logging, PID management, signal handling
- **Scalability**: Easy to add more workers as load increases

### **Current Configuration:**
- **Workers**: Auto-calculated based on your CPU cores
- **Worker Type**: Sync (good for Django apps)
- **Timeout**: 30 seconds
- **Keep-Alive**: 60 seconds
- **Max Requests**: 1000 per worker (prevents memory leaks)

## 📋 Log Files

Your application logs are in the `logs/` directory:
- `logs/gunicorn_access.log` - HTTP access logs
- `logs/gunicorn_error.log` - Application errors
- `logs/gunicorn.pid` - Process ID file
- `logs/security.log` - Security events (M-Pesa callbacks, validation failures)
- `logs/django.log` - General Django application logs

## 🔧 Optional: System Service Setup

To run as a system service (starts automatically on boot):

```bash
# Copy service file
sudo cp mpesa-gunicorn.service /etc/systemd/system/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable mpesa-gunicorn
sudo systemctl start mpesa-gunicorn

# Check status
sudo systemctl status mpesa-gunicorn
```

## 🧪 Testing Your Setup

1. **Test Configuration**: `python test_gunicorn.py`
2. **Test HTTP Response**: `curl http://localhost:5000/`
3. **Test Payment Form**: `curl http://localhost:5000/payments/`
4. **Check Logs**: `./manage_gunicorn.sh logs`
5. **Test M-Pesa Callback**: Use your callback testing tools

## 🔒 Security Notes

- **HTTPS**: Still handled by Cloudflare (external termination)
- **Security Headers**: All Django security headers active
- **IP Detection**: Properly handles Cloudflare's real IP headers
- **M-Pesa Validation**: All callback security measures intact
- **Process Isolation**: Each worker runs in separate process
- **Graceful Shutdowns**: Prevents request interruption

## 🚦 Next Steps

1. **Update Cloudflare Tunnel**: Point to localhost:5000
2. **Test Production**: Verify https://www.digilaboratory.org works
3. **Monitor Logs**: Check logs for any issues
4. **Performance Tuning**: Adjust workers if needed based on traffic
5. **Backup**: Your application is now production-ready!

Your M-Pesa application is now running with enterprise-grade Gunicorn server on port 5000! 🎉
