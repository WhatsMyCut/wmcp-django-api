#!/usr/bin/env python
import os
import sys


def module_exists(module_name):
    try:
        __import__(module_name)
    except ImportError:
        return False
    return True


if __name__ == '__main__':
    # Use `settings.local` by-default
    settings = 'whatsmycut.settings.local'

    # Use `settings.local_test` (if exists) by-default for tests, and `settings.test` otherwise
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        if module_exists('whatsmycut.settings.local_test'):
            settings = 'whatsmycut.settings.local_test'
        else:
            settings = 'whatsmycut.settings.test'
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
