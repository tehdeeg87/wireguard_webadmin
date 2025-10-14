import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import PeerHostnameMapping
from wireguard.models import Peer

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Peer)
def create_peer_hostname_mapping(sender, instance, created, **kwargs):
    """Automatically create HADDNS hostname mapping when a peer is created"""
    if created and instance.hostname:
        try:
            mapping, created = PeerHostnameMapping.objects.get_or_create(
                peer=instance,
                defaults={
                    'hostname': instance.hostname,
                    'enabled': True
                }
            )
            if created:
                logger.info(f"Created HADDNS mapping for peer {instance.hostname}")
            else:
                # Update existing mapping if hostname changed
                if mapping.hostname != instance.hostname:
                    mapping.hostname = instance.hostname
                    mapping.save()
                    logger.info(f"Updated HADDNS mapping for peer {instance.hostname}")
        except Exception as e:
            logger.error(f"Failed to create HADDNS mapping for peer {instance.hostname}: {e}")


@receiver(post_delete, sender=Peer)
def delete_peer_hostname_mapping(sender, instance, **kwargs):
    """Clean up HADDNS hostname mapping when a peer is deleted"""
    try:
        mapping = PeerHostnameMapping.objects.filter(peer=instance).first()
        if mapping:
            mapping.delete()
            logger.info(f"Deleted HADDNS mapping for peer {instance.hostname}")
    except Exception as e:
        logger.error(f"Failed to delete HADDNS mapping for peer {instance.hostname}: {e}")