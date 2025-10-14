# HADDNS Testing Guide

This guide provides comprehensive testing strategies for the HADDNS (Handshake-Aware Dynamic DNS Resolution) implementation.

## 🚀 Quick Start Testing

### 1. Basic Validation
```bash
# Run the quick test suite
python quick_haddns_test.py
```

This will validate:
- ✅ Database migrations
- ✅ Models import correctly
- ✅ HADDNS setup works
- ✅ WireGuard integration
- ✅ dnsmasq config generation
- ✅ HADDNS update functionality

### 2. Comprehensive Testing
```bash
# Run the full test suite
python test_haddns_comprehensive.py
```

This provides detailed testing of all components with verbose output.

## 🧪 Testing Scenarios

### Scenario 1: Fresh Installation
```bash
# 1. Set up HADDNS
python manage.py haddns_setup --domain vpn.local --threshold 300

# 2. Generate dnsmasq configuration
python manage.py generate_dnsmasq_config --output /etc/dnsmasq.d/wireguard_webadmin.conf

# 3. Test DNS resolution
nslookup test.vpn.local
```

### Scenario 2: With Existing Peers
```bash
# 1. Check existing peers
python manage.py shell -c "from wireguard.models import Peer; print(f'Peers: {Peer.objects.count()}')"

# 2. Set up HADDNS for existing peers
python manage.py haddns_setup --domain vpn.local --threshold 300

# 3. Test handshake monitoring
python manage.py haddns_update --verbose

# 4. Check generated mappings
python manage.py shell -c "from dns.models import PeerHostnameMapping; [print(f'{m.hostname} -> {m.peer.public_key[:16]}... (Online: {m.is_online})') for m in PeerHostnameMapping.objects.all()]"
```

### Scenario 3: Production Testing
```bash
# 1. Set up cron job
echo "*/1 * * * * root cd /app && python manage.py haddns_update >> /var/log/haddns.log 2>&1" >> /etc/crontab

# 2. Monitor logs
tail -f /var/log/haddns.log

# 3. Test DNS resolution
nslookup peer-hostname.vpn.local

# 4. Check dynamic hosts file
cat /etc/dnsmasq.d/haddns_dynamic_hosts.conf
```

## 🔍 Manual Testing Steps

### 1. Database Testing
```bash
# Check HADDNS configuration
python manage.py shell -c "from dns.models import HADDNSConfig; config = HADDNSConfig.get_config(); print(f'Enabled: {config.enabled}, Domain: {config.domain_suffix}')"

# Check peer mappings
python manage.py shell -c "from dns.models import PeerHostnameMapping; print(f'Mappings: {PeerHostnameMapping.objects.count()}')"
```

### 2. WireGuard Integration Testing
```bash
# Check handshake data
wg show all latest-handshakes

# Test HADDNS update
python manage.py haddns_update --dry-run --verbose

# Manual update
python manage.py haddns_update --verbose
```

### 3. DNS Resolution Testing
```bash
# Test local DNS
nslookup localhost

# Test HADDNS resolution
nslookup test.vpn.local
nslookup laptop.vpn.local

# Test with different formats
nslookup laptop.wg0.vpn.local
nslookup laptop.offline.vpn.local
```

### 4. dnsmasq Integration Testing
```bash
# Check dnsmasq status
systemctl status dnsmasq

# Test configuration
dnsmasq --test

# Reload configuration
systemctl reload dnsmasq

# Check logs
journalctl -u dnsmasq -f
```

## 🐛 Troubleshooting Tests

### Test 1: Signal Issues
```bash
# Check if signals are working
python manage.py shell -c "from dns.models import PeerHostnameMapping; print(f'Signal test: {PeerHostnameMapping.objects.count()}')"
```

### Test 2: Permission Issues
```bash
# Check file permissions
ls -la /etc/dnsmasq.d/
ls -la /var/log/haddns.log
```

### Test 3: WireGuard Issues
```bash
# Check WireGuard status
wg show

# Check specific interface
wg show wg0 latest-handshakes
```

### Test 4: Database Issues
```bash
# Check migrations
python manage.py showmigrations dns

# Check database integrity
python manage.py check --database default
```

## 📊 Performance Testing

### Test 1: Load Testing
```bash
# Test with many peers
python manage.py shell -c "
from wireguard.models import Peer
from dns.models import PeerHostnameMapping
import string
import random

# Create test peers
for i in range(100):
    peer = Peer.objects.create(
        name=f'test-peer-{i}',
        hostname=f'peer{i}.vpn.local',
        public_key=''.join(random.choices(string.ascii_letters + string.digits, k=44)),
        wireguard_instance_id=1
    )
    PeerHostnameMapping.objects.create(
        peer=peer,
        hostname=f'peer{i}.vpn.local'
    )
print('Created 100 test peers')
"
```

