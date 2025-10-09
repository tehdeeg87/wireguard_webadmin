"""
Django management command to register WireGuard peers with Avahi for hostname resolution
Usage: python manage.py register_peers_avahi [--reload] [--instance-id ID]
"""

import os
import subprocess
from django.core.management.base import BaseCommand
from wireguard.models import Peer, WireGuardInstance, PeerAllowedIP
from mdns.functions import generate_all_mdns_hosts_files, reload_avahi_daemon


class Command(BaseCommand):
    help = 'Register WireGuard peers with Avahi for hostname resolution using hosts files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reload',
            action='store_true',
            help='Reload Avahi daemon after registration',
        )
        parser.add_argument(
            '--instance-id',
            type=int,
            help='Register peers for specific instance only',
        )

    def handle(self, *args, **options):
        self.stdout.write('Registering peers with Avahi using hosts files...')
        
        # Generate hosts files for all instances or specific instance
        if options['instance_id']:
            try:
                instance = WireGuardInstance.objects.get(instance_id=options['instance_id'])
                from mdns.functions import generate_mdns_hosts_file
                success = generate_mdns_hosts_file(instance.instance_id)
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully generated hosts file for instance wg{options["instance_id"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to generate hosts file for instance wg{options["instance_id"]}')
                    )
            except WireGuardInstance.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Instance wg{options["instance_id"]} not found')
                )
                return
        else:
            # Generate hosts files for all instances
            success_count = generate_all_mdns_hosts_files()
            if success_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully generated hosts files for {success_count} instances')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('No instances found or error occurred')
                )
        
        # Reload Avahi daemon if requested
        if options['reload']:
            self.stdout.write('Reloading Avahi daemon...')
            if reload_avahi_daemon():
                self.stdout.write(
                    self.style.SUCCESS('Avahi daemon reloaded successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to reload Avahi daemon')
                )
        
        self.stdout.write('Avahi peer registration completed')
