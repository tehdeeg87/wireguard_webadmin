import subprocess
import os


def get_mdns_dns_config():
    """
    Get the optimal DNS configuration for mDNS-enabled peers.
    Returns a tuple of (primary_dns, secondary_dns)

    For centralized mDNS broker approach, we use:
    1. WireGuard server IP - handles .local domains via mDNS broker
    2. Public DNS as fallback
    """
    # Get the WireGuard server IP (this will be the Ubuntu server IP in production)
    # For now, use a placeholder that should be replaced with actual server IP
    server_ip = '10.188.0.1'  # This should be the WireGuard server's IP
    return server_ip, '8.8.8.8'


def get_optimal_dns_config():
    """
    Get the optimal DNS configuration for new instances.
    Returns a tuple of (primary_dns, secondary_dns)

    Uses mDNS with Avahi + Reflector for automatic peer discovery
    """
    return get_mdns_dns_config()
