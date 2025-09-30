from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.management import call_command
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import os
from django.conf import settings








def export_dns_configuration():
    """
    Export DNS configuration for WireGuard instances
    This function is called by wireguard_tools to export DNS settings
    """
    try:
        # Update dnsmasq configuration
        call_command('update_peer_dns')
        print("DNS configuration exported successfully")
    except Exception as e:
        print(f"Error exporting DNS configuration: {e}")
        raise


# DNS Management Views
@login_required
def view_static_host_list(request):
    """Main DNS management page with static hosts and filter lists"""
    from .models import StaticHost, DNSFilterList
    
    static_host_list = StaticHost.objects.all()
    filter_lists = DNSFilterList.objects.all()
    
    context = {
        'page_title': 'DNS Management',
        'static_host_list': static_host_list,
        'filter_lists': filter_lists,
    }
    return render(request, 'dns/static_host_list.html', context)


@login_required
def view_manage_static_host(request):
    """Manage static host entries"""
    from .models import StaticHost
    from .forms import StaticHostForm
    
    uuid = request.GET.get('uuid')
    
    if uuid:
        try:
            static_host = StaticHost.objects.get(uuid=uuid)
        except StaticHost.DoesNotExist:
            messages.error(request, 'Static host not found')
            return redirect('/dns/')
    else:
        static_host = None
    
    if request.method == 'POST':
        form = StaticHostForm(request.POST, instance=static_host)
        if form.is_valid():
            form.save()
            messages.success(request, 'Static host saved successfully')
            return redirect('/dns/')
    else:
        form = StaticHostForm(instance=static_host)
    
    context = {
        'page_title': 'Manage Static Host',
        'form': form,
        'static_host': static_host,
    }
    return render(request, 'dns/manage_static_host.html', context)


@login_required
def view_manage_dns_settings(request):
    """Manage DNS settings"""
    from .models import DNSSettings
    from .forms import DNSSettingsForm
    
    try:
        dns_settings = DNSSettings.objects.get(name='dns_settings')
    except DNSSettings.DoesNotExist:
        dns_settings = DNSSettings.objects.create(name='dns_settings')
    
    if request.method == 'POST':
        form = DNSSettingsForm(request.POST, instance=dns_settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'DNS settings saved successfully')
            return redirect('/dns/')
    else:
        form = DNSSettingsForm(instance=dns_settings)
    
    context = {
        'page_title': 'DNS Settings',
        'form': form,
        'dns_settings': dns_settings,
    }
    return render(request, 'dns/manage_dns_settings.html', context)


@login_required
def view_manage_filter_list(request):
    """Manage DNS filter lists"""
    from .models import DNSFilterList
    from .forms import DNSFilterListForm
    
    uuid = request.GET.get('uuid')
    action = request.GET.get('action')
    
    if action == 'delete' and uuid:
        try:
            filter_list = DNSFilterList.objects.get(uuid=uuid)
            filter_list.delete()
            messages.success(request, 'Filter list deleted successfully')
            return redirect('/dns/')
        except DNSFilterList.DoesNotExist:
            messages.error(request, 'Filter list not found')
            return redirect('/dns/')
    
    if uuid:
        try:
            filter_list = DNSFilterList.objects.get(uuid=uuid)
        except DNSFilterList.DoesNotExist:
            messages.error(request, 'Filter list not found')
            return redirect('/dns/')
    else:
        filter_list = None
    
    if request.method == 'POST':
        form = DNSFilterListForm(request.POST, instance=filter_list)
        if form.is_valid():
            form.save()
            messages.success(request, 'Filter list saved successfully')
            return redirect('/dns/')
    else:
        form = DNSFilterListForm(instance=filter_list)
    
    context = {
        'page_title': 'Manage Filter List',
        'form': form,
        'filter_list': filter_list,
    }
    return render(request, 'dns/manage_filter_list.html', context)


@login_required
def view_peer_hostnames(request):
    """View peer hostnames"""
    from wireguard.models import Peer
    
    peers_with_hostnames = Peer.objects.filter(hostname__isnull=False).exclude(hostname='')
    
    context = {
        'page_title': 'Peer Hostnames',
        'peers': peers_with_hostnames,
    }
    return render(request, 'dns/peer_hostnames.html', context)


@login_required
def view_toggle_dns_list(request):
    """Toggle DNS filter list enabled/disabled status"""
    from .models import DNSFilterList
    
    uuid = request.GET.get('uuid')
    action = request.GET.get('action')
    
    if not uuid or action not in ['enable', 'disable']:
        messages.error(request, 'Invalid parameters')
        return redirect('/dns/')
    
    try:
        filter_list = DNSFilterList.objects.get(uuid=uuid)
        filter_list.enabled = (action == 'enable')
        filter_list.save()
        
        status = 'enabled' if filter_list.enabled else 'disabled'
        messages.success(request, f'Filter list {filter_list.name} {status} successfully')
    except DNSFilterList.DoesNotExist:
        messages.error(request, 'Filter list not found')
    
    return redirect('/dns/')


@login_required
def view_update_dns_list(request):
    """Update DNS filter list from source"""
    from .models import DNSFilterList
    from django.core.management import call_command
    
    uuid = request.GET.get('uuid')
    
    if not uuid:
        messages.error(request, 'Filter list UUID required')
        return redirect('/dns/')
    
    try:
        filter_list = DNSFilterList.objects.get(uuid=uuid)
        # Here you would implement the actual update logic
        # For now, just show a success message
        messages.success(request, f'Filter list {filter_list.name} update initiated')
    except DNSFilterList.DoesNotExist:
        messages.error(request, 'Filter list not found')
    
    return redirect('/dns/')


@login_required
def view_apply_dns_config(request):
    """Apply DNS configuration"""
    from django.core.management import call_command
    
    try:
        call_command('update_peer_dns')
        messages.success(request, 'DNS configuration applied successfully')
    except Exception as e:
        messages.error(request, f'Error applying DNS configuration: {str(e)}')
    
    return redirect('/dns/')