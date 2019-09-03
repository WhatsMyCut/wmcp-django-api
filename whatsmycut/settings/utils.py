"""
These utils are called from SETTINGS and must NOT contain any local app imports
"""

from contextlib import suppress
from pathlib import Path

import requests


def get_aws_instance_ip(aws_metadata_url):
    try:
        return requests.get(aws_metadata_url, timeout=1).text.strip()
    except Exception:
        print('AWS_METADATA_URL="%s" is not reachable. '
              'You shall only run production settings on an AWS EC2 instance.' % aws_metadata_url)


def safe_mkdir(dir_path):
    """ Make dir. Ignore errors """
    with suppress(Exception):
        Path(dir_path).mkdir(parents=True, exist_ok=True)
