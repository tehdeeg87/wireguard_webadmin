# HADDNS Implementation: Handshake-Aware Dynamic DNS Resolution

This document describes the implementation of HADDNS (Handshake-Aware Dynamic DNS Resolution) for WireGuard WebAdmin, based on the whitepaper provided.

## Overview

HADDNS is a novel approach that leverages WireGuard's handshake mechanism to dynamically activate/deactivate DNS records based on peer "presence" (detected via recent handshakes). This makes DNS resolution presence-aware—hostnames only resolve if the peer is actively communicating.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WireGuard     │    │   HADDNS         │    │   dnsmasq       │
│   Handshakes    │───▶│   Monitor        │───▶│   Dynamic       │
│   (wg show)     │    │   (Cron Job)     │    │   Hosts File    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   DNS Records   │
                       │   (Active Only) │
                       └─────────────────┘
```

## Components Implemented

### 1. Database Models (`dns/models.py`)

#### HADDNSConfig
- Configuration for the HADDNS system
- Handshake threshold (default: 5 minutes)
- Domain suffix (default: vpn.local)
- Update interval settings

#### PeerHostnameMapping
- Maps WireGuard peers to their hostnames
- Tracks online/offline status
- Supports custom domains

### 2. Management Commands

#### `haddns_setup`
```bash
python manage.py haddns_setup --domain vpn.local --threshold 300
```
- Initializes HADDNS configuration
- Creates hostname mappings for existing peers

#### `haddns_update`
```bash
python manage.py haddns_update --dry-run --verbose
```
- Monitors WireGuard handshakes
- Updates DNS records based on peer presence
- Can be run manually or via cron

#### `generate_dnsmasq_config`
```bash
python manage.py generate_dnsmasq_config --output /etc/dnsmasq.d/wireguard_webadmin.conf
```
- Generates dnsmasq configuration including HADDNS dynamic hosts

### 3. Automatic Integration

#### Django Signals (`dns/signals.py`)
- Automatically creates hostname mappings when peers are added
- Cleans up mappings when peers are removed
- Updates mappings when peer hostnames change

#### Cron Integration (`cron/cron_tasks`)
```bash
# HADDNS (Handshake-Aware Dynamic DNS) - Update DNS records based on peer handshakes
*/1 * * * * root cd /app && python manage.py haddns_update >> /var/log/haddns.log 2>&1
```

### 4. Admin Interface

- **HADDNS Config**: Configure system settings
- **Peer Hostname Mappings**: View and manage peer hostname mappings
- Real-time status of peer online/offline state

## Key Features

### Presence-Aware DNS
- Only online peers (recent handshakes) resolve to their hostnames
- Offline peers can optionally resolve with `.offline` suffix
- Automatic cleanup of stale records

### Multiple Hostname Formats
For a peer named `laptop` in instance `wg0`:

| Format | Example | Description |
|--------|---------|-------------|
| Global | `laptop.vpn.local` | Resolves to peer in any instance |
| Instance-specific | `laptop.wg0.vpn.local` | Resolves to peer in specific instance |
| Offline | `laptop.offline.vpn.local` | Offline peer (if enabled) |

### Handshake Monitoring
- Uses `wg show all latest-handshakes` to detect peer activity
- Configurable threshold (default: 5 minutes)
- Updates every minute via cron

### Zero Client Overhead
- No additional software needed on clients
- Uses WireGuard's native handshake mechanism
- Server-side only implementation

## Setup Instructions

### 1. Run Database Migrations
```bash
python manage.py makemigrations dns
python manage.py migrate
```

### 2. Initialize HADDNS
```bash
python manage.py haddns_setup --domain vpn.local --threshold 300
```

### 3. Generate dnsmasq Configuration
```bash
python manage.py generate_dnsmasq_config
```

### 4. Restart dnsmasq
```bash
systemctl restart dnsmasq
```

### 5. Test the System
```bash
# Dry run to see what would be updated
python manage.py haddns_update --dry-run --verbose

# Check logs
tail -f /var/log/haddns.log
```

## Configuration

### HADDNS Settings
Access via Django admin: `/admin/dns/haddnsconfig/`

- **Enabled**: Enable/disable HADDNS functionality
- **Handshake Threshold**: Time in seconds after which a peer is considered offline
- **Domain Suffix**: Domain suffix for peer hostnames (e.g., vpn.local)
- **Update Interval**: How often to check handshakes (cron frequency)
- **Include Offline Peers**: Whether to include offline peers with special suffix

### Peer Hostname Mappings
Access via Django admin: `/admin/dns/peerhostnamemapping/`

- **Hostname**: Primary hostname for the peer
- **Custom Domain**: Override domain for this peer
- **Enabled**: Enable/disable DNS resolution for this peer
- **Online Status**: Real-time online/offline status

## Monitoring and Troubleshooting

### Logs
```bash
# HADDNS logs
tail -f /var/log/haddns.log

# dnsmasq logs
journalctl -u dnsmasq -f
```

### Manual Testing
```bash
# Test DNS resolution
nslookup laptop.vpn.local
nslookup laptop.wg0.vpn.local

# Check handshake data
wg show all latest-handshakes

# Manual HADDNS update
python manage.py haddns_update --verbose
```

### Common Issues

1. **Peers not resolving**: Check if peer has hostname and mapping exists
2. **Stale records**: Verify cron job is running and handshake threshold is appropriate
3. **dnsmasq not reloading**: Check dnsmasq service status and permissions

## Advanced Features

### Custom Domains
Peers can have custom domains instead of the global domain suffix:
```python
mapping = PeerHostnameMapping.objects.get(peer=peer)
mapping.custom_domain = "custom.example.com"
mapping.save()
```

### Offline Peer Handling
When enabled, offline peers resolve with a special suffix:
- Online: `laptop.vpn.local`
- Offline: `laptop.offline.vpn.local`

### Instance-Specific Resolution
Peers can be resolved by instance:
- Global: `laptop.vpn.local`
- Instance: `laptop.wg0.vpn.local`

## Performance Considerations

- **Cron Frequency**: Default 1 minute balances responsiveness with system load
- **Handshake Threshold**: 5 minutes prevents false offline status for idle peers
- **Database Queries**: Optimized with select_related for peer data
- **File I/O**: Minimal - only updates when handshake status changes

## Security

- **Interface Binding**: dnsmasq binds only to WireGuard interface
- **Access Control**: DNS resolution confined to VPN network
- **No External Exposure**: Dynamic hosts file not accessible externally

## Future Enhancements

1. **Prometheus Integration**: Metrics for peer status and handshake frequency
2. **WebSocket Updates**: Real-time status updates in web interface
3. **Custom Handshake Triggers**: Manual handshake initiation from clients
4. **Load Balancing**: Support for multiple WireGuard servers
5. **Health Checks**: Additional peer health indicators beyond handshakes

## Conclusion

This HADDNS implementation provides a robust, presence-aware DNS resolution system for WireGuard networks. It leverages WireGuard's native handshake mechanism to create a dynamic, automated DNS system that requires minimal configuration and zero client-side changes.

The system is production-ready and includes comprehensive monitoring, configuration, and troubleshooting capabilities.
