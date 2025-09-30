# CoreDNS Integration for WireGuard WebAdmin

This directory contains the CoreDNS configuration and integration for centralized DNS resolution in your WireGuard network.

## Overview

CoreDNS provides a centralized DNS server with multiple zones for peer name resolution:

- **peers.wg.local** - Resolves peer hostnames to their assigned IP addresses
- **instances.wg.local** - Resolves WireGuard instance hostnames
- **External DNS** - Forwards queries to upstream DNS servers (Cloudflare, Google)

## Features

- ✅ **Automatic Zone Updates** - Zones are updated automatically when peers are created/modified
- ✅ **Multiple Zones** - Separate zones for peers and instances
- ✅ **Web Management** - Web interface to manage and monitor CoreDNS
- ✅ **API Integration** - REST API for programmatic zone updates
- ✅ **Health Monitoring** - Built-in health checks and metrics
- ✅ **Caching** - DNS response caching for better performance

## Configuration Files

- `Corefile` - Main CoreDNS configuration
- `zones/peers.db` - Zone file for peer hostnames (auto-generated)
- `zones/instances.db` - Zone file for instance hostnames (auto-generated)

## Usage

### Starting CoreDNS

CoreDNS is automatically started with Docker Compose:

```bash
docker-compose up -d coredns
```

### Managing Zones

#### Via Web Interface
1. Navigate to `/dns/coredns/` in your web admin
2. Use the zone management buttons to update zones
3. Monitor zone status and health

#### Via API
```bash
# Update all zones
curl -X POST http://localhost:8000/dns/api/update-zones/ \
  -H "Content-Type: application/json" \
  -d '{"zone": "all"}'

# Update only peers zone
curl -X POST http://localhost:8000/dns/api/update-zones/ \
  -H "Content-Type: application/json" \
  -d '{"zone": "peers"}'
```

#### Via Management Command
```bash
# Update all zones
python manage.py update_coredns_zones

# Update specific zone
python manage.py update_coredns_zones --zone peers
python manage.py update_coredns_zones --zone instances

# Dry run (show what would be updated)
python manage.py update_coredns_zones --dry-run
```

### Client Configuration

Configure your WireGuard clients to use CoreDNS:

```ini
[Interface]
PrivateKey = YOUR_PRIVATE_KEY
Address = 10.188.0.2/24
DNS = YOUR_SERVER_IP:5354  # CoreDNS server IP and port

[Peer]
PublicKey = SERVER_PUBLIC_KEY
Endpoint = YOUR_SERVER_IP:51820
AllowedIPs = 0.0.0.0/0
```

## Testing

### Test DNS Resolution

```bash
# Test peer resolution
dig @YOUR_SERVER_IP -p 5354 phone.wg.local
dig @YOUR_SERVER_IP -p 5354 laptop.wg.local

# Test instance resolution
dig @YOUR_SERVER_IP -p 5354 wg1.instances.wg.local

# Test external resolution
dig @YOUR_SERVER_IP -p 5354 google.com
```

### Test Script

Run the included test script:

```bash
python containers/coredns/test_dns.py
```

## Monitoring

### Health Check
- **Endpoint**: `http://YOUR_SERVER_IP:8080/health`
- **Status**: Returns 200 OK if CoreDNS is healthy

### Metrics
- **Endpoint**: `http://YOUR_SERVER_IP:9153/metrics`
- **Format**: Prometheus metrics

### Logs
```bash
# View CoreDNS logs
docker logs wireguard-coredns

# Follow logs
docker logs -f wireguard-coredns
```

## Zone File Format

### Peers Zone (peers.wg.local)
```
phone.wg.local.    IN  A   10.188.0.2
laptop.wg.local.   IN  A   10.188.0.3
server.wg.local.   IN  A   10.188.0.4
```

### Instances Zone (instances.wg.local)
```
wg1.instances.wg.local.    IN  A   10.188.0.1
wg2.instances.wg.local.    IN  A   10.189.0.1
```

## Troubleshooting

### Common Issues

1. **CoreDNS not starting**
   - Check Docker logs: `docker logs wireguard-coredns`
   - Verify Corefile syntax
   - Check port 53 availability

2. **Zones not updating**
   - Check Django logs for signal errors
   - Manually run: `python manage.py update_coredns_zones`
   - Verify file permissions

3. **DNS resolution not working**
   - Verify client DNS configuration
   - Test with dig/nslookup
   - Check CoreDNS logs

### Debug Commands

```bash
# Check CoreDNS status
docker ps | grep coredns

# Test zone files
cat containers/coredns/zones/peers.db
cat containers/coredns/zones/instances.db

# Check CoreDNS configuration
docker exec wireguard-coredns cat /etc/coredns/Corefile
```

## Security Considerations

- CoreDNS is exposed on port 5354 (UDP/TCP) to avoid conflicts with system DNS
- Consider firewall rules to restrict access
- Monitor DNS queries for suspicious activity
- Regular updates of CoreDNS image

## Performance

- DNS responses are cached for better performance
- Zone files are auto-reloaded every 1 second
- Upstream DNS uses round-robin load balancing
- Health checks ensure upstream availability
