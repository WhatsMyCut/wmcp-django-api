from constance.admin import ConstanceAdmin, Config
from django.contrib import admin

from apps.dynamic_settings.forms import CustomConstanceAdminForm


class CustomConstanceAdmin(ConstanceAdmin):
    change_list_form = CustomConstanceAdminForm

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff


if admin.site.is_registered(Config):
    admin.site.unregister([Config])

admin.site.register([Config], CustomConstanceAdmin)
