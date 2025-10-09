# 🚀 Avahi Integration - Ubuntu Deployment Checklist

## ✅ Pre-Deployment Verification

### Code Changes Made:
- [x] Updated `init.sh` - D-Bus and Avahi startup
- [x] Created `mdns/management/commands/register_peers_avahi.py`
- [x] Updated `mdns/signals.py` - Automatic peer registration
- [x] Created `mdns_config/avahi-daemon.conf` - Avahi configuration
- [x] Updated `wireguard_tools/views.py` - mDNS DNS config
- [x] Updated `Dockerfile` - Added Avahi packages

### Files to Deploy:
- [x] `init.sh` - Updated startup script
- [x] `mdns/` - Complete mDNS app with Avahi integration
- [x] `mdns_config/` - Avahi configuration files
- [x] `Dockerfile` - Updated with Avahi packages
- [x] `docker-compose.yml` - Updated mDNS container
- [x] Test scripts in `test_scripts/`

## 🐧 Ubuntu Server Requirements

### System Requirements:
- [ ] Ubuntu 20.04+ (recommended)
- [ ] Docker and Docker Compose installed
- [ ] WireGuard installed on host (for testing)
- [ ] Ports 8000 (web), 51820-51839 (WireGuard) available

### Network Requirements:
- [ ] Host can access WireGuard interfaces
- [ ] mDNS traffic allowed (UDP 5353)
- [ ] D-Bus access for Avahi

## 🚀 Deployment Steps

### 1. Upload Code
```bash
# Upload all files to Ubuntu server
scp -r . user@ubuntu-server:/path/to/wireguard_webadmin/
```

### 2. Install Dependencies
```bash
# On Ubuntu server
sudo apt update
sudo apt install -y docker.io docker-compose avahi-daemon avahi-utils
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### 3. Build and Start
```bash
cd /path/to/wireguard_webadmin
docker-compose build --no-cache
docker-compose up -d
```

### 4. Verify Installation
```bash
# Check containers
docker-compose ps

# Check Avahi daemon
docker exec wireguard-webadmin ps aux | grep avahi

# Test management commands
docker exec wireguard-webadmin python manage.py register_peers_avahi
```

## 🧪 Testing Commands

### Basic Functionality:
```bash
# Test hostname resolution
avahi-resolve-host-name myphone.local
avahi-resolve-host-name myphone.wg0.local

# Browse services
avahi-browse -a
avahi-browse -t _wireguard._tcp

# Test from peer perspective
ping myphone
ping myphone.wg0.local
```

### Management Commands:
```bash
# Register peers with Avahi
docker exec wireguard-webadmin python manage.py register_peers_avahi --reload

# Update mDNS hosts files
docker exec wireguard-webadmin python manage.py update_peer_mdns --reload

# Test specific instance
docker exec wireguard-webadmin python manage.py register_peers_avahi --instance-id 0 --reload
```

### Web Interface:
- Main app: http://ubuntu-server:8000
- Admin panel: http://ubuntu-server:8000/admin_panel/

## 🔍 Troubleshooting

### Common Issues:
1. **Avahi not starting**: Check D-Bus is running
2. **Hostname resolution fails**: Verify hosts files generated
3. **Container restart loops**: Check init.sh syntax
4. **Permission issues**: Ensure Docker user in docker group

### Debug Commands:
```bash
# Check Avahi daemon status
docker exec wireguard-webadmin pgrep avahi-daemon

# Check hosts files
docker exec wireguard-webadmin cat /etc/avahi/hosts/wg0.hosts

# Check Avahi logs
docker exec wireguard-webadmin journalctl -u avahi-daemon

# Test D-Bus connection
docker exec wireguard-webadmin dbus-send --system --print-reply --dest=org.freedesktop.Avahi / org.freedesktop.Avahi.Server.GetVersion
```

## ✅ Success Criteria

- [ ] Web interface accessible
- [ ] Avahi daemon running in container
- [ ] Peer hostnames resolvable
- [ ] Management commands working
- [ ] Automatic peer registration working
- [ ] Cross-peer hostname resolution working

## 🎯 Expected Results

Once deployed, you should be able to:
1. **Resolve peer hostnames**: `myphone.local` → `10.188.0.3`
2. **Use instance domains**: `myphone.wg0.local` → `10.188.0.3`
3. **Global resolution**: `myphone.wg.local` → `10.188.0.3`
4. **Service discovery**: See WireGuard services via `avahi-browse`
5. **Automatic updates**: Peers auto-register when created/modified