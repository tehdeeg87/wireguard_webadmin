from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.management import call_command
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import os
from django.conf import settings


@login_required
def view_coredns_management(request):
    """Main CoreDNS management page"""
    context = {
        'page_title': 'CoreDNS Management',
    }
    return render(request, 'dns/coredns_management.html', context)


@login_required
@require_http_methods(["POST"])
def update_coredns_zones(request):
    """Update CoreDNS zones via web interface"""
    try:
        data = json.loads(request.body)
        zone = data.get('zone', 'all')
        
        # Call the management command
        call_command('update_coredns_zones', zone=zone)
        
        messages.success(request, f'CoreDNS zones updated successfully for zone: {zone}')
        return JsonResponse({
            'success': True,
            'message': f'CoreDNS zones updated successfully for zone: {zone}'
        })
        
    except Exception as e:
        messages.error(request, f'Error updating CoreDNS zones: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def view_coredns_status(request):
    """View CoreDNS status and zone information"""
    import os
    from django.conf import settings
    
    # Check if zone files exist
    peers_zone = os.path.join(settings.BASE_DIR, 'containers', 'coredns', 'zones', 'peers.db')
    instances_zone = os.path.join(settings.BASE_DIR, 'containers', 'coredns', 'zones', 'instances.db')
    
    context = {
        'page_title': 'CoreDNS Status',
        'peers_zone_exists': os.path.exists(peers_zone),
        'instances_zone_exists': os.path.exists(instances_zone),
        'peers_zone_size': os.path.getsize(peers_zone) if os.path.exists(peers_zone) else 0,
        'instances_zone_size': os.path.getsize(instances_zone) if os.path.exists(instances_zone) else 0,
    }
    
    return render(request, 'dns/coredns_status.html', context)


def export_dns_configuration():
    """
    Export DNS configuration for WireGuard instances
    This function is called by wireguard_tools to export DNS settings
    """
    try:
        # Update CoreDNS zones
        call_command('update_coredns_zones', zone='all')
        print("DNS configuration exported successfully")
    except Exception as e:
        print(f"Error exporting DNS configuration: {e}")
        raise


# Legacy DNS functions (placeholders for compatibility)
@login_required
def view_apply_dns_config(request):
    """Legacy DNS config function - placeholder"""
    messages.info(request, "DNS configuration is now managed through CoreDNS")
    return redirect('/dns/coredns/')


@login_required
def view_manage_dns_settings(request):
    """Legacy DNS settings function - placeholder"""
    messages.info(request, "DNS settings are now managed through CoreDNS")
    return redirect('/dns/coredns/')


@login_required
def view_manage_filter_list(request):
    """Legacy filter list function - placeholder"""
    messages.info(request, "DNS filtering is now managed through CoreDNS")
    return redirect('/dns/coredns/')


@login_required
def view_manage_static_host(request):
    """Legacy static host function - placeholder"""
    messages.info(request, "Static hosts are now managed through CoreDNS zones")
    return redirect('/dns/coredns/')


@login_required
def view_peer_hostnames(request):
    """Legacy peer hostnames function - placeholder"""
    messages.info(request, "Peer hostnames are now managed through CoreDNS")
    return redirect('/dns/coredns/')


@login_required
def view_static_host_list(request):
    """Legacy static host list function - placeholder"""
    messages.info(request, "Static hosts are now managed through CoreDNS zones")
    return redirect('/dns/coredns/')


@login_required
def view_toggle_dns_list(request):
    """Legacy DNS list toggle function - placeholder"""
    messages.info(request, "DNS lists are now managed through CoreDNS")
    return redirect('/dns/coredns/')


@login_required
def view_update_dns_list(request):
    """Legacy DNS list update function - placeholder"""
    messages.info(request, "DNS lists are now managed through CoreDNS")
    return redirect('/dns/coredns/')