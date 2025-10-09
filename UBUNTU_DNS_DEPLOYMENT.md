# Ubuntu DNS Solution Deployment Guide

## 🚀 Quick Deployment Steps

### 1. Pull Latest Changes
```bash
cd /localwg/wireguard_webadmin
git pull origin main
```

### 2. Stop Current Containers
```bash
docker-compose down
```

### 3. Rebuild and Start with DNS Solution
```bash
docker-compose up -d --build
```

### 4. Verify All Containers Are Running
```bash
docker ps
```
You should see:
- `wireguard-webadmin`
- `wireguard-webadmin-cron`
- `wireguard-webadmin-rrdtool`
- `wireguard-dns-cron` (NEW!)

## 🧪 Testing the DNS Solution

### Test 1: API Endpoints
```bash
# Test JSON API
curl http://localhost:8000/api/peers/hosts/

# Test legacy hosts file API
curl http://localhost:8000/api/peers/hosts/legacy/
```

### Test 2: DNS Cron Container
```bash
# Check DNS cron logs
docker logs wireguard-dns-cron

# Manually run DNS update
docker exec wireguard-dns-cron /usr/local/bin/update_peer_hosts.sh
```

### Test 3: Hostname Resolution
```bash
# Check if hostnames are in server's /etc/hosts
docker exec wireguard-webadmin cat /etc/hosts | grep -E "(laptop|myphone)"

# Test DNS resolution from server
docker exec wireguard-webadmin nslookup laptop
docker exec wireguard-webadmin nslookup myphone
```

## 🔍 Expected Results

### API Response (JSON):
```json
{
  "10.188.0.2": "laptop",
  "10.188.0.3": "myphone"
}
```

### API Response (Legacy):
```json
{
  "peer_count": 2,
  "hosts_content": "10.188.0.2 laptop\n10.188.0.3 myphone",
  "json_data": {"10.188.0.2": "laptop", "10.188.0.3": "myphone"}
}
```

### DNS Cron Logs:
```
[2025-10-09 17:33:03] Starting peer hostname update process
[2025-10-09 17:33:03] Fetching peer hostnames from: http://wireguard-webadmin:8000/api/peers/hosts/
[2025-10-09 17:33:03] Updated hosts file with 5 entries
[2025-10-09 17:33:03] Successfully updated peer hostnames
```

## 🎯 What This Enables

1. **Automatic DNS Updates**: Every 5 minutes, peer hostnames are updated
2. **Peer-to-Peer Resolution**: Peers can resolve each other by hostname
3. **Simple API**: Easy to integrate with other systems
4. **Clean Architecture**: No complex mDNS/Avahi setup

## 🔧 Troubleshooting

### If API returns 400/500 errors:
```bash
# Check Django logs
docker logs wireguard-webadmin --tail 20

# Check if containers can communicate
docker exec wireguard-dns-cron ping wireguard-webadmin
```

### If hostname resolution doesn't work:
```bash
# Check if /etc/hosts was updated
docker exec wireguard-webadmin cat /etc/hosts

# Manually trigger DNS update
docker exec wireguard-dns-cron /usr/local/bin/update_peer_hosts.sh
```

### If containers won't start:
```bash
# Check for port conflicts
netstat -tulpn | grep :8000

# Check Docker logs
docker-compose logs
```

## 📋 Next Steps

1. **Test with actual peer connections** - Connect a peer and test hostname resolution
2. **Monitor DNS updates** - Check that the cron job runs every 5 minutes
3. **Add more peers** - Test with additional peers and hostnames
4. **Optional: Set up dnsmasq** - For more advanced DNS features

## 🎉 Success Indicators

- ✅ All 4 containers running
- ✅ API endpoints returning JSON data
- ✅ DNS cron container updating /etc/hosts
- ✅ Peer hostnames resolvable from server
- ✅ No errors in container logs
