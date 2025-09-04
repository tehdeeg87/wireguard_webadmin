# auth_integration/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import jwt
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", None)
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(
                    token,
                    open(settings.JWT_PUBLIC_KEY_PATH).read(),
                    algorithms=["RS256"],
                )
                request.user = User.objects.filter(id=payload.get("user_id")).first() or AnonymousUser()
            except jwt.ExpiredSignatureError:
                request.user = AnonymousUser()
            except jwt.InvalidTokenError:
                request.user = AnonymousUser()
        else:
            request.user = AnonymousUser()
