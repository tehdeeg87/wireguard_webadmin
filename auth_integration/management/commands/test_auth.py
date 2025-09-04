"""
Django management command to test OAuth2 and JWT authentication flow.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from auth_integration.oauth2_client import oauth2_client
from auth_integration.jwt_service import jwt_service
import json


class Command(BaseCommand):
    help = 'Test OAuth2 and JWT authentication flow with portbro.com'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-refresh',
            action='store_true',
            help='Force refresh JWT token',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear JWT token cache',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Testing OAuth2 and JWT authentication flow...')
        )
        
        # Test OAuth2 configuration
        self.stdout.write('\n1. Checking OAuth2 configuration...')
        if not settings.PORTBRO_CLIENT_ID or not settings.PORTBRO_CLIENT_SECRET:
            self.stdout.write(
                self.style.ERROR('OAuth2 credentials not configured!')
            )
            return
        
        self.stdout.write(f'Client ID: {settings.PORTBRO_CLIENT_ID[:10]}...')
        self.stdout.write(f'Token URL: {settings.PORTBRO_TOKEN_URL}')
        self.stdout.write(f'VPN Auth URL: {settings.PORTBRO_VPN_AUTH_URL}')
        
        # Clear cache if requested
        if options['clear_cache']:
            self.stdout.write('\n2. Clearing JWT token cache...')
            jwt_service.clear_cache()
            self.stdout.write(self.style.SUCCESS('Cache cleared'))
        
        # Test OAuth2 token retrieval
        self.stdout.write('\n3. Testing OAuth2 token retrieval...')
        oauth2_token = oauth2_client.get_oauth2_token()
        if oauth2_token:
            self.stdout.write(
                self.style.SUCCESS(f'OAuth2 token obtained: {oauth2_token[:20]}...')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Failed to obtain OAuth2 token')
            )
            return
        
        # Test JWT token retrieval
        self.stdout.write('\n4. Testing JWT token retrieval...')
        jwt_token = oauth2_client.get_jwt_token(oauth2_token)
        if jwt_token:
            self.stdout.write(
                self.style.SUCCESS(f'JWT token obtained: {jwt_token[:20]}...')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Failed to obtain JWT token')
            )
            return
        
        # Test JWT service
        self.stdout.write('\n5. Testing JWT service...')
        force_refresh = options['force_refresh']
        service_jwt_token = jwt_service.get_jwt_token(force_refresh=force_refresh)
        
        if service_jwt_token:
            self.stdout.write(
                self.style.SUCCESS(f'JWT service token: {service_jwt_token[:20]}...')
            )
            
            # Validate token
            token_info = jwt_service.validate_and_get_token_info(service_jwt_token)
            if token_info:
                self.stdout.write('Token validation successful!')
                self.stdout.write(f'Issuer: {token_info.get("iss", "N/A")}')
                self.stdout.write(f'Audience: {token_info.get("aud", "N/A")}')
                self.stdout.write(f'Subject: {token_info.get("sub", "N/A")}')
                self.stdout.write(f'Expires: {token_info.get("exp", "N/A")}')
            else:
                self.stdout.write(
                    self.style.ERROR('Token validation failed')
                )
        else:
            self.stdout.write(
                self.style.ERROR('JWT service failed to obtain token')
            )
        
        # Test caching
        self.stdout.write('\n6. Testing token caching...')
        cached_token = jwt_service.get_cached_jwt_token()
        if cached_token:
            self.stdout.write(
                self.style.SUCCESS(f'Cached token available: {cached_token[:20]}...')
            )
        else:
            self.stdout.write('No cached token available')
        
        self.stdout.write('\n' + self.style.SUCCESS('Authentication flow test completed!'))

