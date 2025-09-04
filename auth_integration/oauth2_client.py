"""
OAuth2 client for authenticating with portbro.com and obtaining JWT tokens.
"""
import requests
import json
from django.conf import settings
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PortbroOAuth2Client:
    """
    OAuth2 client for portbro.com authentication.
    Handles client credentials flow to obtain JWT tokens for VPN operations.
    """
    
    def __init__(self):
        self.client_id = getattr(settings, 'PORTBRO_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'PORTBRO_CLIENT_SECRET', None)
        self.token_url = getattr(settings, 'PORTBRO_TOKEN_URL', 'https://portbro.com/o/token/')
        self.vpn_auth_url = getattr(settings, 'PORTBRO_VPN_AUTH_URL', 'https://portbro.com/vpn/auth/')
        self.scope = getattr(settings, 'PORTBRO_SCOPE', 'read')
        
        if not self.client_id or not self.client_secret:
            logger.warning("Portbro OAuth2 credentials not configured")
    
    def get_oauth2_token(self) -> Optional[str]:
        """
        Get OAuth2 access token using client credentials flow.
        
        Returns:
            OAuth2 access token or None if failed
        """
        if not self.client_id or not self.client_secret:
            logger.error("OAuth2 credentials not configured")
            return None
            
        try:
            response = requests.post(
                self.token_url,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={
                    'grant_type': 'client_credentials',
                    'scope': self.scope
                },
                auth=(self.client_id, self.client_secret),
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')
            else:
                logger.error(f"OAuth2 token request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"OAuth2 token request error: {e}")
            return None
    
    def get_jwt_token(self, oauth2_token: str) -> Optional[str]:
        """
        Get JWT token for VPN authentication using OAuth2 token.
        
        Args:
            oauth2_token: OAuth2 access token
            
        Returns:
            JWT token or None if failed
        """
        try:
            response = requests.post(
                self.vpn_auth_url,
                headers={
                    'Authorization': f'Bearer {oauth2_token}',
                    'Content-Type': 'application/json'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                jwt_data = response.json()
                return jwt_data.get('access_token')
            else:
                logger.error(f"JWT token request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"JWT token request error: {e}")
            return None
    
    def get_vpn_jwt_token(self) -> Optional[str]:
        """
        Complete flow: Get OAuth2 token, then get JWT token for VPN operations.
        
        Returns:
            JWT token for VPN operations or None if failed
        """
        oauth2_token = self.get_oauth2_token()
        if not oauth2_token:
            return None
            
        return self.get_jwt_token(oauth2_token)
    
    def validate_jwt_token(self, jwt_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token by checking its structure and claims.
        This is a basic validation - full validation should be done by the middleware.
        
        Args:
            jwt_token: JWT token to validate
            
        Returns:
            Token claims if valid, None if invalid
        """
        try:
            import jwt as pyjwt
            # Decode without verification to check structure
            decoded = pyjwt.decode(jwt_token, options={"verify_signature": False})
            return decoded
        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            return None


# Global instance
oauth2_client = PortbroOAuth2Client()

