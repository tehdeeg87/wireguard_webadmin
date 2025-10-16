#!/usr/bin/env python
"""
Script to sync existing peer names to hostnames
Run this once to update existing peers
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from wireguard.models import Peer

def sync_existing_peers():
    """Sync name field to hostname field for all existing peers"""
    peers = Peer.objects.all()
    updated_count = 0
    
    print(f"Found {peers.count()} peers to check...")
    
    for peer in peers:
        if peer.name and peer.hostname != peer.name:
            old_hostname = peer.hostname
            peer.hostname = peer.name
            peer.save(update_fields=['hostname'])
            print(f"Updated peer '{peer.name}': hostname '{old_hostname}' -> '{peer.name}'")
            updated_count += 1
        else:
            print(f"Peer '{peer.name}' already synced (hostname: '{peer.hostname}')")
    
    print(f"\nSync complete! Updated {updated_count} peers.")
    return updated_count

if __name__ == '__main__':
    sync_existing_peers()

