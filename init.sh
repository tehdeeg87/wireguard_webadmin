#!/bin/bash
set -e

echo "[init] Starting D-Bus..."
/etc/init.d/dbus start

echo "[init] Starting Avahi Daemon..."
# Ensure Avahi knows about your WireGuard interface (wg0)
sed -i '/^\[server\]/a allow-interfaces=wg0' /etc/avahi/avahi-daemon.conf || true

# Launch Avahi in the background
avahi-daemon -D

echo "[init] Starting WireGuard service..."
# Starts each WireGuard configuration file found in /etc/wireguard
shopt -s nullglob
config_files=(/etc/wireguard/*.conf)
if [ ${#config_files[@]} -gt 0 ]; then
    for f in "${config_files[@]}"; do
        wg-quick up "$(basename "${f}" .conf)"
    done
fi

# Open UDP 5353 for mDNS traffic on WireGuard interface
iptables -A INPUT -i wg0 -p udp --dport 5353 -j ACCEPT
iptables -A OUTPUT -o wg0 -p udp --dport 5353 -j ACCEPT

echo "[init] Generating Avahi hosts file from database..."
python manage.py shell -c "
from mdns.avahi_integration import generate_avahi_hosts_file
generate_avahi_hosts_file()
print('Avahi hosts file generated from database')
"

echo "[init] Starting Django app..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec python manage.py runserver 0.0.0.0:8000
