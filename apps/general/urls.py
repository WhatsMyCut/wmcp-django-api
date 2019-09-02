from django.conf.urls import url
from django.urls import reverse_lazy, re_path
from django.views.generic.base import RedirectView

from apps.general.utils import redirect_to_marketing_site
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^properties$', RedirectView.as_view(url=redirect_to_marketing_site('properties'), permanent=True),
        name='properties'),
    url(r'^partners$', RedirectView.as_view(url=redirect_to_marketing_site('providers'), permanent=True),
        name='partners'),
    url(r'^residents$', RedirectView.as_view(url=redirect_to_marketing_site('residents'), permanent=True),
        name='residents'),
    url(r'^about$', RedirectView.as_view(url=redirect_to_marketing_site('about-us'), permanent=True), name='about'),
    url(r'^learn-more$', RedirectView.as_view(url=redirect_to_marketing_site('contact-us'), permanent=True),
        name='learn_more'),
    url(r'^terms$',
        RedirectView.as_view(url=redirect_to_marketing_site('terms-conditions-privacy-policy'), permanent=True),
        name='terms'),
    url(r'^privacy$',
        RedirectView.as_view(url=redirect_to_marketing_site('terms-conditions-privacy-policy'), permanent=True),
        name='privacy'),
    re_path(r'^800penn$(?i)', RedirectView.as_view(url=reverse_lazy('account:login'))),
    re_path(r'^ettaSF$(?i)', RedirectView.as_view(url=reverse_lazy('account:login'))),
    url(r'^raise_exception', views.raise_exception, name='raise_exception'),  # for internal (developers) use
    url(r'^return-200', views.return_200, name='return-200'),  # for internal devops use
]
