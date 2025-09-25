#!/usr/bin/env python
"""
Apply DNS configuration to Docker environment
This script will generate the DNS config and apply it to the Docker volume
"""
import os
import docker
import tempfile
from dns.functions import generate_dnsmasq_config

def apply_dns_config_to_docker():
    """Apply DNS configuration to Docker dnsmasq container"""
    try:
        # Generate DNS configuration
        print("=== Generating DNS Configuration ===")
        dns_config = generate_dnsmasq_config()
        print("DNS configuration generated successfully!")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.conf') as f:
            f.write(dns_config)
            temp_file = f.name
        
        print(f"Configuration saved to: {temp_file}")
        print("\nConfiguration content:")
        print(dns_config)
        
        # Connect to Docker
        client = docker.from_env()
        
        # Check if dnsmasq container is running
        try:
            dns_container = client.containers.get('wireguard-webadmin-dns')
            if dns_container.status != 'running':
                print("DNS container is not running. Starting it...")
                dns_container.start()
        except docker.errors.NotFound:
            print("DNS container not found. Please run 'docker-compose up -d' first.")
            return
        
        # Copy configuration to container
        print("\n=== Applying Configuration to Docker Container ===")
        with open(temp_file, 'rb') as f:
            dns_container.put_archive('/etc/dnsmasq/', f.read())
        
        print("Configuration applied successfully!")
        print("The dnsmasq container will automatically reload with the new configuration.")
        
        # Clean up
        os.unlink(temp_file)
        
        print("\n=== Testing DNS Resolution ===")
        print("You can now test DNS resolution from your VPN clients:")
        print("  nslookup phone")
        print("  nslookup laptop")
        print("  ping phone")
        print("  ping laptop")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Docker is running and the containers are up.")

if __name__ == "__main__":
    apply_dns_config_to_docker()
