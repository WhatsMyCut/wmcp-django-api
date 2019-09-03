from collections import OrderedDict

from django.conf import settings
from django.contrib.auth.models import Permission, Group
from constance.admin import get_values, Config

from apps.dynamic_settings.constance_settings import CONSTANCE_CONFIG
from apps.general.validators import is_valid_email
from constance import config as dynamic_settings


class DynamicSettingsUtils:
    @staticmethod
    def get_public_dynamic_settings():
        """ Returns constance keys that are public """
        result = OrderedDict()
        for c_key, c_value in get_values().items():
            if c_key in settings.CONSTANCE_EXPOSED_SETTINGS:
                result[c_key] = c_value
        return result

    @staticmethod
    def get_public_settings():
        """ Returns public settings from settings.py and ENV """
        return {
            'PAYMENT_STRIPE_PUBLIC_KEY': getattr(settings, 'PAYMENT_STRIPE_PUBLIC_KEY', None)
        }

    @staticmethod
    def assign_permission_to_group(group_name='staff', group_class=None):
        if group_class is None:
            group_class = Group
        group = group_class.objects.filter(name__iexact=group_name).first()
        if group is None:
            return -1
        permission_name = Config()._meta.get_change_permission()
        # for some reasons, ContentType.objects.get_for_model(Config) does not work
        permission = Permission.objects.filter(
            codename=permission_name, content_type__app_label='constance').first()
        if not permission:
            return
        if permission not in group.permissions.all():
            group.permissions.add(permission)
        return True

    @staticmethod
    def get_settings_type(settings_name):
        return CONSTANCE_CONFIG.get(settings_name, (None, None, str))[2]

    @staticmethod
    def get_no_prices_notification_recipients():
        emails = dynamic_settings.NO_PRICES_NOTIFICATION_RECIPIENTS or ''
        return [x.strip() for x in emails.split(',') if is_valid_email(x.strip())]
