from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from typing import Callable

from apps.general.utils import in_tests


def exceptions_wrapper_factory(logger, msg):
    def exceptions_wrapper(method):
        def on_call(command, *args, **kwargs):
            try:
                return method(command, *args, **kwargs)
            except Exception as e:
                logger.exception(msg)
                return None

        return on_call
    return exceptions_wrapper


def is_prefetched(name):
    def function_wrap(function):
        def wrap(self, *args, **kwargs):
            prefetched = hasattr(self, '_prefetched_objects_cache') and name in self._prefetched_objects_cache
            return function(self, prefetched, *args, **kwargs)
        return wrap
    return function_wrap


def is_staff_or_superuser(view_func=None, redirect_field_name=REDIRECT_FIELD_NAME,
                          login_url='account:login'):
    """
    Decorator for views that checks that the user is logged in and is a staff
    member or superuser, redirecting to the login page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and (u.is_staff or u.is_superuser),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def run_on_commit(lambda_func: Callable):
    """
    Makes sure the func would be called only after the OUTERMOST transaction's been committed.
    :param lambda_func: a function without arguments
    Usage:
        run_on_commit(lambda: run_task(send_booking_updated, instance.id))
    """
    if in_tests():
        return lambda_func()
    with transaction.atomic():
        transaction.on_commit(lambda_func)
