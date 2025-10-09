"""
Lightweight DNS server that resolves hostnames using the discovery API
"""
import asyncio
import socket
import struct
import threading
import time
from typing import Dict, Optional

import requests


class DNSResolver:
    def __init__(self, api_url: str = "http://localhost:5000", port: int = 53):
        self.api_url = api_url
        self.port = port
        self.cache: Dict[str, tuple] = {}  # hostname -> (ip, timestamp)
        self.cache_ttl = 300  # 5 minutes
        self.running = False
        
    def _query_api(self, hostname: str) -> Optional[str]:
        """Query the discovery API for a hostname"""
        try:
            response = requests.get(
                f"{self.api_url}/resolve/{hostname}",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('ip')
        except Exception as e:
            print(f"API query failed for {hostname}: {e}")
        return None
    
    def _get_cached_ip(self, hostname: str) -> Optional[str]:
        """Get IP from cache if not expired"""
        if hostname in self.cache:
            ip, timestamp = self.cache[hostname]
            if time.time() - timestamp < self.cache_ttl:
                return ip
            else:
                del self.cache[hostname]
        return None
    
    def _cache_ip(self, hostname: str, ip: str):
        """Cache an IP address"""
        self.cache[hostname] = (ip, time.time())
    
    def resolve_hostname(self, hostname: str) -> Optional[str]:
        """Resolve a hostname to IP address"""
        # Check cache first
        cached_ip = self._get_cached_ip(hostname)
        if cached_ip:
            return cached_ip
        
        # Query API
        ip = self._query_api(hostname)
        if ip:
            self._cache_ip(hostname, ip)
            return ip
        
        return None
    
    def _create_dns_response(self, query_data: bytes, ip: str) -> bytes:
        """Create a DNS response packet"""
        # Parse the query
        transaction_id = query_data[:2]
        flags = b'\x81\x80'  # Standard response, recursion available
        questions = query_data[4:6]
        answers = b'\x00\x01'  # 1 answer
        authority = b'\x00\x00'
        additional = b'\x00\x00'
        
        # Extract the question section
        question_start = 12
        question_end = question_start
        while question_end < len(query_data) and query_data[question_end] != 0:
            question_end += 1
        question_end += 5  # Include null terminator and QTYPE/QCLASS
        
        question = query_data[question_start:question_end]
        
        # Create answer section
        # Name (compressed pointer to question)
        name = b'\xc0\x0c'
        # Type (A record)
        qtype = b'\x00\x01'
        # Class (IN)
        qclass = b'\x00\x01'
        # TTL (300 seconds)
        ttl = b'\x00\x00\x01\x2c'
        # Data length (4 bytes for IPv4)
        data_length = b'\x00\x04'
        # IP address
        ip_bytes = socket.inet_aton(ip)
        
        answer = name + qtype + qclass + ttl + data_length + ip_bytes
        
        # Combine all sections
        response = (transaction_id + flags + questions + answers + 
                   authority + additional + question + answer)
        
        return response
    
    def _handle_dns_query(self, data: bytes, addr: tuple) -> bytes:
        """Handle a single DNS query"""
        try:
            # Extract hostname from query
            hostname = ""
            pos = 12  # Skip DNS header
            while pos < len(data) and data[pos] != 0:
                length = data[pos]
                if length == 0:
                    break
                pos += 1
                if pos + length <= len(data):
                    hostname += data[pos:pos + length].decode('utf-8') + "."
                    pos += length
                else:
                    break
            
            # Remove trailing dot
            if hostname.endswith('.'):
                hostname = hostname[:-1]
            
            # Remove .local suffix if present
            if hostname.endswith('.local'):
                hostname = hostname[:-6]
            
            print(f"DNS query for: {hostname}")
            
            # Resolve hostname
            ip = self.resolve_hostname(hostname)
            
            if ip:
                print(f"Resolved {hostname} -> {ip}")
                return self._create_dns_response(data, ip)
            else:
                print(f"Could not resolve {hostname}")
                # Return NXDOMAIN response
                transaction_id = data[:2]
                flags = b'\x81\x83'  # NXDOMAIN
                questions = data[4:6]
                answers = b'\x00\x00'
                authority = b'\x00\x00'
                additional = b'\x00\x00'
                question = data[12:]
                return transaction_id + flags + questions + answers + authority + additional + question
                
        except Exception as e:
            print(f"Error handling DNS query: {e}")
            # Return SERVFAIL
            transaction_id = data[:2]
            flags = b'\x81\x82'  # SERVFAIL
            questions = data[4:6]
            answers = b'\x00\x00'
            authority = b'\x00\x00'
            additional = b'\x00\x00'
            question = data[12:]
            return transaction_id + flags + questions + answers + authority + additional + question
    
    def start(self):
        """Start the DNS server"""
        self.running = True
        
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            sock.bind(('0.0.0.0', self.port))
            print(f"DNS server listening on port {self.port}")
            
            while self.running:
                try:
                    data, addr = sock.recvfrom(512)
                    response = self._handle_dns_query(data, addr)
                    sock.sendto(response, addr)
                except Exception as e:
                    print(f"Error in DNS server: {e}")
                    continue
                    
        except Exception as e:
            print(f"Failed to start DNS server: {e}")
        finally:
            sock.close()
    
    def stop(self):
        """Stop the DNS server"""
        self.running = False


# Global DNS resolver instance
dns_resolver = DNSResolver()


def start_dns_server():
    """Start the DNS server in a separate thread"""
    dns_thread = threading.Thread(target=dns_resolver.start, daemon=True)
    dns_thread.start()
    print("DNS server thread started")
