from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from api.views import webhook_create_instance
from django.http import JsonResponse, HttpRequest
from django.contrib.auth.models import User
from user_manager.models import UserAcl
from wireguard.models import WireGuardInstance, PeerGroup
from .models import PaymentToken
import json
import logging
import traceback
import requests
from django.contrib.auth import authenticate
import uuid
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

from .forms import OrderForm

def order_form(request):
    return render(request, 'orders/order_form.html')

def setup_instance_from_token(payment_token):
    """
    Helper function to automatically set up a VPN instance from a payment token.
    This includes creating the WireGuard instance, user account, peer group, and ACL.
    
    Returns:
        dict: {'success': bool, 'user': User, 'instance': WireGuardInstance, 'message': str}
    """
    try:
        # Check if user already exists
        username = payment_token.email
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            instance = WireGuardInstance.objects.filter(name=username).first()
            return {
                'success': True,
                'user': user,
                'instance': instance,
                'message': 'User and instance already exist'
            }
        
        # Check if token is already used
        if payment_token.is_used:
            return {
                'success': False,
                'message': 'Token has already been used'
            }
        
        # Create a mock request for webhook_create_instance
        webhook_request = HttpRequest()
        webhook_request.method = 'GET'
        webhook_request.GET = {
            'email': payment_token.email,
            'user_count': str(payment_token.user_count)
        }
        
        # Call the instance creation function
        response = webhook_create_instance(webhook_request)
        
        if isinstance(response, JsonResponse):
            data = json.loads(response.content)
            if data.get('status') == 'success':
                # Create user account
                user = User.objects.create_user(
                    username=username,
                    email=payment_token.email,
                    password=payment_token.password
                )
                
                # Get the WireGuard instance that was just created
                instance = WireGuardInstance.objects.latest('created')
                
                # Create a peer group for this instance
                peer_group_name = f"{username}_group"
                peer_group, created = PeerGroup.objects.get_or_create(name=peer_group_name)
                peer_group.server_instance.add(instance)
                
                # Create UserAcl with peer manager level
                user_acl = UserAcl.objects.create(
                    user=user,
                    user_level=30,
                    enable_reload=True,
                    enable_restart=True,
                    enable_console=True
                )
                user_acl.peer_groups.add(peer_group)
                
                # Mark token as used
                payment_token.is_used = True
                payment_token.save()
                
                # Call back to n8n webhook to update user state
                try:
                    webhook_data = {
                        'email': user.email,
                    }
                    
                    django_app_url = "https://n8n.portbro.com/webhook/13f687ba-4315-4d38-ac6e-d7d2b41f6112"
                    webhook_response = requests.post(
                        django_app_url,
                        json=webhook_data,
                        timeout=10
                    )
                    
                    if webhook_response.status_code == 200:
                        logger.info(f"Successfully notified n8n webhook for user {user.email}")
                    else:
                        logger.warning(f"Webhook failed: {webhook_response.status_code}")
                        
                except requests.RequestException as e:
                    logger.error(f"Failed to notify n8n webhook: {str(e)}")
                    # Don't fail the entire process if webhook fails
                
                return {
                    'success': True,
                    'user': user,
                    'instance': instance,
                    'message': 'Instance created successfully'
                }
            else:
                return {
                    'success': False,
                    'message': data.get('message', 'Error creating instance')
                }
        else:
            return {
                'success': False,
                'message': 'Unexpected response from instance creation'
            }
            
    except Exception as e:
        logger.error(f"Error setting up instance from token: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'message': f'Error setting up instance: {str(e)}'
        }

