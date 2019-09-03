
print('Loading settings/settings')

import sys
from os import environ

import django.core.mail

if hasattr(django.core.mail, 'outbox') or (len(sys.argv) > 1 and sys.argv[1] == 'test'):
    settings_file = 'whatsmycut.settings.test'
    from whatsmycut.settings.test import *
else:
    settings_file = 'whatsmycut.settings.production'
    from whatsmycut.settings.production import *

environ['DJANGO_SETTINGS_MODULE'] = settings_file
