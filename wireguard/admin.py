from django.contrib import admin
from .models import WireGuardInstance, Peer, PeerAllowedIP, PeerStatus, WebadminSettings


class WireGuardInstanceAdmin(admin.ModelAdmin):
    list_display = ('name', 'instance_id', 'hostname', 'listen_port', 'address', 'netmask', 'allow_peer_to_peer', 'created', 'updated')
    search_fields = ('name', 'instance_id', 'hostname', 'listen_port', 'address', 'netmask')
    list_filter = ('allow_peer_to_peer', 'created', 'updated')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'instance_id', 'hostname', 'listen_port')
        }),
        ('Network Configuration', {
            'fields': ('address', 'netmask', 'dns_primary', 'dns_secondary')
        }),
        ('Keys', {
            'fields': ('private_key', 'public_key'),
            'classes': ('collapse',)
        }),
        ('Advanced Settings', {
            'fields': ('post_up', 'post_down', 'peer_list_refresh_interval', 'allow_peer_to_peer'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('pending_changes', 'legacy_firewall'),
            'classes': ('collapse',)
        })
    )

admin.site.register(WireGuardInstance, WireGuardInstanceAdmin)


class PeerAdmin(admin.ModelAdmin):
    list_display = ('name', 'public_key', 'pre_shared_key', 'persistent_keepalive', 'wireguard_instance', 'created', 'updated', 'uuid')
    search_fields = ('name', 'public_key', 'pre_shared_key', 'persistent_keepalive', 'wireguard_instance', 'created', 'updated', 'uuid')

admin.site.register(Peer, PeerAdmin)


class PeerStatusAdmin(admin.ModelAdmin):
    list_display = ('peer', 'last_handshake', 'created', 'updated', 'uuid')
    search_fields = ('peer', 'last_handshake', 'created', 'updated', 'uuid')

admin.site.register(PeerStatus, PeerStatusAdmin)


class PeerAllowedIPAdmin(admin.ModelAdmin):
    list_display = ('peer', 'priority', 'allowed_ip', 'netmask', 'created', 'updated', 'uuid')
    search_fields = ('peer', 'priority', 'allowed_ip', 'netmask', 'created', 'updated', 'uuid')

admin.site.register(PeerAllowedIP, PeerAllowedIPAdmin)


class WebadminSettingsAdmin(admin.ModelAdmin):
    list_display = ('current_version', 'latest_version', 'update_available', 'created', 'updated', 'uuid')
    search_fields = ('current_version', 'latest_version', 'update_available', 'created', 'updated', 'uuid')

admin.site.register(WebadminSettings, WebadminSettingsAdmin)