"""
Base env vars to build other env files upon
"""

print('Loading envs/base')

import json
from os import getenv
from os.path import join
from tempfile import gettempdir

RDS_DB_NAME = getenv('RDS_DB_NAME', 'whatsmycut')
RDS_USERNAME = getenv('RDS_USERNAME', 'dbuser')
RDS_PASSWORD = getenv('RDS_PASSWORD', '123')
RDS_HOSTNAME = getenv('RDS_HOSTNAME', 'db')
RDS_PORT = getenv('RDS_PORT', 5432)

TMP_DIR = getenv('TMP_DIR', join(gettempdir(), 'whatsmycut'))
LOGS_DIR = getenv('LOGS_DIR', join(TMP_DIR, 'logs'))
MEDIA_ROOT = getenv('MEDIA_ROOT', join(TMP_DIR, 'media'))

HOST_URL = getenv('HOST_URL', 'https://www.whatsmycut.com')
MARKETING_SITE_URL = getenv('MARKETING_SITE_URL', 'https://www.whatsmycut.com')

REACT_APP_ADMIN_URL = getenv('REACT_APP_ADMIN_URL', 'https://admin.whatsmycut.com')

RESET_PASSWORD_PATH = getenv('RESET_PASSWORD_PATH', '/password/reset/')
RESET_PASSWORD_CONFIRM_PATH = getenv('RESET_PASSWORD_CONFIRM_PATH', '/password/confirm')

ADMINS = json.loads(getenv('ADMINS', '[]'))

DEFAULT_FROM_EMAIL = getenv('DJANGO_DEFAULT_FROM_EMAIL', 'WMCP Support <support@whatsmycut.com>')

SALESFORCE_ENABLED = False

RELEASE_GIT_SHA = getenv('RELEASE_GIT_SHA') or ''
