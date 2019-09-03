"""
Env vars to use for Django tests (local & CI)
"""

print('Loading envs/test')

from os import getenv

TEST_RUNNER = getenv('TEST_RUNNER', 'xmlrunner.extra.djangotestrunner.XMLTestRunner')
