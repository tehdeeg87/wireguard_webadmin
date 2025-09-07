#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
django.setup()

from django.contrib.auth.models import User
from user_manager.models import UserAcl

print('=== ALL USERS ===')
for user in User.objects.all():
    print(f'ID: {user.id} | Username: {user.username} | Email: {user.email}')

print('\n=== USERS WITH TARGET EMAILS ===')
target_emails = ['dgillis77@gmail.com', 'danielg@gordonrussell.com']
for email in target_emails:
    users = User.objects.filter(email=email)
    print(f'\nEmail: {email}')
    for user in users:
        print(f'  - ID: {user.id} | Username: {user.username} | Email: {user.email}')
