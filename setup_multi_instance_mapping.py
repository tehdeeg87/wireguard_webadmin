#!/usr/bin/env python3
"""
Multi-Instance HADDNS Peer Mapping Setup Script
Creates peer_hostnames.json mapping files for all WireGuard instances
"""

import json
import os
import sys
import subprocess
from pathlib import Path

def get_wireguard_instances():
    """Get all WireGuard instances from the database"""
    try:
        result = subprocess.run([
            'python', 'manage.py', 'shell', '-c',
            '''
from wireguard.models import WireGuardInstance, Peer, PeerAllowedIP
import json

instances_data = []
for instance in WireGuardInstance.objects.all():
    instance_data = {
        "instance_id": instance.instance_id,
        "name": instance.name or f"wg{instance.instance_id}",
        "address": str(instance.address),
        "peers": []
    }
    
    # Get all peers for this instance
    for peer in Peer.objects.filter(wireguard_instance=instance):
        # Get the peer's IP address (priority 0 from server config)
        peer_ip = PeerAllowedIP.objects.filter(
            peer=peer, 
            config_file='server', 
            priority=0
        ).first()
        
        if peer_ip and peer.hostname:
            instance_data["peers"].append({
                "public_key": peer.public_key,
                "name": peer.name or f"peer_{peer.id}",
                "hostname": peer.hostname,
                "ip_address": str(peer_ip.allowed_ip)
            })
    
    instances_data.append(instance_data)

print(json.dumps(instances_data))
            '''
        ], capture_output=True, text=True, cwd='/app')
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"Error getting instances from Django: {result.stderr}")
            return []
    except Exception as e:
        print(f"Error accessing Django: {e}")
        return []

def create_peer_mappings():
    """Create peer_hostnames.json mapping files for all instances"""
    print("Setting up HADDNS multi-instance peer mapping...")
    
    # Get instance data
    instances = get_wireguard_instances()
    
    if not instances:
        print("No WireGuard instances found. Please add some instances first.")
        return False
    
    total_peers = 0
    
    for instance in instances:
        instance_id = instance['instance_id']
        instance_name = instance['name']
        peers = instance['peers']
        
        if not peers:
            print(f"No peers found for {instance_name}")
            continue
        
        # Create mapping structure for this instance
        mapping = {}
        for peer in peers:
            public_key = peer['public_key']
            hostname = f"{peer['hostname']}.{instance_name}.local"
            ip_address = peer['ip_address']
            
            mapping[public_key] = {
                "hostname": hostname,
                "ip": ip_address,
                "instance": instance_name,
                "original_hostname": peer['hostname']
            }
            
            print(f"Mapped: {peer['name']} -> {hostname} ({ip_address}) in {instance_name}")
        
        # Write instance-specific mapping file
        mapping_file = f"/etc/wireguard/peer_hostnames_wg{instance_id}.json"
        try:
            with open(mapping_file, 'w') as f:
                json.dump(mapping, f, indent=2)
            print(f"Created peer mapping file: {mapping_file}")
            total_peers += len(mapping)
        except Exception as e:
            print(f"Error writing mapping file for {instance_name}: {e}")
    
    # Also create a combined mapping file
    combined_mapping = {}
    for instance in instances:
        instance_id = instance['instance_id']
        mapping_file = f"/etc/wireguard/peer_hostnames_wg{instance_id}.json"
        
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r') as f:
                    instance_mapping = json.load(f)
                    combined_mapping.update(instance_mapping)
            except Exception as e:
                print(f"Error reading {mapping_file}: {e}")
    
    # Write combined mapping file
    combined_file = "/etc/wireguard/peer_hostnames.json"
    try:
        with open(combined_file, 'w') as f:
            json.dump(combined_mapping, f, indent=2)
        print(f"Created combined peer mapping file: {combined_file}")
    except Exception as e:
        print(f"Error writing combined mapping file: {e}")
    
    print(f"\n✅ Multi-instance peer mapping created successfully!")
    print(f"Total peers mapped: {total_peers}")
    print(f"Instances processed: {len(instances)}")
    
    return True

def create_example_mapping():
    """Create example mapping files for manual setup"""
    example_instances = [
        {
            "instance_id": 0,
            "name": "wg0",
            "peers": [
                {
                    "public_key": "AbCd1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab=",
                    "hostname": "client1",
                    "ip_address": "10.0.0.2"
                },
                {
                    "public_key": "EfGh4567890abcdef1234567890abcdef1234567890abcdef1234567890cd=",
                    "hostname": "client2", 
                    "ip_address": "10.0.0.3"
                }
            ]
        },
        {
            "instance_id": 1,
            "name": "wg1",
            "peers": [
                {
                    "public_key": "IjKl789012345678901234567890123456789012345678901234567890ef=",
                    "hostname": "server1",
                    "ip_address": "10.1.0.2"
                }
            ]
        }
    ]
    
    for instance in example_instances:
        instance_id = instance['instance_id']
        instance_name = instance['name']
        
        mapping = {}
        for peer in instance['peers']:
            public_key = peer['public_key']
            hostname = f"{peer['hostname']}.{instance_name}.local"
            ip_address = peer['ip_address']
            
            mapping[public_key] = {
                "hostname": hostname,
                "ip": ip_address,
                "instance": instance_name,
                "original_hostname": peer['hostname']
            }
        
        example_file = f"peer_hostnames_wg{instance_id}_example.json"
        with open(example_file, 'w') as f:
            json.dump(mapping, f, indent=2)
        
        print(f"Created example mapping file: {example_file}")
    
    print("\nEdit these files with your actual peer public keys and copy to /etc/wireguard/")

def main():
    """Main setup function"""
    print("HADDNS Multi-Instance Peer Mapping Setup")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        create_example_mapping()
        return
    
    # Try to create mappings from database
    if create_peer_mappings():
        print("\nNext steps:")
        print("1. Verify the mapping files:")
        print("   ls -la /etc/wireguard/peer_hostnames*.json")
        print("2. Update docker-compose.yml to use haddns_multi.py:")
        print("   Change COPY haddns.py to COPY haddns_multi.py")
        print("3. Rebuild and restart the dns-cron container:")
        print("   docker compose build wireguard-dns-cron")
        print("   docker compose up -d wireguard-dns-cron")
        print("4. Check logs: docker logs -f wireguard-dns-cron")
    else:
        print("\n❌ Failed to create mappings from database")
        print("\nYou can create manual mapping files:")
        print("python setup_multi_instance_mapping.py --example")

if __name__ == "__main__":
    main()
