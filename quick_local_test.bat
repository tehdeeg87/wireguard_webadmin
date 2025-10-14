@echo off
REM Quick Local Test Script for HADDNS on Docker Desktop (Windows)

echo 🚀 HADDNS Quick Local Test for Docker Desktop
echo ==============================================

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo ✅ Docker is running

REM Create shared_hosts directory if it doesn't exist
if not exist ".\shared_hosts" mkdir ".\shared_hosts"

REM Start containers
echo 🐳 Starting containers...
docker compose up -d

REM Wait for containers to start
echo ⏳ Waiting for containers to start...
timeout /t 15 /nobreak >nul

REM Check container status
echo 📊 Container Status:
docker ps --filter name=wireguard --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

REM Create test peer mapping
echo 📝 Creating test peer mapping...
docker exec -i wireguard-webadmin bash -c "cat > /etc/wireguard/peer_hostnames.json" < nul
(
echo {
echo   "test_peer_1_public_key_here_32_chars_long_abcd=": {
echo     "hostname": "testclient1.vpn.local",
echo     "ip": "10.0.0.100"
echo   },
echo   "test_peer_2_public_key_here_32_chars_long_efgh=": {
echo     "hostname": "testclient2.vpn.local",
echo     "ip": "10.0.0.101"
echo   }
echo }
) | docker exec -i wireguard-webadmin bash -c "cat > /etc/wireguard/peer_hostnames.json"

echo ✅ Test peer mapping created

REM Test HADDNS script
echo 🔧 Testing HADDNS script...
docker exec wireguard-dns-cron python /app/haddns.py

REM Check if hosts file was created
echo 📄 Checking hosts file...
if exist ".\shared_hosts\hosts" (
    echo ✅ Hosts file created:
    type ".\shared_hosts\hosts"
) else (
    echo ❌ Hosts file not found
)

REM Test DNS resolution
echo 🌐 Testing DNS resolution...
docker exec wireguard-webadmin nslookup testclient1.vpn.local 127.0.0.1

REM Show logs
echo 📋 Recent HADDNS logs:
docker logs --tail 10 wireguard-dns-cron

echo.
echo 🎉 Quick test complete!
echo Run 'python test_haddns_local.py' for comprehensive testing
pause
