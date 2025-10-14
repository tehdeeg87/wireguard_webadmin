#!/usr/bin/env python3
"""
HADDNS Demonstration Script
This script demonstrates the Handshake-Aware Dynamic DNS Resolution system
"""

import subprocess
import time
import json
from datetime import datetime, timedelta

def run_command(cmd):
    """Run a command and return the output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"

def demonstrate_haddns():
    """Demonstrate HADDNS functionality"""
    print("🚀 HADDNS (Handshake-Aware Dynamic DNS Resolution) Demonstration")
    print("=" * 70)
    
    # 1. Check WireGuard handshakes
    print("\n1. 📡 Checking WireGuard handshakes...")
    success, stdout, stderr = run_command("wg show all latest-handshakes")
    if success:
        print("✅ WireGuard handshake data:")
        for line in stdout.strip().split('\n'):
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 3:
                    interface, peer_key, timestamp = parts[0], parts[1], parts[2]
                    if int(timestamp) > 0:
                        handshake_time = datetime.fromtimestamp(int(timestamp))
                        print(f"   {interface}: {peer_key[:16]}... - {handshake_time}")
                    else:
                        print(f"   {interface}: {peer_key[:16]}... - No handshake")
    else:
        print(f"❌ Failed to get handshake data: {stderr}")
    
    # 2. Check HADDNS configuration
    print("\n2. ⚙️  Checking HADDNS configuration...")
    success, stdout, stderr = run_command("python manage.py shell -c \"from dns.models import HADDNSConfig; config = HADDNSConfig.get_config(); print(f'Enabled: {config.enabled}, Domain: {config.domain_suffix}, Threshold: {config.handshake_threshold_seconds}s')\"")
    if success:
        print(f"✅ HADDNS Config: {stdout.strip()}")
    else:
        print(f"❌ Failed to get HADDNS config: {stderr}")
    
    # 3. Check peer mappings
    print("\n3. 👥 Checking peer hostname mappings...")
    success, stdout, stderr = run_command("python manage.py shell -c \"from dns.models import PeerHostnameMapping; mappings = PeerHostnameMapping.objects.all(); print(f'Total mappings: {mappings.count()}'); [print(f'  {m.hostname} -> {m.peer.public_key[:16]}... (Online: {m.is_online})') for m in mappings[:5]]\"")
    if success:
        print(f"✅ Peer Mappings:\n{stdout}")
    else:
        print(f"❌ Failed to get peer mappings: {stderr}")
    
    # 4. Test HADDNS update (dry run)
    print("\n4. 🔄 Testing HADDNS update (dry run)...")
    success, stdout, stderr = run_command("python manage.py haddns_update --dry-run --verbose")
    if success:
        print("✅ HADDNS update test successful:")
        print(stdout)
    else:
        print(f"❌ HADDNS update test failed: {stderr}")
    
    # 5. Check dynamic hosts file
    print("\n5. 📄 Checking dynamic hosts file...")
    success, stdout, stderr = run_command("cat /etc/dnsmasq.d/haddns_dynamic_hosts.conf 2>/dev/null || echo 'File not found'")
    if success and "File not found" not in stdout:
        print("✅ Dynamic hosts file content:")
        print(stdout)
    else:
        print("ℹ️  Dynamic hosts file not found (normal if not set up yet)")
    
    # 6. Check dnsmasq configuration
    print("\n6. 🔧 Checking dnsmasq configuration...")
    success, stdout, stderr = run_command("grep -A 5 -B 5 'haddns' /etc/dnsmasq.d/wireguard_webadmin.conf 2>/dev/null || echo 'HADDNS not in dnsmasq config'")
    if success:
        print("✅ dnsmasq HADDNS configuration:")
        print(stdout)
    else:
        print("ℹ️  HADDNS not found in dnsmasq config")
    
    # 7. Test DNS resolution
    print("\n7. 🌐 Testing DNS resolution...")
    test_hostnames = [
        "test.vpn.local",
        "laptop.vpn.local", 
        "server.vpn.local"
    ]
    
    for hostname in test_hostnames:
        success, stdout, stderr = run_command(f"nslookup {hostname} 2>/dev/null || echo 'Resolution failed'")
        if success and "Resolution failed" not in stdout:
            print(f"✅ {hostname}: {stdout.split('Address: ')[-1].split()[0] if 'Address:' in stdout else 'Resolved'}")
        else:
            print(f"ℹ️  {hostname}: Not resolvable (normal if no peers configured)")
    
    print("\n" + "=" * 70)
    print("🎉 HADDNS Demonstration Complete!")
    print("\n📚 Next Steps:")
    print("1. Set up HADDNS: python manage.py haddns_setup")
    print("2. Generate dnsmasq config: python manage.py generate_dnsmasq_config")
    print("3. Restart dnsmasq: systemctl restart dnsmasq")
    print("4. Monitor logs: tail -f /var/log/haddns.log")
    print("5. Admin interface: /admin/dns/haddnsconfig/")

if __name__ == "__main__":
    demonstrate_haddns()
