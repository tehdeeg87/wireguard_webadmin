import os

from .models import DNSSettings, StaticHost, DNSFilterList


def generate_unbound_config():
    dns_settings = DNSSettings.objects.get(name='dns_settings')
    static_hosts = StaticHost.objects.all()
    if dns_settings.dns_primary:
        do_not_query_localhost = 'yes'
        forward_zone = f'\nforward-zone:\n    name: "."\n    forward-addr: {dns_settings.dns_primary}\n'
        if dns_settings.dns_secondary:
            forward_zone += f'    forward-addr: {dns_settings.dns_secondary}\n'
    else:
        do_not_query_localhost = 'no'
        forward_zone = ''


    unbound_config = f'''
server:
    interface: 0.0.0.0
    port: 53
    access-control: 0.0.0.0/0 allow
    do-ip4: yes
    do-ip6: no
    do-udp: yes
    local-zone: "local." static
    do-not-query-localhost: {do_not_query_localhost}
    verbosity: 1
'''
    unbound_config += forward_zone

    if static_hosts:
        unbound_config += '\nlocal-zone: "." transparent\n'
        for static_host in static_hosts:
            unbound_config += f'    local-data: "{static_host.hostname}. IN A {static_host.ip_address}"\n'
    return unbound_config


def generate_dnsdist_config():
    dns_settings = DNSSettings.objects.get(name='dns_settings')
    static_hosts = StaticHost.objects.all()
    dnsdist_config = "setLocal('0.0.0.0:53')\n"
    dnsdist_config += "setACL('0.0.0.0/0')\n"

    if dns_settings.dns_primary:
        dnsdist_config += f"newServer({{address='{dns_settings.dns_primary}', pool='upstreams'}})\n"
    if dns_settings.dns_secondary:
        dnsdist_config += f"newServer({{address='{dns_settings.dns_secondary}', pool='upstreams'}})\n"

    if static_hosts:
        dnsdist_config += "addAction(makeRule(''), PoolAction('staticHosts'))\n"
        for static_host in static_hosts:
            dnsdist_config += f"addLocal('{static_host.hostname}', '{static_host.ip_address}')\n"

    return dnsdist_config


def generate_dnsmasq_config():
    from wireguard.models import Peer, PeerAllowedIP, WireGuardInstance
    
    dns_settings = DNSSettings.objects.get(name='dns_settings')
    static_hosts = StaticHost.objects.all()
    dns_lists = DNSFilterList.objects.filter(enabled=True)
    
    dnsmasq_config = f'''
no-dhcp-interface=
listen-address=0.0.0.0
bind-interfaces

'''
    if dns_settings.dns_primary:
        dnsmasq_config += f'server={dns_settings.dns_primary}\n'
    if dns_settings.dns_secondary:
        dnsmasq_config += f'server={dns_settings.dns_secondary}\n'

    # Add static hosts
    if static_hosts:
        dnsmasq_config += '\n# Static hosts\n'
        for static_host in static_hosts:
            dnsmasq_config += f'address=/{static_host.hostname}/{static_host.ip_address}\n'

    # Add per-instance peer hostnames
    instances = WireGuardInstance.objects.all()
    for instance in instances:
        instance_name = instance.name or f'wg{instance.instance_id}'
        peers_with_hostnames = Peer.objects.filter(
            wireguard_instance=instance,
            hostname__isnull=False
        ).exclude(hostname='')
        
        if peers_with_hostnames:
            dnsmasq_config += f'\n# Peer hostnames for {instance_name}\n'
            for peer in peers_with_hostnames:
                # Get the peer's IP address (priority 0 from server config)
                peer_ip = PeerAllowedIP.objects.filter(
                    peer=peer, 
                    config_file='server', 
                    priority=0
                ).first()
                if peer_ip:
                    # Global hostname (e.g., laptop)
                    dnsmasq_config += f'address=/{peer.hostname}/{peer_ip.allowed_ip}\n'
                    # Instance-specific hostname (e.g., laptop.wg0)
                    dnsmasq_config += f'address=/{peer.hostname}.{instance_name}/{peer_ip.allowed_ip}\n'
                    # Instance-specific hostname with domain (e.g., laptop.wg0.local)
                    dnsmasq_config += f'address=/{peer.hostname}.{instance_name}.local/{peer_ip.allowed_ip}\n'

    if dns_lists:
        dnsmasq_config += '\n# DNS filter lists\n'
        for dns_list in dns_lists:
            file_path = os.path.join("/etc/dnsmasq/", f"{dns_list.uuid}.conf")
            dnsmasq_config += f'addn-hosts={file_path}\n'
    
    # Add per-instance hosts files
    dnsmasq_config += '\n# Per-instance hosts files\n'
    for instance in instances:
        hosts_file = f'/etc/dnsmasq/peers_wg{instance.instance_id}.hosts'
        dnsmasq_config += f'addn-hosts={hosts_file}\n'
    
    # Add HADDNS dynamic hosts file
    try:
        from .models import HADDNSConfig
        haddns_config = HADDNSConfig.get_config()
        if haddns_config.enabled:
            dnsmasq_config += f'\n# HADDNS Dynamic Hosts File\n'
            dnsmasq_config += f'addn-hosts={haddns_config.dynamic_hosts_file}\n'
    except Exception:
        # HADDNS not configured yet, skip
        pass
    
    return dnsmasq_config


