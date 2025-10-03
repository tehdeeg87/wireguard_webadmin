#!/usr/bin/env python3
"""
Test script for WireGuard DNS setup
This script helps test the per-instance DNS resolution functionality
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from django.core.management import call_command
from wireguard.models import WireGuardInstance, Peer, PeerAllowedIP

def test_dns_setup():
    print("🔍 Testing WireGuard DNS Setup")
    print("=" * 50)
    
    # Check if we have any instances
    instances = WireGuardInstance.objects.all()
    print(f"📊 Found {instances.count()} WireGuard instances")
    
    if not instances.exists():
        print("❌ No WireGuard instances found. Please create an instance first.")
        return
    
    # Check peers with hostnames
    peers_with_hostnames = Peer.objects.filter(hostname__isnull=False).exclude(hostname='')
    print(f"👥 Found {peers_with_hostnames.count()} peers with hostnames")
    
    if not peers_with_hostnames.exists():
        print("⚠️  No peers with hostnames found. Creating test peer...")
        # Create a test peer
        instance = instances.first()
        test_peer = Peer.objects.create(
            name="test-peer",
            hostname="test-laptop",
            public_key="test-key",
            pre_shared_key="test-psk",
            wireguard_instance=instance
        )
        PeerAllowedIP.objects.create(
            config_file='server',
            peer=test_peer,
            allowed_ip="10.0.0.100",
            priority=0,
            netmask=32
        )
        print("✅ Test peer created")
    
    # Update DNS configuration
    print("\n🔄 Updating DNS configuration...")
    try:
        call_command('update_peer_dns', '--reload')
        print("✅ DNS configuration updated successfully")
    except Exception as e:
        print(f"❌ Error updating DNS configuration: {e}")
        return
    
    # Show current configuration
    print("\n📋 Current DNS Configuration:")
    print("-" * 30)
    
    for instance in instances:
        instance_name = instance.name or f'wg{instance.instance_id}'
        peers = Peer.objects.filter(wireguard_instance=instance, hostname__isnull=False).exclude(hostname='')
        print(f"\n{instance_name}:")
        
        for peer in peers:
            peer_ip = PeerAllowedIP.objects.filter(
                peer=peer, 
                config_file='server', 
                priority=0
            ).first()
            if peer_ip:
                print(f"  • {peer.hostname} -> {peer_ip.allowed_ip}")
                print(f"    - {peer.hostname}.{instance_name}")
                print(f"    - {peer.hostname}.{instance_name}.local")
    
    print("\n🎯 DNS Resolution Examples:")
    print("-" * 30)
    print("From any peer, you can now resolve:")
    print("• peer.hostname (global)")
    print("• peer.hostname.wg0 (instance-specific)")
    print("• peer.hostname.wg0.local (with domain)")
    
    print("\n✅ DNS setup test completed!")
    print("\nTo test DNS resolution from a peer:")
    print("1. Connect to your WireGuard VPN")
    print("2. Run: nslookup <hostname>")
    print("3. Or: ping <hostname>")

if __name__ == "__main__":
    test_dns_setup()
