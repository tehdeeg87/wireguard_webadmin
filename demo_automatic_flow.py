#!/usr/bin/env python3
"""
Demo: Automatic HADDNS Flow
This demonstrates how HADDNS works automatically with peer creation
"""

import subprocess
import time

def run_cmd(cmd):
    """Run command and return success, output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except:
        return False, "", "Command failed"

def demo_automatic_flow():
    print("🤖 HADDNS Automatic Flow Demo")
    print("=" * 50)
    
    print("\n1. 📝 When you create a peer via web interface:")
    print("   ✅ Django signal automatically creates PeerHostnameMapping")
    print("   ✅ Peer is immediately added to HADDNS system")
    print("   ✅ No manual steps required")
    
    print("\n2. ⏰ Every minute (cron job):")
    print("   ✅ python manage.py haddns_update runs automatically")
    print("   ✅ Checks WireGuard handshakes for all peers")
    print("   ✅ Updates DNS records based on online/offline status")
    print("   ✅ Reloads dnsmasq automatically")
    
    print("\n3. 🌐 DNS Resolution:")
    print("   ✅ Online peers: laptop.vpn.local → 10.0.0.2")
    print("   ✅ Offline peers: (no resolution or laptop.offline.vpn.local)")
    print("   ✅ Updates happen automatically as peers connect/disconnect")
    
    print("\n4. 🔍 Let's verify the current state:")
    
    # Check if HADDNS is set up
    success, stdout, stderr = run_cmd("python manage.py shell -c \"from dns.models import HADDNSConfig; config = HADDNSConfig.get_config(); print(f'HADDNS enabled: {config.enabled}')\"")
    if success:
        print(f"   ✅ HADDNS Status: {stdout.strip()}")
    else:
        print("   ❌ HADDNS not set up yet")
    
    # Check peer mappings
    success, stdout, stderr = run_cmd("python manage.py shell -c \"from dns.models import PeerHostnameMapping; print(f'Peer mappings: {PeerHostnameMapping.objects.count()}')\"")
    if success:
        print(f"   ✅ Peer Mappings: {stdout.strip()}")
    else:
        print("   ❌ No peer mappings found")
    
    # Check cron job
    success, stdout, stderr = run_cmd("grep -q 'haddns_update' cron/cron_tasks")
    if success:
        print("   ✅ Cron job configured")
    else:
        print("   ❌ Cron job not configured")
    
    print("\n5. 🎯 What happens when you create a new peer:")
    print("   Step 1: You create peer 'laptop' via web interface")
    print("   Step 2: Signal automatically creates mapping: laptop → peer_key")
    print("   Step 3: Next cron run (within 1 minute) detects the peer")
    print("   Step 4: If peer has handshake, DNS record is created")
    print("   Step 5: nslookup laptop.vpn.local now works!")
    
    print("\n6. 🔄 What happens when peer goes offline:")
    print("   Step 1: Peer stops sending handshakes")
    print("   Step 2: Next cron run detects no recent handshake")
    print("   Step 3: DNS record is removed (or marked .offline)")
    print("   Step 4: nslookup laptop.vpn.local stops working")
    
    print("\n7. ⚙️ Configuration (one-time setup):")
    print("   python manage.py haddns_setup")
    print("   python manage.py generate_dnsmasq_config")
    print("   systemctl restart dnsmasq")
    print("   # That's it! Everything else is automatic")
    
    print("\n🎉 Summary:")
    print("   • Peer creation: 100% automatic")
    print("   • Handshake monitoring: 100% automatic") 
    print("   • DNS updates: 100% automatic")
    print("   • No manual intervention needed after initial setup")

if __name__ == "__main__":
    demo_automatic_flow()
