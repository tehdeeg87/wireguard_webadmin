# 🔐 VPN Node Authentication Flow Guide

## Overview

After implementing JWT authentication with portbro.com, here's how users will login to your VPN node:

## 🚀 **Complete Authentication Flow**

### **Method 1: Web Interface (Recommended for Users)**

1. **User visits VPN node** → `https://your-vpn-node.com/`
2. **Redirected to authentication page** → `https://your-vpn-node.com/auth/login/`
3. **Clicks "Authenticate with Portbro"** → Opens portbro.com
4. **Signs in to portbro.com** → User authenticates with their portbro account
5. **Portbro redirects back with JWT token** → `https://your-vpn-node.com/auth/login/?token=JWT_TOKEN`
6. **VPN node validates JWT** → Creates/updates local user account
7. **User is automatically logged in** → Redirected to dashboard

### **Method 2: API/CLI (For Developers/Integrations)**

1. **Get OAuth2 token from portbro.com**
2. **Exchange OAuth2 token for JWT token**
3. **Use JWT token in API requests**

## 🔧 **Implementation Details**

### **Automatic User Creation**

When a user authenticates via JWT:

```python
# User is automatically created/updated with:
username = claims["sub"]  # From JWT subject
email = claims.get("email", f"{username}@portbro.com")
role = claims.get("role", "basic")

# ACL permissions assigned based on role:
if role == "admin":
    userlevel = 50
elif role == "manager":
    userlevel = 40
else:
    userlevel = 30  # Basic user

# Permissions enabled:
enable_reload = True
enable_restart = True
enable_console = True
```

### **JWT Token Validation**

Every request with a JWT token is validated:

1. **Signature verification** using portbro.com's public key
2. **Expiration check** (10-hour expiry)
3. **Issuer validation** (must be portbro.com)
4. **Audience validation** (must be vpn-nodes)
5. **User synchronization** with local Django user

## 🌐 **Available Endpoints**

### **User Authentication**
- `GET /auth/login/` - JWT login page
- `GET /auth/logout/` - Logout user
- `POST /auth/callback/` - JWT callback from portbro.com
- `GET /auth/status/` - Check authentication status
- `GET /auth/instructions/` - Authentication guide

### **VPN API Endpoints**
- `POST /auth/vpn/auth/` - Get JWT token for VPN operations
- `GET /auth/vpn/status/` - Check VPN authentication status
- `POST /auth/vpn/refresh/` - Force refresh JWT token
- `POST /auth/vpn/clear-cache/` - Clear JWT token cache

## 🎯 **User Experience**

### **First Time Login**
1. User clicks "Authenticate with Portbro"
2. Redirected to portbro.com login page
3. Signs in with portbro credentials
4. Redirected back to VPN node with JWT token
5. VPN node creates user account automatically
6. User is logged in and redirected to dashboard

### **Subsequent Logins**
1. User clicks "Authenticate with Portbro"
2. If already signed in to portbro.com → Immediate redirect back
3. If not signed in → Portbro login page → Redirect back
4. User is logged in automatically

### **Token Expiration**
- JWT tokens expire after 10 hours
- Users are automatically redirected to re-authenticate
- No manual token management required

## 🔒 **Security Features**

### **JWT Token Security**
- **RSA-256 signing** with portbro.com's private key
- **10-hour expiration** with automatic refresh
- **Audience validation** (vpn-nodes only)
- **Issuer validation** (portbro.com only)

### **User ACL Integration**
- **Automatic user creation** from JWT claims
- **Role-based permissions** (admin/manager/basic)
- **ACL synchronization** with local database
- **Session management** with JWT token storage

### **Error Handling**
- **Invalid tokens** → Redirect to re-authentication
- **Expired tokens** → Automatic refresh attempt
- **Network errors** → Graceful fallback
- **User creation failures** → Error messages

## 📱 **Integration Examples**

### **Web Application**
```html
<!-- Login button -->
<a href="/auth/login/" class="btn btn-primary">
    <i class="fas fa-sign-in-alt"></i>
    Login with Portbro
</a>

<!-- Check authentication status -->
<script>
fetch('/auth/status/')
    .then(response => response.json())
    .then(data => {
        if (data.authenticated) {
            console.log('User logged in:', data.user);
        } else {
            console.log('User not authenticated');
        }
    });
</script>
```

### **API Integration**
```bash
# Get JWT token
JWT_TOKEN=$(curl -s -X POST https://your-vpn-node.com/auth/vpn/auth/ | jq -r '.access_token')

# Use JWT token for API requests
curl -H "Authorization: Bearer $JWT_TOKEN" \
     https://your-vpn-node.com/api/peer_list/
```

### **Django Views**
```python
from django.contrib.auth.decorators import login_required

@login_required
def my_view(request):
    # User is automatically authenticated via JWT
    user = request.user
    userlevel = user.useracl.userlevel
    # ... rest of view logic
```

## 🚀 **Deployment Checklist**

- [ ] JWT middleware enabled in Django settings
- [ ] OAuth2 credentials configured
- [ ] JWKS endpoint accessible
- [ ] User ACL models working
- [ ] Authentication templates deployed
- [ ] SSL certificates configured
- [ ] CORS settings configured (if needed)

## 🎉 **Result**

Users can now login to your VPN node by:

1. **Clicking a button** → Authenticate with Portbro
2. **Signing in once** → On portbro.com
3. **Being automatically logged in** → To your VPN node
4. **Having full permissions** → Based on their portbro role

**No passwords to manage, no user accounts to create, no complex setup required!** 🚀

The system handles everything automatically while maintaining security and providing a seamless user experience.
