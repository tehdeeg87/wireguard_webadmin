# PowerShell script to test DNS functionality

Write-Host "🧪 Testing WireGuard WebAdmin DNS Integration..." -ForegroundColor Green

# Check container status
Write-Host "`n📊 Container Status:" -ForegroundColor Cyan
docker ps

# Check DNS status
Write-Host "`n📡 DNS Status:" -ForegroundColor Cyan
docker exec wireguard-webadmin python3 manage.py update_dns --status

# Show hosts file
Write-Host "`n📁 Hosts File Contents:" -ForegroundColor Cyan
Get-Content shared_hosts/hosts_static -ErrorAction SilentlyContinue

# Test DNS resolution (if peers exist)
Write-Host "`n🔍 Testing DNS Resolution:" -ForegroundColor Cyan
Write-Host "Testing from inside container..." -ForegroundColor Yellow
docker exec wireguard-webadmin nslookup testpeer.vpn.local 127.0.0.1 2>$null

Write-Host "`nTesting from host system..." -ForegroundColor Yellow
nslookup testpeer.vpn.local 10.188.0.1 2>$null

Write-Host "`n✅ DNS test complete!" -ForegroundColor Green
Write-Host "If you see 'Name or service not known', create a peer first in the WebAdmin interface." -ForegroundColor Yellow
