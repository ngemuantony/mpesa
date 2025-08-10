# Cloudflare Tunnel Redirect Issue Resolution Guide

## Problem Summary
You were experiencing redirect issues when accessing your Django M-Pesa application through Cloudflare tunnels at `www.digilaboratory.org`.

## Root Causes Identified
1. **SSL Redirect Loop**: Django's `SECURE_SSL_REDIRECT = True` was conflicting with Cloudflare's HTTPS termination
2. **Missing Proxy Headers**: Django wasn't configured to trust Cloudflare's proxy headers
3. **IP Detection Issues**: Application couldn't properly detect real client IPs through Cloudflare

## Solutions Implemented

### 1. Fixed SSL Redirect Configuration
```python
# Before (causing redirect loops)
SECURE_SSL_REDIRECT = not DEBUG

# After (Cloudflare-compatible)
CLOUDFLARE_TUNNEL = env.bool('CLOUDFLARE_TUNNEL', default=True)
SECURE_SSL_REDIRECT = False if CLOUDFLARE_TUNNEL else not DEBUG
```

### 2. Added Cloudflare Proxy Support
```python
if CLOUDFLARE_TUNNEL:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True
```

### 3. Enhanced IP Detection
- Already supported `HTTP_CF_CONNECTING_IP` header
- Added Cloudflare IP ranges to trusted proxies
- Maintained security for M-Pesa callbacks

## Deployment Instructions

### For Production (Cloudflare Tunnel):
```bash
# Use the production script
./start_prod.sh

# Or manually:
export DEBUG=False
export CLOUDFLARE_TUNNEL=True
python manage.py runserver 0.0.0.0:8000
```

### For Local Development:
```bash
# Use the development script
./start_dev.sh

# Or manually:
export DEBUG=True
export CLOUDFLARE_TUNNEL=False
python manage.py runserver
```

## Verification Steps

1. **Test Configuration**:
```bash
python cloudflare_test.py
```

2. **Check Django Settings**:
```bash
python manage.py check
```

3. **Test Redirect Behavior**:
```bash
# Should not have redirect loops
curl -I https://www.digilaboratory.org/
```

## Cloudflare Tunnel Configuration

Make sure your `cloudflared` configuration includes:

```yaml
tunnel: your-tunnel-id
credentials-file: /path/to/credentials.json

ingress:
  - hostname: www.digilaboratory.org
    service: http://localhost:5000
  - hostname: digilaboratory.org
    service: http://localhost:5000
  - service: http_status:404
```

## Key Settings for Cloudflare Tunnels

### ✅ Correct Settings:
- `SECURE_SSL_REDIRECT = False` (when using Cloudflare tunnels)
- `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`
- `USE_X_FORWARDED_HOST = True`
- Domain in `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`

### ❌ Problematic Settings:
- `SECURE_SSL_REDIRECT = True` (causes redirect loops)
- Missing proxy headers configuration
- Not trusting Cloudflare IPs

## Troubleshooting Common Issues

### Issue: "Too Many Redirects" Error
**Cause**: Django trying to redirect HTTP to HTTPS when Cloudflare already handles this
**Solution**: Set `SECURE_SSL_REDIRECT = False` for Cloudflare tunnels

### Issue: CSRF Verification Failed
**Cause**: Django doesn't trust the domain due to proxy headers
**Solution**: Add domain to `CSRF_TRUSTED_ORIGINS` and configure proxy headers

### Issue: Real IP Not Detected
**Cause**: Not reading Cloudflare's IP headers
**Solution**: Our callback security already handles `HTTP_CF_CONNECTING_IP`

## Security Considerations

1. **M-Pesa Callbacks**: Still properly validated using Safaricom IP whitelist
2. **HTTPS**: Enforced by Cloudflare (external) rather than Django (internal)
3. **Real IP**: Correctly extracted for logging and security
4. **CSRF Protection**: Maintained with proper trusted origins

## Testing Your Setup

1. Visit `https://www.digilaboratory.org/` - should load without redirect loops
2. Test payment form functionality
3. Verify M-Pesa callbacks still work (test with callback URL)
4. Check logs for proper IP detection

## Environment Variables

Create a `.env` file in your project root:
```bash
DEBUG=False
CLOUDFLARE_TUNNEL=True
SECRET_KEY=your-secret-key-here
MPESA_CONSUMER_KEY=your-mpesa-consumer-key
MPESA_CONSUMER_SECRET=your-mpesa-consumer-secret
```

## Next Steps

1. **Deploy**: Use `./start_prod.sh` to start your application
2. **Monitor**: Check logs for any remaining issues
3. **Test**: Verify all functionality works through Cloudflare tunnel
4. **Scale**: Consider using Gunicorn for production instead of Django's dev server

Your Django application should now work properly with Cloudflare tunnels without redirect issues!
