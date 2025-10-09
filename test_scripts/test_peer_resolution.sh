#!/bin/bash
# Test script for peer resolution from a simulated peer container

echo "🔍 Testing peer resolution from test-peer container..."
echo "=================================================="

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Test basic connectivity
echo "🌐 Testing basic connectivity..."
ping -c 2 wg-webadmin-test || echo "❌ Cannot reach main container"

# Test Avahi daemon
echo "🔍 Testing Avahi daemon..."
if pgrep avahi-daemon > /dev/null; then
    echo "✅ Avahi daemon is running"
else
    echo "❌ Avahi daemon not found"
fi

# Test mDNS resolution
echo "🔍 Testing mDNS resolution..."
echo "Available services:"
avahi-browse -a || echo "❌ Cannot browse services"

echo "WireGuard services:"
avahi-browse -t _wireguard._tcp || echo "❌ No WireGuard services found"

# Test hostname resolution
echo "🔍 Testing hostname resolution..."
echo "Testing .local domain resolution:"

# Test common hostnames that might be registered
test_hostnames=(
    "wireguard-webadmin.local"
    "wg-webadmin-test.local"
    "test-peer.local"
)

for hostname in "${test_hostnames[@]}"; do
    echo "Testing $hostname..."
    if avahi-resolve-host-name "$hostname" 2>/dev/null; then
        echo "✅ $hostname resolved"
    else
        echo "❌ $hostname not resolved"
    fi
done

# Test with nslookup as fallback
echo "🔍 Testing with nslookup..."
for hostname in "${test_hostnames[@]}"; do
    echo "Testing $hostname with nslookup..."
    if nslookup "$hostname" 2>/dev/null | grep -q "Address:"; then
        echo "✅ $hostname resolved via nslookup"
    else
        echo "❌ $hostname not resolved via nslookup"
    fi
done

echo "=================================================="
echo "✅ Peer resolution test completed!"
