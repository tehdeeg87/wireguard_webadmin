#!/usr/bin/env python
import os
import sys
import django
import requests

# Add the project directory to Python path
sys.path.append('/app')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from wireguard.models import Peer, PeerAllowedIP

print("=== DIRECT DATABASE QUERY ===")
data = {}
for peer in Peer.objects.all():
    allowed_ip = PeerAllowedIP.objects.filter(peer=peer).first()
    if allowed_ip and peer.hostname:
        data[allowed_ip.allowed_ip] = peer.hostname
        print(f"Adding: {allowed_ip.allowed_ip} -> {peer.hostname}")

print(f"Direct query result: {data}")

print("\n=== API ENDPOINT TEST ===")
try:
    response = requests.get('http://localhost:8000/api/peers/hosts/')
    print(f"API Status: {response.status_code}")
    print(f"API Response: {response.text}")
except Exception as e:
    print(f"API Error: {e}")
