#!/usr/bin/env python3
"""
Test script for the new DNS solution
Tests the API endpoints and peer hostname functionality
"""

import requests
import json
import sys

def test_api_endpoints():
    """Test the new DNS API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing DNS Solution API Endpoints")
    print("=" * 50)
    
    # Test 1: JSON API endpoint
    print("\n1. Testing JSON API endpoint...")
    try:
        response = requests.get(f"{base_url}/api/peers/hosts/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ JSON API working - Found {len(data)} peer mappings")
            for ip, hostname in data.items():
                print(f"   {ip} → {hostname}")
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
            print("Hosts file content:")
            print(data['hosts_content'])
        else:
            print(f"❌ Legacy API failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Legacy API error: {e}")
    
    # Test 3: Test with curl command
    print("\n3. Testing with curl command...")
    print("Run this command to test:")
    print(f"curl -s {base_url}/api/peers/hosts/ | jq -r 'to_entries[] | \"\\(.value) \\(.key)\"'")
    
    print("\n" + "=" * 50)
    print("✅ DNS Solution API testing completed!")

def test_peer_resolution():
    """Test peer hostname resolution"""
    print("\n🔍 Testing Peer Hostname Resolution")
    print("=" * 50)
    
    # Get peer data
    try:
        response = requests.get("http://localhost:8000/api/peers/hosts/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            print(f"Found {len(data)} peer hostnames:")
            for ip, hostname in data.items():
                print(f"  {hostname} → {ip}")
                
            print("\nTo test resolution, run these commands:")
            for ip, hostname in data.items():
                print(f"  ping {hostname}")
                print(f"  nslookup {hostname}")
        else:
            print("❌ Failed to get peer data")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_endpoints()
    test_peer_resolution()

