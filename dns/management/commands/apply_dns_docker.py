from django.core.management.base import BaseCommand
from django.conf import settings
from dns.functions import generate_dnsmasq_config
import docker
import tempfile
import os

class Command(BaseCommand):
    help = 'Apply DNS configuration to Docker dnsmasq container'

    def handle(self, *args, **options):
        try:
            # Generate DNS configuration
            self.stdout.write("Generating DNS configuration...")
            dns_config = generate_dnsmasq_config()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.conf') as f:
                f.write(dns_config)
                temp_file = f.name
            
            # Connect to Docker
            client = docker.from_env()
            
            # Check if dnsmasq container is running
            try:
                dns_container = client.containers.get('wireguard-webadmin-dns')
                if dns_container.status != 'running':
                    self.stdout.write("DNS container is not running. Starting it...")
                    dns_container.start()
            except docker.errors.NotFound:
                self.stdout.write(
                    self.style.ERROR("DNS container not found. Please run 'docker-compose up -d' first.")
                )
                return
            
            # Copy configuration to container
            self.stdout.write("Applying configuration to Docker container...")
            with open(temp_file, 'rb') as f:
                dns_container.put_archive('/etc/dnsmasq/', f.read())
            
            self.stdout.write(
                self.style.SUCCESS("DNS configuration applied successfully!")
            )
            self.stdout.write("The dnsmasq container will automatically reload with the new configuration.")
            
            # Clean up
            os.unlink(temp_file)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error applying DNS configuration: {e}")
            )
