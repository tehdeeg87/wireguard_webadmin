import base64
import datetime
import os
import subprocess
import uuid

import pytz
import requests
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from user_manager.models import AuthenticationToken, UserAcl
from vpn_invite.models import InviteSettings, PeerInvite
from wgwadmlibrary.tools import create_peer_invite, get_peer_invite_data, send_email, user_allowed_peers, \
    user_has_access_to_peer
from wireguard.models import Peer, PeerStatus, WebadminSettings, WireGuardInstance
from django.db import models


def get_api_key(api_name):
    api_key = None
    if api_name == 'api':
        api_file_path = '/etc/wireguard/api_key'
    elif api_name == 'routerfleet':
        api_file_path = '/etc/wireguard/routerfleet_key'
    elif api_name == 'rrdkey':
        api_file_path = '/app_secrets/rrdtool_key'
    else:
        return api_key

    if os.path.exists(api_file_path) and os.path.isfile(api_file_path):
        with open(api_file_path, 'r') as api_file:
            api_file_content = api_file.read().strip()
            try:
                uuid_test = uuid.UUID(api_file_content)

                if str(uuid_test) == api_file_content:
                    api_key = str(uuid_test)
            except:
                pass

    return api_key


def routerfleet_authenticate_session(request):
    AuthenticationToken.objects.filter(created__lt=timezone.now() - timezone.timedelta(minutes=1)).delete()
    authentication_token = get_object_or_404(AuthenticationToken, uuid=request.GET.get('token'))
    auth.login(request, authentication_token.user)
    authentication_token.delete()
    return redirect('/')


@require_http_methods(["GET"])
def routerfleet_get_user_token(request):
    data = {'status': '', 'message': '', 'authentication_token': ''}
    if request.GET.get('key'):
        api_key = get_api_key('routerfleet')
        if api_key and api_key == request.GET.get('key'):
            pass
        else:
            return HttpResponseForbidden()
    else:
        return HttpResponseForbidden()

    try:
        default_user_level = int(request.GET.get('default_user_level'))
        if default_user_level not in [10, 20, 30, 40, 50]:
            default_user_level = 0
    except:
        default_user_level = 0

    if request.GET.get('username'):
        user = User.objects.filter(username=request.GET.get('username')).first()

        if request.GET.get('action') == 'test':
            if UserAcl.objects.filter(user=user, user_level__gte=50).exists():
                data['status'] = 'success'
                data['message'] = 'User exists and is an administrator'
            else:
                data['status'] = 'error'
                data['message'] = f'Administrator with username {request.GET.get("username")} not found at wireguard_webadmin.'

        elif request.GET.get('action') == 'login':
            if user:
                user_acl = UserAcl.objects.filter(user=user).first()
            else:
                if default_user_level == 0:
                    data['status'] = 'error'
                    data['message'] = 'User not found'
                else:
                    user = User.objects.create_user(username=request.GET.get('username'), password=str(uuid.uuid4()))
                    user_acl = UserAcl.objects.create(user=user, user_level=default_user_level, enable_reload=True, enable_restart=True)

            if user and user_acl:
                authentication_token = AuthenticationToken.objects.create(user=user)
                data['status'] = 'success'
                data['message'] = 'User authenticated successfully'
                data['authentication_token'] = str(authentication_token.uuid)
        else:
            data['status'] = 'error'
            data['message'] = 'Invalid action'

    else:
        data['status'] = 'error'
        data['message'] = 'No username provided'

    if data['status'] == 'error':
        return JsonResponse(data, status=400)
    else:
        return JsonResponse(data)


@login_required
def peer_info(request):
    peer = get_object_or_404(Peer, uuid=request.GET.get('uuid'))
    user_acl = get_object_or_404(UserAcl, user=request.user)

    if not user_has_access_to_peer(user_acl, peer):
        raise PermissionDenied

    data = {
        'name': str(peer),
        'public_key': str(peer.public_key),
        'uuid': str(peer.uuid),
    }
    return JsonResponse(data)


@require_http_methods(["GET"])
def api_peer_list(request):
    if request.GET.get('key'):
        api_key = get_api_key('api')
        if api_key and api_key == request.GET.get('key'):
            pass
        else:
            return HttpResponseForbidden()
    else:
        return HttpResponseForbidden()
    data = {}

    requested_instance = request.GET.get('instance', 'all')
    if requested_instance == 'all':
        peer_list = Peer.objects.all()
    else:
        peer_list = Peer.objects.filter(wireguard_instance__instance_id=requested_instance.replace('wg', ''))

    for peer in peer_list:
        peer_allowed_ips = []
        for allowed_ip in peer.peerallowedip_set.all().filter(config_file='server'):
            peer_allowed_ips.append(
                {
                    'ip_address': allowed_ip.allowed_ip,
                    'priority': allowed_ip.priority,
                    'netmask': allowed_ip.netmask
                }
            )
        if f'wg{peer.wireguard_instance.instance_id}' not in data:
            data[f'wg{peer.wireguard_instance.instance_id}'] = {'peers': []}
        data[f'wg{peer.wireguard_instance.instance_id}']['peers'].append({
            'name': str(peer),
            'public_key': str(peer.public_key),
            'uuid': str(peer.uuid),
            'rrd_filename' : base64.urlsafe_b64encode(peer.public_key.encode()).decode().replace('=', '') + '.rrd',
            'last_handshake': peer.peerstatus.last_handshake.isoformat() if hasattr(peer, 'peerstatus') and peer.peerstatus.last_handshake else '',
            'allowed_ips': peer_allowed_ips,
        })
    return JsonResponse(data)


@require_http_methods(["GET"])
def api_instance_info(request):
    if request.GET.get('key'):
        api_key = get_api_key('api')
        if api_key and api_key == request.GET.get('key'):
            pass
        else:
            return HttpResponseForbidden()
    else:
        return HttpResponseForbidden()
    data = {}
    requested_instance = request.GET.get('instance', 'all')
    if requested_instance == 'all':
        instances = WireGuardInstance.objects.all()
    else:
        instances = WireGuardInstance.objects.filter(instance_id=requested_instance.replace('wg', ''))

    for instance in instances:
        data[f'wg{instance.instance_id}'] = {
            'name': instance.name,
            'instance_id': f'wg{instance.instance_id}',
            'public_key': instance.public_key,
            'listen_port': instance.listen_port,
            'hostname': instance.hostname,
            'address': instance.address,
            'netmask': instance.netmask,
            'peer_list_refresh_interval': instance.peer_list_refresh_interval,
            'dns_primary': instance.dns_primary if instance.dns_primary else '',
            'dns_secondary': instance.dns_secondary if instance.dns_secondary else '',
            'uuid': str(instance.uuid),
        }
    return JsonResponse(data)

@require_http_methods(["GET"])
def wireguard_status(request):
    user_acl = None
    enhanced_filter = False
    filter_peer_list = []

    if request.user.is_authenticated:
        user_acl = get_object_or_404(UserAcl, user=request.user)
        if user_acl.enable_enhanced_filter and user_acl.peer_groups.count() > 0:
            enhanced_filter = True
    elif request.GET.get('key'):
        api_key = get_api_key('api')
        if api_key and api_key == request.GET.get('key'):
            pass
        else:
            return HttpResponseForbidden()
    elif request.GET.get('rrdkey'):
        api_key = get_api_key('rrdkey')
        if api_key and api_key == request.GET.get('rrdkey'):
            pass
        else:
            return HttpResponseForbidden()
    else:
        return HttpResponseForbidden()

    if enhanced_filter:
        for server_instance in WireGuardInstance.objects.all():
            for peer in user_allowed_peers(user_acl, server_instance):
                if peer.public_key not in filter_peer_list:
                    filter_peer_list.append(peer.public_key)

    commands = {
        'latest-handshakes': "wg show all latest-handshakes | expand | tr -s ' '",
        'allowed-ips': "wg show all allowed-ips | expand | tr -s ' '",
        'transfer': "wg show all transfer | expand | tr -s ' '",
        'endpoints': "wg show all endpoints | expand | tr -s ' '",
    }

    output = {}

    for key, command in commands.items():
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            return JsonResponse({'error': stderr}, status=400)

        current_interface = None
        for line in stdout.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 3:
                interface, peer, value = parts[0], parts[1], " ".join(parts[2:])
                current_interface = interface
            elif len(parts) == 2 and current_interface:
                peer, value = parts
            else:
                continue

            if interface not in output:
                output[interface] = {}
            if enhanced_filter and peer not in filter_peer_list:
                continue
            if peer not in output[interface]:
                output[interface][peer] = {
                    'allowed-ips': [],
                    'latest-handshakes': '',
                    'transfer': {'tx': 0, 'rx': 0},
                    'endpoints': '',
                }

            if key == 'allowed-ips':
                output[interface][peer]['allowed-ips'].append(value)
            elif key == 'transfer':
                rx, tx = value.split()[-2:]
                output[interface][peer]['transfer'] = {'tx': int(tx), 'rx': int(rx)}
            elif key == 'endpoints':
                output[interface][peer]['endpoints'] = value
            else:
                output[interface][peer][key] = value

    return JsonResponse(output)


@require_http_methods(["GET"])
def cron_update_peer_latest_handshake(request):
    command = "wg show all latest-handshakes | expand | tr -s ' '"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        return JsonResponse({'error': stderr}, status=400)
    #debug_information = []
    for line in stdout.strip().split('\n'):
        parts = line.split()
        if len(parts) < 3:
            continue
        interface, peer_public_key, latest_handshake = parts[0], parts[1], parts[2]
        latest_handshake_timestamp = int(latest_handshake)

        if latest_handshake_timestamp > 0:
            last_handshake_time = datetime.datetime.fromtimestamp(latest_handshake_timestamp, tz=pytz.utc)
            #debug_information.append(f'Last handshake for {peer_public_key} is {last_handshake_time}')
            peer = Peer.objects.filter(public_key=peer_public_key).first()
            if peer:
                #debug_information.append(f'Peer found: {peer.public_key}')
                peer_status, created = PeerStatus.objects.get_or_create(
                    peer=peer,
                    defaults={'last_handshake': last_handshake_time}
                )
                if not created:
                    if peer_status.last_handshake != last_handshake_time:
                        #debug_information.append(f'Updating last_handshake for {peer.public_key} to {last_handshake_time}')
                        peer_status.last_handshake = last_handshake_time
                        peer_status.save()
                    #else:
                    #    debug_information.append(f'No changes for {peer.public_key}')

    return JsonResponse({'status': 'success'})


def cron_check_updates(request):
    webadmin_settings, webadmin_settings_created = WebadminSettings.objects.get_or_create(name='webadmin_settings')
    if webadmin_settings.last_checked is None or timezone.now() > (webadmin_settings.last_checked + datetime.timedelta(hours=1)):
        try:
            version = settings.WIREGUARD_WEBADMIN_VERSION / 10000
            url = f'https://updates.eth0.com.br/api/check_updates/?app=wireguard_webadmin&version={version}'
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if 'update_available' in data:
                webadmin_settings.update_available = data['update_available']
                
                if data['update_available']:
                    webadmin_settings.latest_version = float(data['current_version']) * 10000
                    
                webadmin_settings.last_checked = timezone.now()
                webadmin_settings.save()

                response_data = {
                    'update_available': webadmin_settings.update_available,
                    'latest_version': webadmin_settings.latest_version,
                    'current_version': settings.WIREGUARD_WEBADMIN_VERSION,
                }
                return JsonResponse(response_data)
            
        except Exception as e:
            webadmin_settings.update_available = False
            webadmin_settings.save()
            return JsonResponse({'update_available': False})
    
    return JsonResponse({'update_available': webadmin_settings.update_available})


