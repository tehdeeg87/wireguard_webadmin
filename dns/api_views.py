from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
import json


@login_required
@require_http_methods(["POST"])
def update_coredns_zones(request):
    """
    API endpoint to manually update CoreDNS zones
    """
    try:
        data = json.loads(request.body)
        zone = data.get('zone', 'all')
        
        # Call the management command
        call_command('update_coredns_zones', zone=zone)
        
        return JsonResponse({
            'success': True,
            'message': f'CoreDNS zones updated successfully for zone: {zone}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def coredns_status(request):
    """
    API endpoint to check CoreDNS status and zone information
    """
    try:
        import os
        from django.conf import settings
        
        # Check if zone files exist
        peers_zone = os.path.join(settings.BASE_DIR, 'containers', 'coredns', 'zones', 'peers.db')
        instances_zone = os.path.join(settings.BASE_DIR, 'containers', 'coredns', 'zones', 'instances.db')
        
        status = {
            'peers_zone_exists': os.path.exists(peers_zone),
            'instances_zone_exists': os.path.exists(instances_zone),
            'peers_zone_size': os.path.getsize(peers_zone) if os.path.exists(peers_zone) else 0,
            'instances_zone_size': os.path.getsize(instances_zone) if os.path.exists(instances_zone) else 0,
        }
        
        return JsonResponse({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
