#!/usr/bin/env python3
"""
HADDNS Peer Mapping Setup Script
Creates the peer_hostnames.json mapping file for HADDNS
"""

import json
import os
import sys
import subprocess
from pathlib import Path

def get_wireguard_peers():
    """Get WireGuard peer information from the database"""
    try:
        # Try to get peer info from Django management command
        result = subprocess.run([
            'python', 'manage.py', 'shell', '-c',
            '''
from wireguard.models import WireguardPeer
peers = []
for peer in WireguardPeer.objects.all():
    peers.append({
        "public_key": peer.public_key,
        "name": peer.name or f"peer_{peer.id}",
        "ip_address": peer.ip_address
    })
print(json.dumps(peers))
            '''
        ], capture_output=True, text=True, cwd='/app')
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"Error getting peers from Django: {result.stderr}")
            return []
    except Exception as e:
        print(f"Error accessing Django: {e}")
        return []

def create_peer_mapping():
    """Create peer_hostnames.json mapping file"""
    print("Setting up HADDNS peer mapping...")
    
    # Get peer information
    peers = get_wireguard_peers()
    
    if not peers:
        print("No peers found. Please add some WireGuard peers first.")
        return False
    
    # Create mapping structure
    mapping = {}
    for peer in peers:
        public_key = peer['public_key']
        hostname = f"{peer['name']}.vpn.local"
        ip_address = peer['ip_address']
        
        mapping[public_key] = {
            "hostname": hostname,
            "ip": ip_address
        }
        
        print(f"Mapped: {peer['name']} -> {hostname} ({ip_address})")
    
    # Write mapping file
    mapping_file = "/etc/wireguard/peer_hostnames.json"
    try:
        with open(mapping_file, 'w') as f:
            json.dump(mapping, f, indent=2)
        print(f"Created peer mapping file: {mapping_file}")
        return True
    except Exception as e:
        print(f"Error writing mapping file: {e}")
        return False

def create_example_mapping():
    """Create an example mapping file for manual setup"""
    example_mapping = {
        "AbCd1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab=": {
            "hostname": "client1.vpn.local",
            "ip": "10.0.0.2"
        },
        "EfGh4567890abcdef1234567890abcdef1234567890abcdef1234567890cd=": {
            "hostname": "client2.vpn.local", 
            "ip": "10.0.0.3"
        }
    }
    
    example_file = "peer_hostnames_example.json"
    with open(example_file, 'w') as f:
        json.dump(example_mapping, f, indent=2)
    
    print(f"Created example mapping file: {example_file}")
    print("Edit this file with your actual peer public keys and copy to /etc/wireguard/peer_hostnames.json")

def main():
    """Main setup function"""
    print("HADDNS Peer Mapping Setup")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        create_example_mapping()
        return
    
    # Try to create mapping from database
    if create_peer_mapping():
        print("\n✅ Peer mapping created successfully!")
        print("\nNext steps:")
        print("1. Verify the mapping file: cat /etc/wireguard/peer_hostnames.json")
        print("2. Rebuild and restart the dns-cron container:")
        print("   docker compose build wireguard-dns-cron")
        print("   docker compose up -d wireguard-dns-cron")
        print("3. Check logs: docker logs -f wireguard-dns-cron")
    else:
        print("\n❌ Failed to create mapping from database")
        print("\nYou can create a manual mapping file:")
        print("python setup_haddns_mapping.py --example")
        print("Then edit peer_hostnames_example.json and copy to /etc/wireguard/peer_hostnames.json")

if __name__ == "__main__":
    main()
