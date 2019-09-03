print('Loading settings/no_migrations')

# noinspection PyUnresolvedReferences
from .local import *


class DisableMigrations(object):
    """ Used to make tests run faster and not worry about migrations """

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return


MIGRATION_MODULES = DisableMigrations()
