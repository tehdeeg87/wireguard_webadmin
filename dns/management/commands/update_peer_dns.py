from django.core.management.base import BaseCommand
from django.conf import settings
from dns.functions import generate_dnsmasq_config, generate_per_instance_hosts_files, reload_dnsmasq


class Command(BaseCommand):
    help = 'Update DNS configuration with peer hostnames and per-instance hosts files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reload',
            action='store_true',
            help='Reload dnsmasq after updating configuration',
        )

    def handle(self, *args, **options):
        try:
            # Generate main dnsmasq configuration
            dnsmasq_config = generate_dnsmasq_config()
            with open(settings.DNS_CONFIG_FILE, 'w') as f:
                f.write(dnsmasq_config)
            self.stdout.write(
                self.style.SUCCESS('Successfully updated DNS configuration with peer hostnames')
            )
            
            # Generate per-instance hosts files
            generate_per_instance_hosts_files()
            self.stdout.write(
                self.style.SUCCESS('Successfully generated per-instance hosts files')
            )
            
            # Reload dnsmasq if requested
            if options['reload']:
                reload_dnsmasq()
                self.stdout.write(
                    self.style.SUCCESS('dnsmasq reloaded successfully')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating DNS configuration: {e}')
            )
