from django import forms as django_forms
from django.core import exceptions

from . import models as kernel_models


class TaskCreateForm(django_forms.ModelForm):
    """Form for a task."""
    class Meta:
        model = kernel_models.Task
        fields = ['start_time', 'end_time', 'task_desc']
        error_messages = {
            'start_time': {
                'overlap': "{field_label} overlaps the timespan of '{overlapped_task_desc}' task.",
            },
            'end_time': {
                'overlap': "{field_label} overlaps the timespan of '{overlapped_task_desc}' task.",
                'underflow': f"A task's timespan must be at-least"
                             f" {kernel_models.Task.MINIMUM_TASK_DURATION_MINS} minutes."
            },
        }

    def clean_start_time(self):
        """Validates `start_time` field.

        The following is validated:
          * `start_time` does not overlap any existing task's timespan.

        Raises:
            AttributeError: if `self.instance.schedule` is not set.
            ValidationError: if `start_time` overlaps any task's timespan
             in the current day schedule.
        """
        self._check_schedule()
        start_time = self.cleaned_data.get('start_time')
        if start_time:
            task_obj = kernel_models.Task.get_start_time_overlap_task(
                    self.instance.schedule, start_time, self.instance.id
            )
            if task_obj:
                start_time_field = self.fields['start_time']
                raise exceptions.ValidationError(
                    start_time_field.error_messages['overlap'].format(
                        field_label=start_time_field.label,
                        overlapped_task_desc=task_obj.task_desc,
                    )
                )
        return start_time

    def clean_end_time(self):
        """Validates `end_time` field.

        The following is validated:
          * The timespan between `start_time` and `end_time` is greater
            than or equal to the minimum timespan for any task defined at
            `models.Task.MINIMUM_TASK_DURATION_MINS`

          * `end_time` does not overlap any existing task's timespan in
            the current day schedule.

        Raises:
            AttributeError: if `self.instance.schedule` is not set.
            ValidationError: if `start_time` overlaps any task's timespan
             in the current day schedule.
        """
        self._check_schedule()
        start_time = self.cleaned_data.get('start_time')
        end_time = self.cleaned_data.get('end_time')
        if start_time and end_time:
            task_obj = kernel_models.Task.get_end_time_overlap_task(
                self.instance.schedule, start_time, end_time, self.instance.id
            )
            if task_obj:
                end_time_field = self.fields['end_time']
                raise exceptions.ValidationError(
                    end_time_field.error_messages['overlap'].format(
                        field_label=end_time_field.label,
                        overlapped_task_desc=task_obj.task_desc,
                    )
                )

            try:
                kernel_models.Task.validate_minimum_timespan(start_time, end_time)
            except exceptions.ValidationError:
                raise exceptions.ValidationError(self.fields['end_time'].error_messages['underflow'])
        return end_time

    def _check_schedule(self):
        """Checks if `self.instance.schedule` is set.

        Raises:
            ValidationError: if `self.instance.schedule` is not set.
        """
        # if we try to access the schedule and it is not set, django will
        # raise a `RelatedObjectDoesNotExist` exceptions which is defined
        # internally and it is a subclass of `AttributeError`. So we can
        # catch that error by catching `AttributeError` and raising it.
        try:
            _ = self.instance.schedule
        except AttributeError:
            raise AttributeError('schedule is not set.')


class TaskUpdateForm(TaskCreateForm):
    """A form for updating a task."""
    def __init__(self, *args, **kwargs):
        super().__init__(auto_id='id_u_%s', *args, **kwargs)
