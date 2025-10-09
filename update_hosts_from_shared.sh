#!/bin/bash

# Script to copy shared hosts file to /etc/hosts
# This should be run periodically in the main WireGuard container

SHARED_HOSTS="/shared_hosts/hosts"
TARGET_HOSTS="/etc/hosts"

if [ -f "$SHARED_HOSTS" ]; then
    # Create backup of current hosts file
    cp "$TARGET_HOSTS" "${TARGET_HOSTS}.backup.$(date +%s)"
    
    # Copy the shared hosts file to /etc/hosts
    cp "$SHARED_HOSTS" "$TARGET_HOSTS"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Updated /etc/hosts from shared hosts file"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: Shared hosts file not found at $SHARED_HOSTS"
fi
