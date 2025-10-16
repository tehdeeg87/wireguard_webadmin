# PowerShell script to test instance-based DNS naming

Write-Host "🧪 Testing Instance-Based DNS Naming..." -ForegroundColor Green

# Check if containers are running
Write-Host "`n📊 Container Status:" -ForegroundColor Cyan
docker ps | findstr wireguard

# Test DNS status
Write-Host "`n📡 DNS Status:" -ForegroundColor Cyan
docker exec wireguard-webadmin python3 manage.py update_dns --status

# Show current peers and their new DNS names
Write-Host "`n👥 Current Peers with New DNS Names:" -ForegroundColor Cyan
docker exec wireguard-webadmin python3 -c "
from wireguard.models import Peer
for peer in Peer.objects.select_related('wireguard_instance').all():
    if peer.hostname:
        dns_name = f'{peer.hostname}.{peer.wireguard_instance.instance_id}.portbro.vpn'
        print(f'Peer: {peer.name} -> Hostname: {peer.hostname} -> DNS: {dns_name}')
    else:
        print(f'Peer: {peer.name} -> No hostname set')
"

# Update DNS with new naming
Write-Host "`n🔄 Updating DNS with new naming..." -ForegroundColor Yellow
docker exec wireguard-webadmin python3 manage.py update_dns --reload

# Show the hosts file content
Write-Host "`n📁 Hosts File Content:" -ForegroundColor Cyan
Get-Content shared_hosts/hosts_static

Write-Host "`n🌐 Testing DNS Resolution:" -ForegroundColor Cyan
Write-Host "Testing from inside container..." -ForegroundColor Yellow
docker exec wireguard-webadmin nslookup dansphone.0.portbro.vpn 127.0.0.1 2>$null

Write-Host "`n✅ Test complete!" -ForegroundColor Green
Write-Host "Now check the web interface at http://localhost:8000 to see the new DNS format." -ForegroundColor Yellow
Write-Host "Format: hostname.instance_id.portbro.vpn" -ForegroundColor Cyan
