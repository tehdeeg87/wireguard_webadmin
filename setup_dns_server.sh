#!/bin/bash

# Setup dnsmasq as a DNS server for WireGuard hostname resolution

set -e

echo "Setting up dnsmasq DNS server for WireGuard hostnames..."

# Install dnsmasq
apt-get update
apt-get install -y dnsmasq

# Create dnsmasq configuration
cat > /etc/dnsmasq.d/wireguard-hosts.conf << 'EOF'
# WireGuard Peer Hostnames
# This file is automatically updated by the DNS cron container
# Do not edit manually

# Listen on WireGuard interfaces
interface=wg0
interface=wg1
interface=wg2
interface=wg3
interface=wg4
interface=wg5
interface=wg6
interface=wg7

# Use hosts file for local resolution
addn-hosts=/shared_hosts/hosts

# Don't read /etc/hosts
no-hosts

# Log DNS queries for debugging
log-queries
log-dhcp

# Cache size
cache-size=1000
EOF

# Create a script to update dnsmasq when hosts file changes
cat > /usr/local/bin/update_dnsmasq_hosts.sh << 'EOF'
#!/bin/bash
# Reload dnsmasq when hosts file is updated
if [ -f "/shared_hosts/hosts" ]; then
    systemctl reload dnsmasq
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Reloaded dnsmasq with updated hosts file"
fi
EOF

chmod +x /usr/local/bin/update_dnsmasq_hosts.sh

# Start and enable dnsmasq
systemctl enable dnsmasq
systemctl start dnsmasq

echo "dnsmasq DNS server setup complete!"
echo "DNS server is now running on WireGuard interfaces"
echo "Hostname resolution should work for connected peers"
