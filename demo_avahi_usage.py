#!/usr/bin/env python3
"""
Demo script showing how to use the new Avahi peer hostname resolution
"""

import os
import sys
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wireguard_webadmin.settings')
application = get_wsgi_application()

from wireguard.models import Peer, WireGuardInstance, PeerAllowedIP


def demo_peer_hostnames():
    """Demonstrate peer hostname information"""
    print("🔍 WireGuard Peer Hostname Information")
    print("=" * 50)
    
    instances = WireGuardInstance.objects.all()
    
    for instance in instances:
        print(f"\n📡 Instance: wg{instance.instance_id} ({instance.name or 'Unnamed'})")
        print(f"   Hostname: {instance.hostname}")
        print(f"   Address: {instance.address}/{instance.netmask}")
        
        peers = Peer.objects.filter(wireguard_instance=instance)
        
        for peer in peers:
            peer_ip = peer.peerallowedip_set.filter(config_file='server', priority=0).first()
            if not peer_ip:
                continue
                
            hostname = peer.hostname or peer.name or f"peer-{peer.uuid.hex[:8]}"
            instance_domain = f"wg{instance.instance_id}.local"
            global_domain = "wg.local"
            
            print(f"\n   👤 Peer: {peer.name or 'Unnamed'}")
            print(f"      IP Address: {peer_ip.allowed_ip}")
            print(f"      Hostname: {hostname}")
            print(f"      Instance Domain: {hostname}.{instance_domain}")
            print(f"      Global Domain: {hostname}.{global_domain}")
            print(f"      UUID: {peer.uuid}")


def demo_avahi_commands():
    """Demonstrate available Avahi management commands"""
    print("\n\n🛠️  Available Avahi Management Commands")
    print("=" * 50)
    
    commands = [
        {
            'command': 'register_peers_avahi',
            'description': 'Register all peers with Avahi for hostname resolution',
            'example': 'python manage.py register_peers_avahi --reload'
        },
        {
            'command': 'register_peers_avahi --instance-id 0',
            'description': 'Register peers for specific instance only',
            'example': 'python manage.py register_peers_avahi --instance-id 0 --reload'
        },
        {
            'command': 'update_peer_mdns',
            'description': 'Update mDNS hosts files for all instances',
            'example': 'python manage.py update_peer_mdns --reload'
        }
    ]
    
    for cmd in commands:
        print(f"\n📋 {cmd['command']}")
        print(f"   Description: {cmd['description']}")
        print(f"   Example: {cmd['example']}")


def demo_resolution_examples():
    """Show examples of how to resolve peer hostnames"""
    print("\n\n🔍 Peer Hostname Resolution Examples")
    print("=" * 50)
    
    print("""
Once Avahi is running and peers are registered, you can resolve peer hostnames using:

1. Command line tools:
   avahi-resolve-host-name peer-hostname
   avahi-resolve-host-name peer-hostname.wg0.local
   avahi-resolve-host-name peer-hostname.wg.local
   
   nslookup peer-hostname
   nslookup peer-hostname.wg0.local
   
2. From other peers in the VPN:
   ping peer-hostname
   ping peer-hostname.wg0.local
   ssh user@peer-hostname.wg0.local
   
3. Service discovery:
   avahi-browse -t _wireguard._tcp
   avahi-browse -a
   
4. From applications:
   - Most applications will automatically resolve .local domains
   - Use the full hostname for best results: hostname.wg0.local
   - Fallback to IP address if hostname resolution fails
""")


def main():
    """Main demo function"""
    print("🚀 WireGuard WebAdmin - Avahi Peer Hostname Resolution Demo")
    print("=" * 70)
    
    # Show peer information
    demo_peer_hostnames()
    
    # Show available commands
    demo_avahi_commands()
    
    # Show resolution examples
    demo_resolution_examples()
    
    print("\n" + "=" * 70)
    print("✅ Demo completed! Your peers should now be resolvable via hostname.")
    print("💡 Tip: Run 'python test_avahi_peer_resolution.py' to test resolution.")


if __name__ == "__main__":
    main()
