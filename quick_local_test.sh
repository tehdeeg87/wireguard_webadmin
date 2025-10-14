#!/bin/bash
# Quick Local Test Script for HADDNS on Docker Desktop

echo "🚀 HADDNS Quick Local Test for Docker Desktop"
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✅ Docker is running"

# Create shared_hosts directory if it doesn't exist
mkdir -p ./shared_hosts

# Start containers
echo "🐳 Starting containers..."
docker compose up -d

# Wait for containers to start
echo "⏳ Waiting for containers to start..."
sleep 15

# Check container status
echo "📊 Container Status:"
docker ps --filter name=wireguard --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Create test peer mapping
echo "📝 Creating test peer mapping..."
docker exec -i wireguard-webadmin bash -c 'cat > /etc/wireguard/peer_hostnames.json' << 'EOF'
{
  "test_peer_1_public_key_here_32_chars_long_abcd=": {
    "hostname": "testclient1.vpn.local",
    "ip": "10.0.0.100"
  },
  "test_peer_2_public_key_here_32_chars_long_efgh=": {
    "hostname": "testclient2.vpn.local",
    "ip": "10.0.0.101"
  }
}
EOF

echo "✅ Test peer mapping created"

# Test HADDNS script
echo "🔧 Testing HADDNS script..."
docker exec wireguard-dns-cron python3 /app/haddns.py

# Check if hosts file was created
echo "📄 Checking hosts file..."
if [ -f "./shared_hosts/hosts" ]; then
    echo "✅ Hosts file created:"
    cat ./shared_hosts/hosts
else
    echo "❌ Hosts file not found"
fi

# Test DNS resolution
echo "🌐 Testing DNS resolution..."
docker exec wireguard-webadmin nslookup testclient1.vpn.local 127.0.0.1 || echo "DNS test failed (expected if no real peers)"

# Show logs
echo "📋 Recent HADDNS logs:"
docker logs --tail 10 wireguard-dns-cron

echo ""
echo "🎉 Quick test complete!"
echo "Run 'python test_haddns_local.py' for comprehensive testing"
