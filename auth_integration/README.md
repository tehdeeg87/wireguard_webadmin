# Portbro Authentication Integration

This module provides OAuth2 and JWT authentication integration with portbro.com for the VPN node.

## Overview

The authentication flow works as follows:

1. **OAuth2 Client Credentials Flow**: The VPN node authenticates with portbro.com using client credentials to obtain an OAuth2 access token.

2. **JWT Token Exchange**: Using the OAuth2 token, the VPN node requests a JWT token specifically for VPN operations.

3. **JWT Validation**: Incoming requests with JWT tokens are validated using the JWKS endpoint from portbro.com.

4. **User Synchronization**: Valid JWT tokens are used to create/update local Django users with appropriate ACLs.

## Configuration

Add the following settings to your Django settings:

```python
# Portbro OAuth2 Configuration
PORTBRO_CLIENT_ID = "your_client_id"
PORTBRO_CLIENT_SECRET = "your_client_secret"
PORTBRO_TOKEN_URL = "https://portbro.com/o/token/"
PORTBRO_VPN_AUTH_URL = "https://portbro.com/vpn/auth/"
PORTBRO_SCOPE = "read"

# JWT Validation Configuration
PARENT_JWKS_URL = "https://portbro.com/o/jwks/"
PARENT_ISSUER = "https://portbro.com"
PARENT_AUDIENCE = "vpn-node"
```

## API Endpoints

The following API endpoints are available:

### VPN Authentication
- `POST /auth/vpn/auth/` - Get JWT token for VPN operations
- `GET /auth/vpn/status/` - Check authentication status
- `POST /auth/vpn/refresh/` - Force refresh JWT token
- `POST /auth/vpn/clear-cache/` - Clear JWT token cache

### Token Management
- `POST /auth/vpn/token/` - Get or refresh JWT token (with optional `force_refresh` parameter)
- `GET /auth/vpn/token/` - Get token status
- `DELETE /auth/vpn/token/` - Clear token cache

## Usage Examples

### Using the OAuth2 Client

```python
from auth_integration.oauth2_client import oauth2_client

# Get OAuth2 token
oauth2_token = oauth2_client.get_oauth2_token()

# Get JWT token
jwt_token = oauth2_client.get_jwt_token(oauth2_token)

# Complete flow
jwt_token = oauth2_client.get_vpn_jwt_token()
```

### Using the JWT Service

```python
from auth_integration.jwt_service import jwt_service

# Get JWT token (uses cache if available)
jwt_token = jwt_service.get_jwt_token()

# Force refresh
jwt_token = jwt_service.get_jwt_token(force_refresh=True)

# Check if token is valid
is_valid = jwt_service.is_token_valid(jwt_token)

# Clear cache
jwt_service.clear_cache()
```

### Making API Requests

```bash
# Get JWT token
curl -X POST http://localhost:8000/auth/vpn/auth/

# Check status
curl -X GET http://localhost:8000/auth/vpn/status/

# Force refresh
curl -X POST http://localhost:8000/auth/vpn/refresh/

# Clear cache
curl -X POST http://localhost:8000/auth/vpn/clear-cache/
```

## Testing

### Management Command

Test the authentication flow using the Django management command:

```bash
python manage.py test_auth
python manage.py test_auth --force-refresh
python manage.py test_auth --clear-cache
```

### Shell Script

Test the complete flow using the provided shell script:

```bash
chmod +x test_portbro_auth.sh
./test_portbro_auth.sh
```

### Manual Testing

You can also test manually using curl:

```bash
# 1. Get OAuth2 token
TOKEN_RESPONSE=$(curl -X POST https://portbro.com/o/token/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&scope=read" \
  -u "your_client_id:your_client_secret")

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

# 2. Get JWT token
JWT_RESPONSE=$(curl -X POST https://portbro.com/vpn/auth/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json")

JWT_TOKEN=$(echo $JWT_RESPONSE | jq -r '.access_token')

# 3. Use JWT token
curl -X GET http://localhost:8000/auth/vpn/status/ \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## Middleware

The JWT authentication middleware is automatically enabled and will:

1. Extract JWT tokens from the `Authorization: Bearer <token>` header
2. Validate tokens using the JWKS endpoint
3. Create/update local Django users based on JWT claims
4. Attach user information to the request object

## Error Handling

The system includes comprehensive error handling and logging:

- OAuth2 token requests are retried on failure
- JWT tokens are cached to reduce API calls
- Invalid tokens are automatically refreshed
- All errors are logged for debugging

## Security Considerations

- OAuth2 credentials should be stored securely (environment variables recommended)
- JWT tokens are cached in memory with expiration
- All API endpoints require proper authentication
- CORS and CSRF protection should be configured appropriately

## Dependencies

The following packages are required:

- `requests` - HTTP client for API calls
- `PyJWT` - JWT token handling
- `authlib` - OAuth2 and JWT validation
- `django` - Django framework integration

