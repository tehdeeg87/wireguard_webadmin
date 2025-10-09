#!/bin/bash
set -e

# Lets wait for the DNS container to start
sleep 5

# Starts each WireGuard configuration file found in /etc/wireguard
shopt -s nullglob
config_files=(/etc/wireguard/*.conf)
if [ ${#config_files[@]} -gt 0 ]; then
    for f in "${config_files[@]}"; do
        wg-quick up "$(basename "${f}" .conf)"
    done
fi

# Django startup
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Set up hosts file updater
if [ -x "/app/start_hosts_updater.sh" ]; then
    # Start background hosts file updater
    nohup /app/start_hosts_updater.sh > /var/log/hosts_updater.log 2>&1 &
    echo "[init] Background hosts file updater started"
else
    echo "[init] WARNING: start_hosts_updater.sh not executable, fixing permissions"
    chmod +x /app/start_hosts_updater.sh
    nohup /app/start_hosts_updater.sh > /var/log/hosts_updater.log 2>&1 &
    echo "[init] Background hosts file updater started (after fixing permissions)"
fi

# Initial hosts file update
if [ -f "/shared_hosts/hosts" ]; then
    cp /shared_hosts/hosts /etc/hosts
    echo "[init] Initial hosts file update completed"
else
    echo "[init] WARNING: Shared hosts file not found, will retry when available"
fi

# Setup dnsmasq DNS server
echo "[init] Setting up dnsmasq DNS server..."

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

# Cache size
cache-size=1000
EOF

# Start dnsmasq
service dnsmasq start
echo "[init] dnsmasq DNS server started"

exec python manage.py runserver 0.0.0.0:8000
