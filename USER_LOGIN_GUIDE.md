# 🔐 How Users Login After Signing in Through Portbro.com

## 🎯 **Simple Answer: It's Automatic!**

After signing in through portbro.com, users are **automatically logged in** to your VPN node. Here's exactly how it works:

## 🚀 **The Complete Flow**

### **Step 1: User Visits VPN Node**
- User goes to `https://your-vpn-node.com/`
- If not authenticated, they're redirected to `/auth/login/`

### **Step 2: Authentication Page**
- User sees a clean authentication page with a big "Authenticate with Portbro" button
- Page shows instructions and security features
- User clicks the button

### **Step 3: Portbro.com Authentication**
- User is redirected to `https://portbro.com/auth/` (or your OAuth URL)
- User signs in with their portbro.com credentials
- Portbro.com generates a JWT token for the user

### **Step 4: Automatic Login**
- Portbro.com redirects back to your VPN node with the JWT token
- Your VPN node validates the JWT token
- **User is automatically logged in** - no additional steps required!
- User is redirected to the dashboard

## 🔧 **What Happens Behind the Scenes**

### **JWT Token Validation**
```python
# Your VPN node automatically:
1. Validates JWT signature using portbro.com's public key
2. Checks token expiration (10 hours)
3. Verifies issuer (portbro.com) and audience (vpn-nodes)
4. Extracts user information from JWT claims
```

### **User Account Creation**
```python
# User account is automatically created/updated:
username = "user123"  # From JWT subject
email = "user@portbro.com"  # From JWT email claim
role = "admin"  # From JWT role claim

# Permissions are automatically assigned:
userlevel = 50  # Admin level
enable_reload = True
enable_restart = True
enable_console = True
```

### **Session Management**
```python
# JWT token is stored in user's session
request.session['jwt_token'] = jwt_token
# User remains logged in until token expires (10 hours)
```

## 🌐 **Available Login Methods**

### **Method 1: Web Interface (Easiest)**
1. Visit VPN node → Click "Authenticate with Portbro"
2. Sign in to portbro.com → Automatically logged in!

### **Method 2: Direct JWT Token**
1. Get JWT token from portbro.com
2. Visit `https://your-vpn-node.com/auth/login/?token=JWT_TOKEN`
3. Automatically logged in!

### **Method 3: API Integration**
1. Use JWT token in API requests
2. All API endpoints work with JWT authentication

## 🔒 **Security & Permissions**

### **Automatic User Permissions**
- **Admin users** → Full access (level 50)
- **Manager users** → Management access (level 40)  
- **Basic users** → Standard access (level 30)

### **Token Security**
- **RSA-256 signed** by portbro.com
- **10-hour expiration** with automatic refresh
- **Audience validation** (vpn-nodes only)
- **No password storage** required

### **Session Security**
- JWT token stored in secure session
- Automatic logout on token expiration
- No sensitive data in cookies

## 📱 **User Experience**

### **First Time Login**
```
1. Click "Authenticate with Portbro" 
2. Sign in to portbro.com
3. ✅ Automatically logged in to VPN node!
```

### **Subsequent Logins**
```
1. Click "Authenticate with Portbro"
2. If already signed in to portbro.com → ✅ Immediate login!
3. If not signed in → Sign in → ✅ Automatic login!
```

### **Token Expiration**
```
1. After 10 hours, user is redirected to re-authenticate
2. Click "Authenticate with Portbro" again
3. ✅ Automatically logged in with new token!
```

## 🎉 **Benefits for Users**

### **No Passwords to Remember**
- Users only need their portbro.com credentials
- No separate VPN node passwords

### **No Account Creation**
- User accounts are created automatically
- No manual setup required

### **Seamless Experience**
- One-click authentication
- Automatic login after portbro.com sign-in
- No complex token management

### **Secure & Reliable**
- Industry-standard JWT authentication
- Automatic token refresh
- Secure session management

## 🚀 **For VPN Node Administrators**

### **No User Management Required**
- Users are created automatically from JWT claims
- Permissions are assigned based on portbro.com roles
- No manual user account creation needed

### **Centralized Authentication**
- All authentication handled by portbro.com
- No local password storage
- Easy to revoke access (just revoke on portbro.com)

### **Scalable & Secure**
- Supports unlimited users
- JWT tokens are stateless
- No database storage of sensitive auth data

## 🎯 **Summary**

**After signing in through portbro.com, users are automatically logged in to your VPN node with full permissions based on their portbro.com role. No additional steps, passwords, or account creation required!**

The system handles everything automatically while maintaining security and providing a seamless user experience. 🚀
