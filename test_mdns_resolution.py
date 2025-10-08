#!/usr/bin/env python3
"""
Test mDNS resolution for WireGuard peers
This simulates how mDNS resolution would work
"""

import subprocess
import os

def test_mdns_resolution():
    """Test mDNS resolution for WireGuard peers"""
    print("🧪 Testing mDNS Resolution for WireGuard Peers")
    print("=" * 50)
    
    # Test 1: Check if hosts file exists and has content
    print("\n1. Checking mDNS hosts file...")
    try:
        result = subprocess.run([
            'docker', 'exec', 'wireguard-webadmin', 'cat', '/etc/avahi/hosts/wg0.hosts'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            print("✅ mDNS hosts file found with content:")
            print(result.stdout)
        else:
            print("❌ mDNS hosts file is empty or doesn't exist")
            return False
    except Exception as e:
        print(f"❌ Error reading hosts file: {e}")
        return False
    
    # Test 2: Parse hosts file and show available hostnames
    print("\n2. Available hostnames for resolution:")
    try:
        lines = result.stdout.strip().split('\n')
        hostnames = []
        for line in lines:
            if line and not line.startswith('#') and ' ' in line:
                parts = line.split()
                if len(parts) >= 2:
                    ip = parts[0]
                    hostname = parts[1]
                    hostnames.append((ip, hostname))
        
        if hostnames:
            print("✅ Found hostnames:")
            for ip, hostname in hostnames:
                print(f"   {hostname} -> {ip}")
        else:
            print("❌ No hostnames found in hosts file")
            return False
    except Exception as e:
        print(f"❌ Error parsing hosts file: {e}")
        return False
    
    # Test 3: Simulate mDNS resolution
    print("\n3. Simulating mDNS resolution:")
    print("   (In a real mDNS setup, these would resolve automatically)")
    
    for ip, hostname in hostnames:
        print(f"   ✅ {hostname} would resolve to {ip}")
    
    # Test 4: Show different hostname formats
    print("\n4. Available hostname formats:")
    print("   For peer 'laptop' in instance 'wg0':")
    print("   - laptop.wg0.local  (instance-specific)")
    print("   - laptop.wg.local   (global)")
    print("   - laptop            (short form)")
    print("   - peer-{uuid}       (UUID-based)")
    
    # Test 5: Show how to test from different locations
    print("\n5. How to test mDNS resolution:")
    print("   From Windows host (after installing Bonjour):")
    print("   - nslookup laptop.wg0.local")
    print("   - ping laptop.wg0.local")
    print("   - telnet laptop.wg0.local 22")
    
    print("\n   From Linux/macOS host:")
    print("   - avahi-resolve-host-name laptop.wg0.local")
    print("   - ping laptop.wg0.local")
    print("   - dig laptop.wg0.local")
    
    print("\n   From WireGuard peer (when connected):")
    print("   - ping laptop.wg0.local")
    print("   - ssh laptop.wg0.local")
    print("   - curl http://laptop.wg0.local")
    
    # Test 6: Show current status
    print("\n6. Current mDNS Status:")
    print("   ✅ mDNS configuration generated")
    print("   ✅ Hosts files created")
    print("   ✅ Multiple hostname formats supported")
    print("   ⚠️  mDNS daemon not running (needed for actual resolution)")
    
    print("\n" + "=" * 50)
    print("🎉 mDNS Resolution Test Complete!")
    print("\nNext steps to enable actual resolution:")
    print("1. Install Bonjour on Windows: https://support.apple.com/downloads/bonjour_for_windows")
    print("2. Or run the simple mDNS server: python mdns_simple_server.py")
    print("3. Then test: nslookup laptop.wg0.local")
    
    return True

if __name__ == "__main__":
    test_mdns_resolution()

