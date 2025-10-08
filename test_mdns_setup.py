#!/usr/bin/env python3
"""
Test script for mDNS-based WireGuard peer discovery
Run this script to test the mDNS setup
"""

import subprocess
import time
import sys

def test_mdns_container():
    """Test if mDNS container is running"""
    print("🔍 Testing mDNS container...")
    
    try:
        result = subprocess.run(['docker', 'ps', '--filter', 'name=wireguard-mdns', '--format', '{{.Status}}'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and 'Up' in result.stdout:
            print("✅ mDNS container is running")
            return True
        else:
            print("❌ mDNS container is not running")
            print(f"   Status: {result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"❌ Error checking mDNS container: {e}")
        return False

def test_mdns_logs():
    """Test mDNS container logs"""
    print("\n🔍 Checking mDNS logs...")
    
    try:
        result = subprocess.run(['docker', 'logs', '--tail', '10', 'wireguard-mdns'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ mDNS logs retrieved")
            print("   Recent logs:")
            for line in result.stdout.strip().split('\n')[-5:]:
                print(f"   {line}")
            return True
        else:
            print("❌ Could not retrieve mDNS logs")
            return False
    except Exception as e:
        print(f"❌ Error checking mDNS logs: {e}")
        return False

def test_mdns_hosts_files():
    """Test if mDNS hosts files are generated"""
    print("\n🔍 Testing mDNS hosts files...")
    
    try:
        result = subprocess.run(['docker', 'exec', 'wireguard-mdns', 'ls', '-la', '/etc/avahi/hosts/'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ mDNS hosts directory accessible")
            print("   Hosts files:")
            for line in result.stdout.strip().split('\n'):
                if '.hosts' in line:
                    print(f"   {line}")
            return True
        else:
            print("❌ Could not access mDNS hosts directory")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking mDNS hosts files: {e}")
        return False

def test_mdns_resolution():
    """Test mDNS resolution"""
    print("\n🔍 Testing mDNS resolution...")
    
    # Test if we can resolve a .local domain
    test_domains = [
        "test.wg0.local",
        "peer-1.wg0.local", 
        "laptop.wg0.local"
    ]
    
    for domain in test_domains:
        try:
            result = subprocess.run(['nslookup', domain], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and 'Address:' in result.stdout:
                print(f"✅ Successfully resolved {domain}")
                return True
            else:
                print(f"⚠️  Could not resolve {domain} (this is normal if no peers exist)")
        except Exception as e:
            print(f"⚠️  Error testing resolution for {domain}: {e}")
    
    return False

def test_avahi_services():
    """Test Avahi service discovery"""
    print("\n🔍 Testing Avahi service discovery...")
    
    try:
        result = subprocess.run(['docker', 'exec', 'wireguard-mdns', 'avahi-browse', '-a', '-t'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Avahi service discovery working")
            if result.stdout.strip():
                print("   Available services:")
                for line in result.stdout.strip().split('\n')[:5]:
                    print(f"   {line}")
            else:
                print("   No services currently advertised (normal if no peers connected)")
            return True
        else:
            print("❌ Avahi service discovery not working")
            return False
    except Exception as e:
        print(f"❌ Error testing Avahi services: {e}")
        return False

def test_django_mdns_command():
    """Test Django mDNS management command"""
    print("\n🔍 Testing Django mDNS command...")
    
    try:
        result = subprocess.run(['python', 'manage.py', 'update_peer_mdns', '--reload'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Django mDNS command executed successfully")
            print("   Output:")
            for line in result.stdout.strip().split('\n')[-3:]:
                print(f"   {line}")
            return True
        else:
            print("❌ Django mDNS command failed")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running Django mDNS command: {e}")
        return False

def main():
    """Run all mDNS tests"""
    print("🚀 Starting mDNS Setup Tests")
    print("=" * 50)
    
    tests = [
        test_mdns_container,
        test_mdns_logs,
        test_mdns_hosts_files,
        test_avahi_services,
        test_django_mdns_command,
        test_mdns_resolution,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! mDNS setup is working correctly.")
        print("\nNext steps:")
        print("1. Create some WireGuard peers")
        print("2. Test peer-to-peer hostname resolution")
        print("3. Verify cross-instance discovery")
    elif passed >= total * 0.7:
        print("⚠️  Most tests passed. mDNS setup is mostly working.")
        print("Check the failed tests above for issues.")
    else:
        print("❌ Many tests failed. mDNS setup needs attention.")
        print("Check the Docker Compose configuration and container logs.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
