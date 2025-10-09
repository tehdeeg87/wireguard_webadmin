#!/bin/bash

# Background hosts file updater
# This runs in the background to update hosts file every 2 minutes

while true; do
    if [ -f "/shared_hosts/hosts" ]; then
        # Copy shared hosts file to /etc/hosts
        cp /shared_hosts/hosts /etc/hosts
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Updated /etc/hosts from shared hosts file"
        
        # Reload dnsmasq if it's running
        if systemctl is-active --quiet dnsmasq; then
            systemctl reload dnsmasq
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Reloaded dnsmasq DNS server"
        fi
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: Shared hosts file not found"
    fi
    sleep 120  # Wait 2 minutes
done
