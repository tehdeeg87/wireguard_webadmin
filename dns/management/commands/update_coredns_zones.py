import os
import ipaddress
from django.core.management.base import BaseCommand
from django.conf import settings
from wireguard.models import Peer, WireGuardInstance
from dns.models import DNSSettings


class Command(BaseCommand):
    help = 'Update CoreDNS zone files with current peer and instance data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--zone',
            type=str,
            choices=['peers', 'instances', 'all'],
            default='all',
            help='Which zone to update (peers, instances, or all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        zone = options['zone']
        dry_run = options['dry_run']
        
        if zone in ['peers', 'all']:
            self.update_peers_zone(dry_run)
        
        if zone in ['instances', 'all']:
            self.update_instances_zone(dry_run)
        
        self.stdout.write(
            self.style.SUCCESS('CoreDNS zones updated successfully!')
        )

    def update_peers_zone(self, dry_run=False):
        """Update the peers zone file with current peer data"""
        zone_file = os.path.join(settings.BASE_DIR, 'containers', 'coredns', 'zones', 'peers.db')
        
        # Get all peers with their allowed IPs
        peers = Peer.objects.select_related('wireguard_instance').prefetch_related('peerallowedip_set').all()
        
        zone_content = self.generate_peers_zone_content(peers)
        
        if dry_run:
            self.stdout.write("Peers zone content:")
            self.stdout.write(zone_content)
        else:
            with open(zone_file, 'w') as f:
                f.write(zone_content)
            self.stdout.write(f"Updated peers zone file: {zone_file}")

    def update_instances_zone(self, dry_run=False):
        """Update the instances zone file with current instance data"""
        zone_file = os.path.join(settings.BASE_DIR, 'containers', 'coredns', 'zones', 'instances.db')
        
        # Get all WireGuard instances
        instances = WireGuardInstance.objects.all()
        
        zone_content = self.generate_instances_zone_content(instances)
        
        if dry_run:
            self.stdout.write("Instances zone content:")
            self.stdout.write(zone_content)
        else:
            with open(zone_file, 'w') as f:
                f.write(zone_content)
            self.stdout.write(f"Updated instances zone file: {zone_file}")

    def generate_peers_zone_content(self, peers):
        """Generate zone file content for peers"""
        content = [
            "; CoreDNS zone file for WireGuard peer hostnames",
            "; This file is automatically updated when peers are created/modified",
            "; Format: peer-name.wg.local -> IP address",
            "",
            "$TTL 300",
            "@   IN  SOA wg.local. admin.wg.local. (",
            "    2024092601  ; Serial number (YYYYMMDDNN)",
            "    3600        ; Refresh",
            "    1800        ; Retry",
            "    604800      ; Expire",
            "    300         ; Minimum TTL",
            ")",
            "",
            "; NS records",
            "@   IN  NS  wg.local.",
            "",
            "; A records for peers",
            "; These are dynamically updated by the Django application",
            ""
        ]
        
        for peer in peers:
            # Get the primary allowed IP for this peer
            allowed_ips = peer.peerallowedip_set.filter(config_file='server', priority=0)
            if allowed_ips.exists():
                ip = allowed_ips.first().allowed_ip
                
                # Create hostname from peer name or use default
                if peer.hostname:
                    hostname = peer.hostname.lower().replace(' ', '-')
                elif peer.name:
                    hostname = peer.name.lower().replace(' ', '-')
                else:
                    hostname = f"peer-{peer.pk}"
                
                # Add A record
                content.append(f"{hostname}.wg.local.    IN  A   {ip}")
                
                # Add reverse PTR record if possible
                try:
                    ip_obj = ipaddress.ip_address(ip)
                    if ip_obj.version == 4:
                        # Create reverse DNS entry
                        reverse_ip = '.'.join(reversed(ip.split('.')))
                        content.append(f"{reverse_ip}.in-addr.arpa.    IN  PTR   {hostname}.wg.local.")
                except ValueError:
                    pass
        
        return '\n'.join(content)

    def generate_instances_zone_content(self, instances):
        """Generate zone file content for instances"""
        content = [
            "; CoreDNS zone file for WireGuard instance hostnames",
            "; This file is automatically updated when instances are created/modified",
            "; Format: wg1.instances.wg.local -> IP address",
            "",
            "$TTL 300",
            "@   IN  SOA instances.wg.local. admin.instances.wg.local. (",
            "    2024092601  ; Serial number (YYYYMMDDNN)",
            "    3600        ; Refresh",
            "    1800        ; Retry",
            "    604800      ; Expire",
            "    300         ; Minimum TTL",
            ")",
            "",
            "; NS records",
            "@   IN  NS  instances.wg.local.",
            "",
            "; A records for WireGuard instances",
            "; These are dynamically updated by the Django application",
            ""
        ]
        
        for instance in instances:
            # Create instance hostname
            hostname = f"wg{instance.instance_id}"
            content.append(f"{hostname}.instances.wg.local.    IN  A   {instance.address}")
        
        return '\n'.join(content)
