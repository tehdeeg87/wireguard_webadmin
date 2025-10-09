#!/usr/bin/env python
import os
import sys
import django
import requests
import json

# Add the project directory to Python path
sys.path.append('/app')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from wireguard.models import Peer, PeerAllowedIP

print("=== PRODUCTION SERVER DIAGNOSTIC ===")
print()

print("1. DIRECT DATABASE QUERY:")
data = {}
for peer in Peer.objects.all():
    allowed_ip = PeerAllowedIP.objects.filter(peer=peer).first()
    if allowed_ip:
        print(f"   Peer: {peer.name}")
        print(f"   Hostname: '{peer.hostname}'")
        print(f"   IP: {allowed_ip.allowed_ip}")
        if peer.hostname:
            data[allowed_ip.allowed_ip] = peer.hostname
        print()

print(f"Direct query result: {data}")
print()

print("2. API ENDPOINT TEST:")
try:
    response = requests.get('http://localhost:8000/api/peers/hosts/')
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    api_data = response.json()
    print(f"   Parsed: {api_data}")
except Exception as e:
    print(f"   Error: {e}")
print()

print("3. HOSTS FILE CHECK:")
try:
    with open('/etc/hosts', 'r') as f:
        hosts_content = f.read()
        print("   Current /etc/hosts content:")
        for line in hosts_content.split('\n'):
            if 'peer' in line.lower() or '10.188' in line:
                print(f"     {line}")
except Exception as e:
    print(f"   Error reading /etc/hosts: {e}")
print()

print("4. CRON CONTAINER STATUS:")
try:
    import subprocess
    result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
    print("   Running containers:")
    for line in result.stdout.split('\n'):
        if 'dns-cron' in line or 'wireguard' in line:
            print(f"     {line}")
except Exception as e:
    print(f"   Error checking containers: {e}")
