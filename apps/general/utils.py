import csv
import io
import calendar
import datetime
import math
import random
import re
import string
import sys
from collections import OrderedDict, Callable
from itertools import islice
from typing import List, Union

import pytz
from dateutil.rrule import rruleset
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.deprecation import MiddlewareMixin
from pytz.tzinfo import StaticTzInfo, DstTzInfo
import django.core.mail
import django.core.serializers.python
import django.db.utils
from django.apps import apps as django_apps
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core import serializers
from django.core.management import call_command
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.manager import Manager
from django.db.models.fields.related import ManyToManyField
from django.forms.models import model_to_dict
from phonenumber_field.formfields import PhoneNumberField
from recurrence import Weekday, Recurrence
from tinymce import models as tinymce_models
from django.urls import reverse

from apps.general.exceptions import InvalidPhoneNumber


class DateUtils:
    @staticmethod
    def as_utc(dt: datetime.datetime):
        """
        Replaces the tzinfo with the UTC timezone.
        Do not use it for timezones conversion (use `DateUtils.to_timezone()` for that)!
        Use for localizing (making tz aware) naive datetimes (that are actually in UTC)
        """
        return dt.replace(tzinfo=pytz.UTC)

    @staticmethod
    def to_utc(dt: datetime.datetime):
        """ Converts the given datetime into the UTC timezone """
        assert DateUtils.is_zoned(dt), "Can't convert naive datetime. Use DateUtils.as_utc() for that"
        return dt.astimezone(pytz.UTC)

    @staticmethod
    def as_timezone(dt: datetime.datetime, tz: Union[StaticTzInfo, DstTzInfo]):
        """
        Replaces the tzinfo with the given timezone.
        Do not use it for timezones conversion (use `DateUtils.to_timezone()` for that)!
        """
        return tz.normalize(tz.localize(DateUtils.to_naive(dt)))

    @staticmethod
    def to_timezone(zoned_dt: datetime.datetime, tz: Union[StaticTzInfo, DstTzInfo]):
        """ Converts the given zoned datetime to the given timezone """
        assert DateUtils.is_zoned(zoned_dt), "Can't convert naive datetime. Use DateUtils.as_timezone() for that"
        old_tz = zoned_dt.tzinfo
        old_normalized_dt = old_tz.normalize(old_tz.localize(DateUtils.to_naive(zoned_dt)))  # correct original tzinfo
        return old_normalized_dt.astimezone(tz)

    @staticmethod
    def utc_now():
        """ Timezone aware (localized) current datetime in UTC """
        return DateUtils.as_utc(datetime.datetime.utcnow())

    @staticmethod
    def tz_now(tz: Union[StaticTzInfo, DstTzInfo]):
        """ Timezone aware (localized) current datetime in the target tz """
        return DateUtils.utc_now().astimezone(tz)

    @staticmethod
    def date_to_datetime(date: datetime.date, tz: Union[StaticTzInfo, DstTzInfo]):
        """ Converts given datetime.date to datetime.datetime in the given timezone """
        return DateUtils.as_timezone(datetime.datetime.combine(date, datetime.time.min), tz)

    @staticmethod
    def as_date(date_or_datetime: Union[datetime.date, datetime.datetime, None]) -> Union[datetime.date, None]:
        """ Safe extract .date() from datetime """
        if date_or_datetime:
            return date_or_datetime if type(date_or_datetime) is datetime.date else date_or_datetime.date()

    @staticmethod
    def date_at_time(date: datetime.date, zoned_datetime: datetime.datetime):
        """ Combines the given date with time from the given zoned_datetime """
        combined = DateUtils.date_to_datetime(date, pytz.UTC).replace(hour=zoned_datetime.hour,
                                                                      minute=zoned_datetime.minute,
                                                                      second=zoned_datetime.second,
                                                                      tzinfo=zoned_datetime.tzinfo)
        return zoned_datetime.tzinfo.normalize(combined) if zoned_datetime.tzinfo else combined

    @staticmethod
    def start_of_day(dt: datetime.datetime):
        """ Zeroes time in the given datetime """
        return datetime.datetime.combine(dt.date(), datetime.time.min).replace(tzinfo=dt.tzinfo)

    @staticmethod
    def to_millis(dt: datetime.datetime):
        """ Convert the given datetime to timestamp measured in milliseconds """
        return dt.timestamp() * 1000

    @staticmethod
    def is_dst(dt: datetime.datetime, tz: Union[StaticTzInfo, DstTzInfo]):
        """ Converts to the given tz and checks whether the given datetime is in Daylight Savings Time """
        if not DateUtils.is_zoned(dt):
            dt = pytz.UTC.localize(dt)
        return dt.astimezone(tz).dst().total_seconds() != 0

    @staticmethod
    def is_last_day_of_month(dt: datetime.datetime):
        return dt.day == calendar.monthrange(dt.year, dt.month)[1]

    @staticmethod
    def shift_datetime_to_last_day_of_month(dt: datetime.datetime):
        """ Replaces the datetime's day value to the last month's day """
        num_days_in_month = calendar.monthrange(year=dt.year, month=dt.month)[1]
        return dt.replace(day=num_days_in_month)

    @staticmethod
    def is_zoned(dt: datetime.datetime):
        """ Whether the given datetime is timezone-aware (localized) """
        return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None

    @staticmethod
    def to_naive(dt: datetime.datetime):
        return dt.replace(tzinfo=None)

    @staticmethod
    def to_sf_datetime(dt: datetime.datetime, tz: Union[StaticTzInfo, DstTzInfo], convert_to_isoformat=True):
        if not dt:
            return
        if not DateUtils.is_zoned(dt):
            dt = DateUtils.as_utc(dt)
        if tz:
            dt = DateUtils.to_timezone(dt, tz)
        dt = dt.replace(microsecond=0)
        return dt.isoformat() if convert_to_isoformat else dt

    @staticmethod
    def get_rrules_byweekday_from_date(date: datetime.date):
        """ Get `recurrence.Weekday()` instance ready to be passed into `rrule.replace(byweekday=...)` """
        days_in_month = calendar.monthrange(date.year, date.month)[1]
        is_last_week = date.day + 7 > days_in_month
        # Try every week to see if our date belongs to it
        for week in range(1, 6):
            week_start = (week - 1) * 7 + 1  # Day of month that week starts from
            if week_start <= date.day <= week * 7:  # Check if our date belongs to the week
                if is_last_week:  # It's the last week -> turn `BYDAY=+5MO` into `BYDAY=-1MO`
                    week = -1
                return Weekday(date.weekday(), week)

    @staticmethod
    def weekdays_until(to_date: datetime.date):
        """ Days from utc_now() until @to_date. Weekends are excluded. Holidays aren't
        >>> # Given now = datetime.date(2019, 5, 9)
        >>> DateUtils.weekdays_until(datetime.date(2019, 5, 13))
        2
        """
        if isinstance(to_date, datetime.datetime):
            to_date = to_date.date()
        now = DateUtils.utc_now().date()
        daygenerator = (now + datetime.timedelta(x + 1) for x in range((to_date - now).days))
        return sum(1 for day in daygenerator if day.weekday() < 5)


