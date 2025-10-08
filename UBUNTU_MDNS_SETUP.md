# Ubuntu mDNS Setup for Peer-to-Peer Resolution

This guide explains how to set up mDNS on Ubuntu for WireGuard peer-to-peer hostname resolution using the **Avahi + Reflector** method.

## Overview

The **Avahi + Reflector** approach is the simplest and most reliable method for WireGuard peer-to-peer hostname resolution. Each peer runs its own mDNS daemon with reflector enabled, allowing automatic discovery across the WireGuard tunnel.

## Prerequisites

- Ubuntu server with WireGuard WebAdmin deployed
- WireGuard peers connected to the instance
- mDNS daemon running on the server

## Step 1: Install mDNS on Ubuntu Server

```bash
# Install Avahi mDNS daemon
sudo apt update
sudo apt install -y avahi-daemon avahi-utils

# Enable and start the service
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# Check if it's running
sudo systemctl status avahi-daemon
```

## Step 2: Configure Avahi for WireGuard Interface

```bash
# Backup original config
sudo cp /etc/avahi/avahi-daemon.conf /etc/avahi/avahi-daemon.conf.backup

# Edit Avahi configuration
sudo nano /etc/avahi/avahi-daemon.conf
```

**Add/Update these sections in `/etc/avahi/avahi-daemon.conf`:**

```ini
[server]
allow-interfaces=wg0
use-ipv4=yes
use-ipv6=no

[reflector]
enable-reflector=yes
```

**Restart Avahi:**
```bash
sudo systemctl restart avahi-daemon
```

## Step 3: Configure mDNS for WireGuard

```bash
# Create mDNS configuration directory
sudo mkdir -p /etc/avahi/hosts

# Set proper permissions
sudo chown -R avahi:avahi /etc/avahi/hosts
sudo chmod 755 /etc/avahi/hosts
```

## Step 4: Update WireGuard WebAdmin Configuration

The system will automatically:
1. Generate mDNS hosts files in `/etc/avahi/hosts/`
2. Configure peer DNS settings to use the server IP
3. Update mDNS when peers are added/removed

## Step 5: Test mDNS Resolution

### From the Ubuntu Server:
```bash
# Check if mDNS is running
sudo systemctl status avahi-daemon

# Browse available services
avahi-browse -a

# Test resolution
avahi-resolve-host-name phone1.wg0.local
ping phone1.wg0.local
```

### From Connected Peers:

**Windows PC (with Bonjour installed):**
```cmd
nslookup phone1.wg0.local
ping phone1.wg0.local
```

**Android/iOS (built-in mDNS support):**
```bash
ping phone1.wg0.local
```

**Linux (with avahi-utils installed):**
```bash
avahi-resolve-host-name phone1.wg0.local
ping phone1.wg0.local
```

## Step 6: Client Configuration

Each peer's WireGuard config will include DNS settings:

```ini
[Interface]
PrivateKey = <peer-private-key>
Address = 10.188.0.X/24
DNS = 10.188.0.1, 8.8.8.8  # Server IP for mDNS, Google DNS as fallback

[Peer]
PublicKey = <server-public-key>
Endpoint = your-server.com:51820
AllowedIPs = 0.0.0.0/0
```

## Available Hostname Formats

For a peer named `phone1` in instance `wg0`:

| Format | Example | Description |
|--------|---------|-------------|
| Instance-specific | `phone1.wg0.local` | Resolves to peer in specific instance |
| Global | `phone1.wg.local` | Resolves to peer in any instance |
| Short | `phone1` | Resolves to peer in same instance |
| UUID-based | `peer-{uuid}` | Resolves using peer UUID |

## How the Avahi + Reflector Method Works

1. **Server-side**: Avahi daemon runs on the Ubuntu server with reflector enabled
2. **Interface binding**: Avahi listens on the `wg0` interface for mDNS traffic
3. **Reflection**: mDNS queries are automatically reflected across the WireGuard tunnel
4. **Peer discovery**: Each peer can discover and resolve other peers by hostname
5. **Automatic**: No manual configuration needed on peer devices

## Troubleshooting

### mDNS Not Working
```bash
# Check if Avahi is running
sudo systemctl status avahi-daemon

# Check logs
sudo journalctl -u avahi-daemon -f

# Restart Avahi
sudo systemctl restart avahi-daemon
```

### Peers Can't Resolve Each Other
1. Ensure both peers are connected to the same WireGuard instance
2. Check that DNS is set to server IP in peer configs
3. Verify mDNS hosts files are generated:
   ```bash
   sudo cat /etc/avahi/hosts/wg0.hosts
   ```

### Windows Peers Can't Resolve
- Install Bonjour Print Services: https://support.apple.com/downloads/bonjour_for_windows
- Or use the IP address directly: `ping 10.188.0.X`

## Security Considerations

- mDNS is designed for local networks and is safe
- `.local` domains are not routable on the internet
- Consider firewall rules if needed (port 5353 UDP)

## Performance

- Hostname resolution typically < 1ms
- No centralized server means no bottleneck
- Automatic cleanup when peers disconnect
- Minimal overhead on the server

## Example: Phone to PC Communication

1. **Phone connects** to WireGuard with hostname `phone1`
2. **PC connects** to WireGuard with hostname `laptop`
3. **Both peers** can now resolve each other:
   - From phone: `ping laptop.wg0.local`
   - From PC: `ping phone1.wg0.local`
4. **Services work** with hostnames:
   - SSH: `ssh laptop.wg0.local`
   - HTTP: `curl http://phone1.wg0.local:8080`
   - Any service using hostnames

This enables seamless peer-to-peer communication using friendly hostnames instead of IP addresses!

## Quick Setup Script

```bash
#!/bin/bash
# Complete mDNS setup for WireGuard

echo "Installing Avahi mDNS daemon..."
sudo apt update
sudo apt install -y avahi-daemon avahi-utils

echo "Configuring Avahi for WireGuard..."
sudo cp /etc/avahi/avahi-daemon.conf /etc/avahi/avahi-daemon.conf.backup

# Create new config
sudo tee /etc/avahi/avahi-daemon.conf > /dev/null <<EOF
[server]
allow-interfaces=wg0
use-ipv4=yes
use-ipv6=no

[reflector]
enable-reflector=yes
EOF

echo "Setting up directories..."
sudo mkdir -p /etc/avahi/hosts
sudo chown -R avahi:avahi /etc/avahi/hosts
sudo chmod 755 /etc/avahi/hosts

echo "Starting Avahi daemon..."
sudo systemctl enable avahi-daemon
sudo systemctl restart avahi-daemon

echo "Checking status..."
sudo systemctl status avahi-daemon

echo "Testing mDNS..."
avahi-resolve-host-name localhost.local

echo "mDNS setup complete! Peers can now resolve each other by hostname."
```