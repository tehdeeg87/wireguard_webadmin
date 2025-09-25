#!/usr/bin/env python
"""
Simple DNS server for testing WireGuard peer hostname resolution
Run this script and it will serve DNS queries for your peer hostnames
"""
import socket
import struct
import threading
import time

# Peer hostname mappings (from your WireGuard configuration)
PEER_HOSTNAMES = {
    'phone': '10.188.0.2',
    'laptop': '10.188.0.3',
    'phone.ef': '10.188.0.2',
    'laptop.ef': '10.188.0.3',
}

def dns_query_handler(data, addr, sock):
    """Handle DNS queries"""
    try:
        # Parse DNS query
        domain = ''
        i = 12  # Skip DNS header
        while i < len(data):
            length = data[i]
            if length == 0:
                break
            if i + 1 + length < len(data):
                domain += data[i+1:i+1+length].decode('utf-8') + '.'
            i += length + 1
        
        domain = domain.rstrip('.')
        print(f"DNS Query from {addr[0]}: {domain}")
        
        # Check if we have this hostname
        if domain in PEER_HOSTNAMES:
            ip = PEER_HOSTNAMES[domain]
            print(f"  -> Resolved to: {ip}")
            
            # Build DNS response
            response = data[:2]  # Transaction ID
            response += b'\x81\x80'  # Flags (response, recursion available)
            response += b'\x00\x01'  # Questions
            response += b'\x00\x01'  # Answers
            response += b'\x00\x00'  # Authority
            response += b'\x00\x00'  # Additional
            
            # Question section
            response += data[12:i+1]  # Original question
            
            # Answer section
            response += b'\xc0\x0c'  # Name pointer
            response += b'\x00\x01'  # Type A
            response += b'\x00\x01'  # Class IN
            response += b'\x00\x00\x00\x3c'  # TTL 60 seconds
            response += b'\x00\x04'  # Data length 4 bytes
            
            # IP address
            ip_parts = ip.split('.')
            for part in ip_parts:
                response += struct.pack('B', int(part))
            
            sock.sendto(response, addr)
        else:
            print(f"  -> Not found, forwarding to upstream")
            # Forward to upstream DNS (1.1.1.1)
            upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            upstream_sock.sendto(data, ('1.1.1.1', 53))
            upstream_data, _ = upstream_sock.recvfrom(512)
            upstream_sock.close()
            sock.sendto(upstream_data, addr)
            
    except Exception as e:
        print(f"Error handling DNS query: {e}")

def start_dns_server():
    """Start the DNS server"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 53))
    
    print("=== Simple DNS Server Started ===")
    print("Listening on 0.0.0.0:53")
    print("Peer hostnames configured:")
    for hostname, ip in PEER_HOSTNAMES.items():
        print(f"  {hostname} -> {ip}")
    print()
    print("To test from your VPN client:")
    print("  nslookup phone")
    print("  nslookup laptop")
    print("  ping phone")
    print("  ping laptop")
    print()
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            data, addr = sock.recvfrom(512)
            # Handle each query in a separate thread
            thread = threading.Thread(target=dns_query_handler, args=(data, addr, sock))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\nShutting down DNS server...")
    finally:
        sock.close()

if __name__ == "__main__":
    start_dns_server()
