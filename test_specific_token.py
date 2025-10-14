#!/usr/bin/env python3
"""
Test the specific JWT token from the user's URL
"""
import jwt
import json
from datetime import datetime

# The specific JWT token from the user's URL
token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJwb3J0YnJvLmNvbSIsInN1YiI6IjgxIiwiYXVkIjoidnBuLW5vZGVzIiwiaWF0IjoxNzYwMDMyNjAyLCJleHAiOjE3NjAxMTkwMDIsInNjb3BlIjoicmVhZCB3cml0ZSIsInVzZXJfaWQiOjgxLCJ1c2VybmFtZSI6ImRhbiIsImVtYWlsIjoiZGdpbGxpczc3QGdtYWlsLmNvbSIsImlzX2FjdGl2ZSI6dHJ1ZSwiaXNfc3RhZmYiOmZhbHNlLCJpc19zdXBlcnVzZXIiOmZhbHNlLCJjbGllbnRfaWQiOiJJaGJ3QWRWbVZFcVFwUGxya0E4OThuR2VZNmFzb0wzSWpCODRiZUJMIiwiY2xpZW50X25hbWUiOiJVc2VyIEpXVCBHZW5lcmF0b3IgLSBkYW4ifQ.oD_lBbmKaVusU7aUohinZCKdER5oAahVn5u6fN8o0TDTwezIsbBV6pVSjnqb2j63dn7_dtqJEmUb8rIf8DDlhYiRfC-Eej1Nc4bmCwe2PQEjK2iqTOgVHjbMypPPqZ7pxhafYNzQAJEh7rlHHd2pdpnXNgKqw0c-8JQF5l6H_89mC5roUr_IcPAUul6AyV4i8boaCPZWLnLCNT-07a8WVmzpGrjZGe9vlMhJkbsZGqdzGJPQfGbecRvYBXD7Gg8caLepJIKZq_r7ICWL5wtQEYsVMv64LhQhYNd0mySiZ4mPMZN53K9pzEMSx58e6WKfW21Avb5GwzoSJzk-z1B6KQ"

# Your RSA public key
public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAiaGItq0JK2JxMf66rTqF
efn6jVWcpFOn9y7c5eFJM4+FFrr0yFGtcH9DevSYP8nREFYEpTnJckILK1AHDiZl
9KUh3nQTUW1ZKnlT6WLSgUjTc2AiT5kpe5HU9Fq8hL4VL4hEcCnWcdhQZA+/gEnh
R/98OUwGnWgWeai0noLaI53bthm8vyBz2G6VxQ52ZVhfuOmxTHeXvHTWciDUO81/
NInA+iyiuOOP/U4yQP1eFbwyDZA6Tvn9P2Tx5b+FF4azYYjl/BHCEoJNeHGRwRDw
ErY3serZYpd4vzHlWjnrSFV1yTQ8K8DtFMbefpE4A4VpHFFvKlx8r574rNVxBz+p
5wIDAQAB
-----END PUBLIC KEY-----"""

def test_token():
    print("🔍 Testing Specific JWT Token from User's URL")
    print("=" * 60)
    
    # Test 1: Decode without verification
    print("\n1️⃣ Decoding JWT without verification:")
    try:
        decoded_unverified = jwt.decode(token, options={"verify_signature": False})
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
            token, 
            public_key, 
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
    
    # Test 3: Check what the VPN node should be doing
    print("\n3️⃣ VPN Node Configuration Check:")
    print("The VPN node should be configured with:")
    print(f"  - Algorithm: RS256")
    print(f"  - Public Key: {public_key[:50]}...")
    print(f"  - Audience: vpn-nodes")
    print(f"  - Issuer: portbro.com")
    
    # Test 4: Check if this is a different signing key
    print("\n4️⃣ Signature Analysis:")
    try:
        # Try to decode the header to see what algorithm was used
        import base64
        header_data = token.split('.')[0]
        # Add padding if needed
        header_data += '=' * (4 - len(header_data) % 4)
        header = json.loads(base64.urlsafe_b64decode(header_data))
        print(f"JWT Header: {json.dumps(header, indent=2)}")
        
        if header.get('alg') != 'RS256':
            print(f"❌ Token uses {header.get('alg')} algorithm, not RS256")
        else:
            print("✅ Token uses RS256 algorithm")
            
    except Exception as e:
        print(f"❌ Error analyzing JWT header: {e}")

if __name__ == "__main__":
    test_token()
