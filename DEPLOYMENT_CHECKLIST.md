# WireGuard mDNS Deployment Checklist

## Pre-Deployment (Ubuntu Server)

### 1. Fix System Issues
```bash
# Fix broken packages
sudo apt --fix-broken install
sudo apt update
sudo apt upgrade -y

# Fix hostname resolution
echo "127.0.0.1 tor1-wireguard" | sudo tee -a /etc/hosts
sudo hostnamectl set-hostname tor1-wireguard
```

### 2. Install and Configure Avahi + Reflector
```bash
# Run the setup script
sudo ./setup_avahi_reflector.sh

# Or manually:
sudo apt install -y avahi-daemon avahi-utils
sudo cp /etc/avahi/avahi-daemon.conf /etc/avahi/avahi-daemon.conf.backup

# Configure for WireGuard
sudo tee /etc/avahi/avahi-daemon.conf > /dev/null <<EOF
[server]
allow-interfaces=wg0
use-ipv4=yes
use-ipv6=no

[reflector]
enable-reflector=yes
EOF

sudo systemctl enable avahi-daemon
sudo systemctl restart avahi-daemon
```

### 3. Test Avahi Setup
```bash
# Run the test script
python3 test_avahi_setup.py

# Or manually test:
sudo systemctl status avahi-daemon
avahi-resolve-host-name localhost.local
avahi-browse -a
```

## Deployment

### 4. Deploy WireGuard WebAdmin Code
```bash
# Pull latest code
git pull origin main

# Rebuild and restart containers
docker-compose down
docker-compose up -d --build

# Check all services are running
docker-compose ps
```

### 5. Verify mDNS Integration
```bash
# Check if mDNS hosts files are generated
sudo ls -la /etc/avahi/hosts/

# Test from server
avahi-resolve-host-name phone1.wg0.local
ping phone1.wg0.local
```

## Post-Deployment Testing

### 6. Test Peer-to-Peer Resolution

**From Windows PC (with Bonjour installed):**
```cmd
nslookup phone1.wg0.local
ping phone1.wg0.local
```

**From Android/iOS:**
```bash
ping phone1.wg0.local
```

**From Linux:**
```bash
avahi-resolve-host-name phone1.wg0.local
ping phone1.wg0.local
```

### 7. Verify Client Configurations

Check that peer configs include correct DNS:
```ini
[Interface]
PrivateKey = <peer-private-key>
Address = 10.188.0.X/24
DNS = 10.188.0.1, 8.8.8.8  # Server IP for mDNS, Google DNS fallback
```

## Troubleshooting

### If mDNS Not Working
```bash
# Check Avahi status
sudo systemctl status avahi-daemon

# Check logs
sudo journalctl -u avahi-daemon -f

# Restart Avahi
sudo systemctl restart avahi-daemon

# Check WireGuard interface
ip link show wg0
```

### If Peers Can't Resolve Each Other
1. Ensure both peers are connected to the same WireGuard instance
2. Check that DNS is set to server IP in peer configs
3. Verify Avahi is running and configured correctly
4. Test from the server first: `ping phone1.wg0.local`

### If Windows Peers Can't Resolve
- Install Bonjour Print Services: https://support.apple.com/downloads/bonjour_for_windows
- Or use IP addresses directly: `ping 10.188.0.X`

## Expected Results

✅ **Success Indicators:**
- Avahi daemon is running and enabled
- mDNS is listening on port 5353
- Peers can resolve each other by hostname
- No manual configuration needed on peer devices
- Automatic peer discovery works across WireGuard tunnel

❌ **Failure Indicators:**
- Avahi daemon not running
- mDNS not listening on port 5353
- Peers can't resolve hostnames
- Manual configuration required on peer devices

## Quick Commands Reference

```bash
# Check Avahi status
sudo systemctl status avahi-daemon

# Restart Avahi
sudo systemctl restart avahi-daemon

# Test mDNS resolution
avahi-resolve-host-name phone1.wg0.local

# Browse mDNS services
avahi-browse -a

# Check WireGuard interface
ip link show wg0

# Check mDNS port
sudo netstat -tulpn | grep :5353
```

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review logs: `sudo journalctl -u avahi-daemon -f`
3. Verify WireGuard interface is up: `ip link show wg0`
4. Test mDNS from server first before testing from peers