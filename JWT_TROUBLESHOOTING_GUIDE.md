# 🔧 JWT Authentication Troubleshooting Guide

## 🎯 **The Problem: JWT Authentication Works But No Redirect to Status Page**

You're experiencing JWT authentication that works but doesn't redirect properly to the status page. Here's how to diagnose and fix this issue.

## 🔍 **Step 1: Check Authentication Status**

### **Test JWT Authentication:**
```bash
# Check if you can access the auth page
curl -I http://your-server/auth/login/

# Test JWT callback directly
curl -I http://your-server/auth/callback/
```

### **Check User Creation:**
```python
# In Django shell
python manage.py shell

# Check if users are being created
from django.contrib.auth.models import User
from user_manager.models import UserAcl

print("=== USERS ===")
for user in User.objects.all():
    print(f"Username: {user.username}, Email: {user.email}")
    try:
        acl = UserAcl.objects.get(user=user)
        print(f"  User Level: {acl.user_level}")
        print(f"  Peer Groups: {acl.peer_groups.count()}")
        print(f"  Enable Reload: {acl.enable_reload}")
    except:
        print("  No ACL found")
```

## 🔍 **Step 2: Check Redirect Logic**

### **The Issue:**
Looking at the code, after JWT authentication, users are redirected to `wireguard_status`, but this view has a critical security check:

```python
def view_wireguard_status(request):
    user_acl = get_object_or_404(UserAcl, user=request.user)
    
    if user_acl.peer_groups.exists():
        # Show instances user has access to
        wireguard_instances = []
        for peer_group in user_acl.peer_groups.all():
            for instance_temp in peer_group.server_instance.all():
                if instance_temp not in wireguard_instances:
                    wireguard_instances.append(instance_temp)
    else:
        # SECURITY FIX: Users without peer groups see NO instances
        wireguard_instances = []
```

**The problem:** New JWT users get a peer group but no server instances assigned to it!

## 🔧 **Step 3: Fix the Issue**

### **Option A: Assign Instances to User's Peer Group**

```python
# In Django shell
python manage.py shell

from django.contrib.auth.models import User
from user_manager.models import UserAcl
from wireguard.models import WireGuardInstance, PeerGroup

# Get your user
user = User.objects.get(username='your_username')  # or email
acl = UserAcl.objects.get(user=user)

# Get all WireGuard instances
instances = WireGuardInstance.objects.all()
print(f"Available instances: {[i.name for i in instances]}")

# Assign instances to user's peer group
for peer_group in acl.peer_groups.all():
    for instance in instances:
        peer_group.server_instance.add(instance)
        print(f"Added {instance.name} to {peer_group.name}")

# Verify
for peer_group in acl.peer_groups.all():
    print(f"Peer group {peer_group.name} has instances: {[i.name for i in peer_group.server_instance.all()]}")
```

### **Option B: Create a Debug View**

Add this to your `wireguard/views.py`:

```python
def debug_user_status(request):
    """Debug view to see what's happening with user permissions"""
    if not request.user.is_authenticated:
        return HttpResponse("Not authenticated")
    
    try:
        acl = UserAcl.objects.get(user=request.user)
    except:
        return HttpResponse("No UserAcl found")
    
    context = {
        'user': request.user,
        'acl': acl,
        'peer_groups': acl.peer_groups.all(),
        'instances': [],
        'all_instances': WireGuardInstance.objects.all()
    }
    
    # Get instances from peer groups
    for peer_group in acl.peer_groups.all():
        for instance in peer_group.server_instance.all():
            if instance not in context['instances']:
                context['instances'].append(instance)
    
    return render(request, 'debug_user_status.html', context)
```

Add this to your `urls.py`:
```python
path('debug/user/', debug_user_status, name='debug_user_status'),
```

