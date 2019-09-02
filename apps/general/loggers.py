import logging

import sys

django_logger = logging.getLogger('django')
sentry_logger = logging.getLogger('manual_sentry_logger')
logstash_logger = logging.getLogger('logstash')


def log_to_sentry(msg='', level=logging.WARNING):
    locals_ = sys._getframe(1).f_locals
    sentry_logger.log(level, msg, extra={'locals()': locals_})


def log_charge_to_logstash(msg, level=logging.WARNING):
    locals_ = sys._getframe(1).f_locals
    charge = locals_.get('charge', {})
    # Make sure full CC number isn't logged
    if charge and charge.get('source', {}).get('name'):
        charge['source'].pop('name')
    logstash_logger.log(level, msg, extra={'charge': charge})
