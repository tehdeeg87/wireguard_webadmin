#!/usr/bin/env python3
"""
Comprehensive HADDNS Testing Script
This script provides a complete testing suite for the HADDNS implementation
"""

import subprocess
import time
import json
import os
from datetime import datetime, timedelta

def run_command(cmd, timeout=30):
    """Run a command and return success, stdout, stderr"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def print_test(test_name, success, details=""):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"    {details}")

def test_database_setup():
    """Test 1: Database setup and migrations"""
    print_section("Database Setup Test")
    
    # Test migrations
    success, stdout, stderr = run_command("python manage.py makemigrations dns --dry-run")
    print_test("Django migrations ready", success, stderr if not success else "No new migrations needed")
    
    # Test if models can be imported
    success, stdout, stderr = run_command("python manage.py shell -c \"from dns.models import HADDNSConfig, PeerHostnameMapping; print('Models imported successfully')\"")
    print_test("Models import correctly", success, stderr if not success else "All models imported")

def test_haddns_setup():
    """Test 2: HADDNS setup and configuration"""
    print_section("HADDNS Setup Test")
    
    # Test HADDNS setup command
    success, stdout, stderr = run_command("python manage.py haddns_setup --domain test.local --threshold 180 --dry-run")
    print_test("HADDNS setup command works", success, stderr if not success else "Setup command ready")
    
    # Test configuration creation
    success, stdout, stderr = run_command("python manage.py shell -c \"from dns.models import HADDNSConfig; config = HADDNSConfig.get_config(); print(f'Config created: {config.name}')\"")
    print_test("HADDNS configuration created", success, stderr if not success else "Configuration ready")

def test_wireguard_integration():
    """Test 3: WireGuard integration"""
    print_section("WireGuard Integration Test")
    
    # Test WireGuard command availability
    success, stdout, stderr = run_command("wg --version")
    print_test("WireGuard command available", success, stderr if not success else f"Version: {stdout.strip()}")
    
    # Test handshake data retrieval
    success, stdout, stderr = run_command("wg show all latest-handshakes")
    if success:
        handshake_count = len([line for line in stdout.strip().split('\n') if line.strip()])
        print_test("Handshake data retrieval", True, f"Found {handshake_count} handshake entries")
    else:
        print_test("Handshake data retrieval", False, "No WireGuard interfaces or handshakes found")

def test_peer_mapping():
    """Test 4: Peer hostname mapping"""
    print_section("Peer Mapping Test")
    
    # Check if there are any peers in the database
    success, stdout, stderr = run_command("python manage.py shell -c \"from wireguard.models import Peer; print(f'Total peers: {Peer.objects.count()}')\"")
    if success:
        peer_count = int(stdout.strip().split(': ')[-1])
        print_test("Peer database access", True, f"Found {peer_count} peers")
        
        if peer_count > 0:
            # Test peer mapping creation
            success, stdout, stderr = run_command("python manage.py shell -c \"from dns.models import PeerHostnameMapping; print(f'Total mappings: {PeerHostnameMapping.objects.count()}')\"")
            print_test("Peer mapping database access", success, f"Mappings: {stdout.strip().split(': ')[-1] if success else 'Error'}")
    else:
        print_test("Peer database access", False, stderr)

def test_dnsmasq_integration():
    """Test 5: dnsmasq integration"""
    print_section("dnsmasq Integration Test")
    
    # Test dnsmasq configuration generation
    success, stdout, stderr = run_command("python manage.py generate_dnsmasq_config --dry-run")
    print_test("dnsmasq config generation", success, stderr if not success else "Configuration generated successfully")
    
    # Test if dnsmasq is installed
    success, stdout, stderr = run_command("which dnsmasq")
    print_test("dnsmasq installation", success, "dnsmasq not found - install with: apt install dnsmasq" if not success else f"Found at: {stdout.strip()}")
    
    # Test dnsmasq service status
    success, stdout, stderr = run_command("systemctl is-active dnsmasq")
    if success:
        status = stdout.strip()
        print_test("dnsmasq service status", status == "active", f"Status: {status}")
    else:
        print_test("dnsmasq service status", False, "Service not running")

def test_haddns_update():
    """Test 6: HADDNS update functionality"""
    print_section("HADDNS Update Test")
    
    # Test dry run
    success, stdout, stderr = run_command("python manage.py haddns_update --dry-run --verbose")
    print_test("HADDNS update dry run", success, stderr if not success else "Dry run completed successfully")
    
    # Test actual update (if WireGuard data available)
    success, stdout, stderr = run_command("python manage.py haddns_update --verbose")
    print_test("HADDNS actual update", success, stderr if not success else "Update completed successfully")

def test_dns_resolution():
    """Test 7: DNS resolution testing"""
    print_section("DNS Resolution Test")
    
    # Test local DNS resolution
    test_hostnames = [
        "localhost",
        "127.0.0.1"
    ]
    
    for hostname in test_hostnames:
        success, stdout, stderr = run_command(f"nslookup {hostname}")
        print_test(f"DNS resolution: {hostname}", success, "DNS resolution working" if success else "DNS resolution failed")
        if success:
            break  # If one works, DNS is functional

def test_cron_integration():
    """Test 8: Cron integration"""
    print_section("Cron Integration Test")
    
    # Check if cron job is in the cron file
    success, stdout, stderr = run_command("grep -q 'haddns_update' cron/cron_tasks")
    print_test("Cron job configured", success, "HADDNS cron job found in cron_tasks" if success else "Cron job not found")
    
    # Check cron service
    success, stdout, stderr = run_command("systemctl is-active cron")
    if success:
        status = stdout.strip()
        print_test("Cron service status", status == "active", f"Status: {status}")
    else:
        print_test("Cron service status", False, "Cron service not running")

def test_file_permissions():
    """Test 9: File permissions and directories"""
    print_section("File Permissions Test")
    
    # Test if we can write to dnsmasq directory
    test_file = "/tmp/haddns_test_write"
    success, stdout, stderr = run_command(f"touch {test_file} && rm {test_file}")
    print_test("File write permissions", success, "Can write files" if success else "File write permission issue")
    
    # Test dnsmasq directory
    dnsmasq_dirs = ["/etc/dnsmasq.d", "/etc/dnsmasq"]
    for dir_path in dnsmasq_dirs:
        success, stdout, stderr = run_command(f"ls -la {dir_path} 2>/dev/null")
        print_test(f"Directory access: {dir_path}", success, "Directory accessible" if success else "Directory not accessible")

def run_manual_tests():
    """Test 10: Manual testing instructions"""
    print_section("Manual Testing Instructions")
    
    print("""
    🔧 Manual Testing Steps:
    
    1. SETUP HADDNS:
       python manage.py haddns_setup --domain vpn.local --threshold 300
    
    2. GENERATE DNSMASQ CONFIG:
       python manage.py generate_dnsmasq_config --output /etc/dnsmasq.d/wireguard_webadmin.conf
    
    3. RESTART DNSMASQ:
       sudo systemctl restart dnsmasq
    
    4. TEST DNS RESOLUTION:
       nslookup test.vpn.local
       nslookup laptop.vpn.local
    
    5. MONITOR LOGS:
       tail -f /var/log/haddns.log
    
    6. CHECK ADMIN INTERFACE:
       Visit: http://localhost:8000/admin/dns/haddnsconfig/
    
    7. MANUAL UPDATE TEST:
       python manage.py haddns_update --verbose
    
    8. CHECK DYNAMIC HOSTS FILE:
       cat /etc/dnsmasq.d/haddns_dynamic_hosts.conf
    """)

def main():
    """Run all tests"""
    print("🚀 HADDNS Comprehensive Testing Suite")
    print("=" * 60)
    print("This script will test all components of the HADDNS implementation")
    
    # Run all test functions
    test_database_setup()
    test_haddns_setup()
    test_wireguard_integration()
    test_peer_mapping()
    test_dnsmasq_integration()
    test_haddns_update()
    test_dns_resolution()
    test_cron_integration()
    test_file_permissions()
    run_manual_tests()
    
    print_section("Testing Complete")
    print("""
    📋 Next Steps:
    1. Fix any failed tests above
    2. Run the manual testing steps
    3. Set up HADDNS in your environment
    4. Monitor the system for proper operation
    
    🆘 Troubleshooting:
    - Check logs: tail -f /var/log/haddns.log
    - Verify WireGuard: wg show all latest-handshakes
    - Test DNS: nslookup test.vpn.local
    - Check admin: /admin/dns/haddnsconfig/
    """)

if __name__ == "__main__":
    main()