class FieldsUtils:
    @staticmethod
    def get_absolute_media_url(img_or_file_field):
        if not img_or_file_field:
            return
        # There are 3 possible cases - see below:
        if str(img_or_file_field).startswith('http'):
            # 1) the img URI is absolute - return only img URI because it seems like an external link
            return str(img_or_file_field)
        else:
            if settings.MEDIA_URL.startswith('http'):
                # 2) settings.MEDIA_URL is absolute, the img URI is relative
                #     - return joined data because the file seems to be hosted on S3
                return settings.MEDIA_URL + str(img_or_file_field)
            else:
                # 3) settings.MEDIA_URL is relative, the img URL is relative too
                #     - seems like we have to add the domain name
                url = img_or_file_field.url
                if not url.startswith('http'):
                    url = 'http://' + settings.DOMAIN_NAME + url
                return url


class FixtureUtils:
    """ See https://stackoverflow.com/a/39743581 """

    def __init__(self, app_label, fixture_file):
        self._app_label = app_label
        self._fixture_file = fixture_file

    def load_fixture(self, apps, schema_editor):
        # Save the old _get_model() function
        old_get_model = serializers.python._get_model

        # Define new _get_model() function here, which utilizes the apps argument to
        # get the historical version of a model. This piece of code is directly stolen
        # from django.core.serializers.python._get_model, unchanged.
        def _get_model(model_identifier):
            try:
                return apps.get_model(model_identifier)
            except (LookupError, TypeError):
                raise serializers.base.DeserializationError(
                    "Invalid model identifier: '%s'" % model_identifier)

        # Replace the _get_model() function on the module, so loaddata can utilize it.
        serializers.python._get_model = _get_model

        try:
            # Call loaddata command
            call_command('loaddata', self._fixture_file, app_label=self._app_label)
        except django.db.utils.IntegrityError as e:
            if 'already exist' in str(e):
                pass  # do not raise exception if it's just duplicated data
        finally:
            # Restore old _get_model() function
            serializers.python._get_model = old_get_model


