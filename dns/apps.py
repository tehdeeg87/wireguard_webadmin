from django.apps import AppConfig


class DnsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dns'
    
    def ready(self):
        # Import signals to register them
        from . import signals
        from django.db.models.signals import post_save, post_delete
        
        # Register signals for Peer model
        from wireguard.models import Peer, WireGuardInstance
        
        post_save.connect(signals.update_dnsmasq_on_peer_change, sender=Peer)
        post_delete.connect(signals.update_dnsmasq_on_peer_delete, sender=Peer)
        
        # Register signals for WireGuardInstance model
        post_save.connect(signals.update_dnsmasq_on_instance_change, sender=WireGuardInstance)
        post_delete.connect(signals.update_dnsmasq_on_instance_delete, sender=WireGuardInstance)
        
        # HADDNS signals are automatically registered via @receiver decorators