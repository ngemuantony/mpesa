#!/bin/bash

# M-Pesa Callback Testing Script
# This script provides easy commands to test various callback scenarios

BASE_URL="http://localhost:5000"
CALLBACK_ENDPOINT="/payments/callback0126bT36857/"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}M-Pesa Enhanced Callback Security Testing${NC}"
echo "=================================================="

# Test 1: Valid callback from localhost (development)
echo -e "\n${YELLOW}Test 1: Valid callback from localhost${NC}"
curl -X POST "$BASE_URL$CALLBACK_ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.1" \
  -H "User-Agent: TestClient/1.0" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "TEST-LOCAL-001",
        "CheckoutRequestID": "ws_CO_LOCAL_TEST_001",
        "ResultCode": 0,
        "ResultDesc": "Test successful payment from localhost",
        "CallbackMetadata": {
          "Item": [
            {
              "Name": "Amount",
              "Value": 100.00
            },
            {
              "Name": "MpesaReceiptNumber",
              "Value": "TEST001"
            },
            {
              "Name": "PhoneNumber",
              "Value": 254718643064
            }
          ]
        }
      }
    }
  }' && echo -e "\n${GREEN}✓ Local test completed${NC}"

# Test 2: Valid callback from Safaricom IP
echo -e "\n${YELLOW}Test 2: Valid callback from Safaricom IP${NC}"
curl -X POST "$BASE_URL$CALLBACK_ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 196.201.214.200" \
  -H "User-Agent: Safaricom-MpesaCallback/1.0" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "SAFARICOM-TEST-001",
        "CheckoutRequestID": "ws_CO_SAFARICOM_001",
        "ResultCode": 0,
        "ResultDesc": "Successful payment from Safaricom IP",
        "CallbackMetadata": {
          "Item": [
            {
              "Name": "Amount",
              "Value": 500.00
            },
            {
              "Name": "MpesaReceiptNumber",
              "Value": "SAF001"
            },
            {
              "Name": "PhoneNumber",
              "Value": 254700000000
            }
          ]
        }
      }
    }
  }' && echo -e "\n${GREEN}✓ Safaricom IP test completed${NC}"

# Test 3: Failed transaction callback
echo -e "\n${YELLOW}Test 3: Failed transaction callback${NC}"
curl -X POST "$BASE_URL$CALLBACK_ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 196.201.214.206" \
  -H "User-Agent: Safaricom-MpesaCallback/1.0" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "FAILED-TEST-001",
        "CheckoutRequestID": "ws_CO_FAILED_001",
        "ResultCode": 1032,
        "ResultDesc": "Request cancelled by user"
      }
    }
  }' && echo -e "\n${GREEN}✓ Failed transaction test completed${NC}"

# Test 4: Unauthorized IP (should be rejected)
echo -e "\n${YELLOW}Test 4: Unauthorized IP (should be rejected)${NC}"
curl -X POST "$BASE_URL$CALLBACK_ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 192.168.1.100" \
  -H "User-Agent: UnauthorizedBot/1.0" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "UNAUTHORIZED-001",
        "CheckoutRequestID": "ws_CO_UNAUTHORIZED_001",
        "ResultCode": 0,
        "ResultDesc": "This should be rejected"
      }
    }
  }' && echo -e "\n${RED}✗ This request should have been rejected${NC}"

# Test 5: Malformed JSON (should be rejected)
echo -e "\n${YELLOW}Test 5: Malformed JSON (should be rejected)${NC}"
curl -X POST "$BASE_URL$CALLBACK_ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 196.201.214.200" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "MALFORMED-001"
        "CheckoutRequestID": "ws_CO_MALFORMED_001",
      }
    }
  }' && echo -e "\n${RED}✗ This malformed JSON should have been rejected${NC}"

# Test 6: Health check
echo -e "\n${YELLOW}Test 6: Health check (GET request)${NC}"
curl -X GET "$BASE_URL$CALLBACK_ENDPOINT" \
  -H "X-Forwarded-For: 196.201.214.200" \
  -H "User-Agent: Safaricom-HealthCheck/1.0" && echo -e "\n${GREEN}✓ Health check completed${NC}"

echo -e "\n${BLUE}All callback security tests completed!${NC}"
echo "Check your Django logs for detailed security validation results."
echo "Expected: Tests 1, 2, 3, and 6 should succeed. Tests 4 and 5 should be rejected."
