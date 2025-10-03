# WireGuard Per-Instance DNS Resolution Setup

This guide explains the per-instance DNS resolution feature that allows WireGuard peers to resolve each other by hostname within and across instances.

## Overview

The DNS system provides:
- **Per-instance DNS scoping**: Peers can be resolved by instance-specific hostnames
- **Global hostname resolution**: Peers can be resolved by their base hostname
- **Automatic configuration**: DNS updates automatically when peers are added/removed
- **Multiple hostname formats**: Support for various naming conventions

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WireGuard     │    │   dnsmasq        │    │   Per-instance  │
│   Peers         │───▶│   Container      │───▶│   Hosts Files   │
│                 │    │   (Port 53)      │    │   (peers_wg*.hosts)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Hostname Formats

For a peer named `laptop` in instance `wg0`:

| Format | Example | Description |
|--------|---------|-------------|
| Global | `laptop` | Resolves to peer in any instance |
| Instance-specific | `laptop.wg0` | Resolves to peer in specific instance |
| Domain-specific | `laptop.wg0.local` | Resolves with domain suffix |
| UUID-based | `peer-{uuid}` | Resolves using peer UUID |

## Configuration Files

### Main dnsmasq Configuration
- **Location**: `/etc/dnsmasq/wireguard_webadmin_dns.conf`
- **Purpose**: Main dnsmasq configuration with upstream DNS servers
- **Auto-generated**: Yes, via Django management command

### Per-Instance Hosts Files
- **Location**: `/etc/dnsmasq/hosts/peers_wg{instance_id}.hosts`
- **Purpose**: Instance-specific peer hostname mappings
- **Auto-generated**: Yes, when peers are created/modified

## Usage

### 1. Automatic Setup
The DNS system is automatically configured when you:
- Create a new WireGuard instance
- Add a peer with a hostname
- Modify peer hostnames

### 2. Manual DNS Updates
```bash
# Update DNS configuration
python manage.py update_peer_dns

# Update and reload dnsmasq
python manage.py update_peer_dns --reload

# Test DNS resolution
python manage.py test_dns_resolution --show-config --show-hosts --test-resolution
```

### 3. Testing DNS Resolution
```bash
# Run the test script
python test_dns_setup.py

# Test from a peer (after connecting to VPN)
nslookup laptop
nslookup laptop.wg0
nslookup laptop.wg0.local
```

## Docker Configuration

### Updated docker-compose.yml
The dnsmasq service now:
- Uses a custom Dockerfile for better control
- Mounts the hosts directory for per-instance files
- Automatically watches for configuration changes

### dnsmasq Container Features
- **Auto-reload**: Watches for config changes and reloads automatically
- **Per-instance hosts**: Supports multiple instance-specific hosts files
- **Upstream DNS**: Forwards unknown queries to configured upstream servers

## Management Commands

### `update_peer_dns`
Updates DNS configuration and optionally reloads dnsmasq.

**Options:**
- `--reload`: Reload dnsmasq after updating configuration

**Example:**
```bash
python manage.py update_peer_dns --reload
```

### `test_dns_resolution`
Tests DNS functionality and shows current configuration.

**Options:**
- `--show-config`: Display generated dnsmasq configuration
- `--show-hosts`: Display generated hosts files
- `--test-resolution`: Test actual DNS resolution

**Example:**
```bash
python manage.py test_dns_resolution --show-config --test-resolution
```

## Peer Configuration

### Automatic Hostname Generation
When creating a peer without a hostname:
- **Format**: `peer-{last_octet_of_ip}`
- **Example**: For IP `10.0.0.15` → hostname `peer-15`

### Manual Hostname Setting
You can set custom hostnames via:
- Peer management interface
- Django admin
- Direct database modification

## Security Considerations

### Network Isolation
- DNS queries are only available to connected WireGuard peers
- No external access to the DNS server (unless explicitly configured)

### Access Control
- DNS resolution respects user ACLs
- Only authorized peers can resolve hostnames

## Troubleshooting

### Common Issues

1. **DNS not resolving**
   - Check if dnsmasq container is running
   - Verify peer has correct DNS server in config
   - Check hosts files are generated correctly

2. **Configuration not updating**
   - Run `python manage.py update_peer_dns --reload`
   - Check dnsmasq logs for errors
   - Verify file permissions

3. **Peers not visible**
   - Ensure peer has a hostname set
   - Check if peer is in the correct instance
   - Verify user has access to the peer

### Debug Commands
```bash
# Check dnsmasq status
docker logs wireguard-webadmin-dns

# Test DNS resolution
nslookup google.com  # Should work
nslookup peer-hostname  # Should resolve to peer IP

# Check generated files
ls -la /etc/dnsmasq/hosts/
cat /etc/dnsmasq/hosts/peers_wg0.hosts
```

## Advanced Configuration

### Custom DNS Servers
Edit the DNS settings in the admin interface to configure upstream DNS servers.

### Multiple Instances
Each instance gets its own hosts file:
- `peers_wg0.hosts` - Instance 0 peers
- `peers_wg1.hosts` - Instance 1 peers
- etc.

### Custom Domains
You can extend the system to support custom domains by modifying the dnsmasq configuration.

## Integration with Existing Features

### Firewall Integration
DNS resolution works alongside existing firewall rules and port forwarding.

### User Management
DNS hostnames respect user ACLs and peer group memberships.

### Monitoring
DNS queries can be monitored through dnsmasq logs and the existing monitoring system.

## Future Enhancements

Potential improvements:
- **Dynamic DNS**: Support for dynamic hostname updates
- **Service Discovery**: Automatic discovery of services on peers
- **Load Balancing**: Multiple peers with same hostname
- **Custom Domains**: Support for custom domain suffixes
- **DNS over HTTPS**: Secure DNS resolution

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review dnsmasq logs
3. Test with the provided test commands
4. Check the Django admin for configuration issues
