from __future__ import print_function

from django.core.management import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Delete all migrations records from DB for the specified apps"

    def __init__(self, *args, **kwargs):
        self.cursor = connection.cursor()
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('apps', nargs='+', type=str)

    def delete_database_app(self, app):
        self.stdout.write("Deleting APP (%s) in database" % app)
        self.cursor.execute("DELETE from django_migrations WHERE app = %s", [app])

    def handle(self, *args, **options):
        apps = options['apps']
        self.stdout.write("Reseting APP %s" % apps)
        for app in apps:
            self.delete_database_app(app)
