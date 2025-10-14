# HADDNS Multi-Instance Setup Guide

## Overview
HADDNS Multi-Instance extends the handshake-aware DNS system to monitor **all WireGuard instances** (wg0, wg1, wg2, etc.) and provide dynamic DNS resolution across your entire VPN infrastructure.

## How It Works

### 🔍 **Interface Discovery**
- Automatically discovers all WireGuard interfaces (`wg0`, `wg1`, `wg2`, etc.)
- Monitors handshakes across all instances simultaneously
- Consolidates peer data from multiple interfaces

### 📊 **Peer Mapping Structure**
Each WireGuard instance gets its own mapping file:
```
/etc/wireguard/peer_hostnames_wg0.json  # Instance 0 peers
/etc/wireguard/peer_hostnames_wg1.json  # Instance 1 peers  
/etc/wireguard/peer_hostnames_wg2.json  # Instance 2 peers
/etc/wireguard/peer_hostnames.json      # Combined mapping
```

### 🌐 **Hostname Resolution**
Peers are resolvable with instance-specific hostnames:
- `client1.wg0.local` - Client1 in instance wg0
- `server1.wg1.local` - Server1 in instance wg1
- `laptop.wg2.local` - Laptop in instance wg2

## Setup Steps

### Step 1: Create Multi-Instance Peer Mappings
```bash
# Create mappings from your database
python setup_multi_instance_mapping.py

# Or create example files for manual setup
python setup_multi_instance_mapping.py --example
```

### Step 2: Update Docker Configuration
The system is already configured to use `haddns_multi.py` in the Dockerfile.

### Step 3: Rebuild and Deploy
```bash
# Rebuild the container
docker compose build wireguard-dns-cron

# Start the service
docker compose up -d wireguard-dns-cron

# Check logs
docker logs -f wireguard-dns-cron
```

## Configuration Files

### Peer Mapping Format
```json
{
  "AbCd123...": {
    "hostname": "client1.wg0.local",
    "ip": "10.0.0.2",
    "instance": "wg0",
    "original_hostname": "client1"
  },
  "EfGh456...": {
    "hostname": "server1.wg1.local", 
    "ip": "10.1.0.2",
    "instance": "wg1",
    "original_hostname": "server1"
  }
}
```

### Generated Hosts File
```
# WireGuard HADDNS Multi-Instance - Handshake-Aware Dynamic DNS
# Generated automatically - do not edit manually
# Last updated: 2025-10-14 18:30:00
# Active peers: 5

10.0.0.2    client1.wg0.local
10.0.0.3    client2.wg0.local
10.1.0.2    server1.wg1.local
10.2.0.2    laptop.wg2.local
10.2.0.3    phone.wg2.local
```

## Testing Multi-Instance Setup

### Test Interface Discovery
```bash
# Check discovered interfaces
docker exec wireguard-dns-cron python3 -c "
import subprocess
output = subprocess.check_output(['wg', 'show', 'interfaces']).decode()
print('Interfaces:', output.strip().split())
"
```

### Test Peer Mappings
```bash
# Check mapping files
docker exec wireguard-webadmin ls -la /etc/wireguard/peer_hostnames*.json

# View combined mapping
docker exec wireguard-webadmin cat /etc/wireguard/peer_hostnames.json
```

### Test Handshake Monitoring
```bash
# Check handshakes from all interfaces
docker exec wireguard-webadmin wg show wg0 latest-handshakes
docker exec wireguard-webadmin wg show wg1 latest-handshakes
docker exec wireguard-webadmin wg show wg2 latest-handshakes
```

### Test DNS Resolution
```bash
# Test resolution from VPN clients
nslookup client1.wg0.local 10.0.0.1
nslookup server1.wg1.local 10.0.0.1
nslookup laptop.wg2.local 10.0.0.1
```

## Client Configuration

### WireGuard Client Config
Each client should include instance-specific DNS configuration:

```ini
[Interface]
PrivateKey = <client-private-key>
Address = 10.0.0.2/24
DNS = 10.0.0.1
PostUp = resolvectl dns %i 10.0.0.1; resolvectl domain %i ~wg0.local
PersistentKeepalive = 25

[Peer]
PublicKey = <server-public-key>
Endpoint = your-server.com:51820
AllowedIPs = 0.0.0.0/0
```

## Monitoring and Troubleshooting

### Check HADDNS Logs
```bash
# View real-time logs
docker logs -f wireguard-dns-cron

# Check specific log entries
docker exec wireguard-dns-cron tail -f /var/log/haddns.log
```

### Verify Interface Discovery
```bash
# Manual interface discovery test
docker exec wireguard-dns-cron python3 /app/haddns_multi.py
```

### Check Active Peers
```bash
# View current active peers
cat ./shared_hosts/hosts

# Count active peers
grep -v "^#" ./shared_hosts/hosts | wc -l
```

## Advanced Configuration

### Custom Handshake TTL
Edit `HANDSHAKE_TTL` in `dns_cron/haddns_multi.py`:
```python
HANDSHAKE_TTL = 600  # 10 minutes instead of 5
```

### Instance-Specific Domains
Modify the hostname generation in `setup_multi_instance_mapping.py`:
```python
hostname = f"{peer['hostname']}.{instance_name}.vpn"  # .vpn instead of .local
```

### Custom Cron Schedule
Edit the cron expression in `dns_cron/Dockerfile`:
```dockerfile
RUN echo "*/2 * * * * /usr/bin/python3 /app/haddns_multi.py >> /var/log/haddns.log 2>&1" > /etc/cron.d/haddns
```

## Benefits of Multi-Instance HADDNS

### ✅ **Scalability**
- Supports unlimited WireGuard instances
- Automatic interface discovery
- Centralized DNS management

### ✅ **Isolation**
- Instance-specific hostnames
- Separate peer mappings per instance
- Clear network segmentation

### ✅ **Efficiency**
- Single monitoring process
- Consolidated hosts file
- Reduced resource usage

### ✅ **Flexibility**
- Mix of active/inactive instances
- Dynamic peer management
- Easy instance addition/removal

## File Locations

- **Multi-Instance Script**: `dns_cron/haddns_multi.py`
- **Setup Script**: `setup_multi_instance_mapping.py`
- **Instance Mappings**: `/etc/wireguard/peer_hostnames_wg*.json`
- **Combined Mapping**: `/etc/wireguard/peer_hostnames.json`
- **Generated Hosts**: `./shared_hosts/hosts`
- **HADDNS Logs**: `/var/log/haddns.log` (inside container)

## Migration from Single-Instance

If you're upgrading from single-instance HADDNS:

1. **Backup existing configuration**:
   ```bash
   cp ./shared_hosts/hosts ./shared_hosts/hosts.backup
   ```

2. **Update to multi-instance**:
   ```bash
   docker compose build wireguard-dns-cron
   docker compose up -d wireguard-dns-cron
   ```

3. **Verify functionality**:
   ```bash
   docker logs -f wireguard-dns-cron
   ```

The multi-instance version is backward compatible and will work with your existing single-instance setup while adding support for additional instances.
