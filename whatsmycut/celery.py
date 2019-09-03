import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsmycut.settings.local')


app = Celery('whatsmycut')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.loader.override_backends['wmcp-db'] = 'apps.general.celery:WMCPDatabaseBackend'
