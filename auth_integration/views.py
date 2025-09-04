"""
Views for JWT-based authentication flow.
"""
import json
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.urls import reverse

from .jwt_service import jwt_service
from .oauth2_client import oauth2_client

logger = logging.getLogger(__name__)


def jwt_login_view(request):
    """
    JWT-based login view that handles authentication via portbro.com.
    This view can be used as a redirect target after portbro.com authentication.
    """
    # Check if user is already authenticated
    if request.user.is_authenticated:
        return redirect('/')
    
    # Get JWT token from query parameters or session
    jwt_token = request.GET.get('token') or request.session.get('jwt_token')
    
    if not jwt_token:
        # If no token provided, redirect to portbro.com for authentication
        return redirect_to_portbro_auth(request)
    
    # Validate JWT token
    if not jwt_service.is_token_valid(jwt_token):
        messages.error(request, 'Invalid or expired JWT token. Please authenticate again.')
        return redirect_to_portbro_auth(request)
    
    # Get token claims
    claims = jwt_service.validate_and_get_token_info(jwt_token)
    if not claims:
        messages.error(request, 'Unable to validate JWT token.')
        return redirect_to_portbro_auth(request)
    
    # Create or get user from JWT claims
    from .utils.jwt_user import ensure_user_from_jwt
    user = ensure_user_from_jwt(claims)
    
    if user:
        # Log the user in using the ModelBackend
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f'Successfully logged in as {user.username}')
        
        # Store JWT token in session for future use
        request.session['jwt_token'] = jwt_token
        
        # Redirect to dashboard
        return redirect('/')
    else:
        messages.error(request, 'Unable to create user account.')
        return redirect_to_portbro_auth(request)


def redirect_to_portbro_auth(request):
    """
    Show authentication page with instructions for getting JWT token.
    Since we're using client credentials flow, users need to get JWT tokens differently.
    """
    return render(request, 'auth_integration/portbro_auth.html', {
        'portbro_auth_url': 'https://portbro.com/',  # Main portbro.com site
        'vpn_node_url': request.build_absolute_uri('/')
    })


@csrf_exempt
@require_http_methods(["POST"])
def jwt_callback_view(request):
    """
    Callback view for JWT authentication.
    This would be called by portbro.com after successful authentication.
    """
    try:
        data = json.loads(request.body)
        jwt_token = data.get('jwt_token')
        
        if not jwt_token:
            return JsonResponse({'error': 'No JWT token provided'}, status=400)
        
        # Validate JWT token
        if not jwt_service.is_token_valid(jwt_token):
            return JsonResponse({'error': 'Invalid JWT token'}, status=401)
        
        # Get token claims
        claims = jwt_service.validate_and_get_token_info(jwt_token)
        if not claims:
            return JsonResponse({'error': 'Unable to validate JWT token'}, status=401)
        
        # Create or get user from JWT claims
        from .utils.jwt_user import ensure_user_from_jwt
        user = ensure_user_from_jwt(claims)
        
        if user:
            # Log the user in using the ModelBackend
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Store JWT token in session
            request.session['jwt_token'] = jwt_token
            
            return JsonResponse({
                'success': True,
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'userlevel': user.useracl.user_level if hasattr(user, 'useracl') else 30
                },
                'redirect_url': '/'
            })
        else:
            return JsonResponse({'error': 'Unable to create user account'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"JWT callback error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


def jwt_logout_view(request):
    """
    JWT-based logout view.
    """
    # Clear JWT token from session
    if 'jwt_token' in request.session:
        del request.session['jwt_token']
    
    # Logout user
    from django.contrib.auth import logout
    logout(request)
    
    messages.success(request, 'Successfully logged out.')
    return redirect('/')


def auth_status_view(request):
    """
    View to check authentication status.
    """
    if request.user.is_authenticated:
        jwt_token = request.session.get('jwt_token')
        token_valid = jwt_service.is_token_valid(jwt_token) if jwt_token else False
        
        return JsonResponse({
            'authenticated': True,
            'user': {
                'username': request.user.username,
                'email': request.user.email,
                'userlevel': request.user.useracl.user_level if hasattr(request.user, 'useracl') else 30
            },
            'jwt_token_valid': token_valid,
            'jwt_token': jwt_token[:20] + '...' if jwt_token else None
        })
    else:
        return JsonResponse({
            'authenticated': False,
            'jwt_token_valid': False
        })


def auth_instructions_view(request):
    """
    View showing authentication instructions for users.
    """
    return render(request, 'auth_integration/auth_instructions.html', {
        'portbro_auth_url': 'https://portbro.com/',
        'vpn_node_url': request.build_absolute_uri('/')
    })


def generate_user_token_view(request):
    """
    Generate a JWT token for user authentication.
    This is a simplified way for users to get tokens.
    """
    try:
        # Get a fresh JWT token using the service
        jwt_token = jwt_service.get_jwt_token(force_refresh=True)
        
        if jwt_token:
            return JsonResponse({
                'success': True,
                'jwt_token': jwt_token,
                'message': 'JWT token generated successfully',
                'instructions': 'Use this token to authenticate with the VPN node'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to generate JWT token',
                'message': 'Please try again or contact administrator'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Token generation error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error',
            'message': 'Please contact administrator'
        }, status=500)