@login_required
def api_peer_invite(request):
    PeerInvite.objects.filter(invite_expiration__lt=timezone.now()).delete()
    user_acl = get_object_or_404(UserAcl, user=request.user)
    invite_settings = InviteSettings.objects.filter(name='default_settings').first()
    peer_invite = PeerInvite.objects.none()

    if not invite_settings:
        data = {'status': 'error', 'message': 'VPN Invite not configured'}
        return JsonResponse(data, status=400)

    data = {
        'status': '', 'message': '', 'invite_data': {},
        'whatsapp_enabled': invite_settings.invite_whatsapp_enabled,
        'email_enabled': invite_settings.invite_email_enabled,
    }

    # Allow both Peer Managers (30) and above to send invites
    if user_acl.user_level < 30:
        data['status'] = 'error'
        data['message'] = 'Permission denied'
        return JsonResponse(data, status=403)

    if request.GET.get('peer'):
        peer = get_object_or_404(Peer, uuid=request.GET.get('peer'))
        if not user_has_access_to_peer(user_acl, peer):
            data['status'] = 'error'
            data['message'] = 'Permission denied'
            return JsonResponse(data, status=403)
        peer_invite = PeerInvite.objects.filter(peer=peer).first()
        if not peer_invite:
            peer_invite = create_peer_invite(peer, invite_settings)

    elif request.GET.get('invite'):
        peer_invite = get_object_or_404(PeerInvite, uuid=request.GET.get('invite'))
        if request.GET.get('action') == 'refresh':
            peer_invite.invite_expiration = timezone.now() + datetime.timedelta(minutes=invite_settings.invite_expiration)
            peer_invite.save()
        elif request.GET.get('action') == 'delete':
            peer_invite.delete()
            data['status'] = 'success'
            data['message'] = 'Invite deleted'
            return JsonResponse(data)

    if peer_invite:
        data['status'] = 'success'
        data['message'] = ''
        data['invite_data'] = get_peer_invite_data(peer_invite, invite_settings)

        if request.GET.get('action') == 'email':
            data['status'], data['message'] = send_email(request.GET.get('address'), data['invite_data']['email_subject'], data['invite_data']['email_body'])
            if data['status'] == 'success':
                return JsonResponse(data)
            else:
                return JsonResponse(data, status=400)
    else:
        if request.GET.get('action') == 'email':
            data['status'] = 'error'
            data['message'] = 'Invite not found'
            return JsonResponse(data)
    return JsonResponse(data, status=200)


@require_http_methods(["GET"])
def webhook_create_instance(request):

    try:
        # Get user count and email from request
        user_count = int(request.GET.get('user_count', 1))
        customer_email = request.GET.get('email', 'customer@email.com')

        # Calculate netmask based on user count
        # We need to ensure we have enough IPs for the requested users
        # Adding some buffer for future growth
        # Minimum of 6 usable IPs (netmask 29 = 8 IPs total, 6 usable)
        if user_count <= 6:
            netmask = 29  # 8 IPs total, 6 usable
        elif user_count <= 14:
            netmask = 28  # 16 IPs
        elif user_count <= 30:
            netmask = 27  # 32 IPs
        elif user_count <= 62:
            netmask = 26  # 64 IPs
        elif user_count <= 126:
            netmask = 25  # 128 IPs
        elif user_count <= 254:
            netmask = 24  # 256 IPs
        else:
            netmask = 23  # 512 IPs

        # Get the next available instance ID and port
        max_instance_id = WireGuardInstance.objects.all().aggregate(models.Max('instance_id'))['instance_id__max']
        new_instance_id = (max_instance_id + 1) if max_instance_id is not None else 0

        max_listen_port = WireGuardInstance.objects.all().aggregate(models.Max('listen_port'))['listen_port__max']
        new_listen_port = (max_listen_port + 1) if max_listen_port is not None else 51820

        # Generate WireGuard keys
        new_private_key = subprocess.check_output('wg genkey', shell=True).decode('utf-8').strip()
        new_public_key = subprocess.check_output(f'echo {new_private_key} | wg pubkey', shell=True).decode('utf-8').strip()

        # Generate default address
        new_address = f'10.188.{new_instance_id}.1'

        # Create the instance
        instance = WireGuardInstance.objects.create(
            name=customer_email,  # Use provided email as display name
            instance_id=new_instance_id,
            private_key=new_private_key,
            public_key=new_public_key,
            hostname='vpn.portbro.com',  # Set fixed hostname
            listen_port=new_listen_port,
            address=new_address,
            netmask=netmask,  # Use calculated netmask
            dns_primary=request.GET.get('dns_primary', '8.8.8.8'),
            dns_secondary=request.GET.get('dns_secondary', '8.8.4.4'),
            pending_changes=True
        )

        return JsonResponse({
            'status': 'success',
            'message': f'WireGuard instance created successfully',
            'instance': {
                'uuid': str(instance.uuid),
                'name': instance.name,
                'instance_id': instance.instance_id,
                'public_key': instance.public_key,
                'listen_port': instance.listen_port,
                'hostname': instance.hostname,
                'address': instance.address,
                'netmask': instance.netmask,
                'max_users': 2 ** (32 - instance.netmask) - 2  # Calculate max users based on netmask
            }
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)