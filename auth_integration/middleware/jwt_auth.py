import requests
import logging
from django.http import JsonResponse
from django.conf import settings
from authlib.jose import jwt, JsonWebKey
from auth_integration.utils.jwt_user import ensure_user_from_jwt
from auth_integration.utils.jwt_keys import get_rsa_public_key

logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware:
    """
    Middleware that validates incoming JWTs from portbro.com
    and syncs a local Django user + ACL.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.jwks = None  # cache for JWKS keys

    def __call__(self, request):
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            claims = self.validate_jwt(token)

            if claims:
                request.jwt_claims = claims
                # auto-sync user + ACL
                request.user = ensure_user_from_jwt(claims)

        return self.get_response(request)

    def validate_jwt(self, token):
        try:
            # First try to validate with the provided RSA public key
            try:
                import jwt as pyjwt
                
                # Get RSA public key from environment or file
                rsa_public_key = get_rsa_public_key()
                
                if not rsa_public_key:
                    logger.error("RSA public key not available for JWT validation")
                    return None
                
                claims = pyjwt.decode(
                    token, 
                    rsa_public_key, 
                    algorithms=['RS256'],
                    audience='vpn-nodes',
                    issuer='portbro.com'
                )
                
                logger.info(f"JWT validation successful with RSA key for user: {claims.get('username', 'unknown')}")
                return claims
                
            except pyjwt.ExpiredSignatureError:
                logger.warning("JWT token has expired")
                return None
            except pyjwt.InvalidAudienceError:
                logger.warning("Invalid JWT audience - expected 'vpn-nodes'")
                return None
            except pyjwt.InvalidIssuerError:
                logger.warning("Invalid JWT issuer - expected 'portbro.com'")
                return None
            except pyjwt.InvalidSignatureError:
                logger.debug("Invalid JWT signature with RSA key - trying JWKS validation")
                # Fall through to JWKS validation
            except Exception as e:
                logger.debug(f"RSA JWT validation failed: {e} - trying JWKS validation")
                # Fall through to JWKS validation
            
            # Fallback: Try to validate using JWKS from portbro.com
            try:
                if not self.jwks:
                    resp = requests.get(settings.PARENT_JWKS_URL, timeout=5)
                    resp.raise_for_status()
                    self.jwks = JsonWebKey.import_key_set(resp.json())

                claims = jwt.decode(token, self.jwks, algorithms=['RS256'])
                claims.validate()  # checks exp, iat, nbf

                if claims.get("iss") != settings.PARENT_ISSUER:
                    logger.warning(f"Invalid issuer from JWKS: {claims.get('iss')}")
                    return None

                if claims.get("aud") != settings.PARENT_AUDIENCE:
                    logger.warning(f"Invalid audience from JWKS: {claims.get('aud')}")
                    return None

                logger.info(f"JWT validation successful with JWKS for user: {claims.get('username', 'unknown')}")
                return claims
            except requests.RequestException as e:
                logger.error(f"Failed to fetch JWKS from {settings.PARENT_JWKS_URL}: {e}")
                    return None
            except Exception as e:
                logger.error(f"JWKS validation failed: {e}")
                    return None
                
        except Exception as e:
            logger.error(f"JWT validation failed: {e}")
            return None
