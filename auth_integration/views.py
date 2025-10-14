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
    Redirect to portbro.com for authentication.
    """
    return render(request, 'auth_integration/portbro_auth.html', {
        'portbro_auth_url': 'https://portbro.com/',
        'vpn_node_url': request.build_absolute_uri('/')
    })


@csrf_exempt
def jwt_callback_view(request):
    """
    Callback view for JWT authentication.
    Handles both GET (from SSO redirect) and POST (from API) requests.
    """
    jwt_token = None
    
    if request.method == 'GET':
        # Handle SSO redirect from portbro.com
        jwt_token = request.GET.get('token')
        if not jwt_token:
            # If no token, show the manual token entry form
            return render(request, 'auth_integration/portbro_auth.html', {
                'portbro_auth_url': 'https://portbro.com/',
                'vpn_node_url': request.build_absolute_uri('/')
            })
        
        # Process JWT token from URL parameter
        try:
            # Use the same validation logic as the middleware
            from .middleware.jwt_auth import JWTAuthenticationMiddleware
            middleware = JWTAuthenticationMiddleware(None)
            claims = middleware.validate_jwt(jwt_token)
            
            if not claims:
                messages.error(request, 'Invalid JWT token')
                return render(request, 'auth_integration/portbro_auth.html', {
                    'portbro_auth_url': 'https://portbro.com/',
                    'vpn_node_url': request.build_absolute_uri('/')
                })
            
            # Create or get user from JWT claims
            from .utils.jwt_user import ensure_user_from_jwt
            user = ensure_user_from_jwt(claims)
            
            # Log the user in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Store success message
            messages.success(request, f'Successfully authenticated as {user.username}!')
            
            # Redirect to main status page
            return redirect('wireguard_status')
            
        except Exception as e:
            logger.error(f"JWT callback error: {e}")
            messages.error(request, f'Authentication error: {str(e)}')
            return render(request, 'auth_integration/portbro_auth.html', {
                'portbro_auth_url': 'https://portbro.com/',
                'vpn_node_url': request.build_absolute_uri('/')
            })
    
    elif request.method == 'POST':
        # Handle API requests
        try:
            data = json.loads(request.body)
            jwt_token = data.get('jwt_token')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    if not jwt_token:
        return JsonResponse({'error': 'No JWT token provided'}, status=400)
    
    try:
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
    if 'jwt_token' in request.session:
        del request.session['jwt_token']
    
    messages.success(request, 'Successfully logged out.')
    return redirect('/')


def auth_status_view(request):
    """
    View to check authentication status and show user info.
    """
    if request.user.is_authenticated:
        jwt_token = request.session.get('jwt_token')
        token_valid = jwt_service.is_token_valid(jwt_token) if jwt_token else False
        
        return render(request, 'auth_integration/auth_status.html', {
            'user': request.user,
            'jwt_token_valid': token_valid,
            'jwt_token': jwt_token[:20] + '...' if jwt_token else None
        })
    else:
        return render(request, 'auth_integration/auth_status.html', {
            'jwt_token_valid': False
        })


def auth_instructions_view(request):
    """
    View showing authentication instructions.
    """
    return render(request, 'auth_integration/auth_instructions.html', {
        'portbro_auth_url': 'https://portbro.com/',
        'vpn_node_url': request.build_absolute_uri('/')
    })


def generate_user_token_view(request):
    """
    Generate a JWT token for user authentication.
    This creates a user-specific token for testing purposes.
    """
    try:
        # For testing: Create a user-specific JWT token
        # In production, this would come from portbro.com with user details
        
        # Get user info from request (if available) or create test user
        username = request.GET.get('username', 'test_user')
        email = request.GET.get('email', f'{username}@portbro.com')
        role = request.GET.get('role', 'basic')
        
        # Create a mock JWT token with user-specific claims
        import jwt
        import time
        
        # Create user-specific claims
        claims = {
            'iss': 'portbro.com',
            'sub': username,  # This will be the username
            'aud': 'vpn-nodes',
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600,  # 1 hour expiry
            'scope': 'read',
            'user_id': username,
            'username': username,
            'email': email,
            'is_active': True,
            'is_staff': False,
            'is_superuser': False,
            'role': role,
            'client_id': 'yDPrlW2u1iiSbT9ABseK6fAGwN2nWhIFsO7i3CCm',
            'client_name': 'VPN Testing Client'
        }
        
        # For testing, we'll create a simple JWT token
        # In production, this would be signed by portbro.com
        jwt_token = jwt.encode(claims, 'test-secret', algorithm='HS256')
        
        return JsonResponse({
            'success': True,
            'jwt_token': jwt_token,
            'message': f'JWT token generated for user: {username}',
            'instructions': 'Use this token to authenticate with the VPN node',
            'user_info': {
                'username': username,
                'email': email,
                'role': role
            }
        })
            
    except Exception as e:
        logger.error(f"Token generation error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def jwt_token_async_view(request):
    """
    Async JWT token generation endpoint for user portal.
    This generates a JWT token for the authenticated user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Authentication required',
            'message': 'Please log in to generate a JWT token'
        }, status=401)
    
    try:
        # Get user info
        username = request.user.username
        email = request.user.email or f'{username}@portbro.com'
        
        # Get user level from ACL
        user_level = 30  # Default
        if hasattr(request.user, 'useracl'):
            user_level = request.user.useracl.user_level
        
        # Map user level to role
        if user_level >= 50:
            role = 'admin'
        elif user_level >= 40:
            role = 'manager'
        else:
            role = 'basic'
        
        # Create JWT token with user-specific claims
        import jwt
        import time
        
        claims = {
            'iss': 'portbro.com',
            'sub': username,
            'aud': 'vpn-nodes',
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600,  # 1 hour expiry
            'scope': 'read',
            'user_id': username,
            'username': username,
            'email': email,
            'is_active': True,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser,
            'role': role,
            'userlevel': user_level,
            'client_id': 'yDPrlW2u1iiSbT9ABseK6fAGwN2nWhIFsO7i3CCm',
            'client_name': 'VPN User Portal'
        }
        
        # Generate JWT token (using test secret for now)
        jwt_token = jwt.encode(claims, 'test-secret', algorithm='HS256')
        
        return JsonResponse({
            'success': True,
            'token': jwt_token,
            'expires': int(time.time()) + 3600,
            'user': {
                'username': username,
                'email': email,
                'role': role,
                'userlevel': user_level
            }
        })
        
    except Exception as e:
        logger.error(f"JWT token async generation error: {e}")
        return JsonResponse({
            'error': 'Token generation failed',
            'message': str(e)
        }, status=500)