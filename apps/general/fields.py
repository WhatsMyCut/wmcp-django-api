import random
import string

from django.db import models
from django.forms import fields
from model_mommy import mommy
from recurrence.fields import RecurrenceField
from tinymce import models as tinymce_models

from apps.general.widgets import NullableCheckboxInput


class NullableField:
    def __init__(self, *args, **kwargs):
        kwargs.update({'null': True})
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        return value or None


class NullableFormField:
    def to_python(self, value):
        if value is None:
            return None
        else:
            return super().to_python(value)


class UniqueNullableField:
    def __init__(self, *args, **kwargs):
        kwargs.update({'null': True, 'unique': True})
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        return value or None


class UniqueNullableCharField(UniqueNullableField, models.CharField):
    pass


class NullableCharField(NullableField, models.CharField):
    pass


class NullableBooleanFormField(NullableFormField, fields.BooleanField):
    widget = NullableCheckboxInput


class NullableCharFormField(NullableFormField, fields.CharField):
    pass


# fix for model-mummy
def random_html_str(length=400):
    return '<p>%s</p>' % ''.join(
        random.choice(string.ascii_lowercase + string.ascii_uppercase) for i in range(length))


mommy.generators.add(tinymce_models.HTMLField, random_html_str)
mommy.generators.add(RecurrenceField, lambda: 'RRULE:FREQ=DAILY;COUNT=10')
