import uuid

from django.db import models


class DNSSettings(models.Model):
    name = models.CharField(default='dns_settings', max_length=100)
    dns_primary = models.GenericIPAddressField(blank=True, null=True, default='1.1.1.1')
    dns_secondary = models.GenericIPAddressField(blank=True, null=True, default='1.0.0.1')
    pending_changes = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)


class StaticHost(models.Model):
    hostname = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField(protocol='IPv4')
    description = models.TextField(blank=True, null=True)
    enabled = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"{self.hostname} -> {self.ip_address}"


class DNSFilterList(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    enabled = models.BooleanField(default=True)
    file_path = models.CharField(max_length=500, blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.name


class HADDNSConfig(models.Model):
    """Configuration for Handshake-Aware Dynamic DNS Resolution"""
    name = models.CharField(default='haddns_config', max_length=100, unique=True)
    enabled = models.BooleanField(default=True, help_text="Enable HADDNS functionality")
    handshake_threshold_seconds = models.PositiveIntegerField(
        default=300, 
        help_text="Time in seconds after which a peer is considered offline (default: 5 minutes)"
    )
    update_interval_seconds = models.PositiveIntegerField(
        default=60,
        help_text="How often to check handshakes and update DNS records (default: 1 minute)"
    )
    domain_suffix = models.CharField(
        max_length=100, 
        default='vpn.local',
        help_text="Domain suffix for peer hostnames (e.g., vpn.local)"
    )
    dynamic_hosts_file = models.CharField(
        max_length=500,
        default='/etc/dnsmasq.d/haddns_dynamic_hosts.conf',
        help_text="Path to dnsmasq dynamic hosts file"
    )
    include_offline_peers = models.BooleanField(
        default=False,
        help_text="Include offline peers in DNS with a special suffix (e.g., .offline)"
    )
    offline_suffix = models.CharField(
        max_length=50,
        default='.offline',
        help_text="Suffix to add to offline peer hostnames"
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"HADDNS Config ({'enabled' if self.enabled else 'disabled'})"

    @classmethod
    def get_config(cls):
        """Get or create the HADDNS configuration"""
        config, created = cls.objects.get_or_create(name='haddns_config')
        return config


class PeerHostnameMapping(models.Model):
    """Maps WireGuard peers to their hostnames for HADDNS"""
    peer = models.OneToOneField('wireguard.Peer', on_delete=models.CASCADE, related_name='haddns_mapping')
    hostname = models.CharField(max_length=100, help_text="Primary hostname for this peer")
    custom_domain = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Custom domain override (optional)"
    )
    enabled = models.BooleanField(default=True, help_text="Enable DNS resolution for this peer")
    last_handshake_check = models.DateTimeField(blank=True, null=True)
    is_online = models.BooleanField(default=False, help_text="Whether peer is currently online based on handshakes")

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"{self.hostname} -> {self.peer.public_key[:16]}..."

    @property
    def effective_domain(self):
        """Get the effective domain for this peer"""
        if self.custom_domain:
            return self.custom_domain
        config = HADDNSConfig.get_config()
        return config.domain_suffix

    @property
    def full_hostname(self):
        """Get the full hostname with domain"""
        return f"{self.hostname}.{self.effective_domain}"

    @property
    def offline_hostname(self):
        """Get the hostname for offline peers"""
        config = HADDNSConfig.get_config()
        return f"{self.hostname}{config.offline_suffix}.{self.effective_domain}"