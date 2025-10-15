"""
Django management command to update DNS configuration
Usage: python manage.py update_dns [--reload] [--status]
"""

from django.core.management.base import BaseCommand, CommandError
from wireguard.dns_utils import write_dnsmasq_hosts_file, reload_dnsmasq, get_dns_status


class Command(BaseCommand):
    help = 'Update DNS configuration for WireGuard peers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reload',
            action='store_true',
            help='Reload dnsmasq after updating hosts file',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show current DNS status without making changes',
        )

    def handle(self, *args, **options):
        if options['status']:
            self.show_status()
            return

        self.stdout.write('Updating DNS configuration...')
        
        try:
            # Write the hosts file
            if write_dnsmasq_hosts_file():
                self.stdout.write(
                    self.style.SUCCESS('Successfully updated DNS hosts file')
                )
                
                # Reload dnsmasq if requested
                if options['reload']:
                    if reload_dnsmasq():
                        self.stdout.write(
                            self.style.SUCCESS('Successfully reloaded dnsmasq')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING('DNS hosts file updated but dnsmasq reload failed')
                        )
            else:
                raise CommandError('Failed to update DNS hosts file')
                
        except Exception as e:
            raise CommandError(f'Error updating DNS: {e}')

    def show_status(self):
        """Display current DNS configuration status"""
        self.stdout.write('DNS Configuration Status:')
        self.stdout.write('=' * 30)
        
        status = get_dns_status()
        
        self.stdout.write(f"Hosts file path: {status['hosts_file_path']}")
        self.stdout.write(f"Hosts file exists: {'Yes' if status['hosts_file_exists'] else 'No'}")
        self.stdout.write(f"Domain: {status['domain']}")
        self.stdout.write(f"Total peers: {status['peer_count']}")
        self.stdout.write(f"Peers with hostnames: {status['peers_with_hostnames']}")
        
        if status['hosts_file_exists']:
            if 'hosts_file_lines' in status:
                self.stdout.write(f"Hosts file entries: {status['hosts_file_lines']}")
            if 'hosts_file_error' in status:
                self.stdout.write(
                    self.style.ERROR(f"Error reading hosts file: {status['hosts_file_error']}")
                )
        else:
            self.stdout.write(
                self.style.WARNING('Hosts file does not exist - run update_dns to create it')
            )
