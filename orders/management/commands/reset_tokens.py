"""
Django management command to reset PaymentToken records for testing.
"""
from django.core.management.base import BaseCommand
from orders.models import PaymentToken


class Command(BaseCommand):
    help = 'Reset PaymentToken records for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Reset tokens for specific email address',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Reset all tokens',
        )

    def handle(self, *args, **options):
        if options['all']:
            # Reset all tokens
            count = PaymentToken.objects.count()
            PaymentToken.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {count} PaymentToken records')
            )
        elif options['email']:
            # Reset tokens for specific email
            email = options['email']
            tokens = PaymentToken.objects.filter(email=email)
            count = tokens.count()
            tokens.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {count} PaymentToken records for {email}')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --email or --all')
            )
