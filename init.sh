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

# Set up hosts file update cron job
if command -v crontab >/dev/null 2>&1; then
    echo "*/2 * * * * /app/update_hosts_from_shared.sh" | crontab -
    service cron start
    echo "[init] Cron service started for hosts file updates"
else
    echo "[init] WARNING: crontab not available, hosts file updates will be manual"
fi

# Initial hosts file update
/app/update_hosts_from_shared.sh

exec python manage.py runserver 0.0.0.0:8000
