#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from wireguard.models import Peer

print("=== Setting Hostnames for Peers ===")

# Get all peers
peers = Peer.objects.all()

if len(peers) >= 2:
    # Set hostnames for your peers
    peer1 = peers[0]
    peer2 = peers[1]
    
    # Set hostnames (you can change these names)
    peer1.hostname = "phone"  # or "laptop", "desktop", etc.
    peer1.save()
    print(f"Set hostname '{peer1.hostname}' for peer '{peer1.name or 'Unnamed'}'")
    
    peer2.hostname = "laptop"  # or "server", "desktop", etc.
    peer2.save()
    print(f"Set hostname '{peer2.hostname}' for peer '{peer2.name or 'Unnamed'}'")
    
    print("\nHostnames set successfully!")
    print("Now you can ping 'phone' and 'laptop' from your VPN clients")
else:
    print("Not enough peers found to set hostnames")
