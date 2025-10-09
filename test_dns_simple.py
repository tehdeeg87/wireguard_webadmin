#!/usr/bin/env python3
"""
Simple test script for the clean DNS solution
Tests the API endpoints and shows example usage
"""

import requests
import json
import sys

def test_api_endpoints():
    """Test the new DNS API endpoints"""
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing Clean DNS Solution")
    print("=" * 50)
    
    # Test 1: JSON API endpoint
    print("\n1. Testing JSON API endpoint...")
    try:
        response = requests.get(f"{base_url}/api/peers/hosts/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ JSON API working - Found {len(data)} peer mappings")
            if data:
                print("Peer mappings:")
                for ip, hostname in data.items():
                    print(f"   {ip} → {hostname}")
            else:
                print("   No peers with hostnames found")
        else:
            print(f"❌ JSON API failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ JSON API error: {e}")
    
    # Test 2: Legacy hosts file endpoint
    print("\n2. Testing legacy hosts file endpoint...")
    try:
        response = requests.get(f"{base_url}/api/peers/hosts/legacy/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Legacy API working - {data['peer_count']} peers")
            if data['hosts_content']:
                print("Hosts file content:")
                print(data['hosts_content'])
            else:
                print("   No peer hostnames to display")
        else:
            print(f"❌ Legacy API failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Legacy API error: {e}")
    
    # Test 3: Show curl command examples
    print("\n3. Curl command examples:")
    print(f"curl -s {base_url}/api/peers/hosts/")
    print(f"curl -s {base_url}/api/peers/hosts/ | jq -r 'to_entries[] | \"\\(.value) \\(.key)\"'")
    
    print("\n" + "=" * 50)
    print("✅ DNS Solution testing completed!")

if __name__ == "__main__":
    test_api_endpoints()
