#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from wireguard.models import WireGuardInstance, PeerGroup
from user_manager.models import UserAcl
from django.contrib.auth.models import User

print('=== ASSIGNING USERS TO WIREGUARD INSTANCE ===')

# Get the instance we created
instance = WireGuardInstance.objects.first()
if not instance:
    print('❌ No WireGuard instance found!')
    exit()

print(f'Using instance: {instance.name} (Port: {instance.listen_port})')

# Define the users we want to assign (by username to avoid duplicates)
users_to_assign = [
    'dgillis77@gmail.com',  # This is the username for dgillis77@gmail.com
    'DanielG_gordonrussell.com'  # This is the username for DanielG@gordonrussell.com
]

for username in users_to_assign:
    try:
        user = User.objects.get(username=username)
        acl = UserAcl.objects.get(user=user)
        
        # Get or create their peer group
        group_name = f"{user.username}_group"
        group, created = PeerGroup.objects.get_or_create(name=group_name)
        
        # Assign the instance to their peer group
        group.server_instance.add(instance)
        acl.peer_groups.add(group)
        
        print(f'✅ Assigned {user.username} ({user.email}) to instance {instance.instance_id}')
        
    except User.DoesNotExist:
        print(f'❌ User with username {username} not found')
    except UserAcl.DoesNotExist:
        print(f'❌ UserAcl for {username} not found')

print('\n=== FINAL USER ASSIGNMENTS ===')
for acl in UserAcl.objects.all():
    if acl.user.username in users_to_assign:
        peer_groups = [g.name for g in acl.peer_groups.all()]
        instances = list(acl.peer_groups.values_list('server_instance__instance_id', flat=True))
        print(f'User: {acl.user.username} | Email: {acl.user.email} | Peer Groups: {peer_groups} | Instances: {instances}')

print('\n✅ ASSIGNMENT COMPLETE!')
print('Now test logging in as each user - they should only see their assigned instance.')
