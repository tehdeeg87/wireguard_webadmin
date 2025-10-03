from django.core.management.base import BaseCommand
from django.conf import settings
from dns.functions import generate_dnsmasq_config, generate_per_instance_hosts_files
from wireguard.models import WireGuardInstance, Peer, PeerAllowedIP


class Command(BaseCommand):
    help = 'Test DNS resolution functionality and show current configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--show-config',
            action='store_true',
            help='Show the generated dnsmasq configuration',
        )
        parser.add_argument(
            '--show-hosts',
            action='store_true',
            help='Show the generated hosts files',
        )
        parser.add_argument(
            '--test-resolution',
            action='store_true',
            help='Test DNS resolution for peer hostnames',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('DNS Resolution Test'))
        self.stdout.write('=' * 50)
        
        # Show instances and peers
        instances = WireGuardInstance.objects.all()
        self.stdout.write(f"\nFound {instances.count()} WireGuard instances:")
        
        for instance in instances:
            instance_name = instance.name or f'wg{instance.instance_id}'
            peers = Peer.objects.filter(wireguard_instance=instance, hostname__isnull=False).exclude(hostname='')
            self.stdout.write(f"  - {instance_name} (wg{instance.instance_id}): {peers.count()} peers with hostnames")
            
            for peer in peers:
                peer_ip = PeerAllowedIP.objects.filter(
                    peer=peer, 
                    config_file='server', 
                    priority=0
                ).first()
                if peer_ip:
                    self.stdout.write(f"    * {peer.hostname} -> {peer_ip.allowed_ip}")
        
        # Show dnsmasq configuration
        if options['show_config']:
            self.stdout.write(f"\n{self.style.SUCCESS('dnsmasq Configuration:')}")
            self.stdout.write('-' * 30)
            config = generate_dnsmasq_config()
            self.stdout.write(config)
        
        # Show hosts files
        if options['show_hosts']:
            self.stdout.write(f"\n{self.style.SUCCESS('Per-instance Hosts Files:')}")
            self.stdout.write('-' * 30)
            generate_per_instance_hosts_files()
            
            import os
            hosts_dir = '/etc/dnsmasq/hosts'
            if os.path.exists(hosts_dir):
                for file in os.listdir(hosts_dir):
                    if file.endswith('.hosts'):
                        file_path = os.path.join(hosts_dir, file)
                        self.stdout.write(f"\n{file}:")
                        with open(file_path, 'r') as f:
                            self.stdout.write(f.read())
        
        # Test DNS resolution
        if options['test_resolution']:
            self.stdout.write(f"\n{self.style.SUCCESS('DNS Resolution Test:')}")
            self.stdout.write('-' * 30)
            self.test_dns_resolution()
        
        self.stdout.write(f"\n{self.style.SUCCESS('Test completed!')}")

    def test_dns_resolution(self):
        """Test DNS resolution for peer hostnames"""
        import subprocess
        
        # Test basic DNS resolution
        try:
            result = subprocess.run(['nslookup', 'google.com'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.stdout.write("✓ Basic DNS resolution working")
            else:
                self.stdout.write("✗ Basic DNS resolution failed")
        except Exception as e:
            self.stdout.write(f"✗ DNS test error: {e}")
        
        # Test peer hostname resolution
        peers = Peer.objects.filter(hostname__isnull=False).exclude(hostname='')[:3]  # Test first 3 peers
        for peer in peers:
            peer_ip = PeerAllowedIP.objects.filter(
                peer=peer, 
                config_file='server', 
                priority=0
            ).first()
            
            if peer_ip:
                instance_name = peer.wireguard_instance.name or f'wg{peer.wireguard_instance.instance_id}'
                hostnames_to_test = [
                    peer.hostname,
                    f"{peer.hostname}.{instance_name}",
                    f"{peer.hostname}.{instance_name}.local"
                ]
                
                for hostname in hostnames_to_test:
                    try:
                        result = subprocess.run(['nslookup', hostname], capture_output=True, text=True, timeout=5)
                        if result.returncode == 0 and peer_ip.allowed_ip in result.stdout:
                            self.stdout.write(f"✓ {hostname} -> {peer_ip.allowed_ip}")
                        else:
                            self.stdout.write(f"✗ {hostname} (not found)")
                    except Exception as e:
                        self.stdout.write(f"✗ {hostname} (error: {e})")
