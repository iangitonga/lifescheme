from django.contrib import admin

from . import models as scheduler_models


admin.site.register(scheduler_models.UserDaySchedule)
admin.site.register(scheduler_models.Task)
