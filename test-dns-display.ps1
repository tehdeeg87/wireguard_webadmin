# PowerShell script to test DNS hostname display in peer list

Write-Host "🧪 Testing DNS Hostname Display in Peer List..." -ForegroundColor Green

# Check if containers are running
Write-Host "`n📊 Container Status:" -ForegroundColor Cyan
docker ps | findstr wireguard

# Test DNS status
Write-Host "`n📡 DNS Status:" -ForegroundColor Cyan
docker exec wireguard-webadmin python3 manage.py update_dns --status

# Show current peers and their hostnames
Write-Host "`n👥 Current Peers:" -ForegroundColor Cyan
docker exec wireguard-webadmin python3 -c "
from wireguard.models import Peer
for peer in Peer.objects.all():
    print(f'Peer: {peer.name} -> Hostname: {peer.hostname} -> DNS: {peer.hostname}.vpn.local' if peer.hostname else f'Peer: {peer.name} -> No hostname set')
"

Write-Host "`n🌐 Testing DNS Resolution:" -ForegroundColor Cyan
Write-Host "Testing from inside container..." -ForegroundColor Yellow
docker exec wireguard-webadmin nslookup dansphone.vpn.local 127.0.0.1 2>$null

Write-Host "`n✅ Test complete!" -ForegroundColor Green
Write-Host "Now check the web interface at http://localhost:8000 to see the DNS hostnames displayed in the peer list." -ForegroundColor Yellow
