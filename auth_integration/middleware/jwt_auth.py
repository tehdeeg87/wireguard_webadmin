import requests
from django.http import JsonResponse
from django.conf import settings
from authlib.jose import jwt, JsonWebKey
from auth_integration.utils.jwt_user import ensure_user_from_jwt


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
            if not self.jwks:
                resp = requests.get(settings.PARENT_JWKS_URL, timeout=5)
                self.jwks = JsonWebKey.import_key_set(resp.json())

            claims = jwt.decode(token, self.jwks)
            claims.validate()  # checks exp, iat, nbf

            if claims.get("iss") != settings.PARENT_ISSUER:
                return None

            if claims.get("aud") != settings.PARENT_AUDIENCE:
                return None

            return claims
        except Exception as e:
            print(f"JWT validation failed: {e}")
            return None
