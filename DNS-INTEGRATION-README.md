# WireGuard WebAdmin DNS Integration

This document describes the DNS integration feature that allows automatic DNS resolution for WireGuard peers using the `portbro.vpn` domain.

## 🌐 Domain Configuration

The system is configured to use **`portbro.vpn`** as the primary domain for peer resolution. This provides:

- Professional branding for multi-tenant setups
- Avoids conflicts with local `.local` domains
- Enables proper SSL certificate support
- Supports scalable subdomain architecture

## 📁 File Structure

### Core DNS Files
- `wireguard/dns_utils.py` - DNS management utilities
- `wireguard/dns_signals.py` - Django signals for auto-updates
- `wireguard/management/commands/update_dns.py` - Management command
- `init-dns.sh` - Container initialization script
- `shared_hosts/hosts_static` - Generated hosts file for dnsmasq

### Configuration Files
- `wireguard_webadmin/settings.py` - Django settings with DNS config
- `docker-compose.yml` - Container orchestration with DNS setup
- `deploy-dns.sh` / `deploy-dns.bat` - Deployment scripts

## 🚀 Quick Deployment

### Linux/Unix
```bash
chmod +x deploy-dns.sh
./deploy-dns.sh
```

### Windows
```cmd
deploy-dns.bat
```

### Manual Deployment
```bash
# 1. Stop existing containers
docker-compose down

# 2. Deploy with DNS integration
docker-compose up -d

# 3. Wait for initialization
sleep 30

# 4. Test DNS
docker exec wireguard-webadmin python3 manage.py update_dns --status
docker exec wireguard-webadmin python3 manage.py update_dns --reload
```

## 🔧 DNS Configuration

### Automatic Setup
The system automatically:
1. Creates `/shared_hosts` directory
2. Configures dnsmasq with `portbro.vpn` domain
3. Sets up hosts file monitoring
4. Starts dnsmasq service

### Manual Configuration
If automatic setup fails:
```bash
# Configure dnsmasq
docker exec wireguard-webadmin sh -c 'echo "addn-hosts=/shared_hosts/hosts_static" >> /etc/dnsmasq.conf'
docker exec wireguard-webadmin sh -c 'echo "domain=portbro.vpn" >> /etc/dnsmasq.conf'
docker exec wireguard-webadmin sh -c 'echo "expand-hosts" >> /etc/dnsmasq.conf'

# Restart dnsmasq
docker exec wireguard-webadmin pkill -f dnsmasq
docker exec wireguard-webadmin dnsmasq --no-daemon --log-queries --addn-hosts=/shared_hosts/hosts_static --domain=portbro.vpn --expand-hosts &
```

## 📊 Management Commands

### Check DNS Status
```bash
docker exec wireguard-webadmin python3 manage.py update_dns --status
```

### Update DNS Configuration
```bash
docker exec wireguard-webadmin python3 manage.py update_dns --reload
```

### View Generated Hosts File
```bash
cat shared_hosts/hosts_static
```

## 🧪 Testing DNS Resolution

### From Host System
```bash
# Test DNS resolution
nslookup testpeer.portbro.vpn 10.188.0.1

# Test ping
ping testpeer.portbro.vpn
```

### From Inside Container
```bash
# Test DNS resolution
docker exec wireguard-webadmin nslookup testpeer.portbro.vpn 127.0.0.1

# Test ping
docker exec wireguard-webadmin ping testpeer.portbro.vpn
```

## 🔄 Automatic Updates

The system automatically updates DNS when:
- New peers are created
- Peer names are changed
- Peer hostnames are updated
- Peers are deleted
- WireGuard instances are modified

### Manual Trigger
```bash
docker exec wireguard-webadmin python3 manage.py update_dns --reload
```

## 🏗️ Multi-Tenant Support

### Basic Setup
Each peer gets a hostname like:
- `peer-1.portbro.vpn`
- `server-2.portbro.vpn`
- `laptop-3.portbro.vpn`

### Advanced Subdomain Support
For multiple groups, you can extend the system to support:
- `peer-1.group1.portbro.vpn`
- `peer-1.group2.portbro.vpn`

## 🐛 Troubleshooting

### Common Issues

#### DNS Not Resolving
```bash
# Check dnsmasq is running
docker exec wireguard-webadmin ps aux | grep dnsmasq

# Check hosts file exists
cat shared_hosts/hosts_static

# Restart dnsmasq
docker exec wireguard-webadmin pkill -f dnsmasq
docker exec wireguard-webadmin dnsmasq --no-daemon --log-queries --addn-hosts=/shared_hosts/hosts_static --domain=portbro.vpn --expand-hosts &
```

#### Port 53 Already in Use
```bash
# Kill existing dnsmasq processes
docker exec wireguard-webadmin pkill -f dnsmasq
docker exec wireguard-webadmin rm -f /run/dnsmasq/dnsmasq.pid

# Start dnsmasq
docker exec wireguard-webadmin dnsmasq --no-daemon --log-queries --addn-hosts=/shared_hosts/hosts_static --domain=portbro.vpn --expand-hosts &
```

#### Peers Not Auto-Updating
```bash
# Check Django signals
docker exec wireguard-webadmin python3 -c "import wireguard.dns_signals"

# Manual DNS update
docker exec wireguard-webadmin python3 manage.py update_dns --reload
```

### Debug Commands
```bash
# View dnsmasq logs
docker exec wireguard-webadmin journalctl -u dnsmasq

# Check dnsmasq configuration
docker exec wireguard-webadmin cat /etc/dnsmasq.conf

# Test DNS from inside container
docker exec wireguard-webadmin nslookup localhost 127.0.0.1
```

## 📈 Monitoring

### Health Checks
```bash
# Check all services
docker ps

# Check DNS status
docker exec wireguard-webadmin python3 manage.py update_dns --status

# Check dnsmasq process
docker exec wireguard-webadmin ps aux | grep dnsmasq
```

### Logs
```bash
# View container logs
docker logs wireguard-webadmin

# View dnsmasq logs
docker exec wireguard-webadmin journalctl -u dnsmasq
```

## 🔒 Security Considerations

- The `portbro.vpn` domain is only resolvable within the WireGuard network
- DNS queries are handled by dnsmasq running inside the container
- No external DNS servers are involved in peer resolution
- The hosts file is automatically generated and should not be manually edited

## 🎯 Success Criteria

After deployment, you should have:
- ✅ All containers running without errors
- ✅ dnsmasq listening on port 53
- ✅ Hosts file automatically generated
- ✅ DNS resolution working from host system
- ✅ Peer creation automatically sets hostname
- ✅ DNS updates automatically on peer changes
- ✅ Network connectivity working (ping successful)
- ✅ Multiple peers resolvable simultaneously

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all containers are running: `docker ps`
3. Check DNS status: `docker exec wireguard-webadmin python3 manage.py update_dns --status`
4. Review logs: `docker logs wireguard-webadmin`
