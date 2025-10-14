#!/usr/bin/env python3
"""
Debug JWT Token Validation
Test the JWT token validation process
"""

import jwt
import time
import json
import base64

def decode_jwt_payload(token):
    """Decode JWT payload without verification"""
    try:
        # Split the token
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Decode the payload (middle part)
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        print(f"Error decoding JWT: {e}")
        return None

def test_jwt_validation():
    """Test JWT validation logic"""
    
    # Your JWT token
    token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJwb3J0YnJvLmNvbSIsInN1YiI6IjgxIiwiYXVkIjoidnBuLW5vZGVzIiwiaWF0IjoxNzYwMDQzNTM5LCJleHAiOjE3NjAxMjk5MzksInNjb3BlIjoicmVhZCB3cml0ZSIsInVzZXJfaWQiOjgxLCJ1c2VybmFtZSI6ImRhbiIsImVtYWlsIjoiZGdpbGxpczc3QGdtYWlsLmNvbSIsImlzX2FjdGl2ZSI6dHJ1ZSwiaXNfc3RhZmYiOmZhbHNlLCJpc19zdXBlcnVzZXIiOmZhbHNlLCJjbGllbnRfaWQiOiJJaGJ3QWRWbVZFcVFwUGxya0E4OThuR2VZNmFzb0wzSWpCODRiZUJMIiwiY2xpZW50X25hbWUiOiJVc2VyIEpXVCBHZW5lcmF0b3IgLSBkYW4ifQ.aQOwGyI5w0hMqR1otyscapKFqlP3hFeEFKn7KIguCJ8daEtIG95Me3U9O4SxhLaoVmRL2DgvV0iXvCURGEftgkJAzi5S_6W4B-4cVsAqISpLCfZtDwp88nhAC3QbkFDE4cO1nJJjwLqzjp7spvOQv9MBqn52Yx0ILzeo2RjFA-vTeOCpiSYjH1u0BsSeUxCZy3fRxiDdIcu5_RHXzdxcA-SMz70vDI-FgZ6yNLbaIuQGrt1cXC9f3RMuEE2bmCIaPDRudEDeyrz3MXpg-pxTmxYuzIpU8rgZtblUJLVIUVuFJ1tcQ6yIqJtjLxlgFVweEWQJ10KBlO6UE5oJDP744g"
    
    print("🔍 JWT Token Debug Analysis")
    print("=" * 50)
    
    # Decode the payload
    claims = decode_jwt_payload(token)
    if not claims:
        print("❌ Failed to decode JWT payload")
        return
    
    print("📋 JWT Claims:")
    for key, value in claims.items():
        print(f"  {key}: {value}")
    
    print(f"\n⏰ Current time: {int(time.time())}")
    print(f"⏰ Token issued at: {claims.get('iat', 'N/A')}")
    print(f"⏰ Token expires at: {claims.get('exp', 'N/A')}")
    
    # Check expiration
    current_time = int(time.time())
    exp_time = claims.get('exp', 0)
    if exp_time > current_time:
        print("✅ Token is not expired")
    else:
        print("❌ Token is expired")
        return
    
    # Check issuer
    issuer = claims.get('iss')
    expected_issuer = "portbro.com"
    print(f"\n🏷️  Issuer: '{issuer}' (expected: '{expected_issuer}')")
    if issuer == expected_issuer:
        print("✅ Issuer matches")
    else:
        print("❌ Issuer mismatch")
    
    # Check audience
    audience = claims.get('aud')
    expected_audience = "vpn-nodes"
    print(f"🎯 Audience: '{audience}' (expected: '{expected_audience}')")
    if audience == expected_audience:
        print("✅ Audience matches")
    else:
        print("❌ Audience mismatch")
    
    # Check username and email
    username = claims.get('username')
    email = claims.get('email')
    print(f"\n👤 Username: {username}")
    print(f"📧 Email: {email}")
    
    print(f"\n🔧 Django Settings Check:")
    print(f"  PARENT_ISSUER: 'portbro.com'")
    print(f"  PARENT_AUDIENCE: 'vpn-nodes'")
    
    # Simulate the validation logic
    print(f"\n🧪 Validation Test:")
    if claims.get("iss") != "portbro.com":
        print("❌ Issuer validation failed")
    else:
        print("✅ Issuer validation passed")
    
    if claims.get("aud") != "vpn-nodes":
        print("❌ Audience validation failed")
    else:
        print("✅ Audience validation passed")
    
    print(f"\n💡 Recommendation:")
    print("The JWT token appears to be valid. The issue might be:")
    print("1. JWT validation is failing due to network issues fetching JWKS")
    print("2. User creation is failing in ensure_user_from_jwt()")
    print("3. Login process is failing")
    print("\nTry accessing the URL directly to see the error message.")

if __name__ == "__main__":
    test_jwt_validation()
