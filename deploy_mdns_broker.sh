#!/bin/bash
# Deploy centralized mDNS broker for WireGuard peer discovery

echo "🚀 Deploying centralized mDNS broker for WireGuard..."

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

# Step 4: Setup firewall rules
echo "🔥 Setting up firewall rules..."
if [ -f "./setup_mdns_firewall.sh" ]; then
    chmod +x ./setup_mdns_firewall.sh
    ./setup_mdns_firewall.sh
else
    echo "⚠️  Firewall setup script not found"
fi

# Step 5: Deploy Docker containers
echo "🐳 Deploying Docker containers..."
docker-compose down
docker-compose up -d --build

# Step 6: Wait for containers to start
echo "⏳ Waiting for containers to start..."
sleep 10

# Step 7: Check container status
echo "📊 Checking container status..."
docker-compose ps

# Step 8: Test mDNS resolution
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
echo "   • Centralized mDNS broker in Docker container"
echo "   • Firewall rules for mDNS traffic"
echo "   • Host files generated for peer resolution"
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
