"""
Django management command to update mDNS configuration
Usage: python manage.py update_peer_mdns [--reload]
"""

from django.core.management.base import BaseCommand
from mdns.functions import generate_all_mdns_hosts_files, reload_avahi_daemon


class Command(BaseCommand):
    help = 'Update mDNS configuration for WireGuard peer discovery'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reload',
            action='store_true',
            help='Reload Avahi daemon after updating configuration',
        )

    def handle(self, *args, **options):
        self.stdout.write('Updating mDNS configuration...')
        
        # Generate hosts files for all instances
        success_count = generate_all_mdns_hosts_files()
        
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated mDNS configuration for {success_count} instances')
            )
        else:
            self.stdout.write(
                self.style.WARNING('No instances found or error occurred')
            )
        
        # Reload Avahi daemon if requested
        if options['reload']:
            if reload_avahi_daemon():
                self.stdout.write(
                    self.style.SUCCESS('Avahi daemon reloaded successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to reload Avahi daemon')
                )
        
        self.stdout.write('mDNS configuration update completed')
