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
    from wireguard.models import Peer, PeerAllowedIP
    
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

    # Add peer hostnames
    peers_with_hostnames = Peer.objects.filter(hostname__isnull=False).exclude(hostname='')
    if peers_with_hostnames:
        dnsmasq_config += '\n# Peer hostnames\n'
        for peer in peers_with_hostnames:
            # Get the peer's IP address (priority 0 from server config)
            peer_ip = PeerAllowedIP.objects.filter(
                peer=peer, 
                config_file='server', 
                priority=0
            ).first()
            if peer_ip:
                dnsmasq_config += f'address=/{peer.hostname}/{peer_ip.allowed_ip}\n'
                # Also add instance-specific hostname (e.g., laptop.wg0)
                instance_name = peer.wireguard_instance.name or f'wg{peer.wireguard_instance.instance_id}'
                dnsmasq_config += f'address=/{peer.hostname}.{instance_name}/{peer_ip.allowed_ip}\n'

    if dns_lists:
        dnsmasq_config += '\n# DNS filter lists\n'
        for dns_list in dns_lists:
            file_path = os.path.join("/etc/dnsmasq/", f"{dns_list.uuid}.conf")
            dnsmasq_config += f'addn-hosts={file_path}\n'
    return dnsmasq_config
