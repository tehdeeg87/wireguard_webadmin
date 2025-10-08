#!/usr/bin/env python3
"""
Simple mDNS server for WireGuard peer discovery
This runs as a background service to advertise peer hostnames
"""

import socket
import threading
import time
import json
import os
from typing import Dict, List

class SimpleMDNSServer:
    def __init__(self, port=5353):
        self.port = port
        self.services = {}
        self.running = False
        self.socket = None
        self.hosts_file = "/etc/avahi/hosts/wg0.hosts"
        
    def start(self):
        """Start the mDNS server"""
        try:
            # Create socket for mDNS
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', self.port))
            self.socket.settimeout(1.0)
            self.running = True
            
            print(f"Simple mDNS server started on port {self.port}")
            
            # Start listener thread
            listener_thread = threading.Thread(target=self._listen)
            listener_thread.daemon = True
            listener_thread.start()
            
            # Start hosts file monitor
            monitor_thread = threading.Thread(target=self._monitor_hosts_file)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            return True
        except Exception as e:
            print(f"Failed to start mDNS server: {e}")
            return False
    
    def stop(self):
        """Stop the mDNS server"""
        self.running = False
        if self.socket:
            self.socket.close()
    
    def _listen(self):
        """Listen for mDNS queries"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(1024)
                self._handle_query(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error in mDNS listener: {e}")
    
    def _handle_query(self, data, addr):
        """Handle incoming mDNS queries"""
        try:
            # Simple query handling - respond with our services
            query = data.decode('utf-8', errors='ignore')
            if any(hostname in query.lower() for hostname in self.services.keys()):
                response = self._create_response()
                self.socket.sendto(response.encode('utf-8'), addr)
        except Exception as e:
            print(f"Error handling query: {e}")
    
    def _create_response(self):
        """Create mDNS response"""
        response = []
        for name, info in self.services.items():
            response.append(f"{name} A {info['ip']}")
        return "\n".join(response)
    
    def _monitor_hosts_file(self):
        """Monitor hosts file for changes"""
        last_modified = 0
        while self.running:
            try:
                if os.path.exists(self.hosts_file):
                    current_modified = os.path.getmtime(self.hosts_file)
                    if current_modified > last_modified:
                        self._load_hosts_file()
                        last_modified = current_modified
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                print(f"Error monitoring hosts file: {e}")
                time.sleep(10)
    
    def _load_hosts_file(self):
        """Load services from hosts file"""
        try:
            if os.path.exists(self.hosts_file):
                with open(self.hosts_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and ' ' in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                ip = parts[0]
                                hostname = parts[1]
                                self.services[hostname] = {'ip': ip, 'port': 0}
                print(f"Loaded {len(self.services)} services from hosts file")
        except Exception as e:
            print(f"Error loading hosts file: {e}")
    
    def register_service(self, name: str, ip: str, port: int = 0):
        """Register a service with mDNS"""
        self.services[name] = {
            'ip': ip,
            'port': port,
            'timestamp': time.time()
        }
        print(f"Registered service: {name} -> {ip}")
    
    def unregister_service(self, name: str):
        """Unregister a service"""
        if name in self.services:
            del self.services[name]
            print(f"Unregistered service: {name}")
    
    def list_services(self):
        """List all registered services"""
        return self.services.copy()

def main():
    """Run the mDNS server"""
    mdns = SimpleMDNSServer()
    
    if mdns.start():
        print("mDNS server running... Press Ctrl+C to stop")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping mDNS server...")
            mdns.stop()
    else:
        print("Failed to start mDNS server")

if __name__ == "__main__":
    main()
