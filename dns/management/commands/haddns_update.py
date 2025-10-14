import subprocess
import json
import time
import os
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings

from dns.models import HADDNSConfig, PeerHostnameMapping
from wireguard.models import Peer, PeerAllowedIP, WireGuardInstance, PeerStatus

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update HADDNS (Handshake-Aware Dynamic DNS) records based on WireGuard handshakes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interface',
            type=str,
            default='all',
            help='WireGuard interface to check (default: all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        try:
            # Get HADDNS configuration
            config = HADDNSConfig.get_config()
            
            if not config.enabled:
                self.stdout.write(
                    self.style.WARNING('HADDNS is disabled in configuration')
                )
                return

            if options['verbose']:
                self.stdout.write(f"HADDNS Config: {config}")
                self.stdout.write(f"Handshake threshold: {config.handshake_threshold_seconds}s")
                self.stdout.write(f"Domain suffix: {config.domain_suffix}")

            # Get handshake data from WireGuard
            handshake_data = self.get_handshake_data(options['interface'])
            
            if not handshake_data:
                self.stdout.write(
                    self.style.WARNING('No handshake data found')
                )
                return

            # Update peer status and generate DNS records
            active_records = self.update_peer_status_and_generate_records(
                handshake_data, 
                config, 
                options['verbose']
            )

            # Write dynamic hosts file
            if not options['dry_run']:
                self.write_dynamic_hosts_file(active_records, config)
                self.reload_dnsmasq()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated {len(active_records)} DNS records')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'DRY RUN: Would update {len(active_records)} DNS records')
                )
                for record in active_records:
                    self.stdout.write(f"  {record}")

        except Exception as e:
            logger.error(f"HADDNS update failed: {e}")
            raise CommandError(f'HADDNS update failed: {e}')

    def get_handshake_data(self, interface):
        """Get handshake data from WireGuard"""
        try:
            if interface == 'all':
                command = "wg show all latest-handshakes"
            else:
                command = f"wg show {interface} latest-handshakes"
            
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"WireGuard command failed: {result.stderr}")
                return {}

            handshakes = {}
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        interface_name, peer_key, timestamp = parts[0], parts[1], parts[2]
                        handshakes[peer_key.strip()] = {
                            'interface': interface_name.strip(),
                            'timestamp': int(timestamp.strip())
                        }
            
            return handshakes
            
        except subprocess.TimeoutExpired:
            logger.error("WireGuard command timed out")
            return {}
        except Exception as e:
            logger.error(f"Error getting handshake data: {e}")
            return {}

    def update_peer_status_and_generate_records(self, handshake_data, config, verbose=False):
        """Update peer status and generate DNS records"""
        active_records = []
        now = timezone.now()
        threshold_time = now - timedelta(seconds=config.handshake_threshold_seconds)
        
        # Get all peer mappings
        mappings = PeerHostnameMapping.objects.filter(enabled=True).select_related('peer')
        
        for mapping in mappings:
            peer = mapping.peer
            peer_key = peer.public_key
            
            # Check if peer has recent handshake
            handshake_info = handshake_data.get(peer_key)
            is_online = False
            
            if handshake_info and handshake_info['timestamp'] > 0:
                handshake_time = datetime.fromtimestamp(
                    handshake_info['timestamp'], 
                    tz=timezone.utc
                )
                is_online = handshake_time > threshold_time
                
                if verbose:
                    status = "ONLINE" if is_online else "OFFLINE"
                    self.stdout.write(
                        f"Peer {peer.name or peer_key[:16]}: {status} "
                        f"(last handshake: {handshake_time})"
                    )
            
            # Update mapping status
            mapping.is_online = is_online
            mapping.last_handshake_check = now
            mapping.save()
            
            # Get peer's IP address
            peer_ip = PeerAllowedIP.objects.filter(
                peer=peer,
                config_file='server',
                priority=0
            ).first()
            
            if not peer_ip:
                if verbose:
                    self.stdout.write(
                        self.style.WARNING(f"No IP found for peer {peer.name or peer_key[:16]}")
                    )
                continue
            
            # Generate DNS records
            if is_online:
                # Online peer - add normal hostname
                active_records.append(f"{peer_ip.allowed_ip}\t{mapping.full_hostname}")
                
                # Add instance-specific hostname if peer has instance
                if peer.wireguard_instance:
                    instance_name = peer.wireguard_instance.name or f"wg{peer.wireguard_instance.instance_id}"
                    active_records.append(f"{peer_ip.allowed_ip}\t{mapping.hostname}.{instance_name}.{config.domain_suffix}")
                
            elif config.include_offline_peers:
                # Offline peer - add with offline suffix
                active_records.append(f"{peer_ip.allowed_ip}\t{mapping.offline_hostname}")
                
                # Add instance-specific offline hostname
                if peer.wireguard_instance:
                    instance_name = peer.wireguard_instance.name or f"wg{peer.wireguard_instance.instance_id}"
                    offline_instance_hostname = f"{mapping.hostname}{config.offline_suffix}.{instance_name}.{config.domain_suffix}"
                    active_records.append(f"{peer_ip.allowed_ip}\t{offline_instance_hostname}")
        
        return active_records

    def write_dynamic_hosts_file(self, active_records, config):
        """Write the dynamic hosts file for dnsmasq"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(config.dynamic_hosts_file), exist_ok=True)
            
            # Write hosts file
            with open(config.dynamic_hosts_file, 'w') as f:
                f.write("# HADDNS Dynamic Hosts File\n")
                f.write("# Generated automatically - do not edit manually\n")
                f.write(f"# Generated at: {timezone.now()}\n")
                f.write(f"# Total records: {len(active_records)}\n\n")
                
                for record in active_records:
                    f.write(f"{record}\n")
            
            logger.info(f"Wrote {len(active_records)} records to {config.dynamic_hosts_file}")
            
        except Exception as e:
            logger.error(f"Error writing dynamic hosts file: {e}")
            raise

    def reload_dnsmasq(self):
        """Reload dnsmasq configuration"""
        try:
            # Try to reload dnsmasq
            result = subprocess.run(
                ['systemctl', 'reload', 'dnsmasq'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info("dnsmasq reloaded successfully")
            else:
                # Fallback: try SIGHUP
                result = subprocess.run(
                    ['pkill', '-HUP', 'dnsmasq'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    logger.info("dnsmasq reloaded via SIGHUP")
                else:
                    logger.warning("Could not reload dnsmasq")
                    
        except Exception as e:
            logger.error(f"Error reloading dnsmasq: {e}")
            # Don't raise - this is not critical
