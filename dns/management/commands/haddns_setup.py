from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from dns.models import HADDNSConfig, PeerHostnameMapping
from wireguard.models import Peer


class Command(BaseCommand):
    help = 'Set up HADDNS for existing WireGuard peers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force setup even if HADDNS is already configured'
        )
        parser.add_argument(
            '--domain',
            type=str,
            default='vpn.local',
            help='Domain suffix for peer hostnames (default: vpn.local)'
        )
        parser.add_argument(
            '--threshold',
            type=int,
            default=300,
            help='Handshake threshold in seconds (default: 300)'
        )

    def handle(self, *args, **options):
        try:
            # Initialize HADDNS configuration
            config = HADDNSConfig.get_config()
            
            if config.enabled and not options['force']:
                self.stdout.write(
                    self.style.WARNING('HADDNS is already configured. Use --force to reconfigure.')
                )
                return

            # Update configuration
            config.enabled = True
            config.domain_suffix = options['domain']
            config.handshake_threshold_seconds = options['threshold']
            config.save()

            self.stdout.write(
                self.style.SUCCESS(f'HADDNS configuration updated: {config}')
            )

            # Create hostname mappings for existing peers
            created_count = 0
            updated_count = 0

            with transaction.atomic():
                for peer in Peer.objects.all():
                    if not peer.hostname:
                        self.stdout.write(
                            self.style.WARNING(f'Skipping peer {peer.public_key[:16]}... (no hostname)')
                        )
                        continue

                    mapping, created = PeerHostnameMapping.objects.get_or_create(
                        peer=peer,
                        defaults={
                            'hostname': peer.hostname,
                            'enabled': True
                        }
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(f'Created mapping: {mapping.hostname} -> {peer.public_key[:16]}...')
                    else:
                        # Update existing mapping
                        mapping.hostname = peer.hostname
                        mapping.enabled = True
                        mapping.save()
                        updated_count += 1
                        self.stdout.write(f'Updated mapping: {mapping.hostname} -> {peer.public_key[:16]}...')

            self.stdout.write(
                self.style.SUCCESS(
                    f'HADDNS setup complete: {created_count} created, {updated_count} updated'
                )
            )

            # Show next steps
            self.stdout.write('\nNext steps:')
            self.stdout.write('1. Run: python manage.py haddns_update --dry-run')
            self.stdout.write('2. Set up cron job: */1 * * * * python manage.py haddns_update')
            self.stdout.write('3. Regenerate dnsmasq config: python manage.py generate_dnsmasq_config')
            self.stdout.write('4. Restart dnsmasq service')

        except Exception as e:
            raise CommandError(f'HADDNS setup failed: {e}')
