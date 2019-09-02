from django import template

from apps.general.utils import redirect_to_marketing_site

register = template.Library()


@register.simple_tag
def active(request, pattern):
    import re
    if re.search(pattern, request.path):
        return 'active'
    return ''


@register.simple_tag
def marketing_site(url_name):
    return redirect_to_marketing_site(url_name)
