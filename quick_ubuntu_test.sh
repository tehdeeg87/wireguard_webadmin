#!/bin/bash
# Quick Ubuntu Test Script for HADDNS Deployment

echo "🚀 HADDNS Quick Ubuntu Test"
echo "=========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $2 -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "🔍 Testing system requirements..."

# Check Docker
if command -v docker &> /dev/null; then
    print_status "Docker is installed" 0
    docker --version
else
    print_status "Docker is not installed" 1
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    print_status "Docker Compose is available" 0
else
    print_status "Docker Compose is not available" 1
    exit 1
fi

# Check WireGuard
if command -v wg &> /dev/null; then
    print_status "WireGuard tools are installed" 0
    wg --version
else
    print_status "WireGuard tools are not installed" 1
    print_warning "Install with: apt install wireguard-tools"
fi

echo -e "\n🔍 Testing container status..."

# Check if containers are running
containers=("wireguard-webadmin" "wireguard-dns-cron" "wireguard-dnsmasq")
for container in "${containers[@]}"; do
    if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
        print_status "$container is running" 0
    else
        print_status "$container is not running" 1
    fi
done

echo -e "\n🔍 Testing WireGuard interfaces..."

# Check WireGuard interfaces
if wg show interfaces &> /dev/null; then
    interfaces=$(wg show interfaces)
    print_status "WireGuard interfaces found: $interfaces" 0
    
    # Check each interface
    for interface in $interfaces; do
        if wg show "$interface" &> /dev/null; then
            print_status "Interface $interface is active" 0
        else
            print_status "Interface $interface is not active" 1
        fi
    done
else
    print_status "No WireGuard interfaces found" 1
fi

echo -e "\n🔍 Testing peer mappings..."

# Check peer mapping files
if [ -f "/etc/wireguard/peer_hostnames.json" ]; then
    print_status "Main peer mapping file exists" 0
    peer_count=$(python3 -c "import json; print(len(json.load(open('/etc/wireguard/peer_hostnames.json'))))" 2>/dev/null || echo "0")
    print_status "Peer mappings loaded: $peer_count" 0
else
    print_status "Main peer mapping file not found" 1
    print_warning "Run: python3 setup_multi_instance_mapping.py"
fi

# Check instance-specific mappings
instance_files=$(find /etc/wireguard/ -name "peer_hostnames_wg*.json" 2>/dev/null | wc -l)
if [ "$instance_files" -gt 0 ]; then
    print_status "Instance-specific mapping files found: $instance_files" 0
else
    print_warning "No instance-specific mapping files found"
fi

echo -e "\n🔍 Testing HADDNS execution..."

# Test HADDNS script
if docker exec wireguard-dns-cron python3 /app/haddns_multi.py &> /dev/null; then
    print_status "HADDNS script executes successfully" 0
else
    print_status "HADDNS script execution failed" 1
    print_warning "Check logs: docker logs wireguard-dns-cron"
fi

echo -e "\n🔍 Testing hosts file generation..."

# Check hosts file
if [ -f "./shared_hosts/hosts" ]; then
    print_status "Hosts file exists" 0
    host_count=$(grep -v "^#" ./shared_hosts/hosts | grep -v "^$" | wc -l)
    print_status "Active peer records: $host_count" 0
    echo "Hosts file content:"
    cat ./shared_hosts/hosts
else
    print_status "Hosts file not found" 1
fi

echo -e "\n🔍 Testing DNS functionality..."

# Test DNS resolution
if docker exec wireguard-webadmin nslookup google.com 127.0.0.1 &> /dev/null; then
    print_status "Basic DNS resolution works" 0
else
    print_status "Basic DNS resolution failed" 1
fi

# Test local DNS resolution
if docker exec wireguard-webadmin nslookup testclient1.vpn.local 127.0.0.1 &> /dev/null; then
    print_status "Local DNS resolution works" 0
else
    print_warning "Local DNS resolution failed (expected if no test peers)"
fi

echo -e "\n🔍 Testing cron scheduling..."

# Check cron configuration
if docker exec wireguard-dns-cron cat /etc/cron.d/haddns &> /dev/null; then
    print_status "Cron job is configured" 0
    docker exec wireguard-dns-cron cat /etc/cron.d/haddns
else
    print_status "Cron job not configured" 1
fi

# Check if cron is running
if docker exec wireguard-dns-cron ps aux | grep -q cron; then
    print_status "Cron daemon is running" 0
else
    print_status "Cron daemon is not running" 1
fi

echo -e "\n🔍 Testing network connectivity..."

# Test container connectivity
if docker exec wireguard-dns-cron ping -c 1 wireguard-webadmin &> /dev/null; then
    print_status "Container-to-container connectivity works" 0
else
    print_status "Container-to-container connectivity failed" 1
fi

# Test external connectivity
if docker exec wireguard-webadmin ping -c 1 8.8.8.8 &> /dev/null; then
    print_status "External connectivity works" 0
else
    print_status "External connectivity failed" 1
fi

echo -e "\n🔍 Testing ports and services..."

# Check listening ports
if netstat -tlnp | grep -q ":8000"; then
    print_status "WebAdmin port 8000 is listening" 0
else
    print_status "WebAdmin port 8000 is not listening" 1
fi

if netstat -tlnp | grep -q ":51820"; then
    print_status "WireGuard port 51820 is listening" 0
else
    print_status "WireGuard port 51820 is not listening" 1
fi

if netstat -tlnp | grep -q ":53"; then
    print_status "DNS port 53 is listening" 0
else
    print_warning "DNS port 53 is not listening (may be normal if using host networking)"
fi

echo -e "\n📊 System Resources:"

# Check memory usage
echo "Memory usage:"
free -h

# Check disk usage
echo -e "\nDisk usage:"
df -h | head -5

# Check CPU usage
echo -e "\nCPU usage:"
top -bn1 | head -5

echo -e "\n🎯 Quick Test Summary:"
echo "====================="

# Count successes and failures
success_count=0
total_count=0

# Re-run key tests and count results
tests=(
    "docker --version"
    "docker compose version"
    "wg --version"
    "docker ps --format '{{.Names}}' | grep -q wireguard-webadmin"
    "docker ps --format '{{.Names}}' | grep -q wireguard-dns-cron"
    "docker ps --format '{{.Names}}' | grep -q wireguard-dnsmasq"
    "wg show interfaces"
    "[ -f /etc/wireguard/peer_hostnames.json ]"
    "[ -f ./shared_hosts/hosts ]"
    "docker exec wireguard-dns-cron python3 /app/haddns_multi.py"
)

for test in "${tests[@]}"; do
    total_count=$((total_count + 1))
    if eval "$test" &> /dev/null; then
        success_count=$((success_count + 1))
    fi
done

echo "Tests passed: $success_count/$total_count"

if [ $success_count -eq $total_count ]; then
    echo -e "${GREEN}🎉 All tests passed! HADDNS is working correctly.${NC}"
    exit 0
elif [ $success_count -gt $((total_count / 2)) ]; then
    echo -e "${YELLOW}⚠️  Most tests passed, but some issues need attention.${NC}"
    exit 1
else
    echo -e "${RED}❌ Many tests failed. Please check the configuration.${NC}"
    exit 2
fi
