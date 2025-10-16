#!/bin/bash
set -e

echo "🚀 Deploying WireGuard WebAdmin with DNS Integration..."

# Make entrypoint script executable
chmod +x entrypoint-dns.sh

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Remove orphaned containers
echo "🧹 Cleaning up orphaned containers..."
docker-compose down --remove-orphans

# Clean up any existing dnsmasq processes
echo "🧹 Cleaning up existing dnsmasq processes..."
docker system prune -f

# Create shared_hosts directory if it doesn't exist
echo "📁 Creating shared_hosts directory..."
mkdir -p shared_hosts
chmod 755 shared_hosts

# Deploy containers
echo "🐳 Starting containers..."
docker-compose up -d

# Wait for containers to start
echo "⏳ Waiting for containers to start..."
sleep 30

# Check container status
echo "📊 Container Status:"
docker ps

echo ""
echo "🎉 Deployment complete!"
echo "   - DNS integration is automatically configured"
echo "   - Peers will get automatic DNS resolution"
echo "   - Access WebAdmin at: http://localhost:8000"
echo ""
echo "🔍 To check DNS status:"
echo "   docker exec wireguard-webadmin python3 manage.py update_dns --status"
echo ""
echo "🧪 To test DNS resolution:"
echo "   nslookup [peer-name].vpn.local 10.188.0.1"
