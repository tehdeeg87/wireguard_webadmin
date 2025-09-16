from django.core.management.base import BaseCommand
from django.conf import settings
from dns.functions import generate_dnsmasq_config


class Command(BaseCommand):
    help = 'Update DNS configuration with peer hostnames'

    def handle(self, *args, **options):
        try:
            dnsmasq_config = generate_dnsmasq_config()
            with open(settings.DNS_CONFIG_FILE, 'w') as f:
                f.write(dnsmasq_config)
            self.stdout.write(
                self.style.SUCCESS('Successfully updated DNS configuration with peer hostnames')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating DNS configuration: {e}')
            )
