# HADDNS Ubuntu Testing Guide

## 🚀 Complete Testing Strategy for Ubuntu Deployment

### **Phase 1: Pre-Deployment Testing (Local)**

Before pushing to Ubuntu, verify everything works locally:

```bash
# 1. Test multi-instance HADDNS locally
docker exec wireguard-dns-cron python3 /app/haddns_multi.py

# 2. Verify hosts file generation
cat ./shared_hosts/hosts

# 3. Check all containers are healthy
docker ps
```

### **Phase 2: Ubuntu Server Preparation**

#### 1. **System Requirements Check**
```bash
# Check Ubuntu version
lsb_release -a

# Check Docker installation
docker --version
docker compose version

# Check WireGuard tools
wg --version

# Check system resources
free -h
df -h
```

#### 2. **File Transfer to Ubuntu**
```bash
# Copy all modified files to Ubuntu server
scp -r dns_cron/ user@ubuntu-server:/path/to/wireguard_webadmin/
scp docker-compose.yml user@ubuntu-server:/path/to/wireguard_webadmin/
scp setup_multi_instance_mapping.py user@ubuntu-server:/path/to/wireguard_webadmin/
scp test_haddns_ubuntu.py user@ubuntu-server:/path/to/wireguard_webadmin/
scp quick_ubuntu_test.sh user@ubuntu-server:/path/to/wireguard_webadmin/
scp HADDNS_MULTI_INSTANCE_GUIDE.md user@ubuntu-server:/path/to/wireguard_webadmin/
```

### **Phase 3: Ubuntu Deployment Testing**

#### **Step 1: Quick Health Check**
```bash
# Make scripts executable
chmod +x quick_ubuntu_test.sh
chmod +x setup_multi_instance_mapping.py
chmod +x test_haddns_ubuntu.py

# Run quick test
./quick_ubuntu_test.sh
```

#### **Step 2: Comprehensive Testing**
```bash
# Run full test suite
python3 test_haddns_ubuntu.py
```

#### **Step 3: Manual Verification**

##### **A. Container Health**
```bash
# Check all containers are running
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check container logs
docker logs --tail 20 wireguard-webadmin
docker logs --tail 20 wireguard-dns-cron
docker logs --tail 20 wireguard-dnsmasq
```

##### **B. WireGuard Interface Testing**
```bash
# List all WireGuard interfaces
wg show interfaces

# Check each interface
wg show wg0
wg show wg1  # if exists
wg show wg2  # if exists

# Check handshakes
wg show wg0 latest-handshakes
```

##### **C. Peer Mapping Testing**
```bash
# Check mapping files exist
ls -la /etc/wireguard/peer_hostnames*.json

# Validate JSON format
python3 -c "import json; print(json.load(open('/etc/wireguard/peer_hostnames.json')))"

# Check instance-specific mappings
find /etc/wireguard/ -name "peer_hostnames_wg*.json" -exec echo "File: {}" \; -exec python3 -c "import json; print(json.load(open('{}')))" \;
```

##### **D. HADDNS Execution Testing**
```bash
# Test manual execution
docker exec wireguard-dns-cron python3 /app/haddns_multi.py

# Check generated hosts file
cat ./shared_hosts/hosts

# Check HADDNS logs
docker exec wireguard-dns-cron cat /var/log/haddns.log
```

##### **E. DNS Resolution Testing**
```bash
# Test basic DNS
docker exec wireguard-webadmin nslookup google.com 127.0.0.1

# Test local DNS (if peers exist)
docker exec wireguard-webadmin nslookup testclient1.vpn.local 127.0.0.1
docker exec wireguard-webadmin nslookup client1.wg0.local 127.0.0.1
```

##### **F. Cron Job Testing**
```bash
# Check cron configuration
docker exec wireguard-dns-cron cat /etc/cron.d/haddns

# Check cron process
docker exec wireguard-dns-cron ps aux | grep cron

# Wait and check automatic execution
sleep 70
docker exec wireguard-dns-cron tail -20 /var/log/haddns.log
```

### **Phase 4: Real-World Testing**

#### **Test 1: VPN Client Connection**
```bash
# 1. Connect a VPN client to your server
# 2. Wait for handshake to appear
wg show wg0 latest-handshakes

# 3. Check if peer appears in hosts file
grep "client-hostname" ./shared_hosts/hosts

# 4. Test DNS resolution from client
nslookup client-hostname.wg0.local <server-ip>
```

#### **Test 2: Multi-Instance Testing**
```bash
# If you have multiple WireGuard instances:
# 1. Connect clients to different instances
# 2. Verify instance-specific hostnames work
nslookup client1.wg0.local <server-ip>
nslookup server1.wg1.local <server-ip>
nslookup laptop.wg2.local <server-ip>
```

