@echo off
REM Comprehensive test script for Avahi functionality in Docker containers (Windows)

echo 🚀 WireGuard WebAdmin - Avahi Docker Testing
echo =============================================

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker first.
    exit /b 1
)

echo [SUCCESS] Docker is running

REM Step 1: Build and start containers
echo [INFO] Step 1: Building and starting Docker containers...
docker-compose -f docker-compose-test.yml down --remove-orphans
docker-compose -f docker-compose-test.yml build
docker-compose -f docker-compose-test.yml up -d

echo [SUCCESS] Containers started

REM Step 2: Wait for services to be ready
echo [INFO] Step 2: Waiting for services to be ready...
timeout /t 30 /nobreak >nul

REM Check if containers are running
echo [INFO] Checking container status...
docker-compose -f docker-compose-test.yml ps

REM Step 3: Setup test data
echo [INFO] Step 3: Setting up test data...
docker exec wg-webadmin-test python /app/test_scripts/setup_test_data.py

REM Step 4: Test Avahi functionality
echo [INFO] Step 4: Testing Avahi functionality...

REM Test from main container
echo [INFO] Testing from main container...
docker exec wg-webadmin-test python /app/test_avahi_peer_resolution.py

REM Test from peer container
echo [INFO] Testing from peer container...
docker exec test-peer /test_scripts/test_peer_resolution.sh

REM Test from DNS container
echo [INFO] Testing from DNS container...
docker exec dns-test /test_scripts/test_dns_resolution.sh

REM Step 5: Interactive testing
echo [INFO] Step 5: Interactive testing options...
echo.
echo 🔍 You can now test Avahi functionality interactively:
echo.
echo 1. Test hostname resolution:
echo    docker exec wg-webadmin-test avahi-resolve-host-name my-phone
echo    docker exec wg-webadmin-test avahi-resolve-host-name my-phone.wg0.local
echo.
echo 2. Browse services:
echo    docker exec wg-webadmin-test avahi-browse -a
echo    docker exec wg-webadmin-test avahi-browse -t _wireguard._tcp
echo.
echo 3. Test from peer container:
echo    docker exec test-peer avahi-resolve-host-name my-phone
echo    docker exec test-peer ping my-phone
echo.
echo 4. Access the web interface:
echo    http://localhost:8000
echo    Login: admin / admin123
echo.
echo 5. View logs:
echo    docker-compose -f docker-compose-test.yml logs -f
echo.

REM Ask if user wants to keep containers running
set /p keep_running="Do you want to keep the containers running for interactive testing? (y/n): "
if /i "%keep_running%"=="y" (
    echo [INFO] Containers will continue running. Use 'docker-compose -f docker-compose-test.yml down' to stop them.
    echo [INFO] You can run the test scripts again with:
    echo    docker exec wg-webadmin-test python /app/test_avahi_peer_resolution.py
    echo    docker exec test-peer /test_scripts/test_peer_resolution.sh
    echo    docker exec dns-test /test_scripts/test_dns_resolution.sh
) else (
    echo [INFO] Stopping containers...
    docker-compose -f docker-compose-test.yml down
    echo [SUCCESS] Containers stopped
)

echo.
echo [SUCCESS] Avahi Docker testing completed!
echo =============================================
pause
