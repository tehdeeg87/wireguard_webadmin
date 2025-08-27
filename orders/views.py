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
from django.contrib.auth import authenticate
import uuid
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

from .forms import OrderForm

def order_form(request):
    return render(request, 'orders/order_form.html')

@csrf_exempt
def process_payment_success(request):
    """
    Handle the payment success webhook from n8n
    Creates a unique token and returns the configuration URL
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
            
        # Create a payment token
        token = PaymentToken.objects.create(
            email=customer_email,
            expires_at=timezone.now() + timedelta(days=7),  # Token expires in 7 days
            user_count=user_count,  # Store the user_count in the token
            password=generated_password  # Store the password in the token
        )
        
        # Generate configuration URL
        configuration_url = f"https://{request.get_host()}/orders/configure/{token.token}/"
            
        return JsonResponse({
            'status': 'success',
            'message': 'Token created successfully',
            'token': str(token.token),
            'configuration_url': configuration_url,
            'user_count': user_count,
            'password': generated_password  # Include the password in the response
        })
            
    except PermissionDenied as e:
        logger.error(f"Permission denied: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Permission denied'
        }, status=403)
    except Exception as e:
        logger.error(f"Error processing payment success: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def configure_instance(request, token):
    """
    Handle the configuration form for a new VPN instance
    """
    try:
        # Get the payment token
        payment_token = PaymentToken.objects.get(token=token)
        
        # Check if token is valid
        if payment_token.is_used:
            messages.error(request, _('This configuration link has already been used.'))
            return redirect('orders:order_form')
            
        if timezone.now() > payment_token.expires_at:
            messages.error(request, _('This configuration link has expired.'))
            return redirect('orders:order_form')
            
        if request.method == 'POST':
            # Get form data
            #country = request.POST.get('country')
            
            # Create a new request with the required parameters
            webhook_request = HttpRequest()
            webhook_request.method = 'GET'
            webhook_request.GET = {
                'email': payment_token.email,
                'user_count': str(payment_token.user_count)  # Use the stored user_count
            }
            
            # Call the instance creation function
            response = webhook_create_instance(webhook_request)
            
            if isinstance(response, JsonResponse):
                try:
                    data = json.loads(response.content)
                    if data.get('status') == 'success':
                        # Create user account
                        username = payment_token.email
                        if not User.objects.filter(username=username).exists():
                            user = User.objects.create_user(
                                username=username,
                                email=payment_token.email,
                                password=payment_token.password  # Use the stored password
                            )
                            
                            # Get the WireGuard instance that was just created
                            instance = WireGuardInstance.objects.latest('created')
                            
                            # Create a peer group for this instance
                            peer_group_name = f"{username}_group"
                            peer_group = PeerGroup.objects.create(name=peer_group_name)
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
                            payment_token.country = country
                            payment_token.save()
                            
                            messages.success(request, _('VPN instance created successfully! Please check your email for login details.'))
                            return redirect('login')
                        else:
                            messages.error(request, _('A user with this email already exists.'))
                    else:
                        messages.error(request, data.get('message', _('Error creating instance')))
                except json.JSONDecodeError:
                    messages.error(request, _('Invalid response from server'))
            else:
                messages.error(request, _('Unexpected error occurred'))
                
        # Pass the user_count to the template
        return render(request, 'orders/configure_instance.html', {
            'token': token,
            'user_count': payment_token.user_count
        })
        
    except PaymentToken.DoesNotExist:
        messages.error(request, _('Invalid configuration link.'))
        return redirect('orders:order_form')
    except Exception as e:
        logger.error(f"Error configuring instance: {str(e)}")
        messages.error(request, _('An error occurred while processing your request.'))
        return redirect('orders:order_form')

def order_success(request):
    return render(request, 'orders/order_success.html')
