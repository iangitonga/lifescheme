from django.contrib import admin

from . import models as acc_models


admin.site.register(acc_models.UserProfile)
