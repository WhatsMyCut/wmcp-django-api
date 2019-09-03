from django.conf import settings
from django.conf.urls import url, include
from django.urls import re_path
from django.conf.urls.static import static
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView

from apps.general.graphql import GraphQLView


urlpatterns = [
    url(r'^', include(('apps.general.urls', 'general'), namespace='general')),

    url(r'^admin/', admin.site.urls),
    url(r'^account/', include(('apps.account.urls', 'account'), namespace='account')),
    url(r'^partner/', include(('apps.partner.urls', 'partner'), namespace='partner')),
    url(r'^appointments/', include(('apps.appointments.urls', 'appointments'), namespace='appointments')),

    re_path(r'^ettaSF$(?i)', RedirectView.as_view(url=settings.LOGIN_URL, permanent=False), name='ettasf'),
    url(r'^payment/', include(('apps.payment.urls', 'payment'), namespace='payment')),
    url(r'^graphql', csrf_exempt(GraphQLView.as_view(batch=True)), name='graphql_endpoint'),
    url(r'^graphiql', csrf_exempt(GraphQLView.as_view(graphiql=True)), name='graphiql_endpoint'),
    url(r'^tinymce/', include(('tinymce.urls', 'tinymce'), namespace='tinymce')),
    url(r'^salesforce/', include(('apps.salesforce.urls', 'salesforce'), namespace='salesforce')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.PORTAL_STATIC_URL, document_root=settings.PORTAL_STATIC_ROOT)
