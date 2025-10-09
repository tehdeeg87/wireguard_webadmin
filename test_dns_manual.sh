#!/bin/bash

# Manual DNS test script
# Run this to test hostname resolution without cron

echo "=== Manual DNS Test ==="
echo

echo "1. Checking shared hosts file:"
if [ -f "/shared_hosts/hosts" ]; then
    echo "   Shared hosts file exists:"
    cat /shared_hosts/hosts
else
    echo "   WARNING: Shared hosts file not found"
fi
echo

echo "2. Checking current /etc/hosts:"
echo "   Current /etc/hosts content:"
cat /etc/hosts | grep -E "(computer|phone|laptop|myphone)" || echo "   No peer hostnames found in /etc/hosts"
echo

echo "3. Testing hostname resolution:"
if command -v nslookup >/dev/null 2>&1; then
    echo "   Testing nslookup computer:"
    nslookup computer 2>/dev/null || echo "   nslookup failed"
    echo "   Testing nslookup phone:"
    nslookup phone 2>/dev/null || echo "   nslookup failed"
else
    echo "   nslookup not available"
fi
echo

echo "4. Manual hosts file update:"
/app/update_hosts_from_shared.sh
echo

echo "5. Checking /etc/hosts after update:"
cat /etc/hosts | grep -E "(computer|phone|laptop|myphone)" || echo "   Still no peer hostnames found"
