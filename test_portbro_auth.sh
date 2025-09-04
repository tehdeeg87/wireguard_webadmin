#!/bin/bash

# Test script for Portbro OAuth2 and JWT authentication
# This script implements the exact flow you provided

echo "Testing Portbro OAuth2 and JWT authentication flow..."
echo "=================================================="

# 1. Get OAuth2 token
echo "Step 1: Getting OAuth2 token..."
TOKEN_RESPONSE=$(curl -X POST https://portbro.com/o/token/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&scope=read" \
  -u "yDPrlW2u1iiSbT9ABseK6fAGwN2nWhIFsO7i3CCm:dur3nwcu6KYvFgS3LZngtIbFg1cjj7lgB52NMpcZiG6bd1ltp7jF9uHCqnQFfCXfgw1j8leaobnY4XrSJuBN3GEZkbYtv24uZJdLzO4gyp5A4B93neu4Y7WSyb5vLgTO")

echo "OAuth2 Response: $TOKEN_RESPONSE"

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
    echo "ERROR: Failed to get OAuth2 access token"
    exit 1
fi

echo "OAuth2 Access Token: ${ACCESS_TOKEN:0:20}..."

# 2. Get JWT token for VPN authentication
echo ""
echo "Step 2: Getting JWT token for VPN authentication..."
JWT_RESPONSE=$(curl -X POST https://portbro.com/vpn/auth/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json")

echo "JWT Response: $JWT_RESPONSE"

JWT_TOKEN=$(echo $JWT_RESPONSE | jq -r '.access_token')

if [ "$JWT_TOKEN" = "null" ] || [ -z "$JWT_TOKEN" ]; then
    echo "ERROR: Failed to get JWT token"
    exit 1
fi

echo "JWT Token: ${JWT_TOKEN:0:20}..."

# 3. Test using JWT token for VPN operations
echo ""
echo "Step 3: Testing JWT token with VPN node..."
VPN_RESPONSE=$(curl -X GET http://localhost:8000/auth/vpn/status/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json")

echo "VPN Node Response: $VPN_RESPONSE"

# 4. Test JWT token validation
echo ""
echo "Step 4: Testing JWT token validation..."
echo "JWT Token (first 50 chars): ${JWT_TOKEN:0:50}..."

# Decode JWT header and payload (without verification)
echo "JWT Header:"
echo $JWT_TOKEN | cut -d. -f1 | base64 -d 2>/dev/null | jq . 2>/dev/null || echo "Could not decode header"

echo "JWT Payload:"
echo $JWT_TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq . 2>/dev/null || echo "Could not decode payload"

echo ""
echo "Authentication flow completed successfully!"
echo "You can now use the JWT token for VPN operations:"
echo "Authorization: Bearer $JWT_TOKEN"

