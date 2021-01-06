from django import urls

from . import views as scheduler_views

app_name = 'scheduler'


urlpatterns = [
    urls.path('', scheduler_views.HomepageView.as_view(), name='homepage'),
    urls.path(
        'api/create-task',
        scheduler_views.TaskCreationView.as_view(),
        name='api-task-create',
    ),
    urls.path(
        'api/update-task',
        scheduler_views.TaskUpdateView.as_view(),
        name='api-task-update',
    ),
    urls.path(
        'api/delete-task',
        scheduler_views.TaskDeleteView.as_view(),
        name='api-task-delete',
    ),
    urls.path(
        'api/update-task-status',
        scheduler_views.TaskStatusUpdateView.as_view(),
        name='api-task-status-update',
    ),
    urls.path(
        'api/tasks',
        scheduler_views.TasksView.as_view(),
        name='api-tasks',
    ),
]
