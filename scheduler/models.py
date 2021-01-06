import datetime

from django.contrib.auth import models as django_auth_models
from django.core import exceptions
from django.db import models as django_db_models


class UserDayScheduleManager(django_db_models.Manager):
    """Manager for `UserDaySchedule` class.

    This class will provide useful custom methods for retrieving data.
    """
    @property
    def current_schedule(self):
        """Returns the current day day-schedule for a user.

        If the user does not have the current day-schedule, a new schedule
        for the current day is created and returned,

        Raises:
            PermissionError: if not accessed through a related manager by a
             `django.contrib.auth.models.User` instance.

        Notes:
            This method is meant to be accessed by `User` objects through
            related manager to make it a convenience to retrieve the current
            day schedule. Accessing this methods through 'objects' manager of
            `UserDaySchedule` would not make sense because there is no such
            thing as 'current day schedule' for multiple users.
        """
        if not hasattr(self, 'instance') or not isinstance(self.instance, django_auth_models.User):
            raise PermissionError("Only 'user' classes are allowed to access this method.")
        schedule, _ = self.get_or_create(date=self.instance.profile.datetime.date())
        return schedule


class UserDaySchedule(django_db_models.Model):
    """Represents a user-specific schedule bound to a particular date.

    A day-schedule has a user, a date and task(s).
    """
    objects = UserDayScheduleManager()

    user = django_db_models.ForeignKey(
        django_auth_models.User,
        related_name='dayschedules',
        on_delete=django_db_models.CASCADE,
    )
    # The date for a schedule. It cannot be unique since each day-schedule
    # is user-specific.
    date = django_db_models.DateField()

    class Meta:
        constraints = [
            # This constraint will ensure that for every day-schedule, the
            # combination of user and date will be unique. That is, there
            # cannot exist more than one day-schedule with the same user
            # and equal dates.
            django_db_models.UniqueConstraint(fields=['user', 'date'], name='unique_user_schedules'),
        ]

    def __repr__(self):
        return f'DaySchedule(user={self.user.username}, date={self.date})'

    def __str__(self):
        return f'{self.date} - {self.user.username}'


