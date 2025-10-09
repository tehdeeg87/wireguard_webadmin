#!/bin/bash
set -e

echo "[init] Starting D-Bus..."
/etc/init.d/dbus start

echo "[init] Starting Avahi Daemon..."
# Ensure Avahi knows about your WireGuard interfaces
# Copy our custom Avahi config if it doesn't exist
if [ ! -f /etc/avahi/avahi-daemon.conf ]; then
    mkdir -p /etc/avahi
    if [ -f ./mdns_config/avahi-daemon.conf ]; then
        cp ./mdns_config/avahi-daemon.conf /etc/avahi/avahi-daemon.conf
        echo "[init] Using custom Avahi configuration"
    else
        # Fallback to basic config
        cat > /etc/avahi/avahi-daemon.conf << 'EOF'
[server]
host-name=wireguard-webadmin
domain-name=local
allow-interfaces=wg0,wg1,wg2,wg3,wg4,wg5,wg6,wg7,wg8,wg9
use-ipv4=yes
use-ipv6=no
enable-dbus=yes
EOF
        echo "[init] Created basic Avahi configuration"
    fi
fi

# Create hosts directory for Avahi
mkdir -p /etc/avahi/hosts

# Launch Avahi in the background
avahi-daemon -D

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

# Register existing peers with Avahi
echo "[init] Registering peers with Avahi..."
python manage.py register_peers_avahi

exec python manage.py runserver 0.0.0.0:8000
