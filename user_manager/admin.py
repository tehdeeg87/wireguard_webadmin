from django.contrib import admin
from user_manager.models import UserAcl, cancelURL
from wireguard.models import PeerGroup


class UserAclAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_level', 'created', 'updated')
    search_fields = ('user__username', 'user__email')
    filter_horizontal = ('peer_groups',)


class PeerGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'updated')
    search_fields = ('name',)
    filter_horizontal = ('server_instance',)


admin.site.register(UserAcl, UserAclAdmin)
admin.site.register(PeerGroup, PeerGroupAdmin)
admin.site.register(cancelURL)
