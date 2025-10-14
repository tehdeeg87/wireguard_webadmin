# HADDNS Ubuntu Deployment Checklist

## Pre-Deployment Setup

### 1. Server Requirements
- [ ] Ubuntu 20.04+ with Docker and Docker Compose installed
- [ ] WireGuard tools installed: `apt install wireguard-tools`
- [ ] At least 2GB RAM and 10GB free disk space
- [ ] Firewall configured to allow ports 8000, 51820-51839, 53
- [ ] Server has static IP address

### 2. File Transfer
- [ ] Copy all modified files to Ubuntu server:
  - `dns_cron/Dockerfile`
  - `dns_cron/haddns_multi.py`
  - `docker-compose.yml`
  - `setup_multi_instance_mapping.py`
  - `test_haddns_ubuntu.py`
  - `HADDNS_MULTI_INSTANCE_GUIDE.md`

### 3. Environment Variables
- [ ] Set required environment variables:
  ```bash
  export SERVER_ADDRESS="your-server-ip"
  export TIMEZONE="UTC"
  export EXTRA_ALLOWED_HOSTS=""
  ```

## Deployment Steps

### Step 1: Initial Setup
```bash
# Navigate to project directory
cd /path/to/wireguard_webadmin

# Make scripts executable
chmod +x setup_multi_instance_mapping.py
chmod +x test_haddns_ubuntu.py

# Stop existing services
docker compose down
```

### Step 2: Create Peer Mappings
```bash
# Create peer mappings from database
python3 setup_multi_instance_mapping.py

# Verify mappings were created
ls -la /etc/wireguard/peer_hostnames*.json
cat /etc/wireguard/peer_hostnames.json
```

### Step 3: Deploy HADDNS
```bash
# Build new containers
docker compose build wireguard-dns-cron

# Start all services
docker compose up -d

# Check container status
docker ps
```

### Step 4: Verify Deployment
```bash
# Run comprehensive tests
python3 test_haddns_ubuntu.py

# Check HADDNS logs
docker logs -f wireguard-dns-cron

# Monitor hosts file
watch -n 5 'cat ./shared_hosts/hosts'
```

## Testing Scenarios

### 1. Basic Functionality Test
```bash
# Test HADDNS script manually
docker exec wireguard-dns-cron python3 /app/haddns_multi.py

# Check generated hosts file
cat ./shared_hosts/hosts

# Verify DNS resolution
docker exec wireguard-webadmin nslookup testclient1.vpn.local 127.0.0.1
```

### 2. Multi-Instance Test
```bash
# Check all WireGuard interfaces
docker exec wireguard-webadmin wg show interfaces

# Test each interface
docker exec wireguard-webadmin wg show wg0 latest-handshakes
docker exec wireguard-webadmin wg show wg1 latest-handshakes

# Verify instance-specific hostnames
docker exec wireguard-webadmin nslookup client1.wg0.local 127.0.0.1
docker exec wireguard-webadmin nslookup server1.wg1.local 127.0.0.1
```

### 3. Handshake Monitoring Test
```bash
# Connect a VPN client
# Wait for handshake to appear
docker exec wireguard-webadmin wg show wg0 latest-handshakes

# Check if peer appears in hosts file
grep "client1" ./shared_hosts/hosts

# Test DNS resolution from client
nslookup client1.wg0.local <server-ip>
```

### 4. Cron Job Test
```bash
# Wait 2 minutes for automatic execution
sleep 120

# Check HADDNS logs for automatic runs
docker exec wireguard-dns-cron tail -20 /var/log/haddns.log

# Verify hosts file was updated
ls -la ./shared_hosts/hosts
```

## Troubleshooting

### Common Issues

#### 1. HADDNS Script Fails
```bash
# Check container logs
docker logs wireguard-dns-cron

# Test manual execution
docker exec wireguard-dns-cron python3 /app/haddns_multi.py

# Check WireGuard interface access
docker exec wireguard-dns-cron wg show wg0
```

#### 2. DNS Resolution Fails
```bash
# Check dnsmasq status
docker logs wireguard-dnsmasq

# Verify hosts file exists
cat ./shared_hosts/hosts

# Test DNS from container
docker exec wireguard-webadmin nslookup google.com 127.0.0.1
```

