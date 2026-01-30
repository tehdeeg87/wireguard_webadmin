# Transfer Instance Integration Guide

## Overview

When transferring a VPN instance to a new server/node, you need to disconnect peers on the **old node** before the transfer completes. This ensures that:

1. All active peer connections are immediately terminated
2. The WireGuard interface is brought down
3. The configuration file is removed (so it can't be restarted on the old node)
4. The instance remains in the database for use on the new node

## Solution

Two options are available:

### Option 1: API Endpoint (Recommended for Separate Apps)

If your security portal is a separate Django app or service, use the API endpoint:

**Endpoint:** `POST /api/disconnect_instance/`

**Authentication:** Requires `X-API-Key` header (same as `remove_instance`)

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

**Example Integration in `transfer_instance`:**

```python
def transfer_instance(request):
    """
    Transfer user's VPN instance to a new server
    Updates the server field in user_license records
    """
    import logging
    import requests
    import json
    from django.conf import settings
    from django.http import JsonResponse
    
    logger = logging.getLogger(__name__)
    
    if request.method != 'POST':
        logger.warning(f"Invalid method for transfer_instance: {request.method}")
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        user = request.user
        data = json.loads(request.body)
        server_id = data.get('server_id')
        
        if not server_id:
            return JsonResponse({'error': 'Server ID is required'}, status=400)
        
        # Get the target server
        try:
            target_server = servers.objects.get(id=server_id)
        except servers.DoesNotExist:
            return JsonResponse({'error': 'Server not found'}, status=404)
        
        # Get user's active licenses
        user_licenses = user_license.objects.filter(email=user.email, is_active=True)
        
        if not user_licenses.exists():
            return JsonResponse({'error': 'No active licenses found'}, status=404)
        
        # Get the old server value (before transfer)
        old_server_value = user_licenses.first().server
        
        # Disconnect instance on the OLD node (if it exists)
        # This will stop the WireGuard interface and disconnect all peers
        if old_server_value:
            try:
                # Determine the old node's API URL
                # You'll need to map old_server_value to the actual node URL
                old_node_url = get_node_url_from_server(old_server_value)  # Your helper function
                
                if old_node_url:
                    disconnect_url = f"{old_node_url}/api/disconnect_instance/"
                    api_key = getattr(settings, 'N8N_API_KEY', 'test-api-key-123')
                    
                    response = requests.post(
                        disconnect_url,
                        json={'email': user.email},
                        headers={'X-API-Key': api_key},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Successfully disconnected instance on old node for {user.email}")
                    else:
                        logger.warning(f"Failed to disconnect instance on old node: {response.status_code}")
                else:
                    logger.warning(f"Could not determine old node URL for server: {old_server_value}")
            except Exception as e:
                logger.error(f"Error disconnecting instance on old node: {str(e)}")
                # Don't fail the transfer if disconnect fails
        
        # Update server field for all active licenses
        new_server_value = target_server.dns_name if target_server.dns_name else target_server.country
        
        updated_count = 0
        for license in user_licenses:
            license.server = new_server_value
            license.save()
            updated_count += 1
            
            logger.info(f"Updated license {license.id}: server changed from '{old_server_value}' to '{new_server_value}'")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Instance transferred successfully to {target_server.country} ({target_server.dns_name}). Please update your client configurations.',
            'updated_licenses': updated_count,
            'new_server': {
                'country': target_server.country,
                'dns_name': target_server.dns_name
            }
        })
        
    except Exception as e:
        logger.error(f"Error transferring instance: {str(e)}")
        return JsonResponse({
            'error': f'Error transferring instance: {str(e)}'
        }, status=500)
```

### Option 2: Direct Function Call (Same Django App)

If your security portal is in the same Django project, you can import and call the function directly:

```python
from wireguard_tools.views import disconnect_instance_by_email

def transfer_instance(request):
    # ... existing code ...
    
    # Before updating the server field, disconnect on the old node
    old_server_value = user_licenses.first().server
    
    if old_server_value:
        # Disconnect the instance (stops interface, removes config, but keeps DB record)
        success, message, instance_id = disconnect_instance_by_email(user.email)
        
        if success:
            logger.info(f"Disconnected instance wg{instance_id} for {user.email}: {message}")
        else:
            logger.warning(f"Failed to disconnect instance: {message}")
    
    # ... rest of transfer logic ...
```

## How It Works

The `disconnect_instance_by_email` function:

1. **Finds the instance** by matching `email` to `WireGuardInstance.name`
2. **Stops the interface** using `wg-quick down wg{instance_id}`
3. **Removes the config file** at `/etc/wireguard/wg{instance_id}.conf`
4. **Reloads remaining interfaces** to apply changes
5. **Keeps the instance in the database** (unlike `remove_instance` which deletes it)

This ensures:
- ✅ All peer connections are immediately terminated
- ✅ The interface cannot be restarted on the old node
- ✅ The instance record remains for the new node to use
- ✅ Peers will need to reconnect to the new node with updated configurations

## Important Notes

1. **Node URL Mapping**: You'll need a way to map `server` values (from `user_license`) to actual node API URLs. This could be:
   - A mapping table in your database
   - Environment variables
   - A configuration file

2. **Error Handling**: The disconnect operation should not fail the transfer. If it fails, log it but continue with the transfer.

3. **Peer Configurations**: After transfer, users will need to:
   - Download new peer configurations from the new node
   - Update their client apps with the new endpoint hostname
   - Reconnect to the new node

4. **Timing**: The disconnect should happen **before** updating the `server` field, so you know which node to disconnect from.