class Task(django_db_models.Model):
    """Represents a piece of work with a status, bound to a unique time
     block and a user day-schedule.

     The static methods are utilities that are used within and outside of this
     class.
     """
    # The smallest duration that a task is allowed to span.
    MINIMUM_TASK_DURATION_MINS = 5

    schedule = django_db_models.ForeignKey(
        UserDaySchedule,
        related_name='tasks',
        on_delete=django_db_models.CASCADE,
    )
    # The time when a task is scheduled to start.
    start_time = django_db_models.TimeField()
    # The time when a task is scheduled to end.
    end_time = django_db_models.TimeField()
    # `task_desc` is the description of the task itself.
    task_desc = django_db_models.CharField(max_length=50, verbose_name='task')
    # A boolean that informs the status of the task. True means the task
    # is marked as complete and false means the task is/was not completed.
    completed = django_db_models.BooleanField(default=False)

    class Meta:
        ordering = ['start_time']

    def __repr__(self):
        return (
            f'Task(schedule={self.schedule.date}, user={self.schedule.user.username}, task={self.task_desc})'
        )

    def __str__(self):
        return f'{self.schedule.date} - {self.schedule.user.username} - {self.task_desc}'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """Save the current instance.

        We perform sanity checking before saving any data to ensure that
        the data is safe even if a form was not used to validate it.
        This instance must achieve the following to be valid:
          * `self.start_time` must not overlap any other task's time.
          * `self.end_time` must not overlap any other task's time.
          * `self.end_time` - `self.start_time` must be greater than or
            equal to `self.MINIMUM_TASK_DURATION_MINS`.

        Raises:
            TypeError: if any field of this instance is of unexpected type.
            ValidationError: if this instance is not valid.
        """
        task_obj = self.get_start_time_overlap_task(self.schedule, self.start_time, self.id)
        if task_obj:
            raise exceptions.ValidationError(
                {'start_time': f"This field overlaps with '{task_obj.task_desc}' time."}
            )
        task_obj = self.get_end_time_overlap_task(
                self.schedule, self.start_time, self.end_time, self.id
        )
        if task_obj:
            raise exceptions.ValidationError(
                {'end_time': f"This field overlaps with '{task_obj.task_desc}' time."}
            )
        self.validate_minimum_timespan(self.start_time, self.end_time)
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )

    @staticmethod
    def get_start_time_overlap_task(schedule, start_time, task_id):
        """Returns a `Task` instance in `schedule` whose time overlap with
         `start_time` if found.

        Args:
            schedule(UserDaySchedule): The schedule from which to check
             time overlap.
            start_time(datetime.time): the starting time of a task.
            task_id: The id of the task instance that `start_time` belongs to.

        Raises:
            TypeError: if `schedule` is not an instance of `UserDaySchedule`.
            TypeError: if `start_time` is not an instance of `datetime.time`.
        """
        if not isinstance(schedule, UserDaySchedule):
            raise TypeError(f"'schedule' should be of type 'UserDaySchedule', not {type(schedule)}")
        if not isinstance(start_time, datetime.time):
            raise TypeError(f"'start_time' should be of type 'datetime.date', not {type(start_time)}")
        # We create datetime objects from time objects to support
        # comparisons.
        target_start_dt = datetime.datetime.combine(schedule.date, start_time)
        for task_obj in schedule.tasks.all():
            task_start_dt = datetime.datetime.combine(schedule.date, task_obj.start_time)
            task_end_dt = datetime.datetime.combine(schedule.date, task_obj.end_time)
            # We check the ids to make sure that if we call save on an
            # already saved object, we do not mistakenly raise an
            # exception. This would occur because a task's timespan would
            # overlap with its own timespan.
            if task_obj.id != task_id and task_start_dt <= target_start_dt <= task_end_dt:
                return task_obj

    @staticmethod
    def get_end_time_overlap_task(schedule, start_time, end_time, task_id):
        """Returns a `Task` instance in `schedule` whose time overlap with
         `start_time` and `end_time`, if found.

        Args:
            schedule(UserDaySchedule): a schedule from which tasks to compare
             tasks overlaps.
            start_time(datetime.time): starting time for a task.
            end_time(datetime.time): starting time for a task.
            task_id: The id of the task instance that `end_time` belongs to.

        Raises:
            TypeError: if `schedule` is not an instance of `UserDaySchedule`.
            TypeError: if `start_time` is not an instance of `datetime.time`.
            TypeError: if `end_time` is not an instance of `datetime.time`.
        """
        if not isinstance(schedule, UserDaySchedule):
            raise TypeError(f"'schedule' should be of type 'UserDaySchedule', not {type(schedule)}")
        if not isinstance(start_time, datetime.time):
            raise TypeError(f"'start_time' should be of type 'datetime.date', not {type(start_time)}")
        if not isinstance(end_time, datetime.time):
            raise TypeError(f"'end_time' should be of type 'datetime.time', not {type(end_time)}")
        # We create datetime objects from time objects to support
        # comparisons.
        target_start_dt = datetime.datetime.combine(schedule.date, start_time)
        target_end_dt = datetime.datetime.combine(schedule.date, end_time)
        for task_obj in schedule.tasks.all():
            task_start_dt = datetime.datetime.combine(schedule.date, task_obj.start_time)
            task_end_dt = datetime.datetime.combine(schedule.date, task_obj.end_time)
            # We check the ids to make sure that if we call save on an
            # already saved object, we do not mistakenly raise an
            # exception. This would occur because a task's timespan would
            # overlap with its own timespan.
            if task_obj.id != task_id and task_start_dt <= target_end_dt and task_end_dt >= target_start_dt:
                return task_obj

    @staticmethod
    def validate_minimum_timespan(start_time, end_time):
        """Raises an exception if (end_time - start_time) is less that
         `Task.MINIMUM_TASK_DURATION_MINS`.

        Args:
            start_time: a `datetime.time` instance representing start time
             for a particular task.
            end_time: a `datetime.time` instance representing start time
             for a particular task.

        Raises:
            TypeError: if `start_time` or `end_time` is not a
             `datetime.time` object.
            ValidationError: if and only if the (`end_time` - `start_time`)
             is less than `Task.MINIMUM_TASK_DURATION_MINS`.
        """
        if not isinstance(start_time, datetime.time):
            raise TypeError(f"'start_time' should be an instance of 'datetime.time' not {type(start_time)}.")
        if not isinstance(end_time, datetime.time):
            raise TypeError(f"'end_time' should be an instance of 'datetime.time' not {type(end_time)}.")
        # To find the difference between the two times, we create
        # datetimes from the two times and same date and then find the
        # timedelta between the two dates.
        # Note: any date, as long as it is used to create both datetimes,
        # can work.
        date = datetime.date(2000, 1, 1)
        start_time_datetime = datetime.datetime.combine(date, start_time)
        end_time_datetime = datetime.datetime.combine(date, end_time)
        delta = end_time_datetime - start_time_datetime
        if delta.total_seconds() < (Task.MINIMUM_TASK_DURATION_MINS * 60):
            err_msg = (
                f"The difference between 'start_time: {start_time}' and 'end_time: {end_time}' "
                f"is less that the allowed minimum: {Task.MINIMUM_TASK_DURATION_MINS}"
            )
            raise exceptions.ValidationError({'end_time': err_msg})
