#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from wireguard.models import Peer, PeerAllowedIP
from dns.functions import generate_dnsmasq_config

print("=== Checking Peers with Hostnames ===")
peers_with_hostnames = Peer.objects.filter(hostname__isnull=False).exclude(hostname='')

if peers_with_hostnames:
    print(f"Found {peers_with_hostnames.count()} peers with hostnames:")
    for peer in peers_with_hostnames:
        # Get the peer's IP address
        peer_ip = PeerAllowedIP.objects.filter(
            peer=peer, 
            config_file='server', 
            priority=0
        ).first()
        
        instance_name = peer.wireguard_instance.name or f"wg{peer.wireguard_instance.instance_id}"
        ip_addr = peer_ip.allowed_ip if peer_ip else "No IP assigned"
        
        print(f"  - {peer.hostname} -> {ip_addr} (instance: {instance_name})")
else:
    print("No peers have hostnames set!")

print("\n=== Generating DNS Configuration ===")
try:
    dns_config = generate_dnsmasq_config()
    print("DNS Configuration generated successfully!")
    print("\nConfiguration preview:")
    print(dns_config[:500] + "..." if len(dns_config) > 500 else dns_config)
except Exception as e:
    print(f"Error generating DNS config: {e}")

print("\n=== DNS Configuration File Path ===")
from django.conf import settings
print(f"Config file path: {settings.DNS_CONFIG_FILE}")
