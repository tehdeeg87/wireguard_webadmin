#!/bin/bash

# HADDNS (Handshake-Aware Dynamic DNS Resolution) Setup Script
# This script sets up the HADDNS system for WireGuard WebAdmin

set -e

echo "🚀 Setting up HADDNS (Handshake-Aware Dynamic DNS Resolution)..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Check if Django is available
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python first."
    exit 1
fi

# Navigate to project directory
cd /app || { echo "❌ Project directory /app not found"; exit 1; }

echo "📦 Installing required Python packages..."
pip install -r requirements.txt

echo "🗄️  Running database migrations..."
python manage.py makemigrations dns
python manage.py migrate

echo "⚙️  Setting up HADDNS configuration..."
python manage.py haddns_setup --domain vpn.local --threshold 300

echo "🔧 Generating dnsmasq configuration..."
python manage.py generate_dnsmasq_config

echo "📁 Creating necessary directories..."
mkdir -p /etc/dnsmasq.d
mkdir -p /var/log

echo "🔄 Setting up cron job..."
# Add HADDNS cron job if not already present
if ! grep -q "haddns_update" /etc/crontab; then
    echo "*/1 * * * * root cd /app && python manage.py haddns_update >> /var/log/haddns.log 2>&1" >> /etc/crontab
    echo "✅ Added HADDNS cron job"
else
    echo "ℹ️  HADDNS cron job already exists"
fi

echo "🧪 Testing HADDNS setup..."
python manage.py haddns_update --dry-run --verbose

echo "📋 HADDNS Setup Summary:"
echo "========================="
echo "✅ Database migrations completed"
echo "✅ HADDNS configuration created"
echo "✅ dnsmasq configuration generated"
echo "✅ Cron job scheduled (every minute)"
echo "✅ Test run completed"
echo ""
echo "🔧 Next Steps:"
echo "1. Restart dnsmasq: systemctl restart dnsmasq"
echo "2. Check logs: tail -f /var/log/haddns.log"
echo "3. Test DNS resolution: nslookup peer-hostname.vpn.local"
echo "4. Monitor peer status in Django admin: /admin/dns/peerhostnamemapping/"
echo ""
echo "📚 Configuration Files:"
echo "- HADDNS Config: Django admin -> DNS -> HADDNS Configs"
echo "- Dynamic Hosts: /etc/dnsmasq.d/haddns_dynamic_hosts.conf"
echo "- dnsmasq Config: /etc/dnsmasq.d/wireguard_webadmin.conf"
echo ""
echo "🎉 HADDNS setup complete!"
