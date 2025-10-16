from django.core.exceptions import ValidationError
from django.db import models
import uuid

NETMASK_CHOICES = (
        (8, '/8 (255.0.0.0)'),
        (9, '/9 (255.128.0.0)'),
        (10, '/10 (255.192.0.0)'),
        (11, '/11 (255.224.0.0)'),
        (12, '/12 (255.240.0.0)'),
        (13, '/13 (255.248.0.0)'),
        (14, '/14 (255.252.0.0)'),
        (15, '/15 (255.254.0.0)'),
        (16, '/16 (255.255.0.0)'),
        (17, '/17 (255.255.128.0)'),
        (18, '/18 (255.255.192.0)'),
        (19, '/19 (255.255.224.0)'),
        (20, '/20 (255.255.240.0)'),
        (21, '/21 (255.255.248.0)'),
        (22, '/22 (255.255.252.0)'),
        (23, '/23 (255.255.254.0)'),
        (24, '/24 (255.255.255.0)'),
        (25, '/25 (255.255.255.128)'),
        (26, '/26 (255.255.255.192)'),
        (27, '/27 (255.255.255.224)'),
        (28, '/28 (255.255.255.240)'),
        (29, '/29 (255.255.255.248)'),
        (30, '/30 (255.255.255.252)'),
        (32, '/32 (255.255.255.255)'),
    )


class WebadminSettings(models.Model):
    name = models.CharField(default='webadmin_settings', max_length=20, unique=True)
    db_patch_version = models.IntegerField(default=0)
    update_available = models.BooleanField(default=False)
    current_version = models.PositiveIntegerField(default=0)
    latest_version = models.PositiveIntegerField(default=0)
    last_checked = models.DateTimeField(blank=True, null=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.name


class WireGuardInstance(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    instance_id = models.PositiveIntegerField(unique=True, default=0)
    private_key = models.CharField(max_length=100)
    public_key = models.CharField(max_length=100)
    hostname = models.CharField(max_length=100)
    listen_port = models.IntegerField(default=51820, unique=True)
    address = models.GenericIPAddressField(unique=True, protocol='IPv4')
    netmask = models.IntegerField(default=24, choices=NETMASK_CHOICES)
    post_up = models.TextField(blank=True, null=True)
    post_down = models.TextField(blank=True, null=True)
    peer_list_refresh_interval = models.IntegerField(default=10)
    dns_primary = models.GenericIPAddressField(unique=False, protocol='IPv4', default='172.19.0.2', blank=True, null=True)
    dns_secondary = models.GenericIPAddressField(unique=False, protocol='IPv4', default='8.8.8.8', blank=True, null=True)
    pending_changes = models.BooleanField(default=True)
    legacy_firewall = models.BooleanField(default=False)
    #allow_peer_to_peer = models.BooleanField(default=True, help_text="Allow peers within this instance to communicate with each other")
    
    # Bandwidth limiting fields
    bandwidth_limit_enabled = models.BooleanField(default=True, help_text="Enable bandwidth limiting for this instance")
    bandwidth_limit_mbps = models.PositiveIntegerField(default=50, help_text="Bandwidth limit in Mbps")

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)

    def __str__(self):
        if self.name:
            return self.name    
        else:
            return 'wg' + str(self.instance_id)


class Peer(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    hostname = models.CharField(max_length=100, blank=True, null=True, help_text="DNS hostname for this peer (e.g., 'laptop', 'server')")
    public_key = models.CharField(max_length=100)
    pre_shared_key = models.CharField(max_length=100)
    private_key = models.CharField(max_length=100, blank=True, null=True)
    persistent_keepalive = models.IntegerField(default=25)
    wireguard_instance = models.ForeignKey(WireGuardInstance, on_delete=models.CASCADE)
    sort_order = models.IntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)

    def save(self, *args, **kwargs):
        # Automatically set hostname to name if not set or if name changed
        if self.name and (not self.hostname or self.hostname != self.name):
            self.hostname = self.name
        super().save(*args, **kwargs)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return self.public_key[:16] + "..."


class PeerStatus(models.Model):
    peer = models.OneToOneField(Peer, on_delete=models.CASCADE)
    last_handshake = models.DateTimeField(blank=True, null=True)
    transfer_rx = models.BigIntegerField(default=0)
    transfer_tx = models.BigIntegerField(default=0)
    latest_config = models.TextField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)

    def __str__(self):
        return str(self.peer)


class PeerAllowedIP(models.Model):
    peer = models.ForeignKey(Peer, on_delete=models.CASCADE)
    priority = models.PositiveBigIntegerField(default=1)
    allowed_ip = models.GenericIPAddressField(protocol='IPv4')
    netmask = models.IntegerField(default=32, choices=NETMASK_CHOICES)
    config_file = models.CharField(max_length=6, choices=(('server', 'Server Config'), ('client', 'Client config')), default='server')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)

    def __str__(self):
        return str(self.allowed_ip) + '/' + str(self.netmask)


class PeerGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    peer = models.ManyToManyField(Peer, blank=True)
    server_instance = models.ManyToManyField(WireGuardInstance, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)

    def __str__(self):
        return self.name

