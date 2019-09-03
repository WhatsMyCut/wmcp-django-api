"""
Settings to use during local development.
"""
print('Loading settings/local')

import os

os.environ['MARKETING_SITE_URL'] = 'http://127.0.0.1:8000'

os.environ['MANDRILL_API_KEY'] = ''
os.environ['MANDRILL_SUBACCOUNT'] = 'dev'

os.environ['PAYMENT_STRIPE_PUBLIC_KEY'] = 'pk_test_key'
os.environ['PAYMENT_STRIPE_SECRET_KEY'] = 'sk_test_key'
os.environ['PAYMENT_STRIPE_WEBHOOK_SECRET'] = 'whsec'

os.environ['RDS_DB_NAME'] = 'whatsmycut'
os.environ['RDS_USERNAME'] = 'postgres'
os.environ['RDS_PASSWORD'] = '123'
os.environ['RDS_HOSTNAME'] = '0.0.0.0'
os.environ['RDS_PORT'] = '5432'

os.environ['SES_AIM_KEY_ID'] = ''
os.environ['SES_AIM_SECRET_KEY'] = ''

os.environ['S3_BUCKET_NAME'] = ''
os.environ['S3_BUCKET_AIM_KEY_ID'] = ''
os.environ['S3_BUCKET_AIM_SECRET_KEY'] = ''

os.environ['SALESFORCE_USERNAME'] = ''
os.environ['SALESFORCE_PASSWORD'] = ''
os.environ['SALESFORCE_TOKEN'] = ''
os.environ['IS_SALESFORCE_SANDBOX'] = 'True'
os.environ['SALESFORCE_ENABLED'] = 'False'

os.environ['ADMINS'] = '[]'

os.environ['GMAPS_API_KEY'] = 'gmaps-key'
os.environ['YELP_API_KEY'] = ''

os.environ['LOGSTASH_HOST'] = ''
os.environ['LOGSTASH_PORT'] = ''

os.environ['REACT_APP_RESIDENT_URL'] = 'http://127.0.0.1:3000'
os.environ['SESSION_COOKIE_PATH'] = '/'



from .base import *  # noqa

# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['wmcp.local', 'localhost', '127.0.0.1', '0.0.0.0']
INTERNAL_IPS = ['127.0.0.1', '0.0.0.0', '10.0.2.2']

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = TMP_DIR

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 587

ADMINS = [('Admin', 'admin@example.com'), ]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'whatsmycut',
        'USER': 'dbuser',
        'PASSWORD': '123',
        'HOST': 'db',
        'PORT': 5432
    }
}

# MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE

# INSTALLED_APPS += ['debug_toolbar']

# STATIC_ROOT = ""
GOOGLE_MAPS_API_KEY = ""

ACCOUNT_DEFAULT_HTTP_PROTOCOL = ""

DEFAULT_FROM_EMAIL = 'admin@example.com'
DEFAULT_TO_EMAIL = 'admin@example.com'
SERVER_EMAIL = 'admin@example.com'

HOST_URL = 'https://amenify.local'

SALESFORCE_ENABLED = False

DEBUG = True
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
