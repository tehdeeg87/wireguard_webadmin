# Remove Instances API Endpoint

## Overview

The `/remove_instances/` endpoint provides complete removal functionality for WireGuard instances, including all associated peers, peer groups, users, and user ACLs. This is a destructive operation that permanently removes all data related to the specified instance.

## Endpoint Details

- **URL**: `/remove_instances/`
- **Method**: `POST`
- **Authentication**: API Key (x-api-key header)
- **Content-Type**: `application/json`

## Request Format

### Headers
```
x-api-key: your_api_key_here
Content-Type: application/json
```

### Request Body
```json
{
  "body": {
    "instance": "user@example.com"
  }
}
```

## What Gets Removed

The endpoint performs a complete cleanup in the following order:

### 1. WireGuard Instance
- Finds the instance by name (using the provided email as instance name)
- Removes all associated peers
- Deletes the instance

### 2. All Associated Peers
- Removes peer status records
- Removes peer allowed IPs
- Removes peer invites
- Deletes all peers

### 3. Peer Group
- Searches for peer group with name: `{instance}_group`
- Clears all peer and instance associations
- Deletes the peer group

### 4. User Account
- Finds user by email
- Removes user ACL
- Removes authentication tokens
- Terminates all active sessions
- Deletes the user

### 5. Configuration Regeneration
- Regenerates WireGuard configuration files
- Updates system to reflect changes

## Response Format

### Success Response (200)
```json
{
  "status": "success",
  "message": "Removal completed for user@example.com",
  "results": {
    "instance_identifier": "user@example.com",
    "removed_items": [
      {
        "type": "wireguard_instance",
        "identifier": "instance-uuid",
        "peers_removed": 3
      },
      {
        "type": "peer_group",
        "identifier": "user@example.com_group"
      },
      {
        "type": "user_acl",
        "identifier": "acl-uuid"
      },
      {
        "type": "user",
        "identifier": "user@example.com"
      },
      {
        "type": "wireguard_configs",
        "identifier": "regenerated"
      }
    ],
    "errors": []
  }
}
```

### Partial Success Response (207)
```json
{
  "status": "partial_success",
  "message": "Removal completed for user@example.com",
  "results": {
    "instance_identifier": "user@example.com",
    "removed_items": [
      {
        "type": "wireguard_instance",
        "identifier": "instance-uuid",
        "peers_removed": 2
      }
    ],
    "errors": [
      "User not found: user@example.com"
    ]
  }
}
```

### Error Response (400/401/500)
```json
{
  "status": "error",
  "message": "Error description"
}
```

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Complete success |
| 207 | Partial success (some items removed, some errors) |
| 400 | Bad request (invalid JSON or missing fields) |
| 401 | Unauthorized (missing or invalid API key) |
| 500 | Internal server error |

## Security Features

### API Key Authentication
- Requires valid API key in `x-api-key` header
- Uses existing API key validation system

### Database Transactions
- All operations wrapped in database transaction
- Ensures atomicity - either all operations succeed or none do
- Prevents partial data corruption

### Comprehensive Logging
- All operations logged for audit trail
- Error details captured and logged
- Success operations tracked

## Usage Examples

### cURL Example
```bash
curl -X POST https://vpn.portbro.com/remove_instances/ \
  -H "x-api-key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "instance": "dgillis77@gmail.com"
    }
  }'
```

### Node.js Example
```javascript
const axios = require('axios');

const response = await axios.post('https://vpn.portbro.com/remove_instances/', {
  body: {
    instance: 'dgillis77@gmail.com'
  }
}, {
  headers: {
    'x-api-key': 'your_api_key_here',
    'Content-Type': 'application/json'
  }
});

console.log(response.data);
```

### Python Example
```python
import requests

url = 'https://vpn.portbro.com/remove_instances/'
headers = {
    'x-api-key': 'your_api_key_here',
    'Content-Type': 'application/json'
}
data = {
    'body': {
        'instance': 'dgillis77@gmail.com'
    }
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

## Important Notes

### ⚠️ Destructive Operation
This endpoint performs **permanent deletion** of data. There is no undo functionality.

### 🔒 Security Considerations
- Only use with valid API keys
- Ensure proper authorization before calling
- Consider implementing additional confirmation steps for production use

### 📊 Monitoring
- Monitor logs for successful operations
- Track error rates and types
- Set up alerts for failed removals

### 🔄 Idempotency
- Multiple calls with the same instance identifier are safe
- Non-existent instances/users will be logged as errors but won't cause failures

## Integration with Parent Application

This endpoint is designed to be called by a parent application (like a billing system) when:

- User subscription is cancelled
- Payment fails
- Account is suspended
- User requests account deletion

The parent application should:

1. Validate the request internally
2. Call this endpoint with the user's email
3. Handle the response appropriately
4. Update their own records based on the response

## Troubleshooting

### Common Issues

1. **"Invalid API key"**
   - Check that the API key is correct
   - Ensure the key is passed in the `x-api-key` header

2. **"WireGuard instance not found"**
   - Verify the instance name matches exactly
   - Check if the instance was already removed

3. **"User not found"**
   - Verify the email address is correct
   - Check if the user was already removed

4. **Partial success responses**
   - Review the errors array for specific issues
   - Some components may have been removed while others failed

### Log Analysis

Check the application logs for detailed information about:
- Which items were successfully removed
- Specific error messages for failed operations
- Database transaction status
- Configuration regeneration results
