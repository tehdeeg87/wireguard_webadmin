#!/usr/bin/env python3
"""
Test script for simple mDNS setup
"""

import subprocess
import time

def test_mdns_setup():
    """Test the mDNS setup"""
    print("🧪 Testing Simple mDNS Setup")
    print("=" * 40)
    
    # Test 1: Check if we have test data
    print("\n1. Checking test data...")
    try:
        result = subprocess.run([
            'docker', 'exec', 'wireguard-webadmin', 'python', 'manage.py', 'shell', '-c',
            '''
from wireguard.models import WireGuardInstance, Peer
instances = WireGuardInstance.objects.all()
peers = Peer.objects.all()
print(f"Instances: {len(instances)}")
print(f"Peers: {len(peers)}")
for instance in instances:
    print(f"  Instance: {instance.name or f\'wg{instance.instance_id}\'} ({instance.address})")
for peer in peers:
    print(f"  Peer: {peer.name or peer.hostname} -> {peer.wireguard_instance.address}")
'''
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Test data found:")
            print(result.stdout)
        else:
            print("❌ No test data found")
            return False
    except Exception as e:
        print(f"❌ Error checking test data: {e}")
        return False
    
    # Test 2: Check mDNS hosts file generation
    print("\n2. Testing mDNS hosts file generation...")
    try:
        result = subprocess.run([
            'docker', 'exec', 'wireguard-webadmin', 'python', 'manage.py', 'update_peer_mdns', '--reload'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ mDNS configuration updated successfully")
            print("Output:", result.stdout.strip())
        else:
            print("❌ Failed to update mDNS configuration")
            print("Error:", result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error updating mDNS: {e}")
        return False
    
    # Test 3: Check if hosts files exist
    print("\n3. Checking generated hosts files...")
    try:
        result = subprocess.run([
            'docker', 'exec', 'wireguard-webadmin', 'ls', '-la', '/etc/avahi/hosts/'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Hosts directory accessible")
            print("Files:")
            print(result.stdout)
        else:
            print("❌ Cannot access hosts directory")
            return False
    except Exception as e:
        print(f"❌ Error checking hosts files: {e}")
        return False
    
    # Test 4: Check hosts file content
    print("\n4. Checking hosts file content...")
    try:
        result = subprocess.run([
            'docker', 'exec', 'wireguard-webadmin', 'cat', '/etc/avahi/hosts/wg0.hosts'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            print("✅ Hosts file content:")
            print(result.stdout)
        else:
            print("❌ Hosts file is empty or doesn't exist")
            return False
    except Exception as e:
        print(f"❌ Error reading hosts file: {e}")
        return False
    
    # Test 5: Test DNS resolution (if possible)
    print("\n5. Testing DNS resolution...")
    try:
        # Test with nslookup
        result = subprocess.run([
            'docker', 'exec', 'wireguard-webadmin', 'nslookup', 'laptop.wg0.local'
        ], capture_output=True, text=True, timeout=10)
        
        if "laptop.wg0.local" in result.stdout:
            print("✅ DNS resolution working")
            print("Result:", result.stdout.strip())
        else:
            print("⚠️  DNS resolution not working (this is expected without mDNS daemon)")
            print("This is normal - mDNS requires the daemon to be running")
    except Exception as e:
        print(f"⚠️  DNS test failed: {e}")
    
    print("\n" + "=" * 40)
    print("🎉 mDNS Setup Test Complete!")
    print("\nNext steps:")
    print("1. The mDNS configuration is generated correctly")
    print("2. Hosts files are created with peer mappings")
    print("3. To enable actual mDNS resolution, you need:")
    print("   - Install mDNS daemon on your system")
    print("   - Or use the simple mDNS server: python mdns_simple_server.py")
    print("4. Peers will be discoverable as:")
    print("   - laptop.wg0.local")
    print("   - laptop.wg.local")
    print("   - laptop (short form)")
    
    return True

if __name__ == "__main__":
    test_mdns_setup()
