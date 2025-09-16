from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.management import call_command
from wireguard.models import Peer, PeerAllowedIP


@receiver(post_save, sender=Peer)
def update_dns_on_peer_change(sender, instance, created, **kwargs):
    """Update DNS configuration when a peer is created or modified."""
    try:
        call_command('update_peer_dns')
    except Exception as e:
        print(f"Error updating DNS configuration: {e}")


@receiver(post_delete, sender=Peer)
def update_dns_on_peer_delete(sender, instance, **kwargs):
    """Update DNS configuration when a peer is deleted."""
    try:
        call_command('update_peer_dns')
    except Exception as e:
        print(f"Error updating DNS configuration: {e}")


@receiver(post_save, sender=PeerAllowedIP)
def update_dns_on_peer_ip_change(sender, instance, created, **kwargs):
    """Update DNS configuration when a peer's IP address changes."""
    try:
        call_command('update_peer_dns')
    except Exception as e:
        print(f"Error updating DNS configuration: {e}")


@receiver(post_delete, sender=PeerAllowedIP)
def update_dns_on_peer_ip_delete(sender, instance, **kwargs):
    """Update DNS configuration when a peer's IP address is deleted."""
    try:
        call_command('update_peer_dns')
    except Exception as e:
        print(f"Error updating DNS configuration: {e}")
