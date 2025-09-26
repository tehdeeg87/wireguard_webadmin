import os
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings


def update_coredns_on_peer_change(sender, instance, created, **kwargs):
    """Update CoreDNS zones when a peer is created or modified"""
    try:
        from .management.commands.update_coredns_zones import Command as UpdateCoreDNSCommand
        # Update peers zone
        command = UpdateCoreDNSCommand()
        command.update_peers_zone(dry_run=False)
        
        # Also update instances zone in case peer IPs affect instance routing
        command.update_instances_zone(dry_run=False)
        
    except Exception as e:
        # Log error but don't fail the peer creation
        print(f"Error updating CoreDNS zones: {e}")


def update_coredns_on_peer_delete(sender, instance, **kwargs):
    """Update CoreDNS zones when a peer is deleted"""
    try:
        from .management.commands.update_coredns_zones import Command as UpdateCoreDNSCommand
        # Update peers zone
        command = UpdateCoreDNSCommand()
        command.update_peers_zone(dry_run=False)
        
    except Exception as e:
        # Log error but don't fail the peer deletion
        print(f"Error updating CoreDNS zones: {e}")


def update_coredns_on_instance_change(sender, instance, created, **kwargs):
    """Update CoreDNS zones when a WireGuard instance is created or modified"""
    try:
        from .management.commands.update_coredns_zones import Command as UpdateCoreDNSCommand
        # Update instances zone
        command = UpdateCoreDNSCommand()
        command.update_instances_zone(dry_run=False)
        
    except Exception as e:
        # Log error but don't fail the instance creation
        print(f"Error updating CoreDNS zones: {e}")


def update_coredns_on_instance_delete(sender, instance, **kwargs):
    """Update CoreDNS zones when a WireGuard instance is deleted"""
    try:
        from .management.commands.update_coredns_zones import Command as UpdateCoreDNSCommand
        # Update instances zone
        command = UpdateCoreDNSCommand()
        command.update_instances_zone(dry_run=False)
        
    except Exception as e:
        # Log error but don't fail the instance deletion
        print(f"Error updating CoreDNS zones: {e}")