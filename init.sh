#!/bin/bash
set -e

# Lets wait for the DNS container to start
sleep 5

# Check for and handle corrupted WireGuard config files
# Auto-clean corrupted configs if CLEAR_CORRUPTED_CONFIGS environment variable is set
if [ "${CLEAR_CORRUPTED_CONFIGS,,}" == "true" ]; then
    echo "[init] Checking for corrupted WireGuard config files..."
    shopt -s nullglob
    config_files=(/etc/wireguard/*.conf)
    corrupted_files=()
    
    for f in "${config_files[@]}"; do
        interface_name="$(basename "${f}" .conf)"
        # Test if config is valid by trying to parse it
        if ! wg setconf "$interface_name" "$f" 2>/dev/null; then
            # Check if it's a key format error
            if wg-quick up "$interface_name" 2>&1 | grep -q "Key is not the correct length\|Configuration parsing error"; then
                corrupted_files+=("$f")
            fi
        fi
    done
    
    if [ ${#corrupted_files[@]} -gt 0 ]; then
        echo "[init] Found ${#corrupted_files[@]} corrupted config file(s), removing..."
        for f in "${corrupted_files[@]}"; do
            rm -f "$f"
            echo "[init] Removed corrupted config: $f"
        done
    fi
fi

# Starts each WireGuard configuration file found in /etc/wireguard
# Skip corrupted config files and log warnings
shopt -s nullglob
config_files=(/etc/wireguard/*.conf)
if [ ${#config_files[@]} -gt 0 ]; then
    for f in "${config_files[@]}"; do
        interface_name="$(basename "${f}" .conf)"
        echo "[init] Attempting to start WireGuard interface: $interface_name"
        
        # Try to start the interface, but don't fail if it's corrupted
        if wg-quick up "$interface_name" 2>&1; then
            echo "[init] Successfully started WireGuard interface: $interface_name"
        else
            error_output=$(wg-quick up "$interface_name" 2>&1 || true)
            if echo "$error_output" | grep -q "Key is not the correct length\|Configuration parsing error"; then
                echo "[init] ERROR: Config file $f appears to be corrupted (invalid key format)."
                echo "[init] Skipping this interface. To fix: delete $f and regenerate from web interface."
                echo "[init] Or run: python manage.py clear_wireguard_configs"
                echo "[init] Or set CLEAR_CORRUPTED_CONFIGS=true environment variable to auto-clean on startup"
            else
                echo "[init] WARNING: Failed to start WireGuard interface: $interface_name"
                echo "[init] Error: $error_output"
            fi
        fi
    done
else
    echo "[init] No WireGuard configuration files found in /etc/wireguard/"
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

# Create dnsmasq configuration directory
mkdir -p /etc/dnsmasq.d

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
