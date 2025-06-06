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
python manage.py makemigrations orders --noinput
python manage.py migrate orders --noinput
python manage.py collectstatic --noinput
exec python manage.py runserver 0.0.0.0:8000