class AttrDict(dict):
    """ Dictionary subclass whose entries can be accessed by attributes
        (as well as normally). """
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    @staticmethod
    def from_nested_dict(data):
        """ Construct nested AttrDicts from nested dictionaries. """
        if not isinstance(data, dict):
            return data
        else:
            return AttrDict({key: AttrDict.from_nested_dict(data[key])
                             for key in data})


class AdminAutomaticSearchFieldsMixin:
    """ This mixin allows automatic search in model's fields. Lookups via ForeignKeys are also supported.
        Usage:
            1) Add AdminAutomaticSearchFieldsMixin as the first base class in your ModelAdmin subclass
            2) Add auto_search_fields as your ModelAdmin subclass attribute
            3) (optionally) use "self" field name to allow searching in this model's attributes (fields)
    """
    field_types_to_search = (models.CharField, models.TextField, tinymce_models.HTMLField, models.DecimalField)

    def get_search_fields(self, request):
        if not isinstance(getattr(self, 'auto_search_fields'), (list, tuple)):
            raise AttributeError('You have to add `auto_search_fields` list to your Admin class %s' % self)

        search_fields = getattr(self, 'search_fields', [])
        search_fields = list(search_fields)

        look_into_self = 'self' in self.auto_search_fields

        # look into foreign keys
        for model_field in self.model._meta.fields:
            model_field_name = getattr(model_field, 'name')
            if not model_field_name:
                continue
            if look_into_self and model_field.__class__ in self.field_types_to_search:
                # collect `self` attributes (fields)
                search_fields.append(model_field_name)
            else:
                if model_field_name not in self.auto_search_fields:
                    continue  # this field is not supposed to be searchable
                if model_field.__class__ in (models.ForeignKey, GenericForeignKey, models.OneToOneField):
                    # span foreign relations only
                    target_model = model_field.related_model
                else:
                    raise NotImplementedError('Field type %s not supported yet' % model_field.__class__)
                for target_model_field in target_model._meta.fields:
                    if target_model_field.__class__ not in self.field_types_to_search:
                        continue  # field type that is not searchable
                    target_model_field_name = getattr(target_model_field, 'name')
                    if not target_model_field_name:
                        continue
                    search_fields.append(model_field_name + '__' + target_model_field_name)

        return search_fields


class AnyStringWith(str):
    """ Use in Mock tests, just like Any """
    def __eq__(self, other):
        return self in str(other)


def nth_item(iterable, n, default=None):
    """Get n-th element of iterable without generating of entire sequence."""
    return next(islice(iterable, n, None), default)


def clone_model_fields(src, dest):
    """ Clones the src model into dest """
    m2m_fields = [f.name for f in src._meta.get_fields() if isinstance(f, ManyToManyField)]
    src_dict = model_to_dict(src, exclude=['id', 'pk'])
    for k, v in src_dict.items():
        if k in m2m_fields:
            continue
        if isinstance(v, int):
            m = getattr(src, k, None)
            if isinstance(m, models.Model):
                setattr(dest, k, m)
                continue
        setattr(dest, k, v)
    return dest


