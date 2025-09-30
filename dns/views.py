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


# Legacy DNS functions (placeholders for compatibility)
@login_required
def view_apply_dns_config(request):
    """Legacy DNS config function - placeholder"""
    messages.info(request, "DNS configuration is now managed through dnsmasq")
    return redirect('/dns/')


@login_required
def view_manage_dns_settings(request):
    """Legacy DNS settings function - placeholder"""
    messages.info(request, "DNS settings are now managed through dnsmasq")
    return redirect('/dns/')


@login_required
def view_manage_filter_list(request):
    """Legacy filter list function - placeholder"""
    messages.info(request, "DNS filtering is now managed through dnsmasq")
    return redirect('/dns/')


@login_required
def view_manage_static_host(request):
    """Legacy static host function - placeholder"""
    messages.info(request, "Static hosts are now managed through dnsmasq")
    return redirect('/dns/')


@login_required
def view_peer_hostnames(request):
    """Legacy peer hostnames function - placeholder"""
    messages.info(request, "Peer hostnames are now managed through dnsmasq")
    return redirect('/dns/')


@login_required
def view_static_host_list(request):
    """Legacy static host list function - placeholder"""
    messages.info(request, "Static hosts are now managed through dnsmasq")
    return redirect('/dns/')


@login_required
def view_toggle_dns_list(request):
    """Legacy DNS list toggle function - placeholder"""
    messages.info(request, "DNS lists are now managed through dnsmasq")
    return redirect('/dns/')


@login_required
def view_update_dns_list(request):
    """Legacy DNS list update function - placeholder"""
    messages.info(request, "DNS lists are now managed through dnsmasq")
    return redirect('/dns/')