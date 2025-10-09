#!/usr/bin/env python3
"""
Setup test data for Avahi testing in Docker containers
This script creates sample peers and instances for testing
"""

import os
import sys
import django
from django.core.management import call_command

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from wireguard.models import WireGuardInstance, Peer, PeerAllowedIP
from django.contrib.auth.models import User


def create_test_data():
    """Create test data for Avahi testing"""
    print("🔧 Setting up test data for Avahi testing...")
    
    # Create a superuser if it doesn't exist
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
        print("✅ Created admin user (admin/admin123)")
    
    # Create test WireGuard instance
    instance, created = WireGuardInstance.objects.get_or_create(
        instance_id=0,
        defaults={
            'name': 'Test Instance',
            'private_key': 'test-private-key-1234567890123456789012345678901234567890',
            'public_key': 'test-public-key-1234567890123456789012345678901234567890',
            'hostname': 'test-server.local',
            'listen_port': 51820,
            'address': '10.188.0.1',
            'netmask': 24,
            'dns_primary': '127.0.0.1',
            'dns_secondary': '8.8.8.8',
        }
    )
    
    if created:
        print(f"✅ Created test WireGuard instance: {instance}")
    else:
        print(f"ℹ️  Using existing test WireGuard instance: {instance}")
    
    # Create test peers
    test_peers = [
        {
            'name': 'My Phone',
            'hostname': 'my-phone',
            'public_key': 'phone-public-key-1234567890123456789012345678901234567890',
            'pre_shared_key': 'phone-preshared-key-1234567890123456789012345678901234567890',
            'private_key': 'phone-private-key-1234567890123456789012345678901234567890',
            'allowed_ip': '10.188.0.3',
            'netmask': 32,
        },
        {
            'name': 'Laptop',
            'hostname': 'laptop',
            'public_key': 'laptop-public-key-1234567890123456789012345678901234567890',
            'pre_shared_key': 'laptop-preshared-key-1234567890123456789012345678901234567890',
            'private_key': 'laptop-private-key-1234567890123456789012345678901234567890',
            'allowed_ip': '10.188.0.4',
            'netmask': 32,
        },
        {
            'name': 'Server',
            'hostname': 'server',
            'public_key': 'server-public-key-1234567890123456789012345678901234567890',
            'pre_shared_key': 'server-preshared-key-1234567890123456789012345678901234567890',
            'private_key': 'server-private-key-1234567890123456789012345678901234567890',
            'allowed_ip': '10.188.0.5',
            'netmask': 32,
        },
        {
            'name': 'Tablet',
            'hostname': 'tablet',
            'public_key': 'tablet-public-key-1234567890123456789012345678901234567890',
            'pre_shared_key': 'tablet-preshared-key-1234567890123456789012345678901234567890',
            'private_key': 'tablet-private-key-1234567890123456789012345678901234567890',
            'allowed_ip': '10.188.0.6',
            'netmask': 32,
        }
    ]
    
    created_peers = []
    for peer_data in test_peers:
        peer, created = Peer.objects.get_or_create(
            name=peer_data['name'],
            wireguard_instance=instance,
            defaults={
                'hostname': peer_data['hostname'],
                'public_key': peer_data['public_key'],
                'pre_shared_key': peer_data['pre_shared_key'],
                'private_key': peer_data['private_key'],
                'persistent_keepalive': 25,
            }
        )
        
        if created:
            print(f"✅ Created test peer: {peer.name} ({peer.hostname})")
        else:
            print(f"ℹ️  Using existing test peer: {peer.name} ({peer.hostname})")
        
        # Create allowed IP for the peer
        allowed_ip, created = PeerAllowedIP.objects.get_or_create(
            peer=peer,
            allowed_ip=peer_data['allowed_ip'],
            defaults={
                'priority': 0,
                'netmask': peer_data['netmask'],
                'config_file': 'server',
            }
        )
        
        if created:
            print(f"  ✅ Created allowed IP: {allowed_ip.allowed_ip}/{allowed_ip.netmask}")
        else:
            print(f"  ℹ️  Using existing allowed IP: {allowed_ip.allowed_ip}/{allowed_ip.netmask}")
        
        created_peers.append(peer)
    
    print(f"\n🎯 Test data setup complete!")
    print(f"   Instance: {instance.name} (wg{instance.instance_id})")
    print(f"   Peers: {len(created_peers)}")
    print(f"   Domain: wg{instance.instance_id}.local")
    
    # Register peers with Avahi
    print("\n🔧 Registering peers with Avahi...")
    try:
        call_command('register_peers_avahi', '--reload', '--instance-id', instance.instance_id)
        print("✅ Peers registered with Avahi")
    except Exception as e:
        print(f"❌ Error registering peers with Avahi: {e}")
    
    print("\n📋 Test hostnames that should be resolvable:")
    for peer in created_peers:
        print(f"   {peer.hostname} → {peer.peerallowedip_set.filter(config_file='server', priority=0).first().allowed_ip}")
        print(f"   {peer.hostname}.wg{instance.instance_id}.local → {peer.peerallowedip_set.filter(config_file='server', priority=0).first().allowed_ip}")
        print(f"   {peer.hostname}.wg.local → {peer.peerallowedip_set.filter(config_file='server', priority=0).first().allowed_ip}")


if __name__ == "__main__":
    create_test_data()
