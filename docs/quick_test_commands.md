# Quick M-Pesa Callback Test Commands

## 1. Simple Valid Callback (Localhost - Should Work)
```bash
curl -X POST http://localhost:8000/payments/callback0126bT36857/ \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.1" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "TEST-001",
        "CheckoutRequestID": "ws_CO_TEST_001",
        "ResultCode": 0,
        "ResultDesc": "Test successful payment"
      }
    }
  }'
```

## 2. Valid Callback from Safaricom IP (Should Work)
```bash
curl -X POST http://localhost:8000/payments/callback0126bT36857/ \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 196.201.214.200" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "SAFARICOM-001",
        "CheckoutRequestID": "ws_CO_SAFARICOM_001",
        "ResultCode": 0,
        "ResultDesc": "Successful payment from Safaricom"
      }
    }
  }'
```

## 3. Unauthorized IP Test (Should be Rejected)
```bash
curl -X POST http://localhost:8000/payments/callback0126bT36857/ \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 192.168.1.100" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "UNAUTHORIZED-001", 
        "CheckoutRequestID": "ws_CO_UNAUTHORIZED_001",
        "ResultCode": 0,
        "ResultDesc": "This should be rejected"
      }
    }
  }'
```

## 4. Health Check (Should Work)
```bash
curl -X GET http://localhost:8000/payments/callback0126bT36857/ \
  -H "X-Forwarded-For: 196.201.214.200"
```

## 5. Complete Payment Callback with Metadata
```bash
curl -X POST http://localhost:8000/payments/callback0126bT36857/ \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.1" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "COMPLETE-001",
        "CheckoutRequestID": "ws_CO_COMPLETE_001", 
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
              "Value": "TEST123456"
            },
            {
              "Name": "TransactionDate",
              "Value": 20250810000000
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

Expected Results:
- Commands 1, 2, 4, 5: Should return success (200 response)
- Command 3: Should return 403 Forbidden (IP not whitelisted)
