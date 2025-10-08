#!/bin/bash
# Setup Avahi + Reflector for WireGuard mDNS

echo "🚀 Setting up Avahi + Reflector for WireGuard mDNS..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Install Avahi
echo "📦 Installing Avahi mDNS daemon..."
apt update
apt install -y avahi-daemon avahi-utils

# Backup original config
echo "💾 Backing up original Avahi config..."
cp /etc/avahi/avahi-daemon.conf /etc/avahi/avahi-daemon.conf.backup

# Create new config for WireGuard
echo "⚙️  Configuring Avahi for WireGuard interface..."
cat > /etc/avahi/avahi-daemon.conf << 'EOF'
[server]
allow-interfaces=wg0
use-ipv4=yes
use-ipv6=no

[reflector]
enable-reflector=yes
EOF

# Create hosts directory
echo "📁 Setting up mDNS hosts directory..."
mkdir -p /etc/avahi/hosts
chown -R avahi:avahi /etc/avahi/hosts
chmod 755 /etc/avahi/hosts

# Enable and start Avahi
echo "🔄 Starting Avahi daemon..."
systemctl enable avahi-daemon
systemctl restart avahi-daemon

# Check status
echo "✅ Checking Avahi status..."
systemctl status avahi-daemon --no-pager

# Test mDNS
echo "🧪 Testing mDNS resolution..."
if avahi-resolve-host-name localhost.local > /dev/null 2>&1; then
    echo "✅ mDNS is working correctly!"
else
    echo "⚠️  mDNS test failed, but this might be normal"
fi

echo ""
echo "🎉 Setup complete! Avahi + Reflector is now configured for WireGuard."
echo ""
echo "📋 What this enables:"
echo "   • Peers can resolve each other by hostname (e.g., phone1.wg0.local)"
echo "   • Automatic peer discovery across WireGuard tunnel"
echo "   • No manual configuration needed on peer devices"
echo ""
echo "🔧 Next steps:"
echo "   1. Deploy your WireGuard WebAdmin code"
echo "   2. Connect peers to the WireGuard instance"
echo "   3. Test: ping phone1.wg0.local from another peer"
echo ""
echo "📖 For troubleshooting, see: UBUNTU_MDNS_SETUP.md"
