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

print("=== TESTING EMPTY HOSTNAME SCENARIO ===")
print()

# Simulate what happens when hostname is empty
data = {}
for peer in Peer.objects.all():
    allowed_ip = PeerAllowedIP.objects.filter(peer=peer).first()
    print(f"Peer: {peer.name}")
    print(f"Hostname: '{peer.hostname}' (empty: {not peer.hostname})")
    print(f"IP: {allowed_ip.allowed_ip if allowed_ip else 'None'}")
    
    if allowed_ip and peer.hostname:
        data[allowed_ip.allowed_ip] = peer.hostname
        print(f"  -> ADDED: {allowed_ip.allowed_ip} -> {peer.hostname}")
    else:
        print(f"  -> SKIPPED: hostname='{peer.hostname}', allowed_ip={allowed_ip}")
    print()

print(f"Final API result: {data}")
print()

# Check if there's any fallback logic
print("=== CHECKING FOR FALLBACK LOGIC ===")
for peer in Peer.objects.all():
    allowed_ip = PeerAllowedIP.objects.filter(peer=peer).first()
    if allowed_ip and not peer.hostname:
        # This is what might be generating peer-2, peer-3
        fallback_name = f"peer-{peer.uuid.hex[:8]}"
        print(f"Peer {peer.name} has no hostname, fallback would be: {fallback_name}")
