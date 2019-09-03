"""
Settings to use on production-like environments (DEV/ON-DEMAND/STAGE/PROD)
"""
print('Loading settings/production')

import socket

from django.core.exceptions import DisallowedHost

from .base import *
from .utils import get_aws_instance_ip
from ..envs.production import *


# GENERAL
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = 'psmy7d*s2xp9qh+x7jjv%ri^1^zp^e$qsmp_7edep6v^+m@wni'

# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS += [
    '.whatsmycut.com',
    '.devwhatsmycut.com',
    '.whatsmycut.com',
    '.compute-1.amazonaws.com',
    '.elb.amazonaws.com',
]
# For environments with load balancer we want to add local instance ip to `ALLOWED_HOSTS`
if DJANGO_SENTRY_ENV in ('dev', 'stage', 'prod'):
    AWS_INSTANCE_IP = get_aws_instance_ip(AWS_METADATA_URL)
    if AWS_INSTANCE_IP:
        ALLOWED_HOSTS += [AWS_INSTANCE_IP]

# STORAGES
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_ACCESS_KEY_ID = S3_BUCKET_AIM_KEY_ID
AWS_SECRET_ACCESS_KEY = S3_BUCKET_AIM_SECRET_KEY
AWS_STORAGE_BUCKET_NAME = S3_BUCKET_NAME
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

# STATIC
# https://docs.djangoproject.com/en/dev/howto/static-files/
if DJANGO_S3_STATIC:
    STATIC_URL = DJANGO_S3_STATIC
    STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

# MEDIA
# https://docs.djangoproject.com/en/1.9/ref/settings/#media-url
MEDIA_URL = 'https://%s/' % AWS_S3_CUSTOM_DOMAIN
DEFAULT_FILE_STORAGE = 'apps.general.storages.AbsoluteAndS3BotoStorage'

# EMAIL
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
DEFAULT_TO_EMAIL = SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_HOST = 'email-smtp.us-west-2.amazonaws.com'
EMAIL_HOST_USER = SES_AIM_KEY_ID
EMAIL_HOST_PASSWORD = SES_AIM_SECRET_KEY

# Sentry (raven) client
# See https://docs.sentry.io/clients/python/integrations/django/
if DJANGO_SENTRY_URL:
    INSTALLED_APPS.append('raven.contrib.django.raven_compat')
    MIDDLEWARE = [
        'apps.general.middleware.CustomSentry400CatchMiddleware',
        'raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware',
    ] + MIDDLEWARE
    # Sentry's `server_name`
    # https://docs.sentry.io/clients/python/advanced/#client-arguments
    SENTRY_SERVER_NAME = 'HOST_URL=%s, HOST_NAME=%s' % (HOST_URL, socket.gethostname())
    RAVEN_CONFIG = {
        'dsn': DJANGO_SENTRY_URL,
        'name': SENTRY_SERVER_NAME,
        'auto_log_stacks': True,
        'environment': DJANGO_SENTRY_ENV,
        'ignore_exceptions': [KeyboardInterrupt, DisallowedHost],
    }
    if RELEASE_GIT_SHA:
        RAVEN_CONFIG['release'] = RELEASE_GIT_SHA
    # Integration with logging
    # https://docs.sentry.io/clients/python/integrations/django/#integration-with-logging
    LOGGING['handlers']['sentry'] = {
        'level': 'ERROR',
        'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
    }
    LOGGING['loggers']['django']['handlers'].append('sentry')
    # Silent DisallowedHost errors
    LOGGING['handlers']['null'] = {
        'class': 'logging.NullHandler',
    }
    LOGGING['loggers']['django.security.DisallowedHost'] = {
        'handlers': ['null'],
        'propagate': False,
    }
    # Add manual Sentry logger
    LOGGING['handlers']['manual_sentry_handler'] = {
        'level': 'DEBUG',
        'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
    }
    LOGGING['loggers']['manual_sentry_logger'] = {
        'handlers': ['manual_sentry_handler'],
        'level': 'DEBUG',
        'propagate': False,
    }

# Python logging handler for Logstash
# http://logstash.net/
# https://github.com/vklochan/python-logstash#installation
LOGGING['handlers']['logstash'] = {
    'level': 'INFO',
    'class': 'logstash.TCPLogstashHandler',
    'host': LOGSTASH_HOST,
    'port': LOGSTASH_PORT,
    'version': 1,  # Version of logstash event schema
    'message_type': 'backend_whatsmycut',  # 'type' field in logstash message
    'fqdn': False,  # Fully qualified domain name
}
LOGGING['loggers']['logstash'] = {
    'handlers': ['logstash'],
    'level': 'DEBUG',
    'propagate': False,
}
HTTP_LOGGER_KEY = 'some-random-string-*(*32322_|-Ndska92NNgda32113'
HTTP_LOGGER_URL = 'http://log-collector.devwhatsmycut.com'
HTTP_LOGGER_ENABLED = True
