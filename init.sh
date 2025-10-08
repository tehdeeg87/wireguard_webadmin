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

# Start Avahi daemon for mDNS peer discovery
echo "Starting Avahi daemon for mDNS peer discovery..."
mkdir -p /etc/avahi/hosts

# Create Avahi configuration for WireGuard
cat > /etc/avahi/avahi-daemon.conf << 'EOF'
[server]
allow-interfaces=wg0
use-ipv4=yes
use-ipv6=no
enable-reflector=yes

[wide-area]
enable-wide-area=yes

[legacy]
enable-dbus=yes
EOF

# Start D-Bus and Avahi
dbus-daemon --system &
sleep 2
avahi-daemon --no-drop-root --debug &

# Open UDP 5353 for mDNS traffic
iptables -A INPUT -i wg0 -p udp --dport 5353 -j ACCEPT
iptables -A OUTPUT -o wg0 -p udp --dport 5353 -j ACCEPT

echo "Avahi daemon started for mDNS peer discovery"

# Django startup
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec python manage.py runserver 0.0.0.0:8000
