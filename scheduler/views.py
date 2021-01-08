from django import http, shortcuts, views as django_views
from django.core import exceptions
from django.template import defaultfilters

from . import forms as kernel_forms


class BaseView(django_views.View):
    """This class is the views base class from which all other views should be derived.

    This class provides general methods that are typically needed in a view.
    Also the GET and POST methods will, by default, return 403(forbidden)
    error. This will ensure that if a class inherits from this one and does
    not override GET or POST methods, If a request is made, a forbidden error
    will be returned to the client.

    Notes:
        This class is not meant to be instantiated.
    """

    def get(self, request, *args, **kwargs):
        """Processes HTTP GET requests.

        Args:
            request: A HttpRequest instance.

        Returns:
            A HttpResponse or HttpResponse subclass instance with the
             appropriate data.
        """
        return http.HttpResponseForbidden()

    def post(self, request, *args, **kwargs):
        """Processes HTTP POST requests.

        Args:
            request: A HttpRequest instance.

        Returns:
            A HttpResponse or HttpResponse subclass instance with the
            appropriate data.
        """
        return http.HttpResponseForbidden()


class HomepageView(BaseView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return shortcuts.render(request, 'scheduler/landing_page.html')
        return shortcuts.render(request, 'scheduler/homepage.html')


class TaskCreationView(BaseView):
    """A view for creating a task.

    This view only accepts POST requests.
    """
    def post(self, request, *args, **kwargs):
        filled_task_form = kernel_forms.TaskCreateForm(request.POST)
        filled_task_form.instance.schedule = request.user.dayschedules.current_schedule
        if filled_task_form.is_valid():
            saved_task = filled_task_form.save()
            return http.JsonResponse({
                'taskId': saved_task.id,
                'taskStartTime': defaultfilters.time(saved_task.start_time, 'H:i'),
                'taskEndTime': defaultfilters.time(saved_task.end_time, 'H:i'),
                'taskDesc': saved_task.task_desc,
            })
        else:
            return http.JsonResponse({'FORM_ERRORS': filled_task_form.errors}, status=400)


class TaskUpdateView(BaseView):
    """A view for updating an existing task.

    This view only accepts POST requests.
    """
    def post(self, request, *args, **kwargs):
        task_id = int(request.POST.get('task_id'))
        try:
            task_obj = request.user.dayschedules.current_schedule.tasks.get(id=task_id)
        except exceptions.ObjectDoesNotExist:
            return http.JsonResponse({'ERROR': f'Could not retrieve task({task_id})'}, status=400)
        filled_task_form = kernel_forms.TaskUpdateForm(self.request.POST, instance=task_obj)
        if filled_task_form.is_valid():
            filled_task_form.save()
            return http.JsonResponse({
                'taskId': task_id,
                'taskStartTime': defaultfilters.time(filled_task_form.cleaned_data['start_time'], 'H:i'),
                'taskEndTime': defaultfilters.time(filled_task_form.cleaned_data['end_time'], 'H:i'),
                'taskDesc': filled_task_form.cleaned_data['task_desc'],
            })
        else:
            return http.JsonResponse({'FORM_ERRORS': filled_task_form.errors}, status=400)


class TaskDeleteView(BaseView):
    """A view for deleting a task.

    This view only accepts POST requests.
    """
    def post(self, request, *args, **kwargs):
        task_id = int(request.POST.get('task_id'))
        try:
            task_obj = request.user.dayschedules.current_schedule.tasks.get(id=task_id)
        except exceptions.ObjectDoesNotExist:
            return http.JsonResponse({'ERROR': f'Could not retrieve task({task_id})'}, status=400)
        task_obj.delete()
        return http.JsonResponse({
            'taskId': task_id,
        })


class TaskStatusUpdateView(BaseView):
    """A view for marking a task as completed or vice-versa.

    This view only accepts POST requests.
    """
    def post(self, request, *args, **kwargs):
        task_id = int(request.POST.get('task_id'))
        try:
            task_obj = request.user.dayschedules.current_schedule.tasks.get(id=task_id)
        except exceptions.ObjectDoesNotExist:
            return http.JsonResponse({'ERROR': f'Could not retrieve task({task_id})'}, status=400)
        if task_obj.completed:
            task_obj.completed = False
        else:
            task_obj.completed = True
        task_obj.save(update_fields=['completed'])
        return http.JsonResponse({
            'task_id': task_id,
        })


class TasksView(BaseView):
    """A view for retrieving all the tasks for the current schedule for
     request.user."""
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        tasks_qs = request.user.dayschedules.current_schedule.tasks.all()
        serialized_tasks = []
        for task_obj in tasks_qs:
            task_dict = {
                'id': task_obj.id,
                'startTime': defaultfilters.time(task_obj.start_time, 'H:i'),
                'endTime': defaultfilters.time(task_obj.end_time, 'H:i'),
                'desc': task_obj.task_desc,
                'completed': task_obj.completed,
            }
            serialized_tasks.append(task_dict)
        serialized_tasks.sort(key=lambda task: task['startTime'])
        return http.JsonResponse({'TASKS': serialized_tasks})
