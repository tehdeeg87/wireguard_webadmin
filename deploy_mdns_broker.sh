#!/bin/bash
# Deploy mDNS broker for WireGuard peer discovery (Case 1)

echo "🚀 Deploying mDNS broker for WireGuard peer discovery..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Step 1: Install WireGuard on host system
echo "📦 Installing WireGuard on host system..."
apt update
apt install -y wireguard

# Step 2: Copy WireGuard configs from container to host
echo "📋 Copying WireGuard configs from container to host..."
if docker ps | grep -q wireguard-webadmin; then
    docker cp wireguard-webadmin:/etc/wireguard/wg0.conf /etc/wireguard/
    chmod 600 /etc/wireguard/wg0.conf
    chown root:root /etc/wireguard/wg0.conf
    echo "✅ WireGuard config copied to host"
else
    echo "⚠️  WireGuard WebAdmin container not running, skipping config copy"
fi

# Step 3: Start WireGuard daemon on host
echo "🔧 Starting WireGuard daemon on host..."
systemctl start wg-quick@wg0
systemctl enable wg-quick@wg0

# Check if WireGuard interface is up
if ip link show wg0 &> /dev/null; then
    echo "✅ WireGuard interface wg0 is up"
else
    echo "⚠️  WireGuard interface wg0 not found"
fi

# Step 4: Deploy Docker containers
echo "🐳 Deploying Docker containers..."
docker-compose down
docker-compose up -d --build

# Step 5: Wait for containers to start
echo "⏳ Waiting for containers to start..."
sleep 15

# Step 6: Check container status
echo "📊 Checking container status..."
docker-compose ps

# Step 7: Test mDNS resolution
echo "🧪 Testing mDNS resolution..."
if command -v avahi-resolve-host-name &> /dev/null; then
    avahi-resolve-host-name localhost.local
else
    echo "⚠️  avahi-resolve-host-name not found"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📋 What's been set up:"
echo "   • WireGuard daemon running on host system"
echo "   • mDNS broker in Docker container (network_mode: host)"
echo "   • Firewall rules for mDNS traffic (UDP 5353)"
echo "   • Peer configs include multicast subnet (224.0.0.0/24)"
echo ""
echo "🔧 Next steps:"
echo "   1. Connect peers to WireGuard instance"
echo "   2. Test peer-to-peer hostname resolution"
echo "   3. Check logs: docker logs wireguard-mdns"
echo ""
echo "🧪 Test commands:"
echo "   • From server: ping phone.wg0.local"
echo "   • From peer: ping computer.wg0.local"
echo "   • Browse services: avahi-browse -a"
