"""
mDNS-based peer discovery functions for WireGuard WebAdmin
This replaces the dnsmasq approach with a more elegant mDNS solution
"""

import os
import subprocess
from django.conf import settings
from wireguard.models import Peer, WireGuardInstance


def generate_mdns_hosts_file(instance_id):
    """
    Generate mDNS hosts file for a specific WireGuard instance
    This file will be used by Avahi to advertise peer hostnames
    """
    try:
        instance = WireGuardInstance.objects.get(instance_id=instance_id)
        peers = Peer.objects.filter(wireguard_instance=instance)
        
        # Create instance-specific domain (e.g., wg0.local, wg1.local)
        domain = f"wg{instance_id}.local"
        
        hosts_content = []
        hosts_content.append(f"# mDNS hosts file for WireGuard instance {instance.name or f'wg{instance_id}'}")
        hosts_content.append(f"# Domain: {domain}")
        hosts_content.append("# Generated automatically - do not edit manually")
        hosts_content.append("")
        
        for peer in peers:
            # Get peer IP
            peer_ip = peer.peerallowedip_set.filter(config_file='server', priority=0).first()
            if not peer_ip:
                continue
                
            ip = peer_ip.allowed_ip
            hostname = peer.hostname or peer.name or f"peer-{peer.uuid.hex[:8]}"
            
            # Add various hostname formats for mDNS
            hosts_content.append(f"{ip} {hostname}")
            hosts_content.append(f"{ip} {hostname}.{domain}")
            hosts_content.append(f"{ip} {hostname}.wg.local")  # Global domain
            hosts_content.append(f"{ip} peer-{peer.uuid.hex[:8]}")
            hosts_content.append(f"{ip} peer-{peer.uuid.hex[:8]}.{domain}")
            hosts_content.append("")
        
        # Write hosts file to both container and host locations
        hosts_files = [
            f"/etc/avahi/hosts/wg{instance_id}.hosts",
            f"./mdns_hosts/wg{instance_id}.hosts"
        ]
        
        for hosts_file in hosts_files:
            os.makedirs(os.path.dirname(hosts_file), exist_ok=True)
            with open(hosts_file, 'w') as f:
                f.write('\n'.join(hosts_content))
        
        print(f"Generated mDNS hosts file: {hosts_files[0]}")
        return True
        
    except Exception as e:
        print(f"Error generating mDNS hosts file for instance {instance_id}: {e}")
        return False


def generate_all_mdns_hosts_files():
    """Generate mDNS hosts files for all WireGuard instances"""
    instances = WireGuardInstance.objects.all()
    success_count = 0
    
    for instance in instances:
        if generate_mdns_hosts_file(instance.instance_id):
            success_count += 1
    
    print(f"Generated mDNS hosts files for {success_count}/{len(instances)} instances")
    return success_count


def reload_avahi_daemon():
    """Reload Avahi daemon to pick up new host files"""
    try:
        # Send SIGHUP to avahi-daemon processes
        subprocess.run(['pkill', '-HUP', 'avahi-daemon'], check=False)
        print("Avahi daemon reloaded successfully")
        return True
    except Exception as e:
        print(f"Error reloading Avahi daemon: {e}")
        return False


def get_mdns_dns_config():
    """
    Get optimal DNS configuration for mDNS-enabled peers
    Returns primary and secondary DNS servers
    """
    # For mDNS, we want:
    # 1. Local mDNS resolver (system resolver handles .local domains)
    # 2. Fallback to public DNS
    return "127.0.0.1", "8.8.8.8"


def generate_peer_mdns_config(peer):
    """
    Generate mDNS-specific configuration for a peer
    This includes hostname and service discovery settings
    """
    instance = peer.wireguard_instance
    domain = f"wg{instance.instance_id}.local"
    
    # Get peer IP
    peer_ip = peer.peerallowedip_set.filter(config_file='server', priority=0).first()
    if not peer_ip:
        return None
    
    hostname = peer.hostname or peer.name or f"peer-{peer.uuid.hex[:8]}"
    
    config = {
        'hostname': hostname,
        'domain': domain,
        'full_hostname': f"{hostname}.{domain}",
        'global_hostname': f"{hostname}.wg.local",
        'ip_address': peer_ip.allowed_ip,
        'instance_id': instance.instance_id,
        'instance_name': instance.name or f"wg{instance.instance_id}",
    }
    
    return config
