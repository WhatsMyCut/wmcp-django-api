import datetime
import json

from django import template
from django.conf import settings
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.template.defaultfilters import stringfilter
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe

from apps.general.utils import redirect_to_marketing_site, DateUtils, FieldsUtils, get_text_recurrence_rrules
from apps.resident.models import Resident

register = template.Library()


@register.filter
def is_url(request, name):
    # Tests if the request matches the url name
    return request.path == reverse(name)


@register.filter
def jsonify(object):
    if isinstance(object, QuerySet):
        return mark_safe(serialize('json', object))
    else:
        return mark_safe(json.dumps(object))


@register.filter
def home_url(request):
    if request.user.is_authenticated:
        return request.user.home_url

    return redirect_to_marketing_site('/')


@register.filter
def menu_logo(request):
    if not request.user.is_authenticated:
        return static('images/header_logo_green.svg')
    if request.user.property_manager and request.user.property_manager.company.logo:
        return settings.MEDIA_URL + str(request.user.property_manager.company.logo)
    resident = Resident.all_objects.filter(user=request.user).order_by('deleted', '-created_at').first()
    if resident and resident.property.logo:
        return resident.property.logo_as_absolute_url
    return static('images/header_logo_green.svg')


@register.filter
def menu_logo_class(request):
    default = 'default-logo'
    custom = 'custom-logo'
    if not request.user.is_authenticated:
        return default
    return default



@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(is_safe=True)
def html_link(value, target='self'):
    url_parts = value.split('//', 1)
    if len(url_parts) > 1:
        return '<a href="' + value + '" target="_' + target + '">' + url_parts[1] + '</a>'
    else:
        return '<a href="http://' + value + '" target="_' + target+'">' + value + '</a>'


@register.filter
@stringfilter
def parse_date(date_string, format_, as_utc=True):
    """
    Return a datetime corresponding to date_string, parsed according to format.

    For example, to re-display a date string in another format::

        {{ "01/01/1970"|parse_date:"%m/%d/%Y"|date:"F jS, Y" }}
    """
    try:
        parsed_dt = datetime.datetime.strptime(date_string, format_)
        return DateUtils.as_utc(parsed_dt) if as_utc else parsed_dt
    except ValueError:
        pass


@register.filter('startswith')
def startswith(text, starts):
    if isinstance(text, (str, bytes)):
        return text.startswith(starts)
    return False


@register.filter('text_rrules')
def text_rrules(rec):
    return get_text_recurrence_rrules(rec)
