#!/usr/bin/env python3
"""
HADDNS Local Testing Script for Docker Desktop
Tests the HADDNS implementation locally before Ubuntu deployment
"""

import subprocess
import json
import time
import os
import sys
import requests
from datetime import datetime

def run_command(cmd, description, check_output=True):
    """Run a command and return the result"""
    print(f"\n🔍 {description}")
    print(f"Command: {cmd}")
    
    try:
        if check_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        else:
            result = subprocess.run(cmd, shell=True, timeout=30)
            
        if result.returncode == 0:
            print(f"✅ Success")
            if check_output and result.stdout.strip():
                print(f"Output:\n{result.stdout}")
        else:
            print(f"❌ Failed (exit code: {result.returncode})")
            if check_output and result.stderr.strip():
                print(f"Error: {result.stderr}")
        return result
    except subprocess.TimeoutExpired:
        print(f"⏰ Command timed out")
        return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def check_docker_desktop():
    """Check if Docker Desktop is running"""
    print("\n" + "="*60)
    print("CHECKING DOCKER DESKTOP")
    print("="*60)
    
    run_command("docker --version", "Check Docker version")
    run_command("docker compose version", "Check Docker Compose version")
    run_command("docker ps", "Check running containers")

def test_containers_startup():
    """Test container startup and health"""
    print("\n" + "="*60)
    print("TESTING CONTAINER STARTUP")
    print("="*60)
    
    # Start containers
    print("\n🚀 Starting containers...")
    run_command("docker compose up -d", "Start all containers", check_output=False)
    
    # Wait for containers to start
    print("\n⏳ Waiting for containers to start...")
    time.sleep(10)
    
    # Check container status
    containers = [
        "wireguard-webadmin",
        "wireguard-dns-cron", 
        "wireguard-dnsmasq"
    ]
    
    for container in containers:
        run_command(f"docker ps --filter name={container} --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'", 
                   f"Check {container} status")

def test_peer_mapping_creation():
    """Test peer mapping file creation"""
    print("\n" + "="*60)
    print("TESTING PEER MAPPING CREATION")
    print("="*60)
    
    # Check if we can access the webadmin container
    run_command("docker exec wireguard-webadmin ls -la /app", "Check webadmin container access")
    
    # Try to create mapping file
    print("\n📝 Creating peer mapping file...")
    
    # Create a test mapping file
    test_mapping = {
        "test_peer_1_public_key_here_32_chars_long_abcd=": {
            "hostname": "testclient1.vpn.local",
            "ip": "10.0.0.100"
        },
        "test_peer_2_public_key_here_32_chars_long_efgh=": {
            "hostname": "testclient2.vpn.local", 
            "ip": "10.0.0.101"
        }
    }
    
    # Write test mapping to container
    mapping_json = json.dumps(test_mapping, indent=2)
    run_command(f'docker exec -i wireguard-webadmin bash -c "echo \'{mapping_json}\' > /etc/wireguard/peer_hostnames.json"', 
                "Create test peer mapping file")
    
    # Verify mapping file
    run_command("docker exec wireguard-webadmin cat /etc/wireguard/peer_hostnames.json",
                "Verify peer mapping file content")

def test_haddns_execution():
    """Test HADDNS script execution"""
    print("\n" + "="*60)
    print("TESTING HADDNS EXECUTION")
    print("="*60)
    
    # Check if HADDNS script exists
    run_command("docker exec wireguard-dns-cron ls -la /app/haddns.py",
                "Check HADDNS script exists")
    
    # Test HADDNS script manually
    run_command("docker exec wireguard-dns-cron python3 /app/haddns.py",
                "Run HADDNS script manually")
    
    # Check if hosts file was created
    run_command("ls -la ./shared_hosts/", "Check shared_hosts directory")
    run_command("cat ./shared_hosts/hosts", "Check generated hosts file")

