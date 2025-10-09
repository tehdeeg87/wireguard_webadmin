#!/bin/bash
# Don't exit on error for D-Bus/Avahi startup

echo "[init] Starting D-Bus..."
# Check if D-Bus init script exists, otherwise start dbus-daemon directly
if [ -f /etc/init.d/dbus ]; then
    /etc/init.d/dbus start
else
    echo "[init] Starting D-Bus daemon directly..."
    dbus-daemon --system --fork
fi

echo "[init] Starting Avahi Daemon..."
# Check if Avahi is available
if command -v avahi-daemon >/dev/null 2>&1; then
    echo "[init] Avahi found, starting daemon..."
    
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
    echo "[init] Avahi daemon started"
else
    echo "[init] Avahi not available, skipping mDNS setup"
    echo "[init] To enable mDNS, rebuild the container with Avahi installed"
fi

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

# Register existing peers with Avahi (if available)
echo "[init] Registering peers with Avahi..."
if command -v avahi-daemon >/dev/null 2>&1; then
    python manage.py register_peers_avahi
    echo "[init] Peers registered with Avahi"
else
    echo "[init] Skipping Avahi registration (Avahi not available)"
fi

exec python manage.py runserver 0.0.0.0:8000
