#!/bin/bash
set -e

echo "Initializing DNS configuration for portbro.vpn..."

# Create shared_hosts directory
mkdir -p /shared_hosts

# Add hosts file configuration to dnsmasq with custom domain
echo "addn-hosts=/shared_hosts/hosts_static" >> /etc/dnsmasq.conf
echo "domain=portbro.vpn" >> /etc/dnsmasq.conf
echo "expand-hosts" >> /etc/dnsmasq.conf

# Kill any existing dnsmasq processes
pkill -f dnsmasq || true
rm -f /run/dnsmasq/dnsmasq.pid

# Start dnsmasq with our configuration
dnsmasq --no-daemon --log-queries --addn-hosts=/shared_hosts/hosts_static --domain=portbro.vpn --expand-hosts &

echo "DNS initialization complete for portbro.vpn domain"