#### 3. Peer Mappings Missing
```bash
# Recreate mappings
python3 setup_multi_instance_mapping.py

# Check file permissions
ls -la /etc/wireguard/peer_hostnames*.json

# Verify JSON format
python3 -c "import json; print(json.load(open('/etc/wireguard/peer_hostnames.json')))"
```

#### 4. Container Networking Issues
```bash
# Check container network mode
docker inspect wireguard-dns-cron --format='{{.HostConfig.NetworkMode}}'

# Test container connectivity
docker exec wireguard-dns-cron ping wireguard-webadmin

# Restart containers
docker compose restart wireguard-dns-cron
```

## Monitoring Commands

### Real-time Monitoring
```bash
# Monitor HADDNS logs
docker logs -f wireguard-dns-cron

# Monitor hosts file changes
watch -n 5 'cat ./shared_hosts/hosts'

# Monitor WireGuard handshakes
watch -n 10 'docker exec wireguard-webadmin wg show wg0 latest-handshakes'
```

### Health Checks
```bash
# Check all containers
docker ps --format "table {{.Names}}\t{{.Status}}"

# Check system resources
htop

# Check disk usage
df -h

# Check network connectivity
ping 8.8.8.8
```

## Performance Optimization

### 1. Cron Schedule Tuning
Edit `dns_cron/Dockerfile` to adjust frequency:
```dockerfile
# Every 30 seconds (high frequency)
RUN echo "*/30 * * * * * /usr/bin/python3 /app/haddns_multi.py >> /var/log/haddns.log 2>&1" > /etc/cron.d/haddns

# Every 2 minutes (low frequency)
RUN echo "*/2 * * * * /usr/bin/python3 /app/haddns_multi.py >> /var/log/haddns.log 2>&1" > /etc/cron.d/haddns
```

### 2. Handshake TTL Tuning
Edit `dns_cron/haddns_multi.py`:
```python
HANDSHAKE_TTL = 600  # 10 minutes instead of 5
```

### 3. Log Rotation
Add log rotation to prevent disk space issues:
```bash
# Add to crontab
echo "0 0 * * * docker exec wireguard-dns-cron truncate -s 0 /var/log/haddns.log" | crontab -
```

## Security Considerations

### 1. File Permissions
```bash
# Secure peer mapping files
chmod 600 /etc/wireguard/peer_hostnames*.json
chown root:root /etc/wireguard/peer_hostnames*.json

# Secure hosts file
chmod 644 ./shared_hosts/hosts
chown root:root ./shared_hosts/hosts
```

### 2. Container Security
```bash
# Check container capabilities
docker inspect wireguard-dns-cron --format='{{.HostConfig.CapAdd}}'

# Verify no privileged mode
docker inspect wireguard-dns-cron --format='{{.HostConfig.Privileged}}'
```

### 3. Network Security
```bash
# Check firewall rules
ufw status

# Verify only necessary ports are open
netstat -tlnp | grep -E ':(8000|51820|53)'
```

## Success Criteria

### ✅ Deployment Successful When:
- [ ] All containers are running without errors
- [ ] HADDNS script executes successfully
- [ ] Peer mappings are loaded correctly
- [ ] Hosts file is generated and updated
- [ ] DNS resolution works for active peers
- [ ] Cron job runs automatically
- [ ] Multi-instance support works
- [ ] No critical errors in logs

### ✅ Production Ready When:
- [ ] All tests pass
- [ ] Performance is acceptable
- [ ] Security measures are in place
- [ ] Monitoring is configured
- [ ] Backup procedures are established
- [ ] Documentation is complete

## Rollback Plan

If issues occur:
```bash
# Stop HADDNS services
docker compose down wireguard-dns-cron wireguard-dnsmasq

# Restore original configuration
git checkout HEAD -- dns_cron/Dockerfile docker-compose.yml

# Restart original services
docker compose up -d

# Verify rollback
docker ps
```

## Support and Maintenance

### Daily Monitoring
- Check container health: `docker ps`
- Monitor HADDNS logs: `docker logs wireguard-dns-cron`
- Verify DNS resolution: `nslookup <hostname> <server-ip>`

### Weekly Maintenance
- Review HADDNS logs for errors
- Check disk space usage
- Verify peer mappings are current
- Test DNS resolution from clients

### Monthly Maintenance
- Update system packages
- Review and rotate logs
- Test disaster recovery procedures
- Update documentation
