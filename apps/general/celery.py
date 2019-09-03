import json
import subprocess
import importlib

from django.conf.urls import url
from django.core.cache import cache
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django_celery_beat.admin import PeriodicTaskAdmin
from django_celery_beat.models import PeriodicTask
from django_celery_results.admin import TaskResultAdmin
from django_celery_results.backends import DatabaseBackend

from apps.general.decorators import run_on_commit
from apps.general.loggers import django_logger
from apps.general.utils import in_tests


class WMCPDatabaseBackend(DatabaseBackend):
    def mark_as_failure(self, task_id, exc, *args, **kwargs):
        """Mark task as executed with failure."""
        django_logger.exception('Celery task failed: %s' % exc, exc_info=exc)
        super().mark_as_failure(task_id, exc, *args, **kwargs)

    """Custom result backend that also stores a task name."""
    def _store_result(self, task_id, result, status,
                      traceback=None, request=None):
        """Store return value and status of an executed task."""
        content_type, content_encoding, result = self.encode_content(result)
        _, _, meta = self.encode_content({
            'children': self.current_task_children(request),
            'task_name': request.task
        })

        self.TaskModel._default_manager.store_result(
            content_type, content_encoding,
            task_id, result, status,
            traceback=traceback,
            meta=meta,
        )
        return result

# Monkey-patching for displaying also the 'task_name' in the admin task results table.
# A more clean approach with unregister\register leads to errors.
TaskResultAdmin.list_display = ('task_id', 'date_done', 'status', 'task_name')
TaskResultAdmin.task_name = lambda self, obj: json.loads(obj.meta)['task_name']
TaskResultAdmin.task_name.short_description = 'Task name'


def import_task(task_id):
    try:
        task_path = PeriodicTask.objects.get(id=task_id).task
        module_path, task_name = task_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        task = getattr(module, task_name)
        return task, True
    except Exception:
        return None, False


def task_actions(self, obj):
    key = 'task_%s_importable' % obj.pk
    is_importable = cache.get(key)
    if is_importable is None:
        _, is_importable = import_task(obj.pk)
        cache.set(key, is_importable, 60 * 60)

    if is_importable:
        return format_html('<a class="button" href="%s">Run</a>' % reverse('admin:run_task', args=[obj.pk]))
    else:
        return ''


def process_task_run(request, task_id, *args, **kwargs):
    task, _ = import_task(task_id)
    run_task(task)
    return redirect(reverse('admin:django_celery_results_taskresult_changelist'))


def task_get_urls(self):
    return [url(r'^celery_task/(?P<task_id>.+)/run/$', self.admin_site.admin_view(process_task_run), name='run_task')] \
           + super(self.__class__, self).get_urls()


PeriodicTaskAdmin.task_actions = task_actions
PeriodicTaskAdmin.list_display = PeriodicTaskAdmin.list_display + ('task_actions',)
PeriodicTaskAdmin.get_urls = task_get_urls


def run_task(task, *args, **kwargs):
    """
    Runs celery task asynchronously if celery workers are available, else synchronously.
    This works only until we have workers and rabbitmq on the same instance as our app,
    rather than on remote nodes.
    """
    ps = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
    grep1 = subprocess.Popen(['grep', '-v', 'grep'], stdin=ps.stdout, stdout=subprocess.PIPE)
    grep2 = subprocess.Popen(['grep', 'celery.*worker'], stdin=grep1.stdout, stdout=subprocess.PIPE)

    if len(list(grep2.stdout)) > 0 and not in_tests():
        run_on_commit(lambda: task.delay(*args, **kwargs))
    else:
        run_on_commit(lambda: task.run(*args, **kwargs))
