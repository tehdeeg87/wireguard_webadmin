@echo off
setlocal enabledelayedexpansion

echo 🚀 Deploying WireGuard WebAdmin with DNS Integration (portbro.vpn domain)
echo ==================================================================

REM Step 1: Stop existing containers
echo 📦 Stopping existing containers...
docker-compose down

REM Step 2: Clean up any orphaned containers
echo 🧹 Cleaning up orphaned containers...
docker-compose down --remove-orphans

REM Step 3: Create shared_hosts directory if it doesn't exist
echo 📁 Creating shared_hosts directory...
if not exist "shared_hosts" mkdir shared_hosts

REM Step 4: Deploy containers
echo 🐳 Deploying containers...
docker-compose up -d

REM Step 5: Wait for containers to start
echo ⏳ Waiting for containers to start...
timeout /t 30 /nobreak >nul

REM Step 6: Check container status
echo 📊 Checking container status...
docker ps

REM Step 7: Wait for Django to be ready
echo ⏳ Waiting for Django to be ready...
timeout /t 10 /nobreak >nul

REM Step 8: Test DNS configuration
echo 🔍 Testing DNS configuration...
docker exec wireguard-webadmin python3 manage.py update_dns --status

REM Step 9: Update DNS hosts file
echo 📝 Updating DNS hosts file...
docker exec wireguard-webadmin python3 manage.py update_dns --reload

REM Step 10: Test DNS resolution
echo 🌐 Testing DNS resolution...
docker exec wireguard-webadmin nslookup localhost 127.0.0.1 >nul 2>&1
if !errorlevel! equ 0 (
    echo ✅ DNS is working correctly
) else (
    echo ❌ DNS test failed - checking dnsmasq status...
    docker exec wireguard-webadmin ps aux | findstr dnsmasq
)

echo.
echo 🎉 Deployment complete!
echo.
echo 📋 Next steps:
echo 1. Access the web interface at http://localhost:8000
echo 2. Create a test peer
echo 3. Test DNS resolution: nslookup testpeer.portbro.vpn 10.188.0.1
echo 4. Test ping: ping testpeer.portbro.vpn
echo.
echo 🔧 Useful commands:
echo - Check DNS status: docker exec wireguard-webadmin python3 manage.py update_dns --status
echo - Update DNS: docker exec wireguard-webadmin python3 manage.py update_dns --reload
echo - View logs: docker logs wireguard-webadmin
echo - Test DNS: nslookup [peer-name].portbro.vpn 10.188.0.1

pause
