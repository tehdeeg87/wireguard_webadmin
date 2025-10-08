#!/bin/bash
# Setup firewall rules for mDNS traffic on WireGuard interface

echo "🔥 Setting up firewall rules for mDNS traffic..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Check if iptables is available
if ! command -v iptables &> /dev/null; then
    echo "❌ iptables not found. Installing..."
    apt update
    apt install -y iptables
fi

# Add firewall rules for mDNS traffic on WireGuard interface
echo "📡 Adding firewall rules for mDNS traffic..."

# Allow mDNS traffic on WireGuard interface (UDP port 5353)
iptables -A INPUT -i wg0 -p udp --dport 5353 -j ACCEPT
iptables -A OUTPUT -o wg0 -p udp --dport 5353 -j ACCEPT

# Allow multicast traffic on WireGuard interface
iptables -A INPUT -i wg0 -d 224.0.0.0/24 -j ACCEPT
iptables -A OUTPUT -o wg0 -d 224.0.0.0/24 -j ACCEPT

# Save iptables rules
if command -v iptables-save &> /dev/null; then
    iptables-save > /etc/iptables/rules.v4
    echo "✅ Firewall rules saved"
else
    echo "⚠️  iptables-save not found, rules will be lost on reboot"
fi

echo "✅ Firewall rules configured for mDNS traffic on WireGuard interface"
echo ""
echo "📋 Rules added:"
echo "   • Allow UDP 5353 (mDNS) on wg0 interface"
echo "   • Allow multicast traffic (224.0.0.0/24) on wg0 interface"
echo ""
echo "🔧 To make rules persistent, install iptables-persistent:"
echo "   sudo apt install iptables-persistent"