def test_dns_functionality():
    """Test DNS functionality"""
    print("\n" + "="*60)
    print("TESTING DNS FUNCTIONALITY")
    print("="*60)
    
    # Check dnsmasq logs
    run_command("docker logs --tail 10 wireguard-dnsmasq",
                "Check dnsmasq logs")
    
    # Test DNS resolution from inside webadmin container
    run_command("docker exec wireguard-webadmin nslookup testclient1.vpn.local 127.0.0.1",
                "Test DNS resolution for test client 1")
    
    run_command("docker exec wireguard-webadmin nslookup testclient2.vpn.local 127.0.0.1", 
                "Test DNS resolution for test client 2")

def test_cron_scheduling():
    """Test cron job scheduling"""
    print("\n" + "="*60)
    print("TESTING CRON SCHEDULING")
    print("="*60)
    
    # Check cron configuration
    run_command("docker exec wireguard-dns-cron cat /etc/cron.d/haddns",
                "Check cron configuration")
    
    # Check if cron is running
    run_command("docker exec wireguard-dns-cron ps aux | grep cron",
                "Check cron process")
    
    # Wait and check if HADDNS runs automatically
    print("\n⏳ Waiting 70 seconds to test automatic execution...")
    time.sleep(70)
    
    run_command("docker logs --tail 20 wireguard-dns-cron",
                "Check recent HADDNS logs after waiting")

def test_webadmin_api():
    """Test webadmin API accessibility"""
    print("\n" + "="*60)
    print("TESTING WEBADMIN API")
    print("="*60)
    
    # Check if webadmin is accessible
    try:
        response = requests.get("http://localhost:8000", timeout=10)
        print(f"✅ Webadmin accessible (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Webadmin not accessible: {e}")
    
    # Check API endpoints
    try:
        response = requests.get("http://localhost:8000/api/peers/", timeout=10)
        print(f"✅ Peers API accessible (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Peers API not accessible: {e}")

def test_network_connectivity():
    """Test network connectivity between containers"""
    print("\n" + "="*60)
    print("TESTING NETWORK CONNECTIVITY")
    print("="*60)
    
    # Test connectivity between containers
    run_command("docker exec wireguard-dns-cron ping -c 3 wireguard-webadmin",
                "Test dns-cron to webadmin connectivity")
    
    run_command("docker exec wireguard-dnsmasq ping -c 3 wireguard-webadmin",
                "Test dnsmasq to webadmin connectivity")

def cleanup_test():
    """Clean up test environment"""
    print("\n" + "="*60)
    print("CLEANUP TEST ENVIRONMENT")
    print("="*60)
    
    print("\n🧹 Cleaning up test files...")
    run_command("rm -f ./shared_hosts/hosts", "Remove test hosts file")
    run_command("docker exec wireguard-webadmin rm -f /etc/wireguard/peer_hostnames.json",
                "Remove test peer mapping file")

def main():
    """Main test function"""
    print("HADDNS Local Testing Suite for Docker Desktop")
    print("="*60)
    print("This script will test your HADDNS implementation locally")
    print("before deploying to Ubuntu.")
    
    input("\nPress Enter to start testing...")
    
    # Run all tests
    check_docker_desktop()
    test_containers_startup()
    test_peer_mapping_creation()
    test_haddns_execution()
    test_dns_functionality()
    test_cron_scheduling()
    test_webadmin_api()
    test_network_connectivity()
    
    print("\n" + "="*60)
    print("LOCAL TESTING COMPLETE")
    print("="*60)
    
    # Ask if user wants to cleanup
    cleanup_choice = input("\nDo you want to cleanup test files? (y/n): ").lower()
    if cleanup_choice == 'y':
        cleanup_test()
    
    print("\n📋 Test Summary:")
    print("✅ If all tests passed, your HADDNS implementation is ready for Ubuntu deployment")
    print("❌ If any tests failed, check the HADDNS_SETUP_GUIDE.md for troubleshooting")
    print("\n🚀 Next steps for Ubuntu deployment:")
    print("1. Copy the modified files to your Ubuntu server")
    print("2. Run: python setup_haddns_mapping.py")
    print("3. Run: docker compose up -d")
    print("4. Run: python test_haddns.py")

if __name__ == "__main__":
    main()
