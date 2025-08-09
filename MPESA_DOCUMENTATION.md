# M-Pesa STK Push Integration

## Overview
This implementation provides complete M-Pesa STK Push integration with advanced security features, query functionality, and comprehensive callback validation.

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

The system handles various error scenarios:
- Invalid phone numbers
- Network timeouts
- Invalid access tokens
- Callback validation failures
- Database errors

All errors are logged for debugging and monitoring purposes.
