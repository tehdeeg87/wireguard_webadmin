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

exec python manage.py runserver 0.0.0.0:8000
