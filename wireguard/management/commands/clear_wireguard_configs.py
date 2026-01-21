"""
Management command to clear all WireGuard configuration files.
Useful when database is cleared and you want to start fresh.
"""
import os
import glob
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Clear all WireGuard configuration files from /etc/wireguard/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        config_dir = "/etc/wireguard"
        dry_run = options['dry_run']
        
        if not os.path.exists(config_dir):
            self.stdout.write(
                self.style.WARNING(f"Config directory {config_dir} does not exist. This might be a development environment.")
            )
            return
        
        # Find all .conf files
        config_files = glob.glob(os.path.join(config_dir, "*.conf"))
        
        if not config_files:
            self.stdout.write(self.style.SUCCESS("No WireGuard config files found to delete."))
            return
        
        self.stdout.write(f"Found {len(config_files)} WireGuard config file(s):")
        for config_file in config_files:
            self.stdout.write(f"  - {config_file}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN: Would delete the above files."))
            return
        
        # Delete the files
        deleted_count = 0
        for config_file in config_files:
            try:
                os.remove(config_file)
                self.stdout.write(self.style.SUCCESS(f"Deleted: {config_file}"))
                deleted_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error deleting {config_file}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"\nSuccessfully deleted {deleted_count} config file(s).")
        )
