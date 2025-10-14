from django.contrib import admin
from django.utils.html import format_html

from .models import DNSFilterList, DNSSettings, StaticHost, HADDNSConfig, PeerHostnameMapping


class DNSFilterListAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'enabled', 'list_url', 'host_count', 'created', 'updated')
    list_filter = ('enabled', 'created', 'updated')
    search_fields = ('name', 'description', 'list_url')
    ordering = ('name', 'created')
admin.site.register(DNSFilterList, DNSFilterListAdmin)


class DNSSettingsAdmin(admin.ModelAdmin):
    list_display = ('dns_primary', 'dns_secondary', 'pending_changes', 'created', 'updated')
    list_filter = ('pending_changes', 'created', 'updated')
    search_fields = ('dns_primary', 'dns_secondary')
    ordering = ('created', 'updated')
admin.site.register(DNSSettings, DNSSettingsAdmin)


class StaticHostAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'ip_address', 'created', 'updated')
    search_fields = ('hostname', 'ip_address')
    ordering = ('hostname', 'created')
admin.site.register(StaticHost, StaticHostAdmin)


@admin.register(HADDNSConfig)
class HADDNSConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'enabled', 'handshake_threshold_seconds', 'domain_suffix', 'update_interval_seconds')
    list_filter = ('enabled', 'created', 'updated')
    search_fields = ('name', 'domain_suffix')
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Settings', {
            'fields': ('enabled', 'domain_suffix', 'dynamic_hosts_file')
        }),
        ('Timing Settings', {
            'fields': ('handshake_threshold_seconds', 'update_interval_seconds')
        }),
        ('Offline Peer Settings', {
            'fields': ('include_offline_peers', 'offline_suffix'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PeerHostnameMapping)
class PeerHostnameMappingAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'peer_name', 'peer_key_short', 'is_online', 'enabled', 'last_handshake_check')
    list_filter = ('enabled', 'is_online', 'created', 'updated')
    search_fields = ('hostname', 'peer__name', 'peer__public_key')
    ordering = ('hostname',)
    readonly_fields = ('is_online', 'last_handshake_check', 'created', 'updated')
    
    def peer_name(self, obj):
        return obj.peer.name or 'Unnamed'
    peer_name.short_description = 'Peer Name'
    
    def peer_key_short(self, obj):
        return f"{obj.peer.public_key[:16]}..."
    peer_key_short.short_description = 'Public Key'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('peer')