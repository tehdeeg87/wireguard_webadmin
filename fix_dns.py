#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from wireguard.models import Peer, PeerAllowedIP
from dns.functions import generate_dnsmasq_config
from django.conf import settings

print("=== Current Peers ===")
peers = Peer.objects.all()
if peers:
    for peer in peers:
        peer_ip = PeerAllowedIP.objects.filter(
            peer=peer, 
            config_file='server', 
            priority=0
        ).first()
        ip_addr = peer_ip.allowed_ip if peer_ip else "No IP assigned"
        instance_name = peer.wireguard_instance.name or f"wg{peer.wireguard_instance.instance_id}"
        
        print(f"Name: {peer.name or 'Unnamed'}")
        print(f"Hostname: {peer.hostname or 'NOT SET'}")
        print(f"IP: {ip_addr}")
        print(f"Instance: {instance_name}")
        print("---")
else:
    print("No peers found!")

print("\n=== DNS Configuration ===")
try:
    dns_config = generate_dnsmasq_config()
    print("DNS config generated successfully!")
    print("Preview:")
    print(dns_config)
except Exception as e:
    print(f"Error: {e}")

print(f"\nDNS config file path: {settings.DNS_CONFIG_FILE}")
print("Note: This is a Linux path, but you're on Windows!")