def generate_per_instance_hosts_files():
    """Generate per-instance hosts files for dnsmasq"""
    from wireguard.models import Peer, PeerAllowedIP, WireGuardInstance
    import os
    
    # Create dnsmasq_hosts directory if it doesn't exist
    hosts_dir = '/etc/dnsmasq/hosts'
    os.makedirs(hosts_dir, exist_ok=True)
    
    instances = WireGuardInstance.objects.all()
    
    for instance in instances:
        instance_name = instance.name or f'wg{instance.instance_id}'
        hosts_file = os.path.join(hosts_dir, f'peers_wg{instance.instance_id}.hosts')
        
        # Get all peers for this instance with hostnames
        peers_with_hostnames = Peer.objects.filter(
            wireguard_instance=instance,
            hostname__isnull=False
        ).exclude(hostname='')
        
        hosts_content = f"# Hosts file for WireGuard instance {instance_name} (wg{instance.instance_id})\n"
        hosts_content += f"# Generated automatically - do not edit manually\n\n"
        
        for peer in peers_with_hostnames:
            # Get the peer's IP address (priority 0 from server config)
            peer_ip = PeerAllowedIP.objects.filter(
                peer=peer, 
                config_file='server', 
                priority=0
            ).first()
            
            if peer_ip:
                # Add multiple hostname formats for flexibility
                hosts_content += f"{peer_ip.allowed_ip}\t{peer.hostname}\n"
                hosts_content += f"{peer_ip.allowed_ip}\t{peer.hostname}.{instance_name}\n"
                hosts_content += f"{peer_ip.allowed_ip}\t{peer.hostname}.{instance_name}.local\n"
                hosts_content += f"{peer_ip.allowed_ip}\tpeer-{peer.uuid}\n"  # UUID-based hostname
                hosts_content += f"{peer_ip.allowed_ip}\tpeer-{peer.uuid}.{instance_name}\n"
                hosts_content += "\n"
        
        # Write the hosts file
        with open(hosts_file, 'w') as f:
            f.write(hosts_content)
        
        print(f"Generated hosts file: {hosts_file}")


def reload_dnsmasq():
    """Send SIGHUP to dnsmasq to reload configuration"""
    import subprocess
    import signal
    
    try:
        # Find dnsmasq process and send SIGHUP
        result = subprocess.run(['pgrep', 'dnsmasq'], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    os.kill(int(pid), signal.SIGHUP)
            print("dnsmasq configuration reloaded successfully")
        else:
            print("dnsmasq process not found")
    except Exception as e:
        print(f"Error reloading dnsmasq: {e}")
