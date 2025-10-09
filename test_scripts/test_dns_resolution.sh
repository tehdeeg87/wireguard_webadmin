#!/bin/bash
# Test script for DNS resolution testing

echo "🔍 Testing DNS resolution from dns-test container..."
echo "=================================================="

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Test Avahi daemon status
echo "🔍 Testing Avahi daemon status..."
if pgrep avahi-daemon > /dev/null; then
    echo "✅ Avahi daemon is running"
    echo "Avahi daemon processes:"
    pgrep -f avahi-daemon
else
    echo "❌ Avahi daemon not found"
fi

# Test D-Bus connectivity
echo "🔍 Testing D-Bus connectivity..."
if dbus-send --system --print-reply --dest=org.freedesktop.Avahi / org.freedesktop.Avahi.Server.GetVersion 2>/dev/null; then
    echo "✅ D-Bus connection to Avahi successful"
else
    echo "❌ D-Bus connection to Avahi failed"
fi

# Test service discovery
echo "🔍 Testing service discovery..."
echo "All available services:"
avahi-browse -a -t || echo "❌ Cannot browse services"

echo ""
echo "WireGuard specific services:"
avahi-browse -t _wireguard._tcp || echo "❌ No WireGuard services found"

echo ""
echo "HTTP services:"
avahi-browse -t _http._tcp || echo "❌ No HTTP services found"

# Test hostname resolution
echo "🔍 Testing hostname resolution..."
echo "Testing various hostname formats:"

# Test the main container
test_hostnames=(
    "wg-webadmin-test"
    "wg-webadmin-test.local"
    "wireguard-webadmin"
    "wireguard-webadmin.local"
    "localhost"
    "127.0.0.1"
)

for hostname in "${test_hostnames[@]}"; do
    echo ""
    echo "Testing: $hostname"
    
    # Test with avahi-resolve-host-name
    if result=$(avahi-resolve-host-name "$hostname" 2>/dev/null); then
        echo "  ✅ avahi-resolve: $result"
    else
        echo "  ❌ avahi-resolve: failed"
    fi
    
    # Test with nslookup
    if result=$(nslookup "$hostname" 2>/dev/null | grep "Address:" | tail -1); then
        echo "  ✅ nslookup: $result"
    else
        echo "  ❌ nslookup: failed"
    fi
    
    # Test with dig
    if result=$(dig +short "$hostname" 2>/dev/null); then
        if [ -n "$result" ]; then
            echo "  ✅ dig: $result"
        else
            echo "  ❌ dig: no result"
        fi
    else
        echo "  ❌ dig: failed"
    fi
done

# Test reverse DNS
echo "🔍 Testing reverse DNS..."
echo "Testing reverse lookup for 127.0.0.1:"
if result=$(avahi-resolve-address 127.0.0.1 2>/dev/null); then
    echo "  ✅ Reverse: $result"
else
    echo "  ❌ Reverse: failed"
fi

# Test network connectivity
echo "🔍 Testing network connectivity..."
echo "Ping tests:"
ping -c 2 wg-webadmin-test && echo "  ✅ Can ping main container" || echo "  ❌ Cannot ping main container"
ping -c 2 avahi-test && echo "  ✅ Can ping Avahi container" || echo "  ❌ Cannot ping Avahi container"

echo "=================================================="
echo "✅ DNS resolution test completed!"
