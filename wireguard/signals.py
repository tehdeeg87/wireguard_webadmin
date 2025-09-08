from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WireGuardInstance
from firewall.tools import export_firewall_configuration
import subprocess
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=WireGuardInstance)
def apply_firewall_rules_on_instance_creation(sender, instance, created, **kwargs):
    """
    Automatically apply firewall rules when a new WireGuard instance is created.
    This ensures peer-to-peer communication works immediately after instance creation.
    """
    if created:  # Only run for new instances, not updates
        try:
            logger.info(f"New WireGuard instance created: wg{instance.instance_id}")
            
            # Generate firewall script with all instances
            export_firewall_configuration()
            
            # Apply the firewall rules
            result = subprocess.run(['bash', '/etc/wireguard/wg-firewall.sh'], 
                                  capture_output=True, text=True, check=True)
            
            logger.info(f"✅ Firewall rules applied successfully for wg{instance.instance_id}")
            logger.debug(f"Firewall script output: {result.stdout}")
            
        except subprocess.CalledProcessError as e:
            # Log error but don't fail instance creation
            logger.error(f"❌ Failed to apply firewall rules for wg{instance.instance_id}: {e}")
            logger.error(f"Firewall script stderr: {e.stderr}")
        except Exception as e:
            # Log any other errors
            logger.error(f"❌ Unexpected error applying firewall rules for wg{instance.instance_id}: {e}")
