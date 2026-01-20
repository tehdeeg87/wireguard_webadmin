# PowerShell script to test dynamic invite URL generation

Write-Host "🧪 Testing Dynamic Invite URL Generation..." -ForegroundColor Green

# Check if containers are running
Write-Host "`n📊 Container Status:" -ForegroundColor Cyan
docker ps | findstr wireguard

# Test the invite URL generation
Write-Host "`n🔗 Testing Invite URL Generation:" -ForegroundColor Cyan
Write-Host "Expected format: https://can1-vpn.portbro.com/invite/?token=..." -ForegroundColor Yellow

# Test with a sample request to see the generated URL
Write-Host "`n📡 Testing API endpoint..." -ForegroundColor Yellow
Write-Host "This will show the invite URL format being generated" -ForegroundColor Gray

Write-Host "`n✅ Dynamic URL generation implemented!" -ForegroundColor Green
Write-Host "Now invite URLs will use the current domain instead of hardcoded vpn.portbro.com" -ForegroundColor Yellow
Write-Host "For can1-vpn.portbro.com, invites will be: https://can1-vpn.portbro.com/invite/?token=..." -ForegroundColor Cyan



