import subprocess
import os


def get_mdns_dns_config():
    """
    Get the optimal DNS configuration for mDNS-enabled peers.
    Returns a tuple of (primary_dns, secondary_dns)
    
    For mDNS, we use:
    1. Local resolver (127.0.0.1) - handles .local domains via mDNS
    2. Public DNS as fallback
    """
    return '127.0.0.1', '8.8.8.8'


def get_optimal_dns_config():
    """
    Get the optimal DNS configuration for new instances.
    Returns a tuple of (primary_dns, secondary_dns)
    
    Uses mDNS for automatic peer discovery without centralized DNS server
    """
    return get_mdns_dns_config()
