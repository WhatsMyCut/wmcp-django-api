"""
Base settings to build other settings files upon
"""

print('Loading settings/base')

from os.path import dirname, abspath
from urllib.parse import urlsplit

from django.contrib import messages

# Constance - Dynamic Django settings
# https://django-constance.readthedocs.io/en/latest/#configuration
# noinspection PyUnresolvedReferences
from apps.dynamic_settings.constance_settings import *

# noinspection PyUnresolvedReferences
from ..envs.base import *
from .utils import safe_mkdir

# GENERAL
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = '!!! BE_SURE_TO_CHANGE_ME_FOR_PRODUCTION !!!'

# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = False

# Local time zone. Choices are http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'UTC'

# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'en-us'

# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
RECURRENCE_USE_TZ = False
DEFAULT_PROPERTY_TIME_ZONE = 'US/Eastern'

# Build paths inside the project like this: join(BASE_DIR, ...)
BASE_DIR = dirname(dirname(dirname(abspath(__file__))))
PORTAL_DIR = join(dirname(BASE_DIR), 'resident-portal')
PM_DASHBOARD_DIR = join(dirname(BASE_DIR), 'property-manager')

# Make sure dirs exist
safe_mkdir(TMP_DIR)
safe_mkdir(LOGS_DIR)
safe_mkdir(MEDIA_ROOT)

# URLS
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = 'whastmycut.urls'

# # https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'whastmycut.wsgi.application'

# https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-DATABASES
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': RDS_DB_NAME,
        'USER': RDS_USERNAME,
        'PASSWORD': RDS_PASSWORD,
        'HOST': RDS_HOSTNAME,
        'PORT': RDS_PORT,
    }
}

# APPS
# https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-INSTALLED_APPS
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'notifications',
    'crispy_forms',
    'django_extensions',
    'graphene_django',
    'oauth2_provider',
    'corsheaders',
    'recurrence',
    'constance',
    'constance.backends.database',
    'tinymce',
    'phonenumber_field',
    'reversion',
    'reversion_compare',
    'colorfield',
    'import_export',
]

LOCAL_APPS = [
    'apps.account',
    'apps.general',
    'apps.property',
    'apps.property_integration',
    'apps.resident',
    'apps.partner',
    'apps.payment',
    'apps.appointments',
    'apps.api_gateway',
    'apps.faq',
    'apps.dynamic_settings',
    'apps.googleapis',
    'apps.onsite_notifications',
    'apps.onsite_reversions',
    'apps.subscriptions',
    'apps.salesforce',
    'apps.error_email_throttle',
    'apps.credits',
    'apps.reviews',
    'apps.ordering',
    'apps.dashboard_items',
    'apps.zapier_integration'
]

# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# django-autocomplete-light
# https://django-autocomplete-light.readthedocs.io/en/master/install.html
# To let Django find the static files we need by adding to INSTALLED_APPS,
# before django.contrib.admin and grappelli if present
INSTALLED_APPS = ['dal', 'dal_select2'] + INSTALLED_APPS

# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'corsheaders.middleware.CorsPostCsrfMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.general.middleware.AddReleaseIdToResponseMiddleware',
    'apps.account.middleware.OAuth2TokenMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'constance.context_processors.config',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

# AUTHENTICATION
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    'apps.account.backends.OAuth2Backend',
    'apps.account.backends.ProxiedModelBackend',
]

# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = '/account/login-success'

# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = '/account/login/'
LOGOUT_URL = '/account/logout/'

# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'apps.account.password_validation.DiversifiedPasswordValidator',
    },
]

# STATIC
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
# noinspection PyUnresolvedReferences
STATIC_ROOT = join(BASE_DIR, 'www', 'static')

# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'
PORTAL_STATIC_ROOT = join(PORTAL_DIR, 'build')
PM_DASHBOARD_STATIC_ROOT = join(PM_DASHBOARD_DIR, 'build')
PORTAL_STATIC_URL = '/portal_static/'
PM_DASHBOARD_STATIC_URL = '/pm_dashboard_static/'

# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [join(BASE_DIR, 'static'), PORTAL_STATIC_ROOT, PM_DASHBOARD_STATIC_ROOT]

# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'

ACCOUNT_ACTIVATION_DAYS = 10

# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = 'bootstrap3'

MESSAGE_TAGS = {
    messages.ERROR: 'error'
}

DOMAIN_NAME = urlsplit(HOST_URL).netloc if HOST_URL.startswith('http') else HOST_URL

ENCRYPTED_FIELD_KEYS_DIR = join(BASE_DIR, 'keyset')

ONE_TIME_CELERY_TASKS = (  # non-periodic celery tasks
    # Appointment tasks
    'apps.appointments.tasks.send_product_category_subscription_notification',
    # Property integration
    'apps.property_integration.tasks.sync_company_residents',
    # SalesForce
    'apps.salesforce.tasks.receive_sf_object_updated',
    'apps.salesforce.tasks.send_resident_deactivated',
    'apps.salesforce.tasks.receive_sf_object_created',
    'apps.salesforce.tasks.send_booking_canceled',
    'apps.salesforce.tasks.send_subscription_canceled',
    'apps.salesforce.tasks.send_booking_schedule_canceled',
    'apps.salesforce.tasks.send_activation_code_created',
    'apps.salesforce.tasks.send_meet_and_greet_updated',
    'apps.salesforce.tasks.send_resident_updated',
    'apps.salesforce.tasks.send_subscription_created',
    'apps.salesforce.tasks.send_instance_deleted',
    'apps.salesforce.tasks.send_instance_created',
    'apps.salesforce.tasks.send_instance_updated',
    # Zapier
    'apps.zapier_integration.tasks.send_new_subscriber_to_zapier',
    'apps.zapier_integration.tasks.send_new_review_to_zapier',
    'apps.zapier_integration.tasks.send_cancelled_subscription_to_zapier',
    # Payment
    'apps.payment.tasks.create_stripe_product_category_subscription'
)

# LOGGING
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'simulation_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': join(LOGS_DIR, 'integration-simulation.log')
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'apps.error_email_throttle.handler.AdminEmailThrottler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'simulation': {
            'handlers': ['simulation_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['mail_admins', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# EMAIL
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
ERROR_EMAIL_THROTTLING_TIME = 30  # seconds
EMAIL_PORT = 587
EMAIL_USE_TLS = True

SUBSCRIPTION_TRIAL_MONTHS = 1
SUBSCRIPTION_LEEWAY_DAYS = 2
SUBSCRIPTION_COST = 29

PAYMENT_INTERVAL = 'month'
PAYMENT_CURRENCY = 'usd'

GRAPHENE = {
    'SCHEMA': 'apps.api_gateway.schema.schema'
}

SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 2 weeks, in seconds
SESSION_COOKIE_PATH = '/admin'

# https://django-oauth-toolkit.readthedocs.io/en/latest/tutorial/tutorial_01.html
OAUTH2_DEFAULT_CLIENT = 'website'
OAUTH2_PROVIDER_APPLICATION_MODEL = 'account.OAuthClient'
OAUTH2_PROVIDER = {
    'ACCESS_TOKEN_EXPIRE_SECONDS': SESSION_COOKIE_AGE,
}

YELP_API_HOST = 'https://api.yelp.com'

CORS_ORIGIN_ALLOW_ALL = True

# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

TINYMCE_DEFAULT_CONFIG = {
    'plugins': "table,spellchecker,paste,searchreplace",
    'theme': "advanced",
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 20,
}

PYTIDY_OPTIONS = {
    'output-xhtml': 1,
    'indent': 1,
    'tidy-mark': 0,
    'wrap': 0,
    'show-warnings': True,
    'alt-text': '',
    'doctype': 'strict',
    'force-output': 1,
}

PHONENUMBER_DB_FORMAT = 'INTERNATIONAL'

ADD_REVERSION_ADMIN = True

NOTIFICATIONS_USE_JSONFIELD = True

# CELERY
# http://docs.celeryproject.org/en/latest/django/index.html
INSTALLED_APPS += ['django_celery_results', 'django_celery_beat']
CELERY_BROKER_URL = 'amqp://rmq_user:rmq_pass@127.0.0.1:5672/rmq_vhost'
CELERY_TASK_ALWAYS_EAGER = False
CELERY_RESULT_BACKEND = 'wmcp-db'
CELERY_SEND_EVENTS = True
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'
