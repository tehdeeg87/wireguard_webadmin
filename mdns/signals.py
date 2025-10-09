"""
Django signals for mDNS peer discovery
Automatically update mDNS configuration when peers or instances change
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.management import call_command
from wireguard.models import Peer, WireGuardInstance


@receiver(post_save, sender=Peer)
def update_mdns_on_peer_change(sender, instance, created, **kwargs):
    """Update mDNS configuration when a peer is created or modified"""
    try:
        # Update both mDNS hosts files and Avahi registration
        call_command('update_peer_mdns', '--reload')
        call_command('register_peers_avahi', '--reload', '--instance-id', instance.wireguard_instance.instance_id)
        print(f"mDNS and Avahi updated for peer change: {instance}")
    except Exception as e:
        print(f"Error updating mDNS/Avahi for peer change: {e}")


@receiver(post_delete, sender=Peer)
def update_mdns_on_peer_delete(sender, instance, **kwargs):
    """Update mDNS configuration when a peer is deleted"""
    try:
        # Update both mDNS hosts files and Avahi registration
        call_command('update_peer_mdns', '--reload')
        call_command('register_peers_avahi', '--reload', '--instance-id', instance.wireguard_instance.instance_id)
        print(f"mDNS and Avahi updated for peer deletion: {instance}")
    except Exception as e:
        print(f"Error updating mDNS/Avahi for peer deletion: {e}")


@receiver(post_save, sender=WireGuardInstance)
def update_mdns_on_instance_change(sender, instance, created, **kwargs):
    """Update mDNS configuration when a WireGuard instance is created or modified"""
    try:
        # Update both mDNS hosts files and Avahi registration
        call_command('update_peer_mdns', '--reload')
        call_command('register_peers_avahi', '--reload', '--instance-id', instance.instance_id)
        print(f"mDNS and Avahi updated for instance change: {instance}")
    except Exception as e:
        print(f"Error updating mDNS/Avahi for instance change: {e}")


@receiver(post_delete, sender=WireGuardInstance)
def update_mdns_on_instance_delete(sender, instance, **kwargs):
    """Update mDNS configuration when a WireGuard instance is deleted"""
    try:
        # Update both mDNS hosts files and Avahi registration
        call_command('update_peer_mdns', '--reload')
        call_command('register_peers_avahi', '--reload')
        print(f"mDNS and Avahi updated for instance deletion: {instance}")
    except Exception as e:
        print(f"Error updating mDNS/Avahi for instance deletion: {e}")