Create `templates/debug_user_status.html`:
```html
<!DOCTYPE html>
<html>
<head><title>User Debug Status</title></head>
<body>
    <h1>User Debug Status</h1>
    
    <h2>User Info</h2>
    <p><strong>Username:</strong> {{ user.username }}</p>
    <p><strong>Email:</strong> {{ user.email }}</p>
    <p><strong>Is Authenticated:</strong> {{ user.is_authenticated }}</p>
    
    <h2>User ACL</h2>
    <p><strong>User Level:</strong> {{ acl.user_level }}</p>
    <p><strong>Enable Reload:</strong> {{ acl.enable_reload }}</p>
    <p><strong>Enable Restart:</strong> {{ acl.enable_restart }}</p>
    <p><strong>Enable Console:</strong> {{ acl.enable_console }}</p>
    
    <h2>Peer Groups ({{ peer_groups.count }})</h2>
    {% for group in peer_groups %}
        <p><strong>{{ group.name }}</strong></p>
        <ul>
            {% for instance in group.server_instance.all %}
                <li>{{ instance.name }} ({{ instance.hostname }})</li>
            {% empty %}
                <li><em>No instances assigned to this group</em></li>
            {% endfor %}
        </ul>
    {% empty %}
        <p><em>No peer groups assigned</em></p>
    {% endfor %}
    
    <h2>Available Instances ({{ all_instances.count }})</h2>
    {% for instance in all_instances %}
        <p>{{ instance.name }} ({{ instance.hostname }})</p>
    {% empty %}
        <p><em>No instances available</em></p>
    {% endfor %}
    
    <h2>User's Instances ({{ instances|length }})</h2>
    {% for instance in instances %}
        <p>{{ instance.name }} ({{ instance.hostname }})</p>
    {% empty %}
        <p><em>No instances accessible to this user</em></p>
    {% endfor %}
    
    <hr>
    <p><a href="/status/">Go to Status Page</a></p>
    <p><a href="/auth/logout/">Logout</a></p>
</body>
</html>
```

## 🔍 **Step 4: Check JWT Token Claims**

### **Decode JWT Token:**
```python
# In Django shell
import jwt
import json

# Your JWT token (get from browser dev tools or logs)
token = "your_jwt_token_here"

# Decode without verification (for debugging)
decoded = jwt.decode(token, options={"verify_signature": False})
print(json.dumps(decoded, indent=2))
```

### **Check What Claims Are Being Used:**
```python
# In Django shell
from auth_integration.utils.jwt_user import ensure_user_from_jwt

# Test with your JWT claims
claims = {
    "sub": "test_user",
    "email": "test@portbro.com", 
    "role": "admin",
    "userlevel": 50
}

user = ensure_user_from_jwt(claims)
print(f"Created user: {user.username}")
print(f"Email: {user.email}")

acl = UserAcl.objects.get(user=user)
print(f"User level: {acl.user_level}")
print(f"Peer groups: {acl.peer_groups.count()}")
```

## 🎯 **Step 5: Quick Fix for Testing**

### **Temporary Fix - Show All Instances:**
Modify `wireguard/views.py` temporarily:

```python
def view_wireguard_status(request):
    user_acl = get_object_or_404(UserAcl, user=request.user)
    page_title = _("WireGuard Status")

    # TEMPORARY FIX: Show all instances for debugging
    if user_acl.user_level >= 50:  # Admin users
        wireguard_instances = WireGuardInstance.objects.all()
    elif user_acl.peer_groups.exists():
        wireguard_instances = []
        for peer_group in user_acl.peer_groups.all():
            for instance_temp in peer_group.server_instance.all():
                if instance_temp not in wireguard_instances:
                    wireguard_instances.append(instance_temp)
    else:
        wireguard_instances = []

    context = {'page_title': page_title, 'wireguard_instances': wireguard_instances, 'user_acl': user_acl}
    return render(request, 'wireguard/wireguard_status.html', context)
```

## 🚀 **Step 6: Test the Fix**

1. **Visit debug page:** `http://your-server/debug/user/`
2. **Check user permissions and peer groups**
3. **Assign instances to peer groups if needed**
4. **Test status page:** `http://your-server/status/`

## 📋 **Common Issues & Solutions**

| Issue | Symptom | Solution |
|-------|---------|----------|
| No peer groups | Empty status page | Assign peer groups to user |
| No instances in peer groups | Empty status page | Assign instances to peer groups |
| Wrong user level | Access denied | Check JWT claims and user level mapping |
| JWT validation fails | Redirect to auth page | Check JWT token and claims |
| User creation fails | Authentication error | Check email handling and constraints |

## 🎉 **Expected Result**

After fixing, you should see:
- ✅ **JWT authentication works**
- ✅ **User gets redirected to status page**
- ✅ **Status page shows WireGuard instances**
- ✅ **User can manage their assigned instances**

The key is ensuring that JWT users have peer groups with server instances assigned to them!