### Test 2: Update Performance
```bash
# Time the HADDNS update
time python manage.py haddns_update --verbose
```

### Test 3: Memory Usage
```bash
# Monitor memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

## 🔧 Configuration Testing

### Test 1: Different Domains
```bash
# Test with custom domain
python manage.py haddns_setup --domain custom.local --threshold 180
```

### Test 2: Different Thresholds
```bash
# Test with different handshake thresholds
python manage.py shell -c "
from dns.models import HADDNSConfig
config = HADDNSConfig.get_config()
config.handshake_threshold_seconds = 60  # 1 minute
config.save()
print('Updated threshold to 60 seconds')
"
```

### Test 3: Offline Peer Handling
```bash
# Test offline peer configuration
python manage.py shell -c "
from dns.models import HADDNSConfig
config = HADDNSConfig.get_config()
config.include_offline_peers = True
config.offline_suffix = '.offline'
config.save()
print('Enabled offline peer handling')
"
```

## 📈 Monitoring Tests

### Test 1: Log Monitoring
```bash
# Monitor HADDNS logs
tail -f /var/log/haddns.log

# Monitor dnsmasq logs
journalctl -u dnsmasq -f

# Monitor system logs
journalctl -f | grep haddns
```

### Test 2: Status Monitoring
```bash
# Check peer status
python manage.py shell -c "
from dns.models import PeerHostnameMapping
online = PeerHostnameMapping.objects.filter(is_online=True).count()
offline = PeerHostnameMapping.objects.filter(is_online=False).count()
print(f'Online: {online}, Offline: {offline}')
"
```

### Test 3: DNS Query Monitoring
```bash
# Monitor DNS queries
tcpdump -i any port 53

# Test DNS resolution with monitoring
dig @localhost test.vpn.local
```

## 🎯 Success Criteria

### ✅ Basic Functionality
- [ ] All quick tests pass
- [ ] HADDNS setup completes without errors
- [ ] dnsmasq configuration generates correctly
- [ ] DNS resolution works for online peers
- [ ] Offline peers don't resolve (or resolve with .offline suffix)

### ✅ Advanced Functionality
- [ ] Handshake monitoring works correctly
- [ ] Peer status updates automatically
- [ ] Cron job runs without errors
- [ ] Admin interface shows correct data
- [ ] Dynamic hosts file updates correctly

### ✅ Production Readiness
- [ ] System handles many peers efficiently
- [ ] Memory usage is reasonable
- [ ] Logs are informative and not excessive
- [ ] Error handling works correctly
- [ ] Configuration changes take effect

## 🚨 Common Issues and Solutions

### Issue 1: "no such table: dns_haddnsconfig"
**Solution:** Run migrations
```bash
python manage.py makemigrations dns
python manage.py migrate
```

### Issue 2: "DNSSettings matching query does not exist"
**Solution:** Create DNS settings
```bash
python manage.py shell -c "from dns.models import DNSSettings; DNSSettings.objects.get_or_create(name='dns_settings')"
```

### Issue 3: "WireGuard command not found"
**Solution:** Install WireGuard tools
```bash
# Ubuntu/Debian
sudo apt install wireguard-tools

# CentOS/RHEL
sudo yum install wireguard-tools
```

### Issue 4: "dnsmasq not found"
**Solution:** Install dnsmasq
```bash
# Ubuntu/Debian
sudo apt install dnsmasq

# CentOS/RHEL
sudo yum install dnsmasq
```

### Issue 5: "Permission denied"
**Solution:** Check file permissions
```bash
sudo chown -R www-data:www-data /etc/dnsmasq.d/
sudo chmod 755 /etc/dnsmasq.d/
```

## 📝 Testing Checklist

- [ ] Run quick test suite
- [ ] Run comprehensive test suite
- [ ] Test with fresh installation
- [ ] Test with existing peers
- [ ] Test production scenario
- [ ] Test manual DNS resolution
- [ ] Test WireGuard integration
- [ ] Test dnsmasq integration
- [ ] Test error handling
- [ ] Test performance with many peers
- [ ] Test configuration changes
- [ ] Test monitoring and logging
- [ ] Verify all success criteria
- [ ] Document any issues found

## 🎉 Conclusion

This testing guide provides comprehensive coverage of the HADDNS implementation. Use the quick test for basic validation, the comprehensive test for detailed analysis, and the manual testing steps for specific scenarios.

The system is designed to be robust and production-ready, with proper error handling, logging, and monitoring capabilities.
