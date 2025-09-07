#!/usr/bin/env python
import os
import django
import subprocess

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from wireguard.models import WireGuardInstance, PeerGroup
from user_manager.models import UserAcl
from django.contrib.auth.models import User

print('=== CREATING WIREGUARD INSTANCE ===')

# Create a WireGuard instance
instance = WireGuardInstance.objects.create(
    name='Main VPN Instance',
    instance_id=0,
    private_key=subprocess.check_output('wg genkey', shell=True).decode('utf-8').strip(),
    public_key=subprocess.check_output('wg genkey | wg pubkey', shell=True).decode('utf-8').strip(),
    hostname='vpn.portbro.com',
    listen_port=51820,
    address='10.188.0.1',
    netmask=24,
    dns_primary='8.8.8.8',
    dns_secondary='8.8.4.4'
)

print(f'Created instance: {instance.name} (Port: {instance.listen_port})')

print('\n=== ASSIGNING USERS TO INSTANCE ===')

# Get the users we want to assign
users_to_assign = [
    'dgillis77@gmail.com',  # dgillis77@gmail.com
    'danielg@gordonrussell.com'  # danielg@gordonrussell.com
]

for email in users_to_assign:
    try:
        user = User.objects.get(email=email)
        acl = UserAcl.objects.get(user=user)
        
        # Get or create their peer group
        group_name = f"{user.username}_group"
        group, created = PeerGroup.objects.get_or_create(name=group_name)
        
        # Assign the instance to their peer group
        group.server_instance.add(instance)
        acl.peer_groups.add(group)
        
        print(f'✅ Assigned {email} to instance {instance.instance_id}')
        
    except User.DoesNotExist:
        print(f'❌ User with email {email} not found')
    except UserAcl.DoesNotExist:
        print(f'❌ UserAcl for {email} not found')

print('\n=== FINAL USER ASSIGNMENTS ===')
for acl in UserAcl.objects.all():
    if acl.user.email in users_to_assign:
        peer_groups = [g.name for g in acl.peer_groups.all()]
        instances = list(acl.peer_groups.values_list('server_instance__instance_id', flat=True))
        print(f'User: {acl.user.username} | Email: {acl.user.email} | Peer Groups: {peer_groups} | Instances: {instances}')

print('\n✅ SETUP COMPLETE!')
print('Users should now only see their assigned instances.')
