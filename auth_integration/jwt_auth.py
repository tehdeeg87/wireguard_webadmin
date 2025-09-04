import requests
from django.http import JsonResponse
from django.conf import settings
from authlib.jose import jwt, JsonWebKey

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwks = None

    def __call__(self, request):
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            claims = self.validate_jwt(token)
            if claims:
                request.jwt_claims = claims  # attach user info
        return self.get_response(request)

    def validate_jwt(self, token):
        try:
            if not self.jwks:
                resp = requests.get(settings.PARENT_JWKS_URL)
                self.jwks = JsonWebKey.import_key_set(resp.json())
            claims = jwt.decode(token, self.jwks)
            claims.validate()  # validates exp, iat
            if claims.get("iss") != settings.PARENT_ISSUER:
                return None
            if claims.get("aud") != settings.PARENT_AUDIENCE:
                return None
            return claims
        except Exception:
            return None
