import logging
import re

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class AddReleaseIdToResponseMiddleware(MiddlewareMixin):
    def process_response(self, _, response):
        response['x-release-git-sha'] = settings.RELEASE_GIT_SHA.split('-')[-1]
        response['Access-Control-Expose-Headers'] = 'x-release-git-sha'
        return response


class CustomSentry400CatchMiddleware(MiddlewareMixin):
    """ Tweaked version of `raven.contrib.django.middleware.Sentry404CatchMiddleware` to log all 400 responses """
    def process_response(self, request, response):
        if response.status_code != 400:
            return response

        from raven.contrib.django.models import client
        if not client.is_enabled():
            return response

        data = client.get_data_from_request(request)
        # Ignore `django.security.DisallowedHost` errors
        if re.search(r'\d+\.\d+\.\d+\.\d+', data.get('request', {}).get('url', '')):
            return response

        data.update({
            'level': logging.DEBUG,
            'logger': 'manual_sentry_logger',
        })
        result = client.captureMessage(
            message='400 response',
            data=data,
            extra={'response': self._parse_response(response)},
        )
        if not result:
            return response

        request.sentry = {
            'project_id': data.get('project', client.remote.project),
            'id': client.get_ident(result),
        }
        return response

    @staticmethod
    def _parse_response(response):
        """ Convert response obj into a serializable dict """
        try:
            return {
                key: getattr(response, key)
                for key in dir(response)
                if not key.startswith('__') and not callable(getattr(response, key))
            }
        except Exception:
            return {
                'error': 'Failed to parse response.',
                'raw_response': response,
            }
