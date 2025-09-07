from django.contrib import admin
from user_manager.models import UserAcl, cancelURL
from wireguard.models import PeerGroup, WireGuardInstance, Peer, PeerAllowedIP


class UserAclAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_level', 'created', 'updated')
    search_fields = ('user__username', 'user__email')
    filter_horizontal = ('peer_groups',)


class PeerGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'updated')
    search_fields = ('name',)
    filter_horizontal = ('server_instance',)


class WireGuardInstanceAdmin(admin.ModelAdmin):
    list_display = ('name', 'instance_id', 'hostname', 'listen_port', 'address', 'netmask', 'created')
    search_fields = ('name', 'hostname', 'address')
    list_filter = ('created', 'netmask')


class PeerAdmin(admin.ModelAdmin):
    list_display = ('name', 'wireguard_instance', 'public_key', 'created')
    search_fields = ('name', 'public_key')
    list_filter = ('wireguard_instance', 'created')


class PeerAllowedIPAdmin(admin.ModelAdmin):
    list_display = ('peer', 'allowed_ip', 'netmask', 'priority', 'config_file')
    search_fields = ('peer__name', 'allowed_ip')
    list_filter = ('config_file', 'priority')


admin.site.register(UserAcl, UserAclAdmin)
admin.site.register(PeerGroup, PeerGroupAdmin)
admin.site.register(WireGuardInstance, WireGuardInstanceAdmin)
admin.site.register(Peer, PeerAdmin)
admin.site.register(PeerAllowedIP, PeerAllowedIPAdmin)
admin.site.register(cancelURL)
