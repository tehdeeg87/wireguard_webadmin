from django.contrib import admin
from user_manager.models import UserAcl, cancelURL


class UserAclAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_level', 'created', 'updated')
    search_fields = ('user__username', 'user__email')

admin.site.register(UserAcl, UserAclAdmin)
admin.site.register(cancelURL)
