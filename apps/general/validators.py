import decimal
import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_email, _lazy_re_compile, RegexValidator


def is_valid_email(email):
    try:
        validate_email(email)
    except ValidationError:
        return False
    return True


def is_valid_decimal(number):
    try:
        decimal.Decimal(number)
    except (decimal.InvalidOperation, TypeError):
        return False
    return True


def is_valid_integer(number):
    try:
        int(number)
    except (ValueError, TypeError):
        return False
    return True


def list_validator(sep=',', message=None, code='invalid'):
    regexp = _lazy_re_compile(r'^\w+(?:%(sep)s\w+)*\Z' % {
        'sep': re.escape(sep),
    })
    return RegexValidator(regexp, message=message, code=code)


validate_comma_separated_list = list_validator(
    message='Enter value separated by commas.',
)
