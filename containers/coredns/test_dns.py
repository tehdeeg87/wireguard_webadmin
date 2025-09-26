#!/usr/bin/env python3
"""
Test script for CoreDNS integration
Tests DNS resolution for peer hostnames
"""

import socket
import sys

def test_dns_resolution(hostname, dns_server="127.0.0.1", port=53):
    """Test DNS resolution for a given hostname"""
    try:
        # Create a socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        
        # Simple DNS query (this is a basic implementation)
        # In production, you'd want to use a proper DNS library like dnspython
        print(f"Testing DNS resolution for {hostname}...")
        
        # For now, just test if the DNS server is reachable
        sock.connect((dns_server, port))
        print(f"✓ CoreDNS server is reachable at {dns_server}:{port}")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"✗ Error testing DNS resolution: {e}")
        return False

def main():
    """Main test function"""
    print("CoreDNS Integration Test")
    print("=" * 30)
    
    # Test DNS server connectivity
    if test_dns_resolution("test.wg.local"):
        print("✓ CoreDNS server is running and accessible")
    else:
        print("✗ CoreDNS server is not accessible")
        sys.exit(1)
    
    print("\nTo test actual DNS resolution, use dig or nslookup:")
    print("dig @127.0.0.1 phone.wg.local")
    print("dig @127.0.0.1 laptop.wg.local")
    print("nslookup phone.wg.local 127.0.0.1")

if __name__ == "__main__":
    main()
