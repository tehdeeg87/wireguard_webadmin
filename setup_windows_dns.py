#!/usr/bin/env python
import os
import subprocess
import sys

print("=== Windows DNS Setup Options ===")
print()
print("Since you're on Windows, here are your options to get DNS working:")
print()
print("OPTION 1: Use Windows built-in DNS server")
print("1. Open 'Services' (services.msc)")
print("2. Find 'DNS Server' service")
print("3. Start it if not running")
print("4. Configure it to use the generated dns_config.conf")
print()
print("OPTION 2: Install dnsmasq for Windows")
print("1. Download dnsmasq for Windows")
print("2. Run: dnsmasq.exe --conf-file=dns_config.conf")
print()
print("OPTION 3: Use Docker with dnsmasq")
print("1. Install Docker Desktop")
print("2. Run: docker run -d --name dnsmasq -p 53:53/udp -v $(pwd)/dns_config.conf:/etc/dnsmasq.conf dnsmasq")
print()
print("OPTION 4: Use a different DNS solution")
print("1. Configure your WireGuard server to use a different DNS server")
print("2. Set up hostname resolution in your router or another DNS server")
print()
print("Current DNS config file: dns_config.conf")
print("This file contains the peer hostname mappings.")
