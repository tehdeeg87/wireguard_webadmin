#!/usr/bin/env python3
"""
HADDNS Ubuntu Production Testing Script
Comprehensive testing suite for HADDNS deployment on Ubuntu server
"""

import subprocess
import json
import time
import os
import sys
import requests
from datetime import datetime

def run_command(cmd, description, check_output=True, timeout=30):
    """Run a command and return the result"""
    print(f"\n🔍 {description}")
    print(f"Command: {cmd}")
    
    try:
        if check_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        else:
            result = subprocess.run(cmd, shell=True, timeout=timeout)
            
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

def test_system_requirements():
    """Test Ubuntu system requirements"""
    print("\n" + "="*60)
    print("TESTING SYSTEM REQUIREMENTS")
    print("="*60)
    
    # Check Docker
    run_command("docker --version", "Check Docker version")
    run_command("docker compose version", "Check Docker Compose version")
    
    # Check WireGuard
    run_command("wg --version", "Check WireGuard tools")
    run_command("ip link show | grep wg", "Check WireGuard interfaces")
    
    # Check system resources
    run_command("free -h", "Check memory usage")
    run_command("df -h", "Check disk space")
    run_command("systemctl status docker", "Check Docker service status")

def test_containers():
    """Test container deployment and health"""
    print("\n" + "="*60)
    print("TESTING CONTAINER DEPLOYMENT")
    print("="*60)
    
    # Check if containers are running
    containers = [
        "wireguard-webadmin",
        "wireguard-dns-cron", 
        "wireguard-dnsmasq"
    ]
    
    for container in containers:
        run_command(f"docker ps --filter name={container} --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'", 
                   f"Check {container} container")
    
    # Check container logs for errors
    run_command("docker logs --tail 20 wireguard-webadmin", "Check webadmin logs")
    run_command("docker logs --tail 20 wireguard-dns-cron", "Check dns-cron logs")
    run_command("docker logs --tail 20 wireguard-dnsmasq", "Check dnsmasq logs")

def test_wireguard_interfaces():
    """Test WireGuard interface configuration"""
    print("\n" + "="*60)
    print("TESTING WIREGUARD INTERFACES")
    print("="*60)
    
    # List all WireGuard interfaces
    run_command("wg show interfaces", "List all WireGuard interfaces")
    
    # Check each interface
    run_command("wg show wg0", "Check wg0 interface status")
    run_command("wg show wg0 latest-handshakes", "Check wg0 handshakes")
    
    # Check for additional interfaces
    run_command("ls /etc/wireguard/", "List WireGuard config files")
    
    # Check interface IPs
    run_command("ip addr show wg0", "Check wg0 IP configuration")

def test_peer_mappings():
    """Test peer mapping files"""
    print("\n" + "="*60)
    print("TESTING PEER MAPPINGS")
    print("="*60)
    
    # Check mapping files exist
    run_command("ls -la /etc/wireguard/peer_hostnames*.json", "Check peer mapping files")
    
    # Validate JSON format
    run_command("python3 -c 'import json; print(json.load(open(\"/etc/wireguard/peer_hostnames.json\")))'", 
                "Validate main peer mapping JSON")
    
    # Check for instance-specific mappings
    run_command("find /etc/wireguard/ -name 'peer_hostnames_wg*.json' -exec echo 'File: {}' \\; -exec python3 -c 'import json; print(json.load(open(\"{}\")))' \\;", 
                "Check instance-specific mappings")

def test_haddns_execution():
    """Test HADDNS script execution"""
    print("\n" + "="*60)
    print("TESTING HADDNS EXECUTION")
    print("="*60)
    
    # Test manual execution
    run_command("docker exec wireguard-dns-cron python3 /app/haddns_multi.py", 
                "Run HADDNS script manually")
    
    # Check if hosts file was created
    run_command("ls -la ./shared_hosts/", "Check shared_hosts directory")
    run_command("cat ./shared_hosts/hosts", "Check generated hosts file")
    
    # Check HADDNS logs
    run_command("docker exec wireguard-dns-cron cat /var/log/haddns.log", 
                "Check HADDNS logs")

def test_dns_functionality():
    """Test DNS functionality"""
    print("\n" + "="*60)
    print("TESTING DNS FUNCTIONALITY")
    print("="*60)
    
    # Check dnsmasq status
    run_command("docker exec wireguard-dnsmasq ps aux | grep dnsmasq", 
                "Check dnsmasq process")
    
    # Test DNS resolution from inside containers
    run_command("docker exec wireguard-webadmin nslookup google.com 127.0.0.1", 
                "Test basic DNS resolution")
    
    # Test local DNS resolution (if peers exist)
    run_command("docker exec wireguard-webadmin nslookup testclient1.vpn.local 127.0.0.1", 
                "Test local DNS resolution")

