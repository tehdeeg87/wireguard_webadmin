# 🐳 Avahi Docker Testing Guide

This guide shows you how to test the Avahi peer hostname resolution functionality in local Docker containers.

## 🚀 Quick Start

### 1. Run the Complete Test Suite
```bash
# Make the test script executable
chmod +x test_avahi_docker.sh

# Run the complete test suite
./test_avahi_docker.sh
```

This will:
- Build and start all test containers
- Create sample peer data
- Test Avahi functionality from multiple containers
- Provide interactive testing options

### 2. Manual Testing

#### Start the Test Environment
```bash
# Start all containers
docker-compose -f docker-compose-test.yml up -d

# Wait for services to start
sleep 30

# Setup test data
docker exec wg-webadmin-test python /app/test_scripts/setup_test_data.py
```

#### Test Hostname Resolution
```bash
# Test from main container
docker exec wg-webadmin-test avahi-resolve-host-name my-phone
docker exec wg-webadmin-test avahi-resolve-host-name my-phone.wg0.local

# Test from peer container
docker exec test-peer avahi-resolve-host-name my-phone
docker exec test-peer ping my-phone

# Test from DNS container
docker exec dns-test avahi-resolve-host-name my-phone
```

#### Browse Services
```bash
# List all available services
docker exec wg-webadmin-test avahi-browse -a

# List WireGuard services
docker exec wg-webadmin-test avahi-browse -t _wireguard._tcp
```

#### Access Web Interface
- URL: http://localhost:8000
- Username: `admin`
- Password: `admin123`

## 🧪 Test Containers

### Main Container (`wg-webadmin-test`)
- Runs the WireGuard WebAdmin application
- Has Avahi daemon running
- Contains test peer data
- Accessible at http://localhost:8000

### Avahi Container (`avahi-test`)
- Dedicated Avahi daemon for mDNS
- Handles service discovery
- Shares D-Bus with main container

### Test Peer Container (`test-peer`)
- Simulates a WireGuard client
- Tests hostname resolution from peer perspective
- Runs automated tests

### DNS Test Container (`dns-test`)
- Tests DNS resolution functionality
- Verifies mDNS service discovery
- Runs comprehensive DNS tests

## 📋 Test Data

The test setup creates:
- **WireGuard Instance**: `wg0` (10.188.0.1/24)
- **Test Peers**:
  - `my-phone` → 10.188.0.3
  - `laptop` → 10.188.0.4
  - `server` → 10.188.0.5
  - `tablet` → 10.188.0.6

## 🔍 Expected Results

### Hostname Resolution
These hostnames should resolve to their respective IPs:
```bash
my-phone → 10.188.0.3
my-phone.wg0.local → 10.188.0.3
my-phone.wg.local → 10.188.0.3

laptop → 10.188.0.4
laptop.wg0.local → 10.188.0.4
laptop.wg.local → 10.188.0.4
```

### Service Discovery
```bash
# Should show WireGuard services
avahi-browse -t _wireguard._tcp

# Should show HTTP services
avahi-browse -t _http._tcp
```

## 🐛 Troubleshooting

### Containers Won't Start
```bash
# Check Docker is running
docker info

# Check for port conflicts
netstat -tulpn | grep :8000
netstat -tulpn | grep :51820

# Clean up and restart
docker-compose -f docker-compose-test.yml down --remove-orphans
docker system prune -f
```

### Avahi Not Working
```bash
# Check Avahi daemon status
docker exec wg-webadmin-test pgrep avahi-daemon

# Check D-Bus status
docker exec wg-webadmin-test pgrep dbus

# View Avahi logs
docker exec wg-webadmin-test journalctl -u avahi-daemon

# Restart Avahi
docker exec wg-webadmin-test pkill avahi-daemon
docker exec wg-webadmin-test avahi-daemon -D
```

### Hostname Resolution Failing
```bash
# Check hosts files
docker exec wg-webadmin-test cat /etc/avahi/hosts/wg0.hosts

# Regenerate hosts files
docker exec wg-webadmin-test python manage.py register_peers_avahi --reload

# Check Avahi configuration
docker exec wg-webadmin-test cat /etc/avahi/avahi-daemon.conf
```

## 🧹 Cleanup

```bash
# Stop and remove all test containers
docker-compose -f docker-compose-test.yml down --remove-orphans

# Remove test volumes
docker volume prune -f

# Remove test images (optional)
docker rmi $(docker images | grep wireguard_webadmin | awk '{print $3}')
```

## 📊 Monitoring

### View Logs
```bash
# All containers
docker-compose -f docker-compose-test.yml logs -f

# Specific container
docker logs wg-webadmin-test -f
docker logs avahi-test -f
```

### Check Container Status
```bash
docker-compose -f docker-compose-test.yml ps
docker stats
```

## 🎯 Success Criteria

✅ **Avahi daemon running** in all containers  
✅ **Hostname resolution** working for all test peers  
✅ **Service discovery** showing WireGuard services  
✅ **Cross-container resolution** working  
✅ **Web interface** accessible and functional  
✅ **Automatic registration** when peers are created/modified  

If all criteria are met, your Avahi implementation is working correctly! 🎉
