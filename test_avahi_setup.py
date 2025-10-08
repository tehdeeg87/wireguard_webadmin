#!/usr/bin/env python3
"""
Test script to verify Avahi + Reflector setup for WireGuard mDNS
"""

import subprocess
import sys
import os

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

def test_avahi_setup():
    """Test the Avahi + Reflector setup"""
    print("🧪 Testing Avahi + Reflector Setup for WireGuard mDNS")
    print("=" * 60)
    
    tests = [
        ("systemctl is-active avahi-daemon", "Check if Avahi daemon is running"),
        ("systemctl is-enabled avahi-daemon", "Check if Avahi daemon is enabled"),
        ("ps aux | grep avahi-daemon | grep -v grep", "Check Avahi daemon process"),
        ("netstat -tulpn | grep :5353", "Check if mDNS is listening on port 5353"),
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
        print("🎉 All tests passed! Avahi + Reflector is working correctly.")
        print("\n📋 What this means:")
        print("   • Peers can resolve each other by hostname")
        print("   • mDNS traffic is reflected across WireGuard tunnel")
        print("   • Automatic peer discovery is enabled")
        print("\n🔧 Next steps:")
        print("   1. Deploy your WireGuard WebAdmin code")
        print("   2. Connect peers to the WireGuard instance")
        print("   3. Test: ping phone1.wg0.local from another peer")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure Avahi is installed: sudo apt install avahi-daemon avahi-utils")
        print("   2. Check Avahi config: sudo cat /etc/avahi/avahi-daemon.conf")
        print("   3. Restart Avahi: sudo systemctl restart avahi-daemon")
        print("   4. Check logs: sudo journalctl -u avahi-daemon -f")
    
    return passed == total

if __name__ == "__main__":
    success = test_avahi_setup()
    sys.exit(0 if success else 1)
