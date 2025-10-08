# mDNS-Based WireGuard Peer Discovery Setup

This guide explains how to set up mDNS (multicast DNS) for automatic peer discovery in your WireGuard WebAdmin instance.

## Overview

mDNS provides automatic peer discovery without requiring a centralized DNS server. Peers can discover and resolve each other by hostname using the `.local` domain.

### Benefits of mDNS over dnsmasq:
- ✅ **Zero Configuration**: Peers automatically discover each other
- ✅ **No Centralized Server**: Eliminates single point of failure  
- ✅ **Instance-Specific Scoping**: Each instance gets its own `.local` domain
- ✅ **Cross-Platform**: Works on Windows, macOS, Linux, mobile devices
- ✅ **Real-time Discovery**: Peers appear/disappear as they connect/disconnect
- ✅ **No Port Conflicts**: Uses standard mDNS port 5353

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WireGuard     │    │   Avahi mDNS     │    │   Per-instance  │
│   Peers         │───▶│   Container      │───▶│   Hosts Files   │
│   (.local)      │    │   (Port 5353)    │    │   (wg*.hosts)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Hostname Formats

For a peer named `laptop` in instance `wg0`:

| Format | Example | Description |
|--------|---------|-------------|
| Global | `laptop.wg.local` | Resolves to peer in any instance |
| Instance-specific | `laptop.wg0.local` | Resolves to peer in specific instance |
| Short | `laptop` | Resolves to peer in same instance |
| UUID-based | `peer-{uuid}` | Resolves using peer UUID |

## Setup Instructions

### 1. Add mDNS to Docker Compose

Add the mDNS service to your `docker-compose.yml`:

```yaml
services:
  # ... existing services ...
  
  # mDNS daemon for peer discovery
  wireguard-mdns:
    container_name: wireguard-mdns
    image: avahi/avahi:latest
    restart: unless-stopped
    network_mode: host
    environment:
      - AVAHI_DAEMON_DETECT_LOCAL=0
      - AVAHI_DAEMON_DISABLE_USER_SERVICE_PACKETS=0
    volumes:
      - ./mdns_config:/etc/avahi
      - ./mdns_hosts:/etc/avahi/hosts
    command: ["avahi-daemon", "--no-drop-root", "--debug"]
    depends_on:
      - wireguard-webadmin
```

### 2. Add mDNS App to Django

Add `'mdns'` to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'mdns',
]
```

### 3. Start mDNS Service

```bash
# Start the mDNS container
docker-compose up -d wireguard-mdns

# Check if it's running
docker ps | grep mdns
```

### 4. Update Peer Configuration

The system will automatically:
- Generate mDNS host files for each instance
- Update peer configurations to use mDNS
- Reload mDNS when peers are added/removed

## Usage

### For Users

1. **Connect to VPN**: Use your normal WireGuard configuration
2. **Discover Peers**: Peers are automatically discoverable by hostname
3. **Resolve Names**: Use `ping laptop.wg0.local` or `nslookup laptop`

### For Administrators

```bash
# Update mDNS configuration manually
python manage.py update_peer_mdns --reload

# Check mDNS status
docker logs wireguard-mdns

# Test peer discovery
nslookup peer-name.wg0.local
```

## Testing

### Test mDNS Resolution

```bash
# From a connected peer
ping laptop.wg0.local
nslookup laptop.wg0.local
avahi-resolve-host-name laptop.wg0.local
```

### Test Cross-Instance Discovery

```bash
# From wg0 peer, discover wg1 peer
ping server.wg1.local
nslookup server.wg1.local
```

## Troubleshooting

### Common Issues

1. **Peers not discoverable**:
   - Check if mDNS container is running: `docker ps | grep mdns`
   - Check mDNS logs: `docker logs wireguard-mdns`
   - Verify hosts files: `docker exec wireguard-mdns ls -la /etc/avahi/hosts/`

2. **DNS resolution fails**:
   - Ensure peer DNS is set to `127.0.0.1, 8.8.8.8`
   - Check if `.local` domains are being resolved locally

3. **Cross-platform issues**:
   - Windows: May need Bonjour Print Services
   - Linux: Install `avahi-daemon` and `avahi-utils`
   - macOS: Built-in mDNS support

### Debug Commands

```bash
# Check mDNS services
docker exec wireguard-mdns avahi-browse -a

# Test specific hostname
docker exec wireguard-mdns avahi-resolve-host-name laptop.wg0.local

# Check hosts files
docker exec wireguard-mdns cat /etc/avahi/hosts/wg0.hosts
```

## Migration from dnsmasq

If you're migrating from the dnsmasq setup:

1. **Stop dnsmasq container**: `docker-compose stop wireguard-webadmin-dns`
2. **Remove dnsmasq service** from `docker-compose.yml`
3. **Update DNS configuration** in `wgwadmlibrary/dns_utils.py`
4. **Start mDNS service**: `docker-compose up -d wireguard-mdns`
5. **Test peer discovery**: Verify peers can resolve each other

## Advanced Configuration

### Custom Domains

Edit `mdns/functions.py` to customize domain naming:

```python
# Change from wg0.local to custom.domain.local
domain = f"instance-{instance_id}.custom.local"
```

### Service Discovery

Add custom services to be advertised:

```python
# In mdns/functions.py
def advertise_wireguard_service(peer, instance):
    # Advertise WireGuard service for this peer
    service_name = f"wireguard-{peer.hostname}"
    # Implementation for service advertisement
```

## Security Considerations

- mDNS is designed for local networks and is generally safe
- `.local` domains are not routable on the internet
- Consider firewall rules if needed for mDNS traffic (port 5353)
- Peer hostnames should not contain sensitive information

## Performance

- mDNS adds minimal overhead
- Hostname resolution is typically < 1ms
- No centralized server means no bottleneck
- Automatic cleanup when peers disconnect
