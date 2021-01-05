import pytz
from django.db import models as db_models
from django.contrib.auth import models as auth_models
from django.utils import timezone


class UserProfile(db_models.Model):
    """This model stores extra data for a user"""
    TIMEZONES = sorted(pytz.common_timezones_set)
    TIMEZONE_CHOICES = zip(TIMEZONES, TIMEZONES)

    user = db_models.OneToOneField(
        auth_models.User,
        related_name='profile',
        on_delete=db_models.CASCADE,
    )
    timezone = db_models.CharField(
        choices=TIMEZONE_CHOICES,
        max_length=len(max(TIMEZONES, key=len)),
    )

    def __str__(self):
        return f'{self.user.username} Profile'

    @property
    def datetime(self):
        """Return a datetime instance representing the datetime in accordance
        with the timezone of the user associated with the current instance."""
        # We assume that `self.timezone` is set to a valid timezone due to the
        # choices constraint on `timezone` field and the fact that the database
        # will not store a null as timezone's value.
        user_timezone = pytz.timezone(self.timezone)
        return timezone.now().astimezone(user_timezone)