def to_cents(decimal_price):
    """
    :param decimal_price: Decimal price in dollars.
    """
    return math.trunc((decimal_price if decimal_price else 0) * 100)


def redirect_to_marketing_site(url_name):
    if url_name == '/':
        url_name = ''
    marketing_site_url = settings.MARKETING_SITE_URL
    if marketing_site_url.endswith('/'):
        marketing_site_url = marketing_site_url[0:-1]
    return marketing_site_url + '/' + url_name


def unify_phone_number(phone, country='US'):
    """ Converts broad set of phone numbers into a strict international one.
        See https://github.com/jquery-validation/jquery-validation/blob/master/src/additional/phoneUS.js
    """
    if not phone:
        return phone
    phone = ''.join([c for c in phone if c.isdigit() or c == '+'])  # leave only digits and +
    if len(phone) == 10:  # without leading country code
        return '+1' + phone
    elif len(phone) == 11:  # with leading country code (1) but without +
        if phone[0] != '1':
            raise InvalidPhoneNumber('Invalid phone number: unknown country code.')
        return '+' + phone
    elif len(phone) == 12:  # with leading +1
        if phone[0:2] != '+1':
            raise InvalidPhoneNumber('Invalid phone number: should start with +1.')
        return phone
    raise InvalidPhoneNumber('Enter a valid phone number.')


def has_full_access(user):
    return user.is_superuser  # might be as well `... or user.is_staff`


def has_staff_access(user):
    return user.is_staff


def in_tests():
    """ Returns True if we're in tests """
    return hasattr(django.core.mail, 'outbox') or (len(sys.argv) > 1 and sys.argv[1] == 'test')


def to_usd_str(decimal_price):
    """
    >>> to_usd_str(1000)
    '$1,000.00'
    """
    return '${:,.2f}'.format(float(decimal_price or 0))


def decimal_to_sf_str(decimal_price):
    """
    >>> to_usd_str(1.234)
    '1.23'
    """
    return None if decimal_price is None else '{:.2f}'.format(decimal_price)


def named_tuple_to_str(named_tuple):
    return dict_to_str(named_tuple._asdict())


def dict_to_str(source_dict):
    """ E.g. {'IP': '10.178.226.196', 'PORT': 9999} -> "IP='10.178.226.196', PORT=9999" """
    return ', '.join('{!s}={!r}'.format(k, v) for k, v in source_dict.items())


class DisableCSRF(MiddlewareMixin):
    def process_request(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)


def get_modelclass_by_modelname(model_name):
    return next(x for x in django_apps.get_models() if x.__name__ == model_name)


def sf_friendly_tz_choices():
    return [(tz, tz) for tz in pytz.common_timezones if '/' in tz]


def deduplicate_list_of_objects(objects: List[object], get_key: Callable, in_place=False):
    """
    :param objects: source list of objects
    :param get_key: lambda func that takes a single item and extracts key from it
    :param in_place: whether we want to update the source list in place
    :return: deduplicated list with preserved order (in_place=False) or None (in_place=True)

    Usage:
    >>> deduplicate_list_of_objects(
        objects=[{'a': 1}, {'a': 1}, {'a': 2}],
        get_key=lambda x: x['a']
    )
    >>> [{'a': 1}, {'a': 2}]
    """
    unique = list(OrderedDict((get_key(x), x) for x in objects).values())
    if not in_place:
        return unique
    objects.clear()
    objects.extend(unique)


def lower(x):
    """ Safe version of `str.lower()` """
    return x if x is None else str(x).lower()


def replace(old, new, string):
    """ Safe version of `str.replace()` """
    return string if string is None else str(string).replace(old, new)


def strip(x):
    """ Safe version of `str.strip()` """
    return x.strip() if isinstance(x, str) else x