@csrf_exempt
def process_payment_success(request):
    """
    Handle the payment success webhook from n8n
    Automatically creates the VPN instance, user account, and related resources
    """
    try:
        # Verify API key
        api_key = request.headers.get('X-API-Key')
        expected_api_key = getattr(settings, 'N8N_API_KEY', 'test-api-key-123')  # Use default if setting not found
        
        if not api_key or api_key != expected_api_key:
            logger.warning(f"Invalid or missing API key from IP: {request.META.get('REMOTE_ADDR')}")
            raise PermissionDenied("Invalid API key")

        # Get the JSON payload from n8n
        payload = json.loads(request.body)
        
        # Extract required information
        customer_email = payload.get('account')  # Changed from 'email' to 'account'
        user_count = payload.get('user_count', '1')  # Get user_count from payload
        
        if not customer_email:
            return JsonResponse({
                'status': 'error',
                'message': 'No customer email provided'
            }, status=400)
            
        # Generate a password that will be used when creating the user
        generated_password = str(uuid.uuid4())
            
        # Create a payment token (still needed for tracking and potential manual setup)
        token = PaymentToken.objects.create(
            email=customer_email,
            expires_at=timezone.now() + timedelta(days=7),  # Token expires in 7 days
            user_count=user_count,  # Store the user_count in the token
            password=generated_password  # Store the password in the token
        )
        
        # Automatically set up the instance
        setup_result = setup_instance_from_token(token)
        
        if setup_result['success']:
            user = setup_result['user']
            instance = setup_result['instance']
            
            return JsonResponse({
                'status': 'success',
                'message': 'VPN instance created and configured successfully',
                'user': {
                    'username': user.username,
                    'email': user.email,
                },
                'instance': {
                    'uuid': str(instance.uuid) if instance else None,
                    'name': instance.name if instance else None,
                    'instance_id': instance.instance_id if instance else None,
                },
                'token': str(token.token),  # Still return token for reference
                'user_count': user_count,
                'password': generated_password  # Include the password in the response
            })
        else:
            # If setup failed, still return the token so it can be used manually
            configuration_url = f"https://{request.get_host()}/orders/configure/{token.token}/"
            return JsonResponse({
                'status': 'partial',
                'message': f"Token created but automatic setup failed: {setup_result['message']}",
                'token': str(token.token),
                'configuration_url': configuration_url,
                'user_count': user_count,
                'password': generated_password,
                'error': setup_result['message']
            }, status=207)  # 207 Multi-Status
            
    except PermissionDenied as e:
        logger.error(f"Permission denied: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Permission denied'
        }, status=403)
    except Exception as e:
        logger.error(f"Error processing payment success: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def configure_instance(request, token):
    """
    Handle the configuration for a new VPN instance - automatically create on GET request
    This is now mainly used as a fallback/manual setup option since automatic setup
    happens in process_payment_success
    """
    try:
        # Get the payment token
        payment_token = PaymentToken.objects.get(token=token)
        
        # Check if token is expired
        if timezone.now() > payment_token.expires_at:
            messages.error(request, _('This configuration link has expired.'))
            return redirect('orders:order_form')
        
        # Check if user already exists (token was used before)
        username = payment_token.email
        if User.objects.filter(username=username).exists():
            # User already exists, show success message and redirect to login
            messages.success(request, _('Your VPN instance is already set up! Please log in with your credentials.'))
            return redirect('login')
        
        # Use the helper function to set up the instance
        setup_result = setup_instance_from_token(payment_token)
        
        if setup_result['success']:
            messages.success(request, _('VPN instance created successfully! Refer to your welcome email for login details.'))
            return redirect('login')
        else:
            messages.error(request, _(f'Error creating instance: {setup_result["message"]}'))
            
        # If we get here, there was an error, show the form as fallback
        return render(request, 'orders/configure_instance.html', {
            'token': token,
            'user_count': payment_token.user_count
        })
        
    except PaymentToken.DoesNotExist:
        messages.error(request, _('Invalid configuration link.'))
        return redirect('orders:order_form')
    except Exception as e:
        logger.error(f"Error configuring instance: {str(e)}")
        logger.error(traceback.format_exc())
        messages.error(request, _('An error occurred while processing your request.'))
        return redirect('orders:order_form')

def order_success(request):
    return render(request, 'orders/order_success.html')
