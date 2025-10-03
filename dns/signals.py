import os
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings


def update_dnsmasq_on_peer_change(sender, instance, created, **kwargs):
    """Update dnsmasq configuration when a peer is created or modified"""
    try:
        from .management.commands.update_peer_dns import Command as UpdatePeerDNSCommand
        # Update dnsmasq configuration with reload
        command = UpdatePeerDNSCommand()
        command.handle(reload=True)
        
    except Exception as e:
        # Log error but don't fail the peer creation
        print(f"Error updating dnsmasq configuration: {e}")


def update_dnsmasq_on_peer_delete(sender, instance, **kwargs):
    """Update dnsmasq configuration when a peer is deleted"""
    try:
        from .management.commands.update_peer_dns import Command as UpdatePeerDNSCommand
        # Update dnsmasq configuration with reload
        command = UpdatePeerDNSCommand()
        command.handle(reload=True)
        
    except Exception as e:
        # Log error but don't fail the peer deletion
        print(f"Error updating dnsmasq configuration: {e}")


def update_dnsmasq_on_instance_change(sender, instance, created, **kwargs):
    """Update dnsmasq configuration when a WireGuard instance is created or modified"""
    try:
        from .management.commands.update_peer_dns import Command as UpdatePeerDNSCommand
        # Update dnsmasq configuration with reload
        command = UpdatePeerDNSCommand()
        command.handle(reload=True)
        
    except Exception as e:
        # Log error but don't fail the instance creation
        print(f"Error updating dnsmasq configuration: {e}")


def update_dnsmasq_on_instance_delete(sender, instance, **kwargs):
    """Update dnsmasq configuration when a WireGuard instance is deleted"""
    try:
        from .management.commands.update_peer_dns import Command as UpdatePeerDNSCommand
        # Update dnsmasq configuration with reload
        command = UpdatePeerDNSCommand()
        command.handle(reload=True)
        
    except Exception as e:
        # Log error but don't fail the instance deletion
        print(f"Error updating dnsmasq configuration: {e}")