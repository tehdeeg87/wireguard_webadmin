#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/app')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from wireguard.models import Peer, PeerAllowedIP

print("=== PEERS ===")
for peer in Peer.objects.all():
    print(f"UUID: {peer.uuid}, Name: '{peer.name}', Hostname: '{peer.hostname}'")

print("\n=== PEER ALLOWED IPS ===")
for pa in PeerAllowedIP.objects.all():
    print(f"Peer: {pa.peer.name}, IP: {pa.allowed_ip}")

print("\n=== API SIMULATION ===")
data = {}
for peer in Peer.objects.all():
    allowed_ip = PeerAllowedIP.objects.filter(peer=peer).first()
    if allowed_ip and peer.hostname:
        data[allowed_ip.allowed_ip] = peer.hostname
        print(f"Adding: {allowed_ip.allowed_ip} -> {peer.hostname}")
    else:
        print(f"Skipping peer {peer.name}: allowed_ip={allowed_ip}, hostname='{peer.hostname}'")

print(f"\nFinal data: {data}")