def test_network_connectivity():
    """Test network connectivity"""
    print("\n" + "="*60)
    print("TESTING NETWORK CONNECTIVITY")
    print("="*60)
    
    # Test container-to-container connectivity
    run_command("docker exec wireguard-dns-cron ping -c 3 wireguard-webadmin", 
                "Test dns-cron to webadmin connectivity")
    
    run_command("docker exec wireguard-dnsmasq ping -c 3 wireguard-webadmin", 
                "Test dnsmasq to webadmin connectivity")
    
    # Test external connectivity
    run_command("docker exec wireguard-webadmin ping -c 3 8.8.8.8", 
                "Test external connectivity")

def test_webadmin_api():
    """Test webadmin API functionality"""
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
    
    run_command("docker exec wireguard-dns-cron tail -20 /var/log/haddns.log", 
                "Check recent HADDNS logs after waiting")

def test_firewall_and_ports():
    """Test firewall and port configuration"""
    print("\n" + "="*60)
    print("TESTING FIREWALL AND PORTS")
    print("="*60)
    
    # Check listening ports
    run_command("netstat -tlnp | grep :8000", "Check webadmin port 8000")
    run_command("netstat -tlnp | grep :51820", "Check WireGuard port 51820")
    run_command("netstat -tlnp | grep :53", "Check DNS port 53")
    
    # Check firewall status
    run_command("ufw status", "Check UFW firewall status")
    
    # Check iptables rules
    run_command("iptables -L -n | head -20", "Check iptables rules")

def test_performance():
    """Test system performance"""
    print("\n" + "="*60)
    print("TESTING PERFORMANCE")
    print("="*60)
    
    # Check CPU usage
    run_command("top -bn1 | head -20", "Check CPU usage")
    
    # Check memory usage
    run_command("free -h", "Check memory usage")
    
    # Check disk I/O
    run_command("iostat -x 1 3", "Check disk I/O")

def test_security():
    """Test security configuration"""
    print("\n" + "="*60)
    print("TESTING SECURITY")
    print("="*60)
    
    # Check container security
    run_command("docker exec wireguard-dns-cron id", "Check container user")
    
    # Check file permissions
    run_command("ls -la /etc/wireguard/peer_hostnames*.json", "Check mapping file permissions")
    run_command("ls -la ./shared_hosts/", "Check hosts file permissions")
    
    # Check for sensitive data exposure
    run_command("docker exec wireguard-dns-cron env | grep -i key", "Check for exposed keys")

def generate_test_report():
    """Generate a test report"""
    print("\n" + "="*60)
    print("GENERATING TEST REPORT")
    print("="*60)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
HADDNS Ubuntu Production Test Report
Generated: {timestamp}
Server: {os.uname().nodename}

Test Summary:
- System Requirements: Check logs above
- Container Deployment: Check logs above  
- WireGuard Interfaces: Check logs above
- Peer Mappings: Check logs above
- HADDNS Execution: Check logs above
- DNS Functionality: Check logs above
- Network Connectivity: Check logs above
- WebAdmin API: Check logs above
- Cron Scheduling: Check logs above
- Firewall/Ports: Check logs above
- Performance: Check logs above
- Security: Check logs above

Next Steps:
1. Review any ❌ failures above
2. Check container logs: docker logs -f wireguard-dns-cron
3. Monitor HADDNS: tail -f /var/log/haddns.log
4. Test from VPN clients: nslookup <hostname> <server-ip>
"""
    
    print(report)
    
    # Save report to file
    with open("haddns_test_report.txt", "w") as f:
        f.write(report)
    
    print("📄 Test report saved to: haddns_test_report.txt")

def main():
    """Main test function"""
    print("HADDNS Ubuntu Production Testing Suite")
    print("="*60)
    print("This script will comprehensively test your HADDNS deployment")
    print("on Ubuntu server.")
    
    input("\nPress Enter to start testing...")
    
    # Run all tests
    test_system_requirements()
    test_containers()
    test_wireguard_interfaces()
    test_peer_mappings()
    test_haddns_execution()
    test_dns_functionality()
    test_network_connectivity()
    test_webadmin_api()
    test_cron_scheduling()
    test_firewall_and_ports()
    test_performance()
    test_security()
    generate_test_report()
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)
    print("\n📋 Review the test results above and the generated report")
    print("🔧 Fix any ❌ failures before going live")
    print("✅ If all tests pass, your HADDNS deployment is ready!")

if __name__ == "__main__":
    main()
