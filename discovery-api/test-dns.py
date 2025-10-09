#!/usr/bin/env python3
"""
Simple DNS client for testing the discovery API DNS server
"""
import socket
import struct
import sys


def create_dns_query(hostname):
    """Create a DNS query packet"""
    # DNS header
    transaction_id = 0x1234
    flags = 0x0100  # Standard query
    questions = 1
    answers = 0
    authority = 0
    additional = 0
    
    header = struct.pack('!HHHHHH', transaction_id, flags, questions, 
                        answers, authority, additional)
    
    # Question section
    question = b''
    for part in hostname.split('.'):
        question += struct.pack('!B', len(part)) + part.encode()
    question += b'\x00'  # Null terminator
    question += struct.pack('!HH', 1, 1)  # QTYPE=A, QCLASS=IN
    
    return header + question


def parse_dns_response(data):
    """Parse DNS response packet"""
    if len(data) < 12:
        return None
    
    # Parse header
    transaction_id, flags, questions, answers, authority, additional = struct.unpack('!HHHHHH', data[:12])
    
    if flags & 0x8000 == 0:  # Not a response
        return None
    
    if flags & 0x0003 != 0:  # Error response
        error_codes = {1: 'FORMERR', 2: 'SERVFAIL', 3: 'NXDOMAIN', 4: 'NOTIMP', 5: 'REFUSED'}
        error = flags & 0x0003
        return f"DNS Error: {error_codes.get(error, 'Unknown')}"
    
    if answers == 0:
        return "No answers"
    
    # Skip question section
    pos = 12
    while pos < len(data) and data[pos] != 0:
        pos += 1
    pos += 5  # Skip null terminator and QTYPE/QCLASS
    
    # Parse answer section
    if pos + 12 > len(data):
        return "Invalid response"
    
    # Skip name (compressed pointer)
    pos += 2
    qtype, qclass, ttl, data_length = struct.unpack('!HHIH', data[pos:pos+10])
    pos += 10
    
    if qtype == 1 and data_length == 4:  # A record
        ip_bytes = data[pos:pos+4]
        ip = socket.inet_ntoa(ip_bytes)
        return ip
    
    return "Unexpected response format"


def query_dns(hostname, server='127.0.0.1', port=53):
    """Query DNS server for hostname"""
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        
        # Create query
        query = create_dns_query(hostname)
        
        # Send query
        sock.sendto(query, (server, port))
        
        # Receive response
        response, addr = sock.recvfrom(512)
        
        # Parse response
        result = parse_dns_response(response)
        
        sock.close()
        return result
        
    except Exception as e:
        return f"Error: {e}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python test-dns.py <hostname> [server] [port]")
        print("Example: python test-dns.py mypeer.local")
        print("Example: python test-dns.py mypeer.local 127.0.0.1 53")
        sys.exit(1)
    
    hostname = sys.argv[1]
    server = sys.argv[2] if len(sys.argv) > 2 else '127.0.0.1'
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 53
    
    print(f"Querying {hostname} from {server}:{port}")
    result = query_dns(hostname, server, port)
    print(f"Result: {result}")


if __name__ == '__main__':
    main()
