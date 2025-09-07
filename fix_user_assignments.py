#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from wireguard.models import WireGuardInstance
from user_manager.models import UserAcl
from wireguard.models import PeerGroup

print('=== CURRENT USER ASSIGNMENTS ===')
for acl in UserAcl.objects.all():
    peer_groups = [g.name for g in acl.peer_groups.all()]
    instances = list(acl.peer_groups.values_list('server_instance__instance_id', flat=True))
    print(f'User: {acl.user.username} | Email: {acl.user.email} | Peer Groups: {peer_groups} | Instances: {instances}')

print('\n=== CLEARING AUTOMATIC INSTANCE ASSIGNMENTS ===')

# Remove all instance assignments from peer groups
for peer_group in PeerGroup.objects.all():
    peer_group.server_instance.clear()
    print(f'Cleared instances from peer group: {peer_group.name}')

print('\n=== AFTER CLEANUP ===')
for acl in UserAcl.objects.all():
    peer_groups = [g.name for g in acl.peer_groups.all()]
    instances = list(acl.peer_groups.values_list('server_instance__instance_id', flat=True))
    print(f'User: {acl.user.username} | Email: {acl.user.email} | Peer Groups: {peer_groups} | Instances: {instances}')

print('\n=== AVAILABLE WIREGUARD INSTANCES ===')
for instance in WireGuardInstance.objects.all():
    print(f'Instance {instance.instance_id}: {instance.name} (Port: {instance.listen_port})')

print('\n✅ CLEANUP COMPLETE!')
print('Users now have peer groups but NO instance assignments.')
print('Next: Manually assign each user to their correct instance.')
