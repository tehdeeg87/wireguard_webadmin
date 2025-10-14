#!/usr/bin/env python3
"""
Test the JWT endpoint to see what's being returned
"""
import requests
import json

def test_jwt_endpoint():
    # Test the JWT endpoint
    url = "https://can1-vpn.portbro.com/jwt-token-async/"
    
    print("🔍 Testing JWT Endpoint")
    print("=" * 50)
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Response JSON:")
            print(json.dumps(data, indent=2))
            
            # Check if token field exists
            if 'token' in data:
                print("✅ 'token' field found in response")
                print(f"Token length: {len(data['token'])}")
                print(f"Token preview: {data['token'][:50]}...")
            else:
                print("❌ 'token' field NOT found in response")
                print("Available fields:", list(data.keys()))
        else:
            print(f"❌ Error response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Raw response: {response.text}")

if __name__ == "__main__":
    test_jwt_endpoint()
