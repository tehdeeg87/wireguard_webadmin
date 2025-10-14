#!/usr/bin/env python3
"""
Test JWT validation with the provided RSA keys
"""
import jwt
import json
from datetime import datetime

# Your JWT token
token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJwb3J0YnJvLmNvbSIsInN1YiI6IjgxIiwiYXVkIjoidnBuLW5vZGVzIiwiaWF0IjoxNzYwMDQ0MDM2LCJleHAiOjE3NjAxMzA0MzYsInNjb3BlIjoicmVhZCB3cml0ZSIsInVzZXJfaWQiOjgxLCJ1c2VybmFtZSI6ImRhbiIsImVtYWlsIjoiZGdpbGxpczc3QGdtYWlsLmNvbSIsImlzX2FjdGl2ZSI6dHJ1ZSwiaXNfc3RhZmYiOmZhbHNlLCJpc19zdXBlcnVzZXIiOmZhbHNlLCJjbGllbnRfaWQiOiJJaGJ3QWRWbVZFcVFwUGxya0E4OThuR2VZNmFzb0wzSWpCODRiZUJMIiwiY2xpZW50X25hbWUiOiJVc2VyIEpXVCBHZW5lcmF0b3IgLSBkYW4ifQ.DEhGjwYWbetH5Pb43kXmU8rcq62kifFDjVyYgbnorGZfEoMnJMvDWeGPYkBTFGy-48dLlD8hhhnTmWAHwIhoWpbWG2BrFruDVJQP4KM_nCX19_ZcXjaMMJhJ-_Kl33SsYtDTjB6fNRnVKFxRo1hAdrN95MxKIMQJnFepKVbaBb8x-jjo2FimM4mLajOKsyuCye2I8ucdpAzfr_fnCbznPJkZgQXX0zwG_LeFLBchr06SvCzcR6GJm2vHhUBADbTqDHlGRV8C3IkZoV5MU00SIwKeXhrN-kMxDBL7f9WO-t6ElLvXIuUbA9EHCkYClhwoyYGkzDE59pKmv9Scq9w"

# Your RSA keys
private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCJoYi2rQkrYnEx
/rqtOoV5+fqNVZykU6f3Ltzl4Ukzj4UWuvTIUa1wf0N69Jg/ydEQVgSlOclyQgsr
UAcOJmX0pSHedBNRbVkqeVPpYtKBSNNzYCJPmSl7kdT0WryEvhUviERwKdZx2FBk
D7+ASeFH/3w5TAadaBZ5qLSegtojndu2Gby/IHPYbpXFDnZlWF+46bFMd5e8dNZy
INQ7zX80icD6LKK444/9TjJA/V4VvDINkDpO+f0/ZPHlv4UXhrNhiOX8EcISgk14
cZHBEPAStjex6tlil3i/MeVaOetIVXXJNDwrwO0Uxt5+kTgDhWkcUW8qXHyvnvis
1XEHP6nnAgMBAAECggEAAZJnOdLjGmw+57fFkQnskVaSDoAuUFAmSHPwEO4QRHb8
qaRL/Ge2Z+UEM8jMXlojOaEJ34s36kan0wBQfFBi9LbYGq7Ps6vgi1QkabN3vQNE
avprmeYha6hgOsQ4h/mVy1uukGth6B302Re287OkT4qy9AKSxsR0EUKkgXT0Idj8
6jwwSFIjKH6AxdfTvciha1JENYOhELF00gM4cypicKWldJLiAqV1wjx5h+PYN4AM
7WKH6eTFf6yVYoR+gYKiMPNDyCOFXhbKNdu0xedQL893Rz/NiGhhONxEAkLYkfKG
Axw4/wcIlbXo/fi9PH8Fv6c/pxJh8N5Wmfe0NeF6nQKBgQC9NmgH3LXg7mWt0678
JKbB1LmuIwA0Rt9Qdmiun0ovqRxyIQES22ZbdrDMz1x8MTITFV16zX/X/AyJRM9T
zmWSHvll8g+D4tL4w1pSTjtzckFb9/nZVUGKTR7I8ak3VMEa0aVMYB+xKXWuvtaa
lI1oYpEvDhfvnGMBuPgOn57sUwKBgQC6NiAAS8j6VFjYxpYr5JBfJcqYA7qRWbPJ
itbw+sucfNyZgPwp7xz1stODwjdVYG3t6YF7IMs9kJz2iAMqnWOVWKK+qUkJ0esU
3thxWHgVzusqfN0RFLgLxuYuLyfurZreFb8f7zCAPTtmK45sccmTZBOZGKogOky7
2ZiT9+T5nQKBgQCi9z82tlQ4fVw6ET5/kRnHjG64mxDL9dbVOIcFD9EXp7IGYoLI
OQu570prvJXNqZmVcitnX6Oi5UXu3MMtTXGSHvdzZL8UOsK225rplNQDpP7CNZyO
Ia4nbjD7pZi3PVpsvPCADbJ+JlVjwp6X2SbKJ0sgmiTnjWyAyU1tWvHIXQKBgDkt
vY3Zt5EGrXGDKUG5IYvV8uvS2UsgnFBazb2ZhUQ8IxEPxl6qCd54VvKyhIM25QqV
FSlV3JK/ATPCeBZx1c5aNT8OhFr7lpAGDbhgTh+ENjoJtWg1UH5tSOkNmdl0fYWM
b+/CZsY6By9MWKN8HUWhCVONe1ACFuXn3y4whKMRAoGAU6aMU9sq4yPXCtZ8Ezig
Y8JIfB+Mtpr0BsGYoeBIlXx1qq5K+pfglNh2m5949VnpGKNqNUPg0+FTyq8OxVlR
F7mJnu9iyFu+YVBhfOWKutNkUmYwh6t/K/7Ex14ESZxCuXEfXl9p7Dqt/3qsVQuk
Ft41RWPeCWTS5UxQDruLC+o=
-----END PRIVATE KEY-----"""

public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAiaGItq0JK2JxMf66rTqF
efn6jVWcpFOn9y7c5eFJM4+FFrr0yFGtcH9DevSYP8nREFYEpTnJckILK1AHDiZl
9KUh3nQTUW1ZKnlT6WLSgUjTc2AiT5kpe5HU9Fq8hL4VL4hEcCnWcdhQZA+/gEnh
R/98OUwGnWgWeai0noLaI53bthm8vyBz2G6VxQ52ZVhfuOmxTHeXvHTWciDUO81/
NInA+iyiuOOP/U4yQP1eFbwyDZA6Tvn9P2Tx5b+FF4azYYjl/BHCEoJNeHGRwRDw
ErY3serZYpd4vzHlWjnrSFV1yTQ8K8DtFMbefpE4A4VpHFFvKlx8r574rNVxBz+p
5wIDAQAB
-----END PUBLIC KEY-----"""

