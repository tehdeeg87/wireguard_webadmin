#!/bin/bash
set -e

echo "🚀 Deploying WireGuard WebAdmin with DNS Integration (portbro.vpn domain)"
echo "=================================================================="

# Step 1: Stop existing containers
echo "📦 Stopping existing containers..."
docker-compose down

# Step 2: Clean up any orphaned containers
echo "🧹 Cleaning up orphaned containers..."
docker-compose down --remove-orphans

# Step 3: Create shared_hosts directory if it doesn't exist
echo "📁 Creating shared_hosts directory..."
mkdir -p shared_hosts

# Step 4: Make init script executable (on Linux/Unix)
if command -v chmod >/dev/null 2>&1; then
    echo "🔧 Making init script executable..."
    chmod +x init-dns.sh
fi

# Step 5: Deploy containers
echo "🐳 Deploying containers..."
docker-compose up -d

# Step 6: Wait for containers to start
echo "⏳ Waiting for containers to start..."
sleep 30

# Step 7: Check container status
echo "📊 Checking container status..."
docker ps

# Step 8: Wait for Django to be ready
echo "⏳ Waiting for Django to be ready..."
sleep 10

# Step 9: Test DNS configuration
echo "🔍 Testing DNS configuration..."
docker exec wireguard-webadmin python3 manage.py update_dns --status

# Step 10: Update DNS hosts file
echo "📝 Updating DNS hosts file..."
docker exec wireguard-webadmin python3 manage.py update_dns --reload

# Step 11: Test DNS resolution
echo "🌐 Testing DNS resolution..."
if docker exec wireguard-webadmin nslookup localhost 127.0.0.1 >/dev/null 2>&1; then
    echo "✅ DNS is working correctly"
else
    echo "❌ DNS test failed - checking dnsmasq status..."
    docker exec wireguard-webadmin ps aux | grep dnsmasq
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Access the web interface at http://localhost:8000"
echo "2. Create a test peer"
echo "3. Test DNS resolution: nslookup testpeer.portbro.vpn 10.188.0.1"
echo "4. Test ping: ping testpeer.portbro.vpn"
echo ""
echo "🔧 Useful commands:"
echo "- Check DNS status: docker exec wireguard-webadmin python3 manage.py update_dns --status"
echo "- Update DNS: docker exec wireguard-webadmin python3 manage.py update_dns --reload"
echo "- View logs: docker logs wireguard-webadmin"
echo "- Test DNS: nslookup [peer-name].portbro.vpn 10.188.0.1"
