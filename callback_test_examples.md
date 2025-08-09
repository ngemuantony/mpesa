# M-Pesa Callback Testing with cURL

## Overview
This document provides comprehensive cURL examples for testing the enhanced M-Pesa callback security system.

## Test Scenarios

### 1. Valid Callback Request (Local Testing)

```bash
curl -X POST http://localhost:8000/payments/callback/ \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.1" \
  -H "User-Agent: Safaricom-MpesaCallback/1.0" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "29115-34620561-1",
        "CheckoutRequestID": "ws_CO_191220191020363925",
        "ResultCode": 0,
        "ResultDesc": "The service request is processed successfully.",
        "CallbackMetadata": {
          "Item": [
            {
              "Name": "Amount",
              "Value": 100.00
            },
            {
              "Name": "MpesaReceiptNumber", 
              "Value": "NLJ7RT61SV"
            },
            {
              "Name": "TransactionDate",
              "Value": 20191219102115
            },
            {
              "Name": "PhoneNumber",
              "Value": 254708374149
            }
          ]
        }
      }
    }
  }'
```

### 2. Valid Callback from Safaricom IP (Production-like)

```bash
curl -X POST http://localhost:8000/payments/callback/ \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 196.201.214.200" \
  -H "X-Real-IP: 196.201.214.200" \
  -H "User-Agent: Safaricom-MpesaCallback/1.0" \
  -H "X-Timestamp: $(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "TEST-MERCHANT-123",
        "CheckoutRequestID": "ws_CO_TEST_456789",
        "ResultCode": 0,
        "ResultDesc": "The service request is processed successfully.",
        "CallbackMetadata": {
          "Item": [
            {
              "Name": "Amount",
              "Value": 250.00
            },
            {
              "Name": "MpesaReceiptNumber",
              "Value": "TEST12345"
            },
            {
              "Name": "TransactionDate", 
              "Value": $(date +%Y%m%d%H%M%S)
            },
            {
              "Name": "PhoneNumber",
              "Value": 254718643064
            }
          ]
        }
      }
    }
  }'
```

### 3. Failed Transaction Callback

```bash
curl -X POST http://localhost:8000/payments/callback/ \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 196.201.214.206" \
  -H "User-Agent: Safaricom-MpesaCallback/1.0" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "29115-34620561-2", 
        "CheckoutRequestID": "ws_CO_191220191020363926",
        "ResultCode": 1032,
        "ResultDesc": "Request cancelled by user"
      }
    }
  }'
```

### 4. Test Unauthorized IP (Should be Rejected)

```bash
curl -X POST http://localhost:8000/payments/callback/ \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 192.168.1.100" \
  -H "User-Agent: UnauthorizedBot/1.0" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "UNAUTHORIZED-REQUEST",
        "CheckoutRequestID": "ws_CO_UNAUTHORIZED",
        "ResultCode": 0,
        "ResultDesc": "Fake callback attempt"
      }
    }
  }'
```

### 5. Test Malformed JSON (Should be Rejected)

```bash
curl -X POST http://localhost:8000/payments/callback/ \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 196.201.214.200" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "MALFORMED-JSON"
        "CheckoutRequestID": "ws_CO_MALFORMED",
        "ResultCode": 0
      }
    }
  }'
```

### 6. Test Missing Required Fields (Should be Rejected)

```bash
curl -X POST http://localhost:8000/payments/callback/ \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 196.201.214.200" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "INCOMPLETE-DATA"
      }
    }
  }'
```

### 7. Test with HMAC Signature (If HMAC validation enabled)

```bash
# Generate HMAC signature (example with openssl)
PAYLOAD='{"Body":{"stkCallback":{"MerchantRequestID":"HMAC-TEST-123","CheckoutRequestID":"ws_CO_HMAC_TEST","ResultCode":0,"ResultDesc":"HMAC test callback"}}}'
SECRET_KEY="your-secret-key"
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET_KEY" -binary | base64)

curl -X POST http://localhost:8000/payments/callback/ \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 196.201.214.200" \
  -H "X-Mpesa-Signature: $SIGNATURE" \
  -H "X-Timestamp: $(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" \
  -d "$PAYLOAD"
```

### 8. Test Health Check (GET Request)

```bash
curl -X GET http://localhost:8000/payments/callback/ \
  -H "X-Forwarded-For: 196.201.214.200" \
  -H "User-Agent: Safaricom-HealthCheck/1.0"
```

## Rate Limiting Test

### Test Multiple Requests (Rate Limiting)

```bash
# Send 5 rapid requests to test rate limiting
for i in {1..5}; do
  echo "Request $i:"
  curl -X POST http://localhost:8000/payments/callback/ \
    -H "Content-Type: application/json" \
    -H "X-Forwarded-For: 196.201.214.200" \
    -d "{
      \"Body\": {
        \"stkCallback\": {
          \"MerchantRequestID\": \"RATE-TEST-$i\",
          \"CheckoutRequestID\": \"ws_CO_RATE_$i\",
          \"ResultCode\": 0,
          \"ResultDesc\": \"Rate limit test $i\"
        }
      }
    }" && echo -e "\n---"
  sleep 0.1
done
```

## Expected Responses

### Successful Callback Response
```json
{
  "status": "success",
  "message": "Callback processed successfully"
}
```

### Security Rejection Response  
```json
{
  "status": "Rejected",
  "reason": "IP not whitelisted"
}
```

### Rate Limit Response
```json
{
  "status": "Rejected", 
  "reason": "Rate limit exceeded"
}
```

### Structure Validation Error
```json
{
  "status": "Rejected",
  "reason": "Structure validation failed"
}
```

## Testing Tips

1. **Local Development**: Use `127.0.0.1` or `localhost` in X-Forwarded-For header
2. **Production Testing**: Use official Safaricom IPs (196.201.214.200, etc.)
3. **Security Testing**: Try various unauthorized IPs to verify rejection
4. **Rate Limiting**: Send multiple rapid requests to test rate limiting
5. **Logging**: Check Django logs for detailed security validation results

## Environment Variables for Testing

```bash
# Set these before running tests
export MPESA_CONSUMER_KEY="your_consumer_key"
export MPESA_CONSUMER_SECRET="your_consumer_secret"  
export MPESA_SHORTCODE="your_shortcode"
export MPESA_PASSKEY="your_passkey"
export MPESA_CALLBACK_URL="https://yourdomain.com/payments/callback/"
```

## Monitoring Security Events

Check Django logs for security events:

```bash
# Monitor callback security events
tail -f /path/to/your/django.log | grep "M-Pesa callback\|SECURITY EVENT"
```

## Advanced Testing with Variables

```bash
# Set common variables
BASE_URL="http://localhost:8000"
CALLBACK_ENDPOINT="/payments/callback/"
SAFARICOM_IP="196.201.214.200"
LOCAL_IP="127.0.0.1"

# Test valid callback
curl -X POST "$BASE_URL$CALLBACK_ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: $SAFARICOM_IP" \
  -d @valid_callback.json

# Test unauthorized IP
curl -X POST "$BASE_URL$CALLBACK_ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 10.0.0.1" \
  -d @valid_callback.json
```