def parse_phone(phone):
    return str(PhoneNumberField().to_python(unify_phone_number(phone)))


def get_all_model_managers(app_model_class: ModelBase):
    managers = ('objects', '_default_manager', '_base_manager')
    result_managers = []
    for manager in managers:
        manager_attr = getattr(app_model_class, manager, None)
        if manager_attr is None or not isinstance(manager_attr, Manager):
            continue
        if not hasattr(manager_attr, 'get'):
            continue
        result_managers.append(manager_attr)
    return result_managers


class attrgetter:
    """ Override python base method from operator module. Add checks: hasattr, None.
    Makes sort like string only.
    Return a callable object that fetches the given attribute(s) from its operand.
    After f = attrgetter('name'), the call f(r) returns r.name.
    After g = attrgetter('name', 'date'), the call g(r) returns (r.name, r.date).
    After h = attrgetter('name.first', 'name.last'), the call h(r) returns
    (r.name.first, r.name.last).
    """
    __slots__ = ('_attrs', '_call')

    def __init__(self, attr, *attrs):
        if not attrs:
            if not isinstance(attr, str):
                raise TypeError('attribute name must be a string')
            self._attrs = (attr,)
            names = attr.split('.')
            def func(obj):
                for name in names:
                    # add checks: hasattr, None
                    if hasattr(obj, name) and getattr(obj, name) is not None:
                        obj = getattr(obj, name)
                    else:
                        obj = ''
                # makes sort like sting only
                return str(obj)
            self._call = func
        else:
            self._attrs = (attr,) + attrs
            getters = tuple(map(attrgetter, self._attrs))
            def func(obj):
                return tuple(getter(obj) for getter in getters)
            self._call = func

    def __call__(self, obj):
        return self._call(obj)

    def __repr__(self):
        return '%s.%s(%s)' % (self.__class__.__module__,
                              self.__class__.__qualname__,
                              ', '.join(map(repr, self._attrs)))

    def __reduce__(self):
        return self.__class__, self._attrs


def random_string(length=20):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class CustomJSONEncoder(DjangoJSONEncoder):
    """ DjangoJSONEncoder subclass that fallbacks to str(o) instead of TypeError """
    def default(self, o):
        try:
            return super(DjangoJSONEncoder, self).default(o)
        except TypeError:
            return str(o)


def clean_unit_name(unit_name, default=None):
    """ A unit name can start/end with letters + digits. In between minus signs are also allowed """
    # If non-letter or non-digit, replace with minus
    letters_digits_minuses = re.sub(r'[^a-zA-Z\d]', '-', unit_name or '')
    # Strip extra minuses + leading & trailing
    stripped = re.sub(r'-{2,}', '-', letters_digits_minuses).strip('-')
    return stripped if stripped else default


def rruleset_from_recurrence_field(recurrence: Recurrence, dtstart=None, as_rruleset=None, as_str=None) \
        -> Union[str, rruleset]:
    # TODO: Create separated methods, so rrulesrt should return rrules, exrules, rdate, exdate info
    assert as_rruleset or as_str
    if as_str:
        return str(recurrence)
    rec_set = rruleset()
    rec_set._rrule = [r.to_dateutil_rrule(dtstart=dtstart or recurrence.dtstart) for r in recurrence.rrules]
    rec_set._exrule = [r.to_dateutil_rrule(dtstart=dtstart or recurrence.dtstart) for r in recurrence.exrules]
    rec_set._rdate = recurrence.rdates
    rec_set._exdate = recurrence.exdates
    return rec_set


def get_text_recurrence_rrules(rec: Recurrence) -> str:
    text_rules = []
    for rrule in rec.rrules:
        text_rules.append(rrule.to_text())
    return '; '.join(text_rules)


def csv_value_from_dict(headers: List[str], data: List[dict]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()


def admin_url_from_object(db_obj: ModelBase):
    admin_path = 'admin:%s_%s_change' % (db_obj._meta.app_label, db_obj._meta.model_name)
    return settings.HOST_URL + reverse(admin_path, args=[db_obj.pk])
