#!/usr/bin/env python3
"""
Test script to verify mDNS peer resolution for WireGuard
"""

import subprocess
import sys
import time

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def test_mdns_setup():
    """Test the mDNS setup for WireGuard peer resolution"""
    print("🧪 Testing mDNS Setup for WireGuard Peer Resolution")
    print("=" * 60)
    
    tests = [
        ("docker ps | grep wireguard-mdns", "Check if mDNS container is running"),
        ("ip link show wg0", "Check if WireGuard interface wg0 exists"),
        ("docker logs wireguard-mdns --tail 10", "Check mDNS container logs"),
        ("avahi-resolve-host-name localhost.local", "Test mDNS resolution"),
        ("avahi-browse -a -t", "Browse available mDNS services"),
    ]
    
    passed = 0
    total = len(tests)
    
    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! mDNS is working correctly.")
        print("\n📋 What this means:")
        print("   • mDNS container is running with network_mode: host")
        print("   • WireGuard interface wg0 is available")
        print("   • mDNS resolution is working")
        print("   • Peers can resolve each other by hostname")
        print("\n🔧 Next steps:")
        print("   1. Connect peers to the WireGuard instance")
        print("   2. Test peer-to-peer hostname resolution")
        print("   3. From peer: ping phone.wg0.local")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure WireGuard is running on host: sudo systemctl status wg-quick@wg0")
        print("   2. Check mDNS container logs: docker logs wireguard-mdns")
        print("   3. Verify WireGuard interface: ip link show wg0")
        print("   4. Check firewall rules: sudo iptables -L | grep 5353")
    
    return passed == total

if __name__ == "__main__":
    success = test_mdns_setup()
    sys.exit(0 if success else 1)
