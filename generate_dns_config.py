#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from wireguard.models import Peer, PeerAllowedIP
from dns.functions import generate_dnsmasq_config

print("=== Generating DNS Configuration ===")

# Generate the DNS configuration
dns_config = generate_dnsmasq_config()

# Save to a Windows-compatible location
windows_dns_path = "dns_config.conf"
with open(windows_dns_path, 'w') as f:
    f.write(dns_config)

print(f"DNS configuration saved to: {windows_dns_path}")
print("\nConfiguration content:")
print(dns_config)

print("\n=== Next Steps ===")
print("1. You need to run a DNS server (like dnsmasq) with this configuration")
print("2. Or configure your WireGuard server to use a different DNS solution")
print("3. Make sure your VPN clients use the correct DNS server IP")
