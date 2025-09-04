"""
API views for VPN authentication and token management.
"""
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
import json

from .jwt_service import jwt_service
from .oauth2_client import oauth2_client

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def vpn_auth_view(request):
    """
    VPN authentication endpoint.
    Returns JWT token for VPN operations.
    """
    try:
        # Get JWT token (will use cache if available)
        jwt_token = jwt_service.get_jwt_token()
        
        if not jwt_token:
            return JsonResponse({
                'error': 'authentication_failed',
                'message': 'Failed to obtain JWT token from portbro.com'
            }, status=401)
        
        # Validate token before returning
        if not jwt_service.is_token_valid(jwt_token):
            # Try to get a fresh token
            jwt_token = jwt_service.get_jwt_token(force_refresh=True)
            if not jwt_token:
                return JsonResponse({
                    'error': 'token_validation_failed',
                    'message': 'JWT token validation failed'
                }, status=401)
        
        return JsonResponse({
            'access_token': jwt_token,
            'token_type': 'Bearer',
            'expires_in': 300  # 5 minutes
        })
        
    except Exception as e:
        logger.error(f"VPN auth error: {e}")
        return JsonResponse({
            'error': 'internal_error',
            'message': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def vpn_status_view(request):
    """
    VPN authentication status endpoint.
    Returns current authentication status and token info.
    """
    try:
        # Get cached token
        cached_token = jwt_service.get_cached_jwt_token()
        
        if cached_token:
            token_info = jwt_service.validate_and_get_token_info(cached_token)
            if token_info:
                return JsonResponse({
                    'authenticated': True,
                    'token_valid': True,
                    'expires_at': token_info.get('exp', 0),
                    'issued_at': token_info.get('iat', 0),
                    'issuer': token_info.get('iss', ''),
                    'audience': token_info.get('aud', '')
                })
        
        return JsonResponse({
            'authenticated': False,
            'token_valid': False,
            'message': 'No valid token available'
        })
        
    except Exception as e:
        logger.error(f"VPN status error: {e}")
        return JsonResponse({
            'error': 'internal_error',
            'message': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def vpn_refresh_view(request):
    """
    Force refresh JWT token endpoint.
    """
    try:
        # Force refresh token
        jwt_token = jwt_service.get_jwt_token(force_refresh=True)
        
        if not jwt_token:
            return JsonResponse({
                'error': 'refresh_failed',
                'message': 'Failed to refresh JWT token'
            }, status=401)
        
        return JsonResponse({
            'access_token': jwt_token,
            'token_type': 'Bearer',
            'expires_in': 300,
            'refreshed': True
        })
        
    except Exception as e:
        logger.error(f"VPN refresh error: {e}")
        return JsonResponse({
            'error': 'internal_error',
            'message': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def vpn_clear_cache_view(request):
    """
    Clear JWT token cache endpoint.
    """
    try:
        jwt_service.clear_cache()
        return JsonResponse({
            'message': 'JWT token cache cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Clear cache error: {e}")
        return JsonResponse({
            'error': 'internal_error',
            'message': 'Internal server error'
        }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class VPNTokenView(View):
    """
    Class-based view for VPN token operations.
    """
    
    def post(self, request):
        """
        POST /vpn/token/ - Get or refresh JWT token
        """
        try:
            data = json.loads(request.body) if request.body else {}
            force_refresh = data.get('force_refresh', False)
            
            jwt_token = jwt_service.get_jwt_token(force_refresh=force_refresh)
            
            if not jwt_token:
                return JsonResponse({
                    'error': 'token_unavailable',
                    'message': 'Failed to obtain JWT token'
                }, status=401)
            
            return JsonResponse({
                'access_token': jwt_token,
                'token_type': 'Bearer',
                'expires_in': 300,
                'refreshed': force_refresh
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'invalid_json',
                'message': 'Invalid JSON in request body'
            }, status=400)
        except Exception as e:
            logger.error(f"VPN token view error: {e}")
            return JsonResponse({
                'error': 'internal_error',
                'message': 'Internal server error'
            }, status=500)
    
    def get(self, request):
        """
        GET /vpn/token/ - Get token status
        """
        return vpn_status_view(request)
    
    def delete(self, request):
        """
        DELETE /vpn/token/ - Clear token cache
        """
        return vpn_clear_cache_view(request)

