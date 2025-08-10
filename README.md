# M-Pesa STK Push Integration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-5.2+-green.svg)](https://www.djangoproject.com/)
[![Gunicorn](https://img.shields.io/badge/gunicorn-ready-brightgreen.svg)](https://gunicorn.org/)

## Overview

This implementation provides a complete, production-ready M-Pesa STK Push integration with enterprise-grade security features, comprehensive callback validation, print-friendly receipts, and Cloudflare tunnel support. Built with Django and optimized for high-traffic scenarios using Gunicorn.

### Key Features

- 🔒 **Enterprise Security**: Multi-layer callback validation with IP whitelisting and HMAC verification
- 🖨️ **Print-Friendly Receipts**: Clean, professional PDF-ready transaction receipts
- ☁️ **Cloudflare Ready**: Optimized for Cloudflare tunnel deployments
- 🚀 **Production Ready**: Gunicorn WSGI server with optimized configuration
- 📊 **Comprehensive Logging**: Structured security logging with data sanitization
- 🛡️ **Input Validation**: XSS and injection attack prevention
- 📱 **Responsive Design**: Mobile-first UI with Bootstrap 5
- 🔍 **Transaction Tracking**: Complete audit trail for all payments

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Security Features](#enhanced-security-features)
- [API Documentation](#api-endpoints)
- [Usage Examples](#example-usage)
- [Deployment](#deployment)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)
- [Authors](#authors)
- [Disclaimer](#disclaimer)

## Installation

### Prerequisites

- Python 3.8+
- Django 5.2+
- PostgreSQL/MySQL (recommended) or SQLite (development)
- Redis (for production caching)
- SSL certificate (for production)

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ngemuantony/mpesa.git
   cd mpesa
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your M-Pesa credentials
   ```

5. **Database setup**
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```

6. **Run development server**
   ```bash
   ./start_dev.sh
   ```

### Production Deployment

For production deployment with Gunicorn:

```bash
# Production setup
./start_prod.sh

# Or with systemd service
sudo cp mpesa-gunicorn.service /etc/systemd/system/
sudo systemctl enable mpesa-gunicorn
sudo systemctl start mpesa-gunicorn
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Configuration
DEBUG=False
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (Production)
DATABASE_URL=postgresql://user:password@localhost/dbname

# M-Pesa Configuration
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=your_shortcode
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://yourdomain.com/payments/callback/

# Cloudflare Tunnel Support
CLOUDFLARE_TUNNEL=True

# Security
MPESA_HMAC_SECRET=your-callback-hmac-secret
ENABLE_CALLBACK_SECURITY=True
```

## Enhanced Security Features

### Multi-Layer Security System
The system implements comprehensive security for M-Pesa callbacks:

1. **IP Whitelisting**: Validates requests against official Safaricom IP addresses
2. **HMAC Signature Validation**: Cryptographic validation of callback authenticity  
3. **Structure Validation**: Ensures callback payloads have proper format and required fields
4. **Rate Limiting**: Prevents callback flooding and abuse
5. **Comprehensive Logging**: Detailed security event logging and monitoring

### Security Configuration

To configure enhanced callback security in your settings:

```python
# M-Pesa Security Configuration
MPESA_SECURITY = {
    'ENABLE_HMAC_VALIDATION': True,  # Enable HMAC signature validation
    'ENABLE_STRUCTURE_VALIDATION': True,  # Enable payload structure validation
    'HMAC_SECRET_KEY': 'your-secret-key',  # HMAC secret (defaults to Django SECRET_KEY)
    'CALLBACK_TIMEOUT': 300,  # Callback timeout in seconds (5 minutes)
    'MAX_CALLBACK_RATE': 100,  # Max callbacks per minute per IP
}
```

### Callback Security Usage

```python
from mpesa.callback_security import EnhancedCallbackSecurity

# Initialize security system
security = EnhancedCallbackSecurity(
    enable_hmac=True,
    enable_structure_validation=True
)

# Validate incoming callback
result = security.validate_callback(request, view)

if result['overall_status'] == 'approved':
    # Process callback
    process_mpesa_callback(request.data)
else:
    # Reject callback
    return Response({'error': 'Security validation failed'}, status=403)
```

## API Endpoints

### 1. Initiate STK Push Payment
**Endpoint:** `POST /payments/checkout/`

**Request Body:**
```json
{
    "phone_number": "0718643064",
    "amount": 100,
    "reference": "INV-2024-001",
    "description": "Payment for services"
}
```

**Response:**
```json
{
    "MerchantRequestID": "29115-34620561-1",
    "CheckoutRequestID": "ws_CO_191220191020363925",
    "ResponseCode": "0",
    "ResponseDescription": "Success. Request accepted for processing",
    "CustomerMessage": "Success. Request accepted for processing"
}
```

### 2. Query STK Push Status
**Endpoint:** `POST /payments/query/`

**Request Body:**
```json
{
    "checkout_request_id": "ws_CO_191220191020363925"
}
```

**Response:**
```json
{
    "ResponseCode": "0",
    "ResponseDescription": "The service request has been accepted successfully",
    "MerchantRequestID": "29115-34620561-1",
    "CheckoutRequestID": "ws_CO_191220191020363925",
    "ResultCode": "0",
    "ResultDesc": "The service request is processed successfully.",
    "local_transaction": {
        "transaction_no": "432930cf-222d-421e-9151-bc4b7b296f9c",
        "phone_number": "+254718643064",
        "amount": "100",
        "status": "0",
        "receipt_no": "NLJ7RT61SV",
        "created": "2025-08-04T02:05:13.577718Z"
    }
}
```

### 3. Callback Endpoint (Internal Use)
**Endpoint:** `POST /payments/callback/`

This endpoint receives callbacks from Safaricom and is IP-whitelisted for security.

## Data Flow

1. **Initiate Payment**: Client calls `/payments/checkout/`
2. **STK Push Sent**: User receives STK push on their phone
3. **User Responds**: User enters PIN or cancels
4. **Callback Received**: Safaricom sends callback to `/payments/callback/`
5. **Transaction Updated**: Local database is updated with final status
6. **Query Status**: Client can query status using `/payments/query/`

## Transaction Status Codes

- `0`: Complete/Successful
- `1`: Pending/Failed

## Phone Number Formats Supported

- `0718643064` → Converted to `254718643064`
- `+254718643064` → Converted to `254718643064`
- `254718643064` → Remains as is

## Security Features

- IP whitelisting for callback endpoint (Safaricom IPs only)
- CSRF protection
- Input validation and sanitization
- Error logging and monitoring

## Example Usage

### Using curl:

```bash
# Initiate payment
curl -X POST http://127.0.0.1:8000/payments/checkout/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "0718643064",
    "amount": 100,
    "reference": "INV-2024-001",
    "description": "Payment for services"
  }'

# Query payment status
curl -X POST http://127.0.0.1:8000/payments/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "checkout_request_id": "ws_CO_191220191020363925"
  }'
```

### Using JavaScript:

```javascript
// Initiate payment
const initiatePayment = async (phoneNumber, amount, reference, description) => {
    const response = await fetch('/payments/checkout/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            phone_number: phoneNumber,
            amount: amount,
            reference: reference,
            description: description
        })
    });
    return await response.json();
};

// Query payment status
const queryPayment = async (checkoutRequestId) => {
    const response = await fetch('/payments/query/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            checkout_request_id: checkoutRequestId
        })
    });
    return await response.json();
};
```

## Environment Variables Required

```bash
consumer_key=your_consumer_key
consumer_secret=your_consumer_secret
shortcode=your_shortcode
pass_key=your_passkey
access_token_url=https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials
checkout_url=https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest
mpesa_query_check_url=https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query
c2b_callback=https://yourdomain.com/payments/callback/
```

## Error Handling

## Error Handling

The system handles various error scenarios:
- Invalid phone numbers
- Network timeouts
- Invalid access tokens
- Callback validation failures
- Database errors

All errors are logged for debugging and monitoring purposes.

## Deployment

### Production Deployment Options

#### 1. Traditional Server Deployment

```bash
# Using Gunicorn with systemd
sudo cp mpesa-gunicorn.service /etc/systemd/system/
sudo systemctl enable mpesa-gunicorn
sudo systemctl start mpesa-gunicorn
sudo systemctl status mpesa-gunicorn
```

#### 2. Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "config.wsgi:application"]
```

#### 3. Cloudflare Tunnel Integration

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Create tunnel
cloudflared tunnel create mpesa-tunnel
cloudflared tunnel route dns mpesa-tunnel yourdomain.com

# Run tunnel
cloudflared tunnel --config config.yml run
```

### Performance Optimization

- **Gunicorn Workers**: Configured based on CPU cores (2 * cores + 1)
- **Database Connection Pooling**: Optimized for high-traffic scenarios
- **Static File Serving**: Nginx recommended for production
- **Caching**: Redis integration for session and query caching

## Testing

### Running Tests

```bash
# Unit tests
python manage.py test mpesa

# Security tests
python test_security.py

# Integration tests
python test_integration.py

# Print functionality tests
python test_print.py
```

### Test Coverage

```bash
# Install coverage
pip install coverage

# Run with coverage
coverage run --source='.' manage.py test mpesa
coverage report -m
coverage html
```

### Manual Testing

Use the provided curl commands or test scripts:

```bash
# Test payment initiation
./test_payment.sh

# Test callback security
./test_callback_security.sh

# Test print functionality
./test_print_receipts.sh
```

## Contributing

We welcome contributions! Please follow these guidelines:

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/mpesa.git
   cd mpesa
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Pre-commit hooks**
   ```bash
   pre-commit install
   ```

### Code Standards

- **Python**: Follow PEP 8 style guidelines
- **Documentation**: Update README.md for new features
- **Testing**: Write tests for all new functionality
- **Security**: Follow OWASP security practices
- **Logging**: Use structured logging for all operations

### Pull Request Process

1. Update documentation
2. Add/update tests
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Submit pull request with detailed description

### Code Review Checklist

- [ ] Code follows project style guidelines
- [ ] Tests cover new functionality
- [ ] Documentation is updated
- [ ] Security implications considered
- [ ] Performance impact assessed
- [ ] Backward compatibility maintained

## License

This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2025 Anthony Ngemu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Authors

### Lead Developer
**Anthony Ngemu**
- GitHub: [@ngemuantony](https://github.com/ngemuantony)
- Email: ngemuantony@gmail.com
- LinkedIn: [Anthony Ngemu](https://linkedin.com/in/anthony-ngemu)

### Contributors
- Special thanks to all contributors who have helped improve this project
- Django and Python community for excellent frameworks and libraries
- Safaricom for the M-Pesa API documentation and support

## Acknowledgments

- **Django Framework**: Robust web framework for rapid development
- **Gunicorn**: Reliable Python WSGI HTTP Server
- **Bootstrap**: Responsive front-end framework
- **Cloudflare**: CDN and security services
- **Safaricom**: M-Pesa API and payment gateway

## Disclaimer

### Important Notice

This software is provided for educational and development purposes. Please note:

⚠️ **Production Use Disclaimer**
- This implementation is designed for learning and development
- Thoroughly test in sandbox environment before production deployment
- Implement additional security measures as required by your use case
- Regular security audits and updates are recommended

⚠️ **Financial Transaction Responsibility**
- Users are responsible for compliance with financial regulations
- Implement proper transaction logging and audit trails
- Ensure PCI DSS compliance for card data handling
- Follow local banking and payment processing regulations

⚠️ **API Terms and Conditions**
- Comply with Safaricom's M-Pesa API terms of service
- Respect rate limits and usage guidelines
- Implement proper error handling and retry mechanisms
- Monitor API usage and costs

⚠️ **Security Considerations**
- Regularly update dependencies for security patches
- Implement proper access controls and authentication
- Use HTTPS in production environments
- Sanitize and validate all user inputs
- Follow OWASP security guidelines

### Support

For support and questions:
- Create an issue on GitHub
- Check existing documentation and FAQ
- Review test files for usage examples
- Join community discussions

### Changelog

See `CHANGELOG.md` for version history and updates.

---

**Built with ❤️ by Anthony Ngemu**

*Making M-Pesa integration simple, secure, and scalable.*
