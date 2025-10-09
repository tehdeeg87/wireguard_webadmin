#!/usr/bin/env python3
"""
Test script to verify Avahi peer hostname resolution
This script tests that peers can be resolved by their hostnames through mDNS
"""

import subprocess
import sys
import time
import os
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
application = get_wsgi_application()

from wireguard.models import Peer, WireGuardInstance, PeerAllowedIP


def test_avahi_resolution():
    """Test Avahi peer hostname resolution"""
    print("🔍 Testing Avahi peer hostname resolution...")
    
    # Get all peers with their hostnames and IPs
    instances = WireGuardInstance.objects.all()
    
    if not instances.exists():
        print("❌ No WireGuard instances found")
        return False
    
    print(f"📡 Found {instances.count()} WireGuard instances")
    
    for instance in instances:
        print(f"\n🔧 Testing instance wg{instance.instance_id} ({instance.name or 'Unnamed'})")
        
        peers = Peer.objects.filter(wireguard_instance=instance)
        if not peers.exists():
            print(f"   ⚠️  No peers found for instance wg{instance.instance_id}")
            continue
        
        print(f"   👥 Found {peers.count()} peers")
        
        for peer in peers:
            # Get peer IP
            peer_ip = peer.peerallowedip_set.filter(config_file='server', priority=0).first()
            if not peer_ip:
                print(f"   ❌ No IP found for peer {peer.name or peer.uuid}")
                continue
            
            hostname = peer.hostname or peer.name or f"peer-{peer.uuid.hex[:8]}"
            instance_domain = f"wg{instance.instance_id}.local"
            global_domain = "wg.local"
            
            print(f"   🔍 Testing peer: {hostname} ({peer_ip.allowed_ip})")
            
            # Test different hostname formats
            test_hostnames = [
                hostname,
                f"{hostname}.{instance_domain}",
                f"{hostname}.{global_domain}",
            ]
            
            for test_hostname in test_hostnames:
                try:
                    # Use avahi-resolve-host-name to test resolution
                    result = subprocess.run(
                        ['avahi-resolve-host-name', test_hostname],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        resolved_ip = result.stdout.strip().split()[-1]
                        if resolved_ip == str(peer_ip.allowed_ip):
                            print(f"      ✅ {test_hostname} → {resolved_ip}")
                        else:
                            print(f"      ⚠️  {test_hostname} → {resolved_ip} (expected {peer_ip.allowed_ip})")
                    else:
                        print(f"      ❌ {test_hostname} → Resolution failed")
                        
                except subprocess.TimeoutExpired:
                    print(f"      ⏰ {test_hostname} → Timeout")
                except FileNotFoundError:
                    print(f"      ❌ avahi-resolve-host-name not found - using nslookup")
                    # Fallback to nslookup
                    try:
                        result = subprocess.run(
                            ['nslookup', test_hostname],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if str(peer_ip.allowed_ip) in result.stdout:
                            print(f"      ✅ {test_hostname} → {peer_ip.allowed_ip} (via nslookup)")
                        else:
                            print(f"      ❌ {test_hostname} → Not found (via nslookup)")
                    except:
                        print(f"      ❌ {test_hostname} → Resolution failed")
                except Exception as e:
                    print(f"      ❌ {test_hostname} → Error: {e}")


def test_avahi_services():
    """Test Avahi service discovery"""
    print("\n🔍 Testing Avahi service discovery...")
    
    try:
        # Use avahi-browse to list services
        result = subprocess.run(
            ['avahi-browse', '-t', '_wireguard._tcp'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            print("✅ WireGuard services found:")
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    print(f"   📡 {line}")
        else:
            print("⚠️  No WireGuard services advertised")
            
    except FileNotFoundError:
        print("❌ avahi-browse not found")
    except Exception as e:
        print(f"❌ Error browsing services: {e}")


def test_avahi_daemon():
    """Test if Avahi daemon is running"""
    print("🔍 Testing Avahi daemon status...")
    
    try:
        # Check if avahi-daemon is running
        result = subprocess.run(
            ['pgrep', 'avahi-daemon'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✅ Avahi daemon is running (PIDs: {', '.join(pids)})")
            return True
        else:
            print("❌ Avahi daemon is not running")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Avahi daemon: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Starting Avahi peer resolution tests...")
    print("=" * 50)
    
    # Test Avahi daemon
    if not test_avahi_daemon():
        print("\n❌ Avahi daemon is not running. Please start it first:")
        print("   sudo systemctl start avahi-daemon")
        print("   or")
        print("   avahi-daemon -D")
        return False
    
    # Test service discovery
    test_avahi_services()
    
    # Test hostname resolution
    test_avahi_resolution()
    
    print("\n" + "=" * 50)
    print("✅ Avahi peer resolution tests completed!")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