def test_jwt_validation():
    print("🔍 Testing JWT Validation with RSA Keys")
    print("=" * 50)
    
    # Test 1: Decode without verification to see the structure
    print("\n1️⃣ Decoding JWT without verification:")
    try:
        decoded_unverified = jwt.decode(token, options={"verify_signature": False})
        print("✅ JWT decoded successfully!")
        print("📋 JWT Header:")
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
    
    # Test 2: Verify with public key
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
    
    # Test 3: Test with different audiences/issuers
    print("\n3️⃣ Testing with different validation options:")
    
    # Test without audience/issuer validation
    try:
        decoded_no_validation = jwt.decode(token, public_key, algorithms=["RS256"])
        print("✅ JWT verification successful (no audience/issuer validation)")
    except Exception as e:
        print(f"❌ JWT verification failed: {e}")
    
    # Test 4: Check what the VPN node should be doing
    print("\n4️⃣ VPN Node Configuration Requirements:")
    print("The VPN node should be configured with:")
    print(f"  - Algorithm: RS256")
    print(f"  - Public Key: {public_key[:50]}...")
    print(f"  - Audience: vpn-nodes")
    print(f"  - Issuer: portbro.com")
    
    # Test 5: Generate a test token with the private key
    print("\n5️⃣ Testing token generation with private key:")
    try:
        test_claims = {
            "iss": "portbro.com",
            "sub": "test_user",
            "aud": "vpn-nodes",
            "iat": int(datetime.now().timestamp()),
            "exp": int(datetime.now().timestamp()) + 3600,
            "username": "test_user",
            "email": "test@portbro.com"
        }
        
        test_token = jwt.encode(test_claims, private_key, algorithm="RS256")
        print("✅ Test token generated successfully!")
        
        # Verify the test token
        test_decoded = jwt.decode(test_token, public_key, algorithms=["RS256"])
        print("✅ Test token verification successful!")
        print(f"Test token: {test_token[:50]}...")
        
    except Exception as e:
        print(f"❌ Test token generation/verification failed: {e}")

if __name__ == "__main__":
    test_jwt_validation()
