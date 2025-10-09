"""
Avahi integration for WireGuard WebAdmin
Uses existing Peer and PeerAllowedIP models to generate mDNS host files
"""

import os
from django.conf import settings
from wireguard.models import Peer, PeerAllowedIP, WireGuardInstance


def generate_avahi_hosts_file(instance_id=None):
    """
    Generate Avahi hosts file using existing Peer and PeerAllowedIP models
    
    Args:
        instance_id: Specific instance ID, or None for all instances
    
    Returns:
        str: Path to generated hosts file
    """
    if instance_id is not None:
        instances = [WireGuardInstance.objects.get(instance_id=instance_id)]
    else:
        instances = WireGuardInstance.objects.all()
    
    hosts_content = []
    hosts_content.append("# Avahi hosts file for WireGuard peer resolution")
    hosts_content.append("# Generated automatically from Peer and PeerAllowedIP models")
    hosts_content.append("")
    
    for instance in instances:
        # Get all peers for this instance
        peers = Peer.objects.filter(wireguard_instance=instance)
        
        # Create instance-specific domain
        instance_domain = f"wg{instance.instance_id}.local"
        instance_name = instance.name or f"wg{instance.instance_id}"
        
        hosts_content.append(f"# Instance: {instance_name} ({instance_domain})")
        
        for peer in peers:
            # Get the peer's IP address (priority 0, server config)
            allowed_ip = PeerAllowedIP.objects.filter(
                peer=peer,
                config_file='server',
                priority=0
            ).first()
            
            if not allowed_ip:
                continue
            
            ip = allowed_ip.allowed_ip
            hostname = peer.hostname or peer.name or f"peer-{peer.uuid.hex[:8]}"
            
            # Add multiple hostname formats for flexibility
            hosts_content.append(f"# Peer: {peer.name}")
            hosts_content.append(f"{ip} {hostname}")
            hosts_content.append(f"{ip} {hostname}.{instance_domain}")
            hosts_content.append(f"{ip} {hostname}.wg.local")  # Global domain
            hosts_content.append(f"{ip} peer-{peer.uuid.hex[:8]}")
            hosts_content.append(f"{ip} peer-{peer.uuid.hex[:8]}.{instance_domain}")
            hosts_content.append("")
    
    # Write hosts file
    hosts_file = "/etc/avahi/hosts/wireguard_peers.hosts"
    os.makedirs(os.path.dirname(hosts_file), exist_ok=True)
    
    with open(hosts_file, 'w') as f:
        f.write('\n'.join(hosts_content))
    
    print(f"Generated Avahi hosts file: {hosts_file}")
    return hosts_file


def update_avahi_hosts():
    """
    Update Avahi hosts file and reload Avahi daemon
    """
    try:
        # Generate hosts file
        hosts_file = generate_avahi_hosts_file()
        
        # Reload Avahi daemon
        import subprocess
        subprocess.run(['pkill', '-HUP', 'avahi-daemon'], check=False)
        
        print("Avahi hosts file updated and daemon reloaded")
        return True
        
    except Exception as e:
        print(f"Error updating Avahi hosts: {e}")
        return False


def get_peer_mdns_info(peer):
    """
    Get mDNS information for a specific peer
    
    Args:
        peer: Peer instance
    
    Returns:
        dict: mDNS information for the peer
    """
    instance = peer.wireguard_instance
    instance_domain = f"wg{instance.instance_id}.local"
    
    # Get peer IP
    allowed_ip = PeerAllowedIP.objects.filter(
        peer=peer,
        config_file='server',
        priority=0
    ).first()
    
    if not allowed_ip:
        return None
    
    hostname = peer.hostname or peer.name or f"peer-{peer.uuid.hex[:8]}"
    
    return {
        'hostname': hostname,
        'ip_address': allowed_ip.allowed_ip,
        'instance_domain': instance_domain,
        'global_domain': 'wg.local',
        'full_hostname': f"{hostname}.{instance_domain}",
        'global_hostname': f"{hostname}.wg.local",
        'uuid_hostname': f"peer-{peer.uuid.hex[:8]}",
        'uuid_full_hostname': f"peer-{peer.uuid.hex[:8]}.{instance_domain}",
    }
