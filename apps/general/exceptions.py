from collections import namedtuple

from django.utils.safestring import mark_safe

ErrorDto = namedtuple('ErrorDto', ['key', 'message'])


class AppException(Exception):
    def __init__(self, detail, errors=None, **kwargs):
        self.detail = detail
        self.errors = errors
        super().__init__(detail)

    @property
    def code(self):
        return NotImplemented

    def as_html(self, separator='<br>'):
        result = str(self.detail)
        if not result.endswith(' '):
            result += ' '
        if not result.strip().endswith(separator.strip()):
            result += separator
        result += separator.join(['%s: %s' % (e.key, e.message) for e in self.errors])
        return mark_safe(result)


class InternalErrorException(AppException):
    code = 'internal_error'


class InvalidParamException(AppException):
    code = 'invalid_input'


class ValidationErrorException(AppException):
    code = 'validation_error'


class InvalidPhoneNumber(Exception):
    pass
