# PowerShell deployment script for WireGuard WebAdmin with DNS Integration

Write-Host "🚀 Deploying WireGuard WebAdmin with DNS Integration..." -ForegroundColor Green

# Stop existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Remove orphaned containers
Write-Host "🧹 Cleaning up orphaned containers..." -ForegroundColor Yellow
docker-compose down --remove-orphans

# Clean up any existing dnsmasq processes
Write-Host "🧹 Cleaning up existing dnsmasq processes..." -ForegroundColor Yellow
docker system prune -f

# Create shared_hosts directory if it doesn't exist
Write-Host "📁 Creating shared_hosts directory..." -ForegroundColor Yellow
if (!(Test-Path "shared_hosts")) {
    New-Item -ItemType Directory -Path "shared_hosts"
}

# Deploy containers
Write-Host "🐳 Starting containers..." -ForegroundColor Yellow
docker-compose up -d

# Wait for containers to start
Write-Host "⏳ Waiting for containers to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check container status
Write-Host "📊 Container Status:" -ForegroundColor Cyan
docker ps

Write-Host ""
Write-Host "🎉 Deployment complete!" -ForegroundColor Green
Write-Host "   - DNS integration is automatically configured" -ForegroundColor White
Write-Host "   - Peers will get automatic DNS resolution" -ForegroundColor White
Write-Host "   - Access WebAdmin at: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "🔍 To check DNS status:" -ForegroundColor Cyan
Write-Host "   docker exec wireguard-webadmin python3 manage.py update_dns --status" -ForegroundColor White
Write-Host ""
Write-Host "🧪 To test DNS resolution:" -ForegroundColor Cyan
Write-Host "   nslookup [peer-name].vpn.local 10.188.0.1" -ForegroundColor White
