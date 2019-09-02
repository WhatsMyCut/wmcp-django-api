from django.apps import AppConfig


class GeneralConfig(AppConfig):
    name = 'apps.general'

    # noinspection PyUnresolvedReferences
    def ready(self):
        import apps.general.celery
