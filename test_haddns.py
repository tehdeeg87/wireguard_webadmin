#!/usr/bin/env python3
"""
HADDNS Test Script
Tests the HADDNS implementation
"""

import subprocess
import json
import time
import os
import sys

def run_command(cmd, description):
    """Run a command and return the result"""
    print(f"\n🔍 {description}")
    print(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Success")
            if result.stdout.strip():
                print(f"Output:\n{result.stdout}")
        else:
            print(f"❌ Failed (exit code: {result.returncode})")
            if result.stderr.strip():
                print(f"Error: {result.stderr}")
        return result
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_containers():
    """Test if containers are running"""
    print("\n" + "="*50)
    print("TESTING CONTAINERS")
    print("="*50)
    
    containers = [
        "wireguard-webadmin",
        "wireguard-dns-cron", 
        "wireguard-dnsmasq"
    ]
    
    for container in containers:
        run_command(f"docker ps --filter name={container} --format 'table {{.Names}}\\t{{.Status}}'", 
                   f"Check {container} container")

def test_peer_mapping():
    """Test peer mapping file"""
    print("\n" + "="*50)
    print("TESTING PEER MAPPING")
    print("="*50)
    
    # Check if mapping file exists
    run_command("docker exec wireguard-webadmin ls -la /etc/wireguard/peer_hostnames.json",
                "Check peer mapping file exists")
    
    # Validate JSON format
    run_command("docker exec wireguard-webadmin python3 -c 'import json; print(json.load(open(\"/etc/wireguard/peer_hostnames.json\")))'",
                "Validate peer mapping JSON")

def test_wireguard_interface():
    """Test WireGuard interface"""
    print("\n" + "="*50)
    print("TESTING WIREGUARD INTERFACE")
    print("="*50)
    
    # Check WireGuard interface
    run_command("docker exec wireguard-webadmin wg show wg0",
                "Check WireGuard interface status")
    
    # Check handshakes
    run_command("docker exec wireguard-webadmin wg show wg0 latest-handshakes",
                "Check latest handshakes")

def test_haddns_logs():
    """Test HADDNS logs"""
    print("\n" + "="*50)
    print("TESTING HADDNS LOGS")
    print("="*50)
    
    # Check HADDNS logs
    run_command("docker logs --tail 20 wireguard-dns-cron",
                "Check recent HADDNS logs")
    
    # Check if cron is running
    run_command("docker exec wireguard-dns-cron ps aux | grep cron",
                "Check cron process")

def test_hosts_file():
    """Test hosts file generation"""
    print("\n" + "="*50)
    print("TESTING HOSTS FILE")
    print("="*50)
    
    # Check hosts file
    run_command("cat ./shared_hosts/hosts",
                "Check generated hosts file")
    
    # Check file modification time
    run_command("ls -la ./shared_hosts/hosts",
                "Check hosts file timestamp")

def test_dns_resolution():
    """Test DNS resolution"""
    print("\n" + "="*50)
    print("TESTING DNS RESOLUTION")
    print("="*50)
    
    # Check dnsmasq status
    run_command("docker logs --tail 10 wireguard-dnsmasq",
                "Check dnsmasq logs")
    
    # Test DNS resolution from inside the container
    run_command("docker exec wireguard-webadmin nslookup client1.vpn.local 127.0.0.1",
                "Test DNS resolution (if peers exist)")

def test_manual_haddns():
    """Test HADDNS script manually"""
    print("\n" + "="*50)
    print("TESTING MANUAL HADDNS EXECUTION")
    print("="*50)
    
    # Run HADDNS script manually
    run_command("docker exec wireguard-dns-cron python3 /app/haddns.py",
                "Run HADDNS script manually")

def main():
    """Main test function"""
    print("HADDNS Test Suite")
    print("="*50)
    print("This script will test your HADDNS implementation")
    print("Make sure all containers are running first!")
    
    input("\nPress Enter to continue...")
    
    # Run all tests
    test_containers()
    test_peer_mapping()
    test_wireguard_interface()
    test_haddns_logs()
    test_hosts_file()
    test_dns_resolution()
    test_manual_haddns()
    
    print("\n" + "="*50)
    print("TEST COMPLETE")
    print("="*50)
    print("\nIf you see any ❌ errors above, check the HADDNS_SETUP_GUIDE.md")
    print("for troubleshooting steps.")

if __name__ == "__main__":
    main()
