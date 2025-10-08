#!/usr/bin/env python3
"""
Simple mDNS-like peer discovery using Python
This provides basic mDNS functionality without complex container setup
"""

import socket
import time
import threading
import json
from typing import Dict, List

class SimpleMDNS:
    def __init__(self, port=5353):
        self.port = port
        self.services = {}
        self.running = False
        self.socket = None
        
    def start(self):
        """Start the mDNS service"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', self.port))
            self.socket.settimeout(1.0)
            self.running = True
            
            print(f"Simple mDNS started on port {self.port}")
            
            # Start listener thread
            listener_thread = threading.Thread(target=self._listen)
            listener_thread.daemon = True
            listener_thread.start()
            
            return True
        except Exception as e:
            print(f"Failed to start mDNS: {e}")
            return False
    
    def stop(self):
        """Stop the mDNS service"""
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
            if 'laptop' in query.lower() or 'peer' in query.lower():
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
    """Test the simple mDNS implementation"""
    mdns = SimpleMDNS()
    
    if mdns.start():
        # Register some test services
        mdns.register_service("laptop.wg0.local", "10.188.0.2")
        mdns.register_service("server.wg0.local", "10.188.0.1")
        mdns.register_service("phone.wg1.local", "10.188.1.2")
        
        print("Services registered:")
        for name, info in mdns.list_services().items():
            print(f"  {name} -> {info['ip']}")
        
        try:
            print("mDNS service running... Press Ctrl+C to stop")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping mDNS service...")
            mdns.stop()
    else:
        print("Failed to start mDNS service")

if __name__ == "__main__":
    main()
