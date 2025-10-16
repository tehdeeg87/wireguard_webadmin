"""
Django signals for DNS management
Automatically update dnsmasq hosts file when peers or instances change
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Peer, WireGuardInstance
from .dns_utils import write_dnsmasq_hosts_file, reload_dnsmasq


@receiver(post_save, sender=Peer)
def sync_name_to_hostname(sender, instance, created, **kwargs):
    """Automatically sync the name field to hostname field for DNS"""
    if instance.name and instance.hostname != instance.name:
        instance.hostname = instance.name
        instance.save(update_fields=['hostname'])
        print(f"DNS: Synced hostname to name for peer: {instance.name}")


@receiver(post_save, sender=Peer)
def update_dns_on_peer_change(sender, instance, created, **kwargs):
    """Update DNS configuration when a peer is created or modified"""
    try:
        print(f"DNS: Peer {'created' if created else 'updated'}: {instance}")
        
        # Write the updated hosts file
        if write_dnsmasq_hosts_file():
            # Optionally reload dnsmasq (it will auto-detect file changes)
            reload_dnsmasq()
        else:
            print(f"DNS: Failed to update hosts file for peer {instance}")
            
    except Exception as e:
        print(f"DNS: Error updating DNS for peer change: {e}")


@receiver(post_delete, sender=Peer)
def update_dns_on_peer_delete(sender, instance, **kwargs):
    """Update DNS configuration when a peer is deleted"""
    try:
        print(f"DNS: Peer deleted: {instance}")
        
        # Write the updated hosts file
        if write_dnsmasq_hosts_file():
            # Optionally reload dnsmasq
            reload_dnsmasq()
        else:
            print(f"DNS: Failed to update hosts file after peer deletion")
            
    except Exception as e:
        print(f"DNS: Error updating DNS for peer deletion: {e}")


@receiver(post_save, sender=WireGuardInstance)
def update_dns_on_instance_change(sender, instance, created, **kwargs):
    """Update DNS configuration when a WireGuard instance is modified"""
    try:
        print(f"DNS: WireGuard instance {'created' if created else 'updated'}: {instance}")
        
        # Only update if this affects peer IPs (like address changes)
        if not created:
            # Rebuild the entire hosts file to ensure consistency
            write_dnsmasq_hosts_file()
            
    except Exception as e:
        print(f"DNS: Error updating DNS for instance change: {e}")
