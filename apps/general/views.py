import json

from django.http.response import HttpResponseBadRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from apps.general.exceptions import ErrorDto
from apps.general.utils import redirect_to_marketing_site


class PostView(View):
    http_method_names = ['post']

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        # check for allowed request methods
        if request.method.lower() not in self.http_method_names:
            return self.http_method_not_allowed(request=request)
        # decode raw data
        request.raw_data = str(request.body, 'utf-8')
        try:
            request.data = json.loads(request.raw_data)
        except Exception as e:
            return HttpResponseBadRequest(json.dumps({
                'detail': 'JsonDecodeError',
                'description': [ErrorDto(key='error', message=str(e))]
            }))
        return super().dispatch(request, *args, **kwargs)


def index(request):
    if request.user.is_authenticated:
        return redirect(request.user.home_url)

    return redirect(redirect_to_marketing_site('/'))


def raise_exception(request):
    """ Use this to test error reporting/logging """
    assert False, "this is a test error"


def return_200(request):
    """ Used in devops to monitor if the backend is up and running """
    return HttpResponse('ok')
