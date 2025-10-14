#!/usr/bin/env python3
"""
Test the specific JWT token from the Manage button
"""
import jwt
import json
import requests
from datetime import datetime

# The JWT token from the Manage button
manage_button_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJwb3J0YnJvLmNvbSIsInN1YiI6IjgxIiwiYXVkIjoidnBuLW5vZGVzIiwiaWF0IjoxNzYwMDMyNjAyLCJleHAiOjE3NjAxMTkwMDIsInNjb3BlIjoicmVhZCB3cml0ZSIsInVzZXJfaWQiOjgxLCJ1c2VybmFtZSI6ImRhbiIsImVtYWlsIjoiZGdpbGxpczc3QGdtYWlsLmNvbSIsImlzX2FjdGl2ZSI6dHJ1ZSwiaXNfc3RhZmYiOmZhbHNlLCJpc19zdXBlcnVzZXIiOmZhbHNlLCJjbGllbnRfaWQiOiJJaGJ3QWRWbVZFcVFwUGxya0E4OThuR2VZNmFzb0wzSWpCODRiZUJMIiwiY2xpZW50X25hbWUiOiJVc2VyIEpXVCBHZW5lcmF0b3IgLSBkYW4ifQ.oD_lBbmKaVusU7aUohinZCKdER5oAahVn5u6fN8o0TDTwezIsbBV6pVSjnqb2j63dn7_dtqJEmUb8rIf8DDlhYiRfC-Eej1Nc4bmCwe2PQEjK2iqTOgVHjbMypPPqZ7pxhafYNzQAJEh7rlHHd2pdpnXNgKqw0c-8JQF5l6H_89mC5roUr_IcPAUul6AyV4i8boaCPZWLnLCNT-07a8WVmzpGrjZGe9vlMhJkbsZGqdzGJPQfGbecRvYBXD7Gg8caLepJIKZq_r7ICWL5wtQEYsVMv64LhQhYNd0mySiZ4mPMZN53K9pzEMSx58e6WKfW21Avb5GwzoSJzk-z1B6KQ"

# Your RSA public key
rsa_public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAiaGItq0JK2JxMf66rTqF
efn6jVWcpFOn9y7c5eFJM4+FFrr0yFGtcH9DevSYP8nREFYEpTnJckILK1AHDiZl
9KUh3nQTUW1ZKnlT6WLSgUjTc2AiT5kpe5HU9Fq8hL4VL4hEcCnWcdhQZA+/gEnh
R/98OUwGnWgWeai0noLaI53bthm8vyBz2G6VxQ52ZVhfuOmxTHeXvHTWciDUO81/
NInA+iyiuOOP/U4yQP1eFbwyDZA6Tvn9P2Tx5b+FF4azYYjl/BHCEoJNeHGRwRDw
ErY3serZYpd4vzHlWjnrSFV1yTQ8K8DtFMbefpE4A4VpHFFvKlx8r574rNVxBz+p
5wIDAQAB
-----END PUBLIC KEY-----"""

def test_manage_button_token():
    print("🔍 Testing Manage Button JWT Token")
    print("=" * 50)
    
    # Test 1: Decode without verification
    print("\n1️⃣ Decoding JWT without verification:")
    try:
        decoded_unverified = jwt.decode(manage_button_token, options={"verify_signature": False})
        print("✅ JWT decoded successfully!")
        print("📋 JWT Claims:")
        print(json.dumps(decoded_unverified, indent=2))
        
        # Check expiration
        exp = decoded_unverified.get('exp', 0)
        current_time = int(datetime.now().timestamp())
        if exp > current_time:
            print(f"✅ Token is valid until: {datetime.fromtimestamp(exp)}")
        else:
            print(f"❌ Token expired at: {datetime.fromtimestamp(exp)}")
            
    except Exception as e:
        print(f"❌ Error decoding JWT: {e}")
        return
    
    # Test 2: Verify with RSA public key
    print("\n2️⃣ Verifying JWT with RSA public key:")
    try:
        decoded_verified = jwt.decode(
            manage_button_token, 
            rsa_public_key, 
            algorithms=["RS256"],
            audience="vpn-nodes",
            issuer="portbro.com"
        )
        print("✅ JWT verification successful!")
        print("📋 Verified Claims:")
        print(json.dumps(decoded_verified, indent=2))
        
    except jwt.ExpiredSignatureError:
        print("❌ JWT token has expired")
    except jwt.InvalidAudienceError:
        print("❌ Invalid audience - expected 'vpn-nodes'")
    except jwt.InvalidIssuerError:
        print("❌ Invalid issuer - expected 'portbro.com'")
    except jwt.InvalidSignatureError:
        print("❌ Invalid signature - token was not signed with this key")
    except Exception as e:
        print(f"❌ JWT verification failed: {e}")
    
    # Test 3: Try JWKS validation
    print("\n3️⃣ Testing JWKS validation:")
    try:
        # Get JWKS from portbro.com
        jwks_response = requests.get("https://portbro.com/o/jwks/", timeout=10)
        if jwks_response.status_code == 200:
            jwks_data = jwks_response.json()
            print("✅ JWKS retrieved successfully")
            print(f"JWKS keys: {len(jwks_data.get('keys', []))}")
            
            # Try to validate with JWKS
            from authlib.jose import JsonWebKey
            jwks = JsonWebKey.import_key_set(jwks_data)
            
            # This is how the middleware tries to validate
            claims = jwt.decode(manage_button_token, jwks)
            print("✅ JWT validation with JWKS successful!")
            print("📋 JWKS Verified Claims:")
            print(json.dumps(claims, indent=2))
            
        else:
            print(f"❌ Failed to get JWKS: {jwks_response.status_code}")
            
    except Exception as e:
        print(f"❌ JWKS validation failed: {e}")

if __name__ == "__main__":
    test_manage_button_token()