#### **Test 3: Handshake Monitoring**
```bash
# 1. Connect a client
# 2. Monitor handshake activity
watch -n 5 'wg show wg0 latest-handshakes'

# 3. Check HADDNS updates
watch -n 10 'cat ./shared_hosts/hosts'

# 4. Disconnect client and verify it disappears from DNS
```

### **Phase 5: Performance and Monitoring**

#### **Performance Testing**
```bash
# Monitor system resources
htop

# Check container resource usage
docker stats

# Monitor disk usage
df -h

# Check network connectivity
ping 8.8.8.8
```

#### **Log Monitoring**
```bash
# Real-time HADDNS monitoring
docker logs -f wireguard-dns-cron

# Monitor hosts file changes
watch -n 5 'cat ./shared_hosts/hosts'

# Check system logs
journalctl -f
```

### **Phase 6: Troubleshooting Common Issues**

#### **Issue 1: HADDNS Script Fails**
```bash
# Check container logs
docker logs wireguard-dns-cron

# Test manual execution
docker exec wireguard-dns-cron python3 /app/haddns_multi.py

# Check WireGuard interface access
docker exec wireguard-dns-cron wg show wg0
```

#### **Issue 2: DNS Resolution Fails**
```bash
# Check dnsmasq status
docker logs wireguard-dnsmasq

# Verify hosts file exists and has content
cat ./shared_hosts/hosts

# Test DNS from container
docker exec wireguard-webadmin nslookup google.com 127.0.0.1
```

#### **Issue 3: Peer Mappings Missing**
```bash
# Recreate mappings
python3 setup_multi_instance_mapping.py

# Check file permissions
ls -la /etc/wireguard/peer_hostnames*.json

# Verify JSON format
python3 -c "import json; print(json.load(open('/etc/wireguard/peer_hostnames.json')))"
```

#### **Issue 4: Container Networking Issues**
```bash
# Check container network mode
docker inspect wireguard-dns-cron --format='{{.HostConfig.NetworkMode}}'

# Test container connectivity
docker exec wireguard-dns-cron ping wireguard-webadmin

# Restart containers
docker compose restart wireguard-dns-cron
```

### **Phase 7: Production Readiness Checklist**

#### **✅ System Health**
- [ ] All containers running without errors
- [ ] No critical errors in logs
- [ ] System resources within acceptable limits
- [ ] Network connectivity working

#### **✅ HADDNS Functionality**
- [ ] Script executes successfully
- [ ] Peer mappings loaded correctly
- [ ] Hosts file generated and updated
- [ ] Handshake monitoring working
- [ ] Multi-instance support working

#### **✅ DNS Resolution**
- [ ] Basic DNS resolution works
- [ ] Local DNS resolution works
- [ ] Instance-specific hostnames work
- [ ] Only active peers are resolvable

#### **✅ Automation**
- [ ] Cron job configured and running
- [ ] Automatic updates working
- [ ] Log rotation configured
- [ ] Monitoring in place

#### **✅ Security**
- [ ] File permissions correct
- [ ] Container security configured
- [ ] Network security in place
- [ ] No sensitive data exposed

### **Phase 8: Go-Live Testing**

#### **Final Verification**
```bash
# 1. Run complete test suite
python3 test_haddns_ubuntu.py

# 2. Test with real VPN clients
# 3. Verify DNS resolution from clients
# 4. Monitor for 24 hours
# 5. Check logs for any issues
```

#### **Monitoring Commands**
```bash
# Real-time monitoring
docker logs -f wireguard-dns-cron

# System monitoring
htop
df -h
free -h

# Network monitoring
netstat -tlnp | grep -E ':(8000|51820|53)'
```

## 🎯 Success Criteria

### **Deployment Successful When:**
- ✅ All tests pass
- ✅ HADDNS script works
- ✅ DNS resolution works
- ✅ Multi-instance support works
- ✅ No critical errors
- ✅ Performance acceptable

### **Production Ready When:**
- ✅ All functionality tested
- ✅ Real clients can connect
- ✅ DNS resolution works from clients
- ✅ Monitoring configured
- ✅ Backup procedures in place
- ✅ Documentation complete

## 🚨 Rollback Plan

If issues occur during testing:
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

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review container logs
3. Run the test scripts
4. Check the HADDNS_MULTI_INSTANCE_GUIDE.md
5. Verify system requirements

The testing process ensures your HADDNS deployment is robust, secure, and ready for production use! 🚀
