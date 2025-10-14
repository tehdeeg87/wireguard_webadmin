#!/usr/bin/env python3
"""
DNS Diagnosis Script
Check WireGuard instances, peers, and DNS configuration
"""

import subprocess
import sys

def run_cmd(cmd):
    """Run command and return success, output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except:
        return False, "", "Command failed"

def main():
    print("🔍 DNS Diagnosis for WireGuard WebAdmin")
    print("=" * 50)
    
    # Check WireGuard instances
    print("\n1. 📡 WireGuard Instances:")
    success, stdout, stderr = run_cmd("python manage.py shell -c \"from wireguard.models import WireGuardInstance; instances = WireGuardInstance.objects.all(); print('Instances:'); [print(f'  {i.name or f\"wg{i.instance_id}\"}: {i.address}/{i.netmask} (DNS: {i.dns_primary})') for i in instances]\"")
    if success:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # Check peers
    print("\n2. 👥 Peers:")
    success, stdout, stderr = run_cmd("python manage.py shell -c \"from wireguard.models import Peer; peers = Peer.objects.all(); print(f'Total peers: {peers.count()}'); [print(f'  {p.name or \"Unnamed\"}: {p.hostname} (Key: {p.public_key[:16]}...)') for p in peers]\"")
    if success:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # Check HADDNS configuration
    print("\n3. ⚙️ HADDNS Configuration:")
    success, stdout, stderr = run_cmd("python manage.py shell -c \"from dns.models import HADDNSConfig; config = HADDNSConfig.get_config(); print(f'Enabled: {config.enabled}'); print(f'Domain: {config.domain_suffix}'); print(f'Threshold: {config.handshake_threshold_seconds}s')\"")
    if success:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # Check peer mappings
    print("\n4. 🗺️ Peer Mappings:")
    success, stdout, stderr = run_cmd("python manage.py shell -c \"from dns.models import PeerHostnameMapping; mappings = PeerHostnameMapping.objects.all(); print(f'Total mappings: {mappings.count()}'); [print(f'  {m.hostname}: {m.peer.public_key[:16]}... (Online: {m.is_online})') for m in mappings]\"")
    if success:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # Check DNS settings
    print("\n5. 🌐 DNS Settings:")
    success, stdout, stderr = run_cmd("python manage.py shell -c \"from dns.models import DNSSettings; settings = DNSSettings.objects.first(); print(f'Primary DNS: {settings.dns_primary if settings else \"Not configured\"}'); print(f'Secondary DNS: {settings.dns_secondary if settings else \"Not configured\"}')\"")
    if success:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # Check if dnsmasq config exists
    print("\n6. 📄 dnsmasq Configuration:")
    success, stdout, stderr = run_cmd("ls -la /etc/dnsmasq.d/wireguard_webadmin.conf 2>/dev/null || echo 'Config file not found'")
    if success:
        print(f"Config file: {stdout.strip()}")
    else:
        print("Config file not found")
    
    # Check HADDNS dynamic hosts file
    print("\n7. 📋 HADDNS Dynamic Hosts:")
    success, stdout, stderr = run_cmd("cat /etc/dnsmasq.d/haddns_dynamic_hosts.conf 2>/dev/null || echo 'Dynamic hosts file not found'")
    if success:
        print(f"Dynamic hosts: {stdout.strip()}")
    else:
        print("Dynamic hosts file not found")
    
    print("\n8. 🔧 Troubleshooting Steps:")
    print("   If HADDNS is not set up:")
    print("   python manage.py haddns_setup --domain vpn.local --threshold 300")
    print("   python manage.py generate_dnsmasq_config")
    print("   systemctl restart dnsmasq")
    print("")
    print("   If peers don't have hostnames:")
    print("   - Edit peers in web interface to add hostnames")
    print("   - Or run: python manage.py haddns_setup (creates mappings)")
    print("")
    print("   If DNS server is not running:")
    print("   systemctl status dnsmasq")
    print("   systemctl start dnsmasq")

if __name__ == "__main__":
    main()

