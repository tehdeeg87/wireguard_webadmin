from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from api.views import webhook_create_instance
from django.http import JsonResponse
from django.http import HttpRequest
from django.contrib.auth.models import User
from user_manager.models import UserAcl
from wireguard.models import WireGuardInstance, PeerGroup
import json
import logging
import traceback
from django.contrib.auth import authenticate

logger = logging.getLogger(__name__)

from .forms import OrderForm

def order_form(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user_count = form.cleaned_data['user_count']
            
            logger.info(f"Processing order for email: {email} with user_count: {user_count}")
            
            # Check if user already exists
            username = email  # Use full email as username
            if User.objects.filter(username=username).exists():
                logger.error(f"User with username {username} already exists")
                messages.error(request, _('A user with this email already exists. Please use a different email address.'))
                return render(request, 'orders/order_form.html', {'form': form})
            
            # Create a new request with the required parameters
            webhook_request = HttpRequest()
            webhook_request.method = 'GET'
            webhook_request.GET = {
                'email': email,
                'user_count': str(user_count)
            }
            
            # Call the webhook function directly
            try:
                response = webhook_create_instance(webhook_request)
                logger.info(f"Webhook response: {response.content}")
                
                if isinstance(response, JsonResponse):
                    try:
                        data = json.loads(response.content)
                        if data.get('status') == 'success':
                            try:
                                # Create user with the email
                                logger.info(f"Attempting to create user with username: {username} and email: {email}")
                                user = User.objects.create_user(
                                    username=username,  # Use full email as username
                                    email=email,
                                    password='password'  # Set password directly in create_user
                                )
                                logger.info(f"User created successfully: {user.username}")
                                
                                # Get the WireGuard instance that was just created
                                instance = WireGuardInstance.objects.latest('created')
                                logger.info(f"Found WireGuard instance: {instance}")
                                
                                # Create a peer group for this instance
                                peer_group_name = f"{username}_group"
                                peer_group = PeerGroup.objects.create(name=peer_group_name)
                                peer_group.server_instance.add(instance)
                                logger.info(f"Created peer group: {peer_group}")
                                
                                # Create UserAcl with peer manager level and link to peer group
                                logger.info(f"Attempting to create UserAcl for user: {user.username}")
                                user_acl = UserAcl.objects.create(
                                    user=user,
                                    user_level=30,  # Peer manager level
                                    enable_reload=False,
                                    enable_restart=False,
                                    enable_console=True  # Enable console access
                                )
                                user_acl.peer_groups.add(peer_group)
                                logger.info(f"UserAcl created successfully for user: {user.username}")
                                
                                messages.success(request, _('WireGuard instance created successfully! Please login with your email username and password "password".'))
                                return redirect('login')
                            except Exception as e:
                                error_details = traceback.format_exc()
                                logger.error(f"Error creating user or UserAcl: {str(e)}\nTraceback:\n{error_details}")
                                messages.error(request, _('Error creating user account. Please contact support.'))
                        else:
                            error_msg = data.get('message', _('An error occurred while creating the instance.'))
                            logger.error(f"Webhook returned error: {error_msg}")
                            messages.error(request, error_msg)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {str(e)}")
                        messages.error(request, _('Invalid response from server.'))
                else:
                    logger.error(f"Unexpected response type: {type(response)}")
                    messages.error(request, _('An unexpected error occurred.'))
            except Exception as e:
                logger.error(f"Error calling webhook: {str(e)}")
                messages.error(request, _('Error processing your request. Please try again.'))
    else:
        form = OrderForm()
    
    return render(request, 'orders/order_form.html', {'form': form})

def order_success(request):
    return render(request, 'orders/order_success.html')
