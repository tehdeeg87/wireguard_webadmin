import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from dns.functions import generate_dnsmasq_config


class Command(BaseCommand):
    help = 'Generate and write dnsmasq configuration file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='/etc/dnsmasq.d/wireguard_webadmin.conf',
            help='Output file path for dnsmasq configuration'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show configuration without writing to file'
        )

    def handle(self, *args, **options):
        try:
            # Generate dnsmasq configuration
            config_content = generate_dnsmasq_config()
            
            if options['dry_run']:
                self.stdout.write('Generated dnsmasq configuration:')
                self.stdout.write('=' * 50)
                self.stdout.write(config_content)
                self.stdout.write('=' * 50)
            else:
                # Write to file
                output_path = options['output']
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                with open(output_path, 'w') as f:
                    f.write(config_content)
                
                self.stdout.write(
                    self.style.SUCCESS(f'dnsmasq configuration written to {output_path}')
                )
                
                # Show file size
                file_size = os.path.getsize(output_path)
                self.stdout.write(f'File size: {file_size} bytes')

        except Exception as e:
            raise CommandError(f'Failed to generate dnsmasq configuration: {e}')
