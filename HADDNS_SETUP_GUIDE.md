# HADDNS Setup Guide

## Overview
HADDNS (Handshake-Aware Dynamic DNS) automatically updates DNS records based on WireGuard peer handshake activity. Only active peers (with recent handshakes) will be resolvable via DNS.

## Components

### 1. wireguard-dns-cron
- Monitors WireGuard handshakes every minute
- Updates `/shared_hosts/hosts` file with active peers
- Uses `haddns.py` script for handshake monitoring

### 2. wireguard-dnsmasq  
- Provides DNS service for VPN clients
- Reads from `/shared_hosts/hosts` file
- Serves `.vpn.local` domain

### 3. shared_hosts/hosts
- Dynamic hosts file updated by HADDNS
- Contains only active peer records

## Setup Steps

### Step 1: Create Peer Mapping
The HADDNS system needs a mapping file that connects WireGuard public keys to hostnames and IP addresses.

```bash
# Run the setup script to create mapping from your database
python setup_haddns_mapping.py

# Or create a manual mapping file
python setup_haddns_mapping.py --example
```

### Step 2: Manual Mapping (if needed)
If the automatic setup doesn't work, create `/etc/wireguard/peer_hostnames.json` manually:

```json
{
  "AbCd1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab=": {
    "hostname": "client1.vpn.local",
    "ip": "10.0.0.2"
  },
  "EfGh4567890abcdef1234567890abcdef1234567890abcdef1234567890cd=": {
    "hostname": "client2.vpn.local",
    "ip": "10.0.0.3"
  }
}
```

### Step 3: Rebuild and Start Services
```bash
# Rebuild the dns-cron container
docker compose build wireguard-dns-cron

# Start all services
docker compose up -d

# Check logs
docker logs -f wireguard-dns-cron
```

### Step 4: Configure Client DNS
Add these lines to your WireGuard client configs:

```ini
[Interface]
DNS = 10.0.0.1
PostUp = resolvectl dns %i 10.0.0.1; resolvectl domain %i ~vpn.local
PersistentKeepalive = 25
```

## Testing

### Check HADDNS Logs
```bash
# View real-time logs
docker logs -f wireguard-dns-cron

# Check hosts file
cat ./shared_hosts/hosts
```

### Test DNS Resolution
From a VPN client:
```bash
# Test DNS resolution
nslookup client1.vpn.local 10.0.0.1

# Test connectivity
ping client1.vpn.local
```

### Verify Handshake Monitoring
```bash
# Check WireGuard handshakes
docker exec wireguard-webadmin wg show wg0 latest-handshakes

# Check active peers in hosts file
grep -v "^#" ./shared_hosts/hosts
```

## Configuration

### Handshake TTL
Default: 300 seconds (5 minutes)
To change, edit `HANDSHAKE_TTL` in `dns_cron/haddns.py`

### Cron Schedule
Default: Every minute
To change, edit the cron expression in `dns_cron/Dockerfile`

### DNS Domain
Default: `vpn.local`
To change, edit the `--domain` parameter in docker-compose.yml

## Troubleshooting

### No DNS Resolution
1. Check if dnsmasq is running: `docker ps | grep dnsmasq`
2. Verify hosts file has entries: `cat ./shared_hosts/hosts`
3. Check dnsmasq logs: `docker logs wireguard-dnsmasq`

### No Handshake Updates
1. Check HADDNS logs: `docker logs wireguard-dns-cron`
2. Verify peer mapping file exists: `ls -la /etc/wireguard/peer_hostnames.json`
3. Check WireGuard interface: `docker exec wireguard-webadmin wg show wg0`

### Mapping File Issues
1. Verify JSON format: `python -m json.tool /etc/wireguard/peer_hostnames.json`
2. Check file permissions: `ls -la /etc/wireguard/peer_hostnames.json`
3. Ensure public keys match exactly (including padding)

## File Locations

- **Peer Mapping**: `/etc/wireguard/peer_hostnames.json`
- **Hosts File**: `./shared_hosts/hosts`
- **HADDNS Script**: `dns_cron/haddns.py`
- **HADDNS Logs**: `/var/log/haddns.log` (inside container)

## Security Notes

- The hosts file is automatically generated - do not edit manually
- Only peers with recent handshakes are included in DNS
- DNS queries are only served to VPN clients
- Peer mapping file should be kept secure as it contains network topology
