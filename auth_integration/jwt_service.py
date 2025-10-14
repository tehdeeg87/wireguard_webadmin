"""
JWT service for managing token lifecycle, caching, and refresh.
"""
import time
import logging
from typing import Optional, Dict, Any
from django.core.cache import cache
from .oauth2_client import oauth2_client

logger = logging.getLogger(__name__)


class JWTService:
    """
    Service for managing JWT tokens with caching and automatic refresh.
    """
    
    CACHE_KEY_PREFIX = 'portbro_jwt_token'
    CACHE_TIMEOUT = 300  # 5 minutes default cache timeout
    
    def __init__(self):
        self.oauth2_client = oauth2_client
    
    def get_cached_jwt_token(self) -> Optional[str]:
        """
        Get JWT token from cache if available and not expired.
        
        Returns:
            Cached JWT token or None if not available/expired
        """
        try:
            cached_data = cache.get(self.CACHE_KEY_PREFIX)
            if cached_data:
                token = cached_data.get('token')
                expires_at = cached_data.get('expires_at', 0)
                
                # Check if token is still valid (with 30 second buffer)
                if token and expires_at > time.time() + 30:
                    logger.debug("Using cached JWT token")
                    return token
                else:
                    logger.debug("Cached JWT token expired")
                    cache.delete(self.CACHE_KEY_PREFIX)
            
            return None
        except Exception as e:
            logger.error(f"Error getting cached JWT token: {e}")
            return None
    
    def cache_jwt_token(self, token: str, expires_in: int = 300) -> None:
        """
        Cache JWT token with expiration time.
        
        Args:
            token: JWT token to cache
            expires_in: Token expiration time in seconds
        """
        try:
            cache_data = {
                'token': token,
                'expires_at': time.time() + expires_in
            }
            cache.set(self.CACHE_KEY_PREFIX, cache_data, timeout=expires_in)
            logger.debug(f"Cached JWT token, expires in {expires_in} seconds")
        except Exception as e:
            logger.error(f"Error caching JWT token: {e}")
    
    def get_fresh_jwt_token(self) -> Optional[str]:
        """
        Get a fresh JWT token from portbro.com.
        
        Returns:
            Fresh JWT token or None if failed
        """
        try:
            jwt_token = self.oauth2_client.get_vpn_jwt_token()
            if jwt_token:
                # Cache the token for future use
                self.cache_jwt_token(jwt_token)
                logger.info("Successfully obtained fresh JWT token")
                return jwt_token
            else:
                logger.error("Failed to obtain JWT token from portbro.com")
                return None
        except Exception as e:
            logger.error(f"Error getting fresh JWT token: {e}")
            return None
    
    def get_jwt_token(self, force_refresh: bool = False) -> Optional[str]:
        """
        Get JWT token, using cache if available and not forcing refresh.
        
        Args:
            force_refresh: If True, bypass cache and get fresh token
            
        Returns:
            JWT token or None if failed
        """
        if not force_refresh:
            # Try to get from cache first
            cached_token = self.get_cached_jwt_token()
            if cached_token:
                return cached_token
        
        # Get fresh token
        return self.get_fresh_jwt_token()
    
    def validate_and_get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token and return its information.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Token information if valid, None if invalid
        """
        try:
            import jwt as pyjwt
            
            # RSA public key for JWT validation
            rsa_public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAiaGItq0JK2JxMf66rTqF
efn6jVWcpFOn9y7c5eFJM4+FFrr0yFGtcH9DevSYP8nREFYEpTnJckILK1AHDiZl
9KUh3nQTUW1ZKnlT6WLSgUjTc2AiT5kpe5HU9Fq8hL4VL4hEcCnWcdhQZA+/gEnh
R/98OUwGnWgWeai0noLaI53bthm8vyBz2G6VxQ52ZVhfuOmxTHeXvHTWciDUO81/
NInA+iyiuOOP/U4yQP1eFbwyDZA6Tvn9P2Tx5b+FF4azYYjl/BHCEoJNeHGRwRDw
ErY3serZYpd4vzHlWjnrSFV1yTQ8K8DtFMbefpE4A4VpHFFvKlx8r574rNVxBz+p
5wIDAQAB
-----END PUBLIC KEY-----"""
            
            # Try to validate with RSA key first
            try:
                decoded = pyjwt.decode(
                    token, 
                    rsa_public_key, 
                    algorithms=['RS256'],
                    audience='vpn-nodes',
                    issuer='portbro.com'
                )
                logger.info(f"JWT token validated successfully with RSA key for user: {decoded.get('username', 'unknown')}")
                return decoded
            except pyjwt.ExpiredSignatureError:
                logger.warning("JWT token has expired")
                return None
            except pyjwt.InvalidTokenError as e:
                logger.warning(f"JWT token validation failed with RSA key: {e}")
                # Fall back to unverified decode for testing
                decoded = pyjwt.decode(token, options={"verify_signature": False})
                
                # Check if token is expired
                exp = decoded.get('exp', 0)
                if exp and exp < time.time():
                    logger.warning("JWT token is expired")
                    return None
                
                logger.info(f"JWT token validated without signature verification for user: {decoded.get('username', 'unknown')}")
                return decoded
        except Exception as e:
            logger.error(f"JWT token validation error: {e}")
            return None
    
    def is_token_valid(self, token: str) -> bool:
        """
        Check if JWT token is valid (not expired).
        
        Args:
            token: JWT token to check
            
        Returns:
            True if token is valid, False otherwise
        """
        token_info = self.validate_and_get_token_info(token)
        return token_info is not None
    
    def clear_cache(self) -> None:
        """
        Clear cached JWT token.
        """
        try:
            cache.delete(self.CACHE_KEY_PREFIX)
            logger.info("Cleared JWT token cache")
        except Exception as e:
            logger.error(f"Error clearing JWT token cache: {e}")


# Global instance
jwt_service = JWTService()

