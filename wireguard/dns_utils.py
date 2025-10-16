"""
DNS management utilities for WireGuard WebAdmin
Handles writing peer information to dnsmasq hosts file
"""

import os
import subprocess
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from .models import Peer, WireGuardInstance


def get_peer_ip_address(peer):
    """
    Get the IP address for a peer from its allowed IPs
    Returns the first allowed IP found, or None if none found
    """
    allowed_ips = peer.peerallowedip_set.filter(config_file='server').order_by('priority')
    if allowed_ips.exists():
        return allowed_ips.first().allowed_ip
    return None


def get_peer_dns_name(peer):
    """
    Get the full DNS name for a peer using instance-based subdomains
    Format: hostname.instance_id.vpn.local
    """
    if not peer.hostname:
        return None
    
    instance_id = peer.wireguard_instance.instance_id
    domain = settings.DNSMASQ_DOMAIN
    
    return f"{peer.hostname}.{instance_id}.{domain}"


def write_dnsmasq_hosts_file():
    """
    Write all peers to the dnsmasq hosts file
    This creates a static hosts file that dnsmasq will read
    """
    hosts_file_path = settings.DNSMASQ_HOSTS_FILE
    domain = settings.DNSMASQ_DOMAIN
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(hosts_file_path), exist_ok=True)
    
    try:
        with open(hosts_file_path, 'w') as f:
            # Write header comment
            f.write("# WireGuard WebAdmin DNS hosts file\n")
            f.write("# Auto-generated - do not edit manually\n\n")
            
            # Get all peers with their IP addresses
            peers = Peer.objects.select_related('wireguard_instance').all()
            
            for peer in peers:
                ip_address = get_peer_ip_address(peer)
                if ip_address and peer.hostname:
                    # Get the full DNS name with instance ID
                    dns_name = get_peer_dns_name(peer)
                    if dns_name:
                        # Write: IP_address hostname hostname.instance_id.domain
                        f.write(f"{ip_address}\t{peer.hostname}\t{dns_name}\n")
                        print(f"DNS: Added {dns_name} -> {ip_address}")
                elif ip_address and peer.name:
                    # Fallback to peer name if no hostname
                    instance_id = peer.wireguard_instance.instance_id
                    fallback_dns = f"{peer.name}.{instance_id}.{domain}"
                    f.write(f"{ip_address}\t{peer.name}\t{fallback_dns}\n")
                    print(f"DNS: Added {fallback_dns} -> {ip_address}")
        
        print(f"DNS: Successfully wrote hosts file to {hosts_file_path}")
        return True
        
    except Exception as e:
        print(f"DNS: Error writing hosts file: {e}")
        return False


def reload_dnsmasq():
    """
    Reload dnsmasq configuration
    This sends a SIGHUP signal to dnsmasq to reload its configuration
    """
    try:
        # Try to reload dnsmasq using pkill
        result = subprocess.run(['pkill', '-HUP', 'dnsmasq'], 
                              capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            print("DNS: Successfully reloaded dnsmasq")
            return True
        else:
            print(f"DNS: Warning - dnsmasq reload returned code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"DNS: Error reloading dnsmasq: {e}")
        return False


def update_dns_for_peer(peer):
    """
    Update DNS configuration for a specific peer
    This is a convenience function that rebuilds the entire hosts file
    """
    return write_dnsmasq_hosts_file()


def get_dns_status():
    """
    Get the current status of DNS configuration
    Returns a dictionary with status information
    """
    hosts_file_path = settings.DNSMASQ_HOSTS_FILE
    
    status = {
        'hosts_file_exists': os.path.exists(hosts_file_path),
        'hosts_file_path': hosts_file_path,
        'domain': settings.DNSMASQ_DOMAIN,
        'peer_count': Peer.objects.count(),
        'peers_with_hostnames': Peer.objects.exclude(hostname__isnull=True).exclude(hostname='').count(),
    }
    
    if status['hosts_file_exists']:
        try:
            with open(hosts_file_path, 'r') as f:
                content = f.read()
                status['hosts_file_lines'] = len([line for line in content.split('\n') if line.strip() and not line.startswith('#')])
        except Exception as e:
            status['hosts_file_error'] = str(e)
    
    return status
