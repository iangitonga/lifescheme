import datetime

from django import conf, http, test, shortcuts
from django.core import exceptions
from django.contrib.auth import models as django_auth_models
from django.core.serializers import json as dj_json
from django.template import defaultfilters

from accounts import models as account_models

from . import (
    forms as scheduler_forms,
    models as scheduler_models,
    views as scheduler_views,
)


class UserDayScheduleManagerTest(test.TestCase):
    """Tests `models.UserDayScheduleManager` class.

    Test cases:
      - Returns the correct schedule when called by an allowed caller.
      - Raises an exception when called by a disallowed caller.
      - Raises an exception when the current schedule cannot be found.
    """
    def test_get_current_day_schedule_allowed_caller(self):
        user = django_auth_models.User.objects.create(username='Testuser')
        user_profile = account_models.UserProfile(user=user, timezone=conf.settings.TIME_ZONE)
        user_profile.save()
        current_schedule = user.dayschedules.create(date=datetime.date.today())
        test_schedule = user.dayschedules.current_schedule
        self.assertEqual(current_schedule, test_schedule)

    def test_get_current_day_schedule_disallowed_caller(self):
        err_msg = "Only 'user' classes are allowed to access this method."
        with self.assertRaisesMessage(PermissionError, err_msg):
            _ = scheduler_models.UserDaySchedule.objects.current_schedule

    def test_get_current_day_schedule_missing_schedule(self):
        user = django_auth_models.User.objects.create(username='Testuser')
        self.assertRaises(
            exceptions.ObjectDoesNotExist,
            lambda: user.dayschedules.current_schedule
        )


# noinspection PyTypeChecker
class TaskModelTest(test.TestCase):
    """Tests `kernel.Task` model.

    Test cases:
      Cases for `validate_minimum_timespan` static method:
        - Does not raise any exception if timespan is gte the minimum.
        - Raises `TypeError` if start_time is not an instance of
          class 'datetime.date'.
        - Raises `TypeError` if end_time is not an instance of
          class 'datetime.date'.
        - Raises ValidationError if end_time - start_time is less than
          the expected minimum.
      Cases for `get_start_time_overlap_task` and `get_end_time_overlap_task` static methods:
        - Does not raise any exception if no time overlap.
        - Raises `TypeError` if schedule is not an instance of
          `models.UserDaySchedule`.
        - Raises `TypeError` if `start_time` is not an instance of
          `datetime.date`.
        - Returns the expected task object if there is a time overlap.
      Cases for `save` method:
        - Saves an object with correct inputs.
    """
    def test_validate_minimum_timespan_with_correct_inputs(self):
        start_time = datetime.time(7, 0)
        end_time = datetime.time(7, 5)
        scheduler_models.Task.validate_minimum_timespan(start_time, end_time)

    def test_validate_minimum_timespan_with_start_time_of_wrong_type(self):
        start_time = None
        end_time = datetime.time(7, 5)
        msg = f"'start_time' should be an instance of 'datetime.time' not {type(start_time)}."
        with self.assertRaisesMessage(TypeError, msg):
            scheduler_models.Task.validate_minimum_timespan(start_time, end_time)

    def test_validate_minimum_timespan_with_end_time_of_wrong_type(self):
        start_time = datetime.time(7, 5)
        end_time = None
        msg = f"'end_time' should be an instance of 'datetime.time' not {type(end_time)}."
        with self.assertRaisesMessage(TypeError, msg):
            scheduler_models.Task.validate_minimum_timespan(start_time, end_time)

    def test_validate_minimum_timespan_with_invalid_inputs(self):
        start_time = datetime.time(7, 0)
        end_time = datetime.time(7, 4)
        msg = (
            f"The difference between 'start_time: {start_time}' and 'end_time: {end_time}' "
            f"is less that the allowed minimum: {scheduler_models.Task.MINIMUM_TASK_DURATION_MINS}"
        )
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            scheduler_models.Task.validate_minimum_timespan(start_time, end_time)

    def test_get_start_time_overlap_task_with_correct_input(self):
        user = django_auth_models.User.objects.create(username='TestUser')
        schedule = scheduler_models.UserDaySchedule.objects.create(
            user=user,
            date=datetime.date(2000, 1, 1)
        )
        schedule.tasks.create(
            schedule=schedule,
            start_time=datetime.time(7, 0),
            end_time=datetime.time(7, 45),
            task_desc='Test task'
        )
        self.assertIsNone(
            scheduler_models.Task.get_start_time_overlap_task(schedule, datetime.time(8, 0), task_id=99)
        )

    def test_get_start_time_overlap_task_with_schedule_of_wrong_type(self):
        schedule = None
        msg = f"'schedule' should be of type 'UserDaySchedule', not {type(schedule)}"
        with self.assertRaisesMessage(TypeError, msg):
            scheduler_models.Task.get_start_time_overlap_task(schedule, datetime.time(7, 0), task_id=99)

    def test_get_start_time_overlap_task_with_start_time_of_wrong_type(self):
        user = django_auth_models.User.objects.create(username='TestUser')
        schedule = scheduler_models.UserDaySchedule.objects.create(
            user=user,
            date=datetime.date(2000, 1, 1)
        )

        start_time = None
        msg = f"'start_time' should be of type 'datetime.date', not {type(start_time)}"
        with self.assertRaisesMessage(TypeError, msg):
            scheduler_models.Task.get_start_time_overlap_task(schedule, start_time, task_id=99)

    def test_get_start_time_overlap_task_with_overlapping_start_time(self):
        user = django_auth_models.User.objects.create(username='TestUser')
        schedule = scheduler_models.UserDaySchedule.objects.create(
            user=user,
            date=datetime.date(2000, 1, 1)
        )
        test_task = schedule.tasks.create(
            schedule=schedule,
            start_time=datetime.time(7, 0),
            end_time=datetime.time(7, 45),
            task_desc='Test task',
        )

        start_time = datetime.time(7, 45)
        overlapped_task = scheduler_models.Task.get_start_time_overlap_task(
            schedule,
            start_time,
            task_id=99,
        )
        self.assertIsInstance(overlapped_task, scheduler_models.Task)
        self.assertEqual(test_task, overlapped_task)

    def test_get_end_time_overlap_task_with_correct_input(self):
        user = django_auth_models.User.objects.create(username='TestUser')
        schedule = scheduler_models.UserDaySchedule.objects.create(
            user=user,
            date=datetime.date(2000, 1, 1)
        )
        s = datetime.time(7, 0)
        e = datetime.time(7, 45)
        schedule.tasks.create(schedule=schedule, start_time=s, end_time=e, task_desc='Test task')
        self.assertIsNone(
            scheduler_models.Task.get_end_time_overlap_task(
                schedule,
                datetime.time(8, 0),
                datetime.time(9, 0),
                99,
            )
        )

    def test_get_end_time_overlap_task_with_schedule_of_wrong_type(self):
        schedule = None
        msg = f"'schedule' should be of type 'UserDaySchedule', not {type(schedule)}"
        with self.assertRaisesMessage(TypeError, msg):
            scheduler_models.Task.get_end_time_overlap_task(
                schedule, datetime.time(7, 0), datetime.time(9, 0), task_id=99
            )

    def test_get_end_time_overlap_task_with_end_time_of_wrong_type(self):
        user = django_auth_models.User.objects.create(username='TestUser')
        schedule = scheduler_models.UserDaySchedule.objects.create(
            user=user,
            date=datetime.date(2000, 1, 1)
        )

        end_time = None
        msg = f"'end_time' should be of type 'datetime.time', not {type(end_time)}"
        with self.assertRaisesMessage(TypeError, msg):
            scheduler_models.Task.get_end_time_overlap_task(
                schedule,
                datetime.time(9, 0),
                end_time,
                task_id=99,
            )

    def test_get_end_time_overlap_task_with_overlapping_end_time_1(self):
        user = django_auth_models.User.objects.create(username='TestUser')
        schedule = scheduler_models.UserDaySchedule.objects.create(
            user=user,
            date=datetime.date(2000, 1, 1)
        )
        s = datetime.time(7, 0)
        e = datetime.time(7, 45)
        new_task = schedule.tasks.create(
            schedule=schedule, start_time=s, end_time=e, task_desc='Test task',
        )

        end_time = datetime.time(7, 0)
        overlapped_task = scheduler_models.Task.get_end_time_overlap_task(
            schedule, datetime.time(6, 0), end_time, task_id=99
        )
        self.assertIsInstance(overlapped_task, scheduler_models.Task)
        self.assertEqual(new_task, overlapped_task)

    def test_get_end_time_overlap_task_with_overlapping_end_time_2(self):
        user = django_auth_models.User.objects.create(username='TestUser')
        schedule = scheduler_models.UserDaySchedule.objects.create(
            user=user,
            date=datetime.date(2000, 1, 1)
        )
        s = datetime.time(7, 0)
        e = datetime.time(7, 45)
        new_task = schedule.tasks.create(
            schedule=schedule, start_time=s, end_time=e, task_desc='Test task',
        )

        end_time = datetime.time(7, 30)
        overlapped_task = scheduler_models.Task.get_end_time_overlap_task(
            schedule, datetime.time(6, 0), end_time, task_id=99
        )
        self.assertIsInstance(overlapped_task, scheduler_models.Task)
        self.assertEqual(new_task, overlapped_task)

    def test_validate_end_time_does_not_overlap_with_overlapping_end_time_3(self):
        user = django_auth_models.User.objects.create(username='TestUser')
        schedule = scheduler_models.UserDaySchedule.objects.create(
            user=user,
            date=datetime.date(2000, 1, 1)
        )
        s = datetime.time(7, 0)
        e = datetime.time(7, 45)
        new_task = schedule.tasks.create(
            schedule=schedule, start_time=s, end_time=e, task_desc='Test task',
        )

        end_time = datetime.time(7, 30)
        overlapped_task = scheduler_models.Task.get_end_time_overlap_task(
            schedule, datetime.time(7, 5), end_time, task_id=99
        )
        self.assertIsInstance(overlapped_task, scheduler_models.Task)
        self.assertEqual(new_task, overlapped_task)

    def test_save_with_correct_inputs(self):
        user = django_auth_models.User.objects.create(username='Testuser')
        schedule = scheduler_models.UserDaySchedule.objects.create(user=user, date=datetime.date(2000, 1, 2))
        task = scheduler_models.Task(
            schedule=schedule,
            start_time=datetime.time(7, 0),
            end_time=datetime.time(8, 0),
            task_desc='Test task',
        )
        task.save()

    def test_saved_object(self):
        """Tests calling save on an already saved object behaves correctly."""
        user = django_auth_models.User.objects.create(username='Testuser')
        schedule = scheduler_models.UserDaySchedule.objects.create(user=user, date=datetime.date(2000, 1, 2))
        task = scheduler_models.Task(
            schedule=schedule,
            start_time=datetime.time(7, 0),
            end_time=datetime.time(8, 0),
            task_desc='Test task',
        )
        task.save()
        # Here, we call save again to ensure that calling `save` on an
        # existing object, which is valid, does not raise an exception.
        task.save()


class TaskFormTest(test.TestCase):
    """Test class for `forms.TaskCreateForm` form.

    The following test cases are performed:
     Note: In this context, 'invalid' means 'that cannot be parsed'.
      * All fields have the expected CSS classes.
      * A valid form with its schedule not set causes an error to be raised.
      * Saving a filled form with correct data saves the data as expected.
      * An empty `start_time` field causes the expected error to be raised.
      * An invalid `start_time` value causes the expected error to be raised.
      * A valid `start_time` value whose time overlap with a task's timespan
        in the current day schedule, causes the expected error to be raised.
      * An empty `end_time` field causes the expected error to be raised.
      * An invalid `end_time` value causes the expected error to be raised.
      * A valid `end_time` value whose time overlap with a task's timespan
        in the current day schedule, causes the expected error to be raised.
      * The timespan between valid `start_time` and `end_time` is less than
        the minimum defined in `models.Task.MINIMUM_TASK_DURATION_MINS`.
      * An empty `task_time` field causes the expected error to be raised.
      * An valid `task_time` whose value is equal to an existing task's
        task text causes the expected error to be raised.
    """
    def _get_schedule(self):
        user = django_auth_models.User.objects.create(username='Testuser')
        schedule = scheduler_models.UserDaySchedule.objects.create(
            user=user, date=datetime.date(2020, 1, 1)
        )
        return schedule

    def test__valid_data_is_saved(self):
        form_data = {
            'start_time': datetime.time(7, 0),
            'end_time': datetime.time(8, 0),
            'task_desc': 'Test task',
        }
        test_form = scheduler_forms.TaskCreateForm(data=form_data)
        schedule = self._get_schedule()
        test_form.instance.schedule = schedule
        saved_task = test_form.save()
        self.assertEqual(form_data['start_time'], saved_task.start_time)
        self.assertEqual(form_data['end_time'], saved_task.end_time)
        self.assertEqual(form_data['task_desc'], saved_task.task_desc)
        self.assertEqual(schedule, saved_task.schedule)

    def test__valid_form_with_no_schedule(self):
        form_data = {
            'start_time': datetime.time(7, 0),
            'end_time': datetime.time(8, 0),
            'task_desc': 'Test task',
        }
        test_form = scheduler_forms.TaskCreateForm(data=form_data)
        with self.assertRaisesMessage(AttributeError, 'schedule is not set.'):
            test_form.save()

    def test__form_with_empty_start_time(self):
        form_data = {
            'start_time': '',
            'end_time': datetime.time(8, 0),
            'task_desc': 'Test task',
        }
        test_form = scheduler_forms.TaskCreateForm(data=form_data)
        test_form.instance.schedule = self._get_schedule()
        start_time_error_list = test_form.errors['start_time']
        self.assertEqual(1, len(start_time_error_list))
        self.assertEqual(
            test_form.fields['start_time'].error_messages['required'],
            start_time_error_list[0],
        )

    def test__form_with_invalid_start_time(self):
        form_data = {
            'start_time': 'invalid',
            'end_time': datetime.time(8, 0),
            'task_desc': 'Test task',
        }
        test_form = scheduler_forms.TaskCreateForm(data=form_data)
        test_form.instance.schedule = self._get_schedule()
        start_time_error_list = test_form.errors['start_time']
        self.assertEqual(1, len(start_time_error_list))
        self.assertEqual(
            test_form.fields['start_time'].error_messages['invalid'],
            start_time_error_list[0],
        )

    def test__form_with_overlapping_start_time(self):
        form_data = {
            'start_time': datetime.time(7, 0),
            'end_time': datetime.time(8, 0),
            'task_desc': 'Test task 1',
        }
        test_form = scheduler_forms.TaskCreateForm(data=form_data)
        schedule = self._get_schedule()
        overlapped_task = schedule.tasks.create(
            start_time=datetime.time(6, 30),
            end_time=datetime.time(7, 30),
            task_desc='Test task 2',
        )
        test_form.instance.schedule = schedule
        start_time_error_list = test_form.errors['start_time']
        self.assertEqual(1, len(start_time_error_list))
        start_time_field = test_form.fields['start_time']
        err_msg = start_time_field.error_messages['overlap'].format(
            field_label=start_time_field.label,
            overlapped_task_desc=overlapped_task.task_desc,
        )
        self.assertEqual(err_msg, start_time_error_list[0])

    def test__form_with_empty_end_time(self):
        form_data = {
            'start_time': datetime.time(7, 0),
            'end_time': '',
            'task_desc': 'Test task',
        }
        test_form = scheduler_forms.TaskCreateForm(data=form_data)
        test_form.instance.schedule = self._get_schedule()
        end_time_error_list = test_form.errors['end_time']
        self.assertEqual(1, len(end_time_error_list))
        self.assertEqual(
            test_form.fields['end_time'].error_messages['required'],
            end_time_error_list[0],
        )

    def test__form_with_invalid_end_time(self):
        form_data = {
            'start_time': datetime.time(8, 0),
            'end_time': 'invalid',
            'task_desc': 'Test task',
        }
        test_form = scheduler_forms.TaskCreateForm(data=form_data)
        test_form.instance.schedule = self._get_schedule()
        end_time_error_list = test_form.errors['end_time']
        self.assertEqual(1, len(end_time_error_list))
        self.assertEqual(
            test_form.fields['end_time'].error_messages['invalid'],
            end_time_error_list[0],
        )

    def test__form_with_overlapping_end_time(self):
        form_data = {
            'start_time': datetime.time(7, 0),
            'end_time': datetime.time(8, 0),
            'task_desc': 'Test task 1',
        }
        test_form = scheduler_forms.TaskCreateForm(data=form_data)
        schedule = self._get_schedule()
        overlapped_task = schedule.tasks.create(
            start_time=datetime.time(7, 30), end_time=datetime.time(8, 30), task_desc='Test task 2',
        )
        test_form.instance.schedule = schedule
        end_time_error_list = test_form.errors['end_time']
        self.assertEqual(1, len(end_time_error_list))
        end_time_field = test_form.fields['end_time']
        err_msg = end_time_field.error_messages['overlap'].format(
            field_label=end_time_field.label,
            overlapped_task_desc=overlapped_task.task_desc,
        )
        self.assertEqual(err_msg, end_time_error_list[0])

    def test__form_with_underflow_timespan(self):
        form_data = {
            'start_time': datetime.time(7, 0),
            'end_time': datetime.time(7, 4),
            'task_desc': 'Test task',
        }
        test_form = scheduler_forms.TaskCreateForm(data=form_data)
        schedule = self._get_schedule()
        test_form.instance.schedule = schedule
        end_time_error_list = test_form.errors['end_time']
        self.assertEqual(1, len(end_time_error_list))
        end_time_field = test_form.fields['end_time']
        err_msg = end_time_field.error_messages['underflow']
        self.assertEqual(err_msg, end_time_error_list[0])

    def test__form_with_empty_task_desc(self):
        form_data = {
            'start_time': datetime.time(7, 0),
            'end_time': datetime.time(8, 0),
            'task_desc': '',
        }
        test_form = scheduler_forms.TaskCreateForm(data=form_data)
        test_form.instance.schedule = self._get_schedule()
        task_desc_error_list = test_form.errors['task_desc']
        self.assertEqual(1, len(task_desc_error_list))
        self.assertEqual(
            test_form.fields['task_desc'].error_messages['required'],
            task_desc_error_list[0],
        )

    def test_form_update(self):
        """Tests updating an already saved object behaves correctly."""
        schedule = self._get_schedule()
        task = scheduler_models.Task(
            schedule=schedule,
            start_time=datetime.time(7, 0),
            end_time=datetime.time(8, 0),
            task_desc='Test task',
        )
        task.save()

        form_data = {
            'start_time': datetime.time(7, 0),
            'end_time': datetime.time(9, 0),
            'task_desc': 'Test task update',
        }
        test_form = scheduler_forms.TaskCreateForm(data=form_data, instance=task)
        print(test_form.errors)
        self.assertTrue(test_form.is_valid())
        saved_task = test_form.save()
        self.assertEqual(form_data['start_time'], saved_task.start_time)
        self.assertEqual(form_data['end_time'], saved_task.end_time)
        self.assertEqual(form_data['task_desc'], saved_task.task_desc)
        self.assertEqual(schedule, saved_task.schedule)


class BaseViewTest(test.TestCase):
    """Test class for `views.BaseView` class.

    The `views.BaseView` class is meant as base class for other views.
    However, it has it own specification of its methods.
    The following test cases are implemented:
        - The get method returns HttpResponseForbidden(403) response.
        - The post method returns HttpResponseForbidden(403) response.
    """

    def test_get_returns_response_forbidden(self):
        request = test.RequestFactory().get('/')
        view = scheduler_views.BaseView()
        view.setup(request)
        response = view.get(request)
        self.assertIsInstance(response, http.HttpResponseForbidden)

    def test_post_returns_response_forbidden(self):
        request = test.RequestFactory().post('/')
        view = scheduler_views.BaseView()
        view.setup(request)
        response = view.post(request)
        self.assertIsInstance(response, http.HttpResponseForbidden)


class TaskCreationViewTest(test.TestCase):
    """Tests `views.TaskCreationView` class."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.path = shortcuts.reverse('scheduler:api-task-create')
        cls.encoder = dj_json.DjangoJSONEncoder()

    def login_user(self):
        user = django_auth_models.User.objects.create(username='Testuser')
        user.set_password('ateadick6969')
        user.save()
        account_models.UserProfile.objects.create(
            user=user,
            timezone=conf.settings.TIME_ZONE,
        )
        self.client.login(username=user.username, password='ateadick6969')
        user.dayschedules.create(date=user.profile.datetime.date())
        return user

    def test_non_ajax_post_response(self):
        form_data = {
            'start_time': datetime.time(7, 0), 'end_time': datetime.time(8, 0), 'task_desc': 'Test task'
        }
        response = self.client.post(path=self.path, data=form_data)
        self.assertEqual(403, response.status_code)

    def test_post_request_valid_form(self):
        user = self.login_user()
        form_data = {
            'start_time': datetime.time(7, 0),
            'end_time': datetime.time(8, 0),
            'task_desc': 'Test task',
        }
        response = self.client.post(path=self.path, data=form_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        saved_task = user.dayschedules.current_schedule.tasks.get(task_desc='Test task')
        self.assertEqual(saved_task.start_time, form_data['start_time'])
        self.assertEqual(saved_task.end_time, form_data['end_time'])
        self.assertEqual(saved_task.task_desc, form_data['task_desc'])
        response_data = response.json()
        self.assertEqual(saved_task.id, response_data['taskId'])
        self.assertEqual(
            self.encoder.encode(defaultfilters.time(form_data['start_time'], 'H:i')),
            self.encoder.encode(response_data['taskStartTime'])
        )
        self.assertEqual(
            self.encoder.encode(defaultfilters.time(form_data['end_time'], 'H:i')),
            self.encoder.encode(response_data['taskEndTime'])
        )
        self.assertEqual(
            self.encoder.encode(form_data['task_desc']),
            self.encoder.encode(response_data['taskDesc'])
        )

    def test_post_request_empty_form(self):
        self.login_user()
        form_data = {
            'start_time': '', 'end_time': '', 'task_desc': ''
        }
        response = self.client.post(path=self.path, data=form_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(400, response.status_code)
        error_list = response.json()['FORM_ERRORS']
        task_form = scheduler_forms.TaskCreateForm()
        self.assertEqual(
            error_list['start_time'],
            [task_form.fields['start_time'].error_messages['required']],
        )
        self.assertEqual(
            error_list['end_time'],
            [task_form.fields['end_time'].error_messages['required']],
        )
        self.assertEqual(
            error_list['task_desc'],
            [task_form.fields['task_desc'].error_messages['required']],
        )

    def test_post_request_invalid_form(self):
        self.login_user()
        form_data = {
            'start_time': 'invalid',
            'end_time': 'invalid',
            'task_desc': ''
        }
        response = self.client.post(path=self.path, data=form_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(400, response.status_code)
        error_list = response.json()['FORM_ERRORS']
        task_form = scheduler_forms.TaskCreateForm()
        self.assertEqual(
            error_list['start_time'],
            [task_form.fields['start_time'].error_messages['invalid']],
        )
        self.assertEqual(
            error_list['end_time'],
            [task_form.fields['end_time'].error_messages['invalid']],
        )

    def test_post_overlapping_start_time(self):
        user = self.login_user()
        user.dayschedules.current_schedule.tasks.create(
            start_time=datetime.time(7, 0),
            end_time=datetime.time(8, 0),
            task_desc='Test task',
        )
        form_data = {
            'start_time': datetime.time(7, 5),
            'end_time': '',
            'task_desc': ''
        }
        response = self.client.post(path=self.path, data=form_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(400, response.status_code)
        error_list = response.json()['FORM_ERRORS']
        task_form = scheduler_forms.TaskCreateForm()
        start_time_err = task_form.fields['start_time'].error_messages['overlap'].format(
            field_label=task_form.fields['start_time'].label,
            overlapped_task_desc='Test task'
        )
        self.assertEqual(error_list['start_time'], [start_time_err])

    def test_post_overlapping_end_time(self):
        user = self.login_user()
        user.dayschedules.current_schedule.tasks.create(
            start_time=datetime.time(7, 0),
            end_time=datetime.time(8, 0),
            task_desc='Test task',
        )
        form_data = {
            'start_time': datetime.time(6, 0),
            'end_time': datetime.time(7, 5),
            'task_desc': ''
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(400, response.status_code)
        error_list = response.json()['FORM_ERRORS']
        task_form = scheduler_forms.TaskCreateForm()
        end_time_err = task_form.fields['end_time'].error_messages['overlap'].format(
            field_label=task_form.fields['end_time'].label,
            overlapped_task_desc='Test task'
        )
        self.assertEqual(error_list['end_time'], [end_time_err])


class TaskUpdateViewTest(test.TestCase):
    """Tests `views.TaskUpdateView` class."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.path = shortcuts.reverse('scheduler:api-task-update')
        cls.encoder = dj_json.DjangoJSONEncoder()

    def login_user(self):
        user = django_auth_models.User.objects.create(username='Testuser')
        user.set_password('ateadick6969')
        user.save()
        account_models.UserProfile.objects.create(
            user=user,
            timezone=conf.settings.TIME_ZONE,
        )
        self.client.login(username=user.username, password='ateadick6969')
        user.dayschedules.create(date=user.profile.datetime.date())
        return user

    def test_non_ajax_post_response(self):
        form_data = {
            'start_time': datetime.time(7, 0),
            'end_time': datetime.time(8, 0),
            'task_desc': 'Test task',
        }
        response = self.client.post(path=self.path, data=form_data)
        self.assertEqual(403, response.status_code)

    def test_post_request_valid_form(self):
        user = self.login_user()
        task = user.dayschedules.current_schedule.tasks.create(
            start_time=datetime.time(7, 0),
            end_time=datetime.time(8, 0),
            task_desc='Test task',
        )
        form_data = {
            'start_time': datetime.time(8, 0),
            'end_time': datetime.time(9, 0),
            'task_desc': 'Test task new',
            'task_id': task.id,
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(200, response.status_code)
        task.refresh_from_db()
        self.assertEqual(task.start_time, form_data['start_time'])
        self.assertEqual(task.end_time, form_data['end_time'])
        self.assertEqual(task.task_desc, form_data['task_desc'])
        response_data = response.json()
        self.assertEqual(task.id, response_data['taskId'])
        self.assertEqual(
            self.encoder.encode(defaultfilters.time(form_data['start_time'], 'H:i')),
            self.encoder.encode(response_data['taskStartTime'])
        )
        self.assertEqual(
            self.encoder.encode(defaultfilters.time(form_data['end_time'], 'H:i')),
            self.encoder.encode(response_data['taskEndTime'])
        )
        self.assertEqual(
            self.encoder.encode(form_data['task_desc']),
            self.encoder.encode(response_data['taskDesc'])
        )

    def test_post_request_empty_form(self):
        user = self.login_user()
        task = user.dayschedules.current_schedule.tasks.create(
            start_time=datetime.time(7, 0),
            end_time=datetime.time(8, 0),
            task_desc='Test task',
        )
        form_data = {
            'start_time': '',
            'end_time': '',
            'task_desc': '',
            'task_id': task.id,
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(400, response.status_code)
        error_list = response.json()['FORM_ERRORS']
        task_form = scheduler_forms.TaskUpdateForm()
        self.assertEqual(
            error_list['start_time'],
            [task_form.fields['start_time'].error_messages['required']],
        )
        self.assertEqual(
            error_list['end_time'],
            [task_form.fields['end_time'].error_messages['required']],
        )
        self.assertEqual(
            error_list['task_desc'],
            [task_form.fields['task_desc'].error_messages['required']],
        )

    def test_post_request_invalid_form(self):
        user = self.login_user()
        task = user.dayschedules.current_schedule.tasks.create(
            start_time=datetime.time(7, 0),
            end_time=datetime.time(8, 0),
            task_desc='Test task',
        )
        form_data = {
            'start_time': 'invalid',
            'end_time': 'invalid',
            'task_desc': '',
            'task_id': task.id,
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(400, response.status_code)
        error_list = response.json()['FORM_ERRORS']
        task_form = scheduler_forms.TaskCreateForm()
        self.assertEqual(
            error_list['start_time'],
            [task_form.fields['start_time'].error_messages['invalid']],
        )
        self.assertEqual(
            error_list['end_time'],
            [task_form.fields['end_time'].error_messages['invalid']],
        )

    def test_post_overlapping_start_time(self):
        user = self.login_user()
        user.dayschedules.current_schedule.tasks.create(
            start_time=datetime.time(7, 0),
            end_time=datetime.time(8, 0),
            task_desc='Test task',
        )
        task = user.dayschedules.current_schedule.tasks.create(
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            task_desc='Test task',
        )
        form_data = {
            'start_time': datetime.time(7, 30),
            'end_time': '',
            'task_desc': '',
            'task_id': task.id,
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(400, response.status_code)
        error_list = response.json()['FORM_ERRORS']
        task_form = scheduler_forms.TaskCreateForm()
        start_time_err = task_form.fields['start_time'].error_messages['overlap'].format(
            field_label=task_form.fields['start_time'].label,
            overlapped_task_desc='Test task'
        )
        self.assertEqual(error_list['start_time'], [start_time_err])

    def test_post_overlapping_end_time(self):
        user = self.login_user()
        user.dayschedules.current_schedule.tasks.create(
            start_time=datetime.time(7, 0),
            end_time=datetime.time(8, 0),
            task_desc='Test task',
        )
        task = user.dayschedules.current_schedule.tasks.create(
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            task_desc='Test task',
        )
        form_data = {
            'start_time': datetime.time(6, 30),
            'end_time': datetime.time(7, 30),
            'task_desc': '',
            'task_id': task.id,
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(400, response.status_code)
        error_list = response.json()['FORM_ERRORS']
        task_form = scheduler_forms.TaskCreateForm()
        end_time_err = task_form.fields['end_time'].error_messages['overlap'].format(
            field_label=task_form.fields['end_time'].label,
            overlapped_task_desc='Test task'
        )
        self.assertEqual(error_list['end_time'], [end_time_err])


class TaskDeleteViewTest(test.TestCase):
    """Tests `views.TaskDeleteView` class."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.path = shortcuts.reverse('scheduler:api-task-delete')

    def login_user(self):
        user = django_auth_models.User.objects.create(username='Testuser')
        user.set_password('ateadick6969')
        user.save()
        account_models.UserProfile.objects.create(
            user=user,
            timezone=conf.settings.TIME_ZONE,
        )
        self.client.login(username=user.username, password='ateadick6969')
        user.dayschedules.create(date=user.profile.datetime.date())
        return user

    def test_non_ajax_post_response(self):
        form_data = {
            'task_id': 0,
        }
        response = self.client.post(path=self.path, data=form_data)
        self.assertEqual(403, response.status_code)

    def test_post_request_valid_form(self):
        user = self.login_user()
        task = user.dayschedules.current_schedule.tasks.create(
            start_time=datetime.time(7, 0),
            end_time=datetime.time(8, 0),
            task_desc='Test task',
        )
        form_data = {
            'task_id': task.id,
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(200, response.status_code)
        with self.assertRaises(exceptions.ObjectDoesNotExist):
            scheduler_models.Task.objects.get(id=task.id)


class TaskStatusUpdateViewTest(test.TestCase):
    """Tests `views.TaskStatusUpdateView` class."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.path = shortcuts.reverse('scheduler:api-task-status-update')

    def login_user(self):
        user = django_auth_models.User.objects.create(username='Testuser')
        user.set_password('ateadick6969')
        user.save()
        account_models.UserProfile.objects.create(
            user=user,
            timezone=conf.settings.TIME_ZONE,
        )
        self.client.login(username=user.username, password='ateadick6969')
        user.dayschedules.create(date=user.profile.datetime.date())
        return user

    def test_non_ajax_post_response(self):
        form_data = {
            'task_id': 0,
        }
        response = self.client.post(path=self.path, data=form_data)
        self.assertEqual(403, response.status_code)

    def test_post_request_valid_form(self):
        user = self.login_user()
        task = user.dayschedules.current_schedule.tasks.create(
            start_time=datetime.time(7, 0),
            end_time=datetime.time(8, 0),
            task_desc='Test task',
        )
        self.assertFalse(task.completed)
        form_data = {
            'task_id': task.id,
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(200, response.status_code)
        task.refresh_from_db()
        self.assertTrue(task.completed)


class TasksViewTest(test.TestCase):
    """Tests `views.TasksView` class."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.path = shortcuts.reverse('scheduler:api-tasks')
        cls.encoder = dj_json.DjangoJSONEncoder()

    def login_user(self):
        user = django_auth_models.User.objects.create(username='Testuser')
        user.set_password('ateadick6969')
        user.save()
        account_models.UserProfile.objects.create(
            user=user,
            timezone=conf.settings.TIME_ZONE,
        )
        self.client.login(username=user.username, password='ateadick6969')
        user.dayschedules.create(date=user.profile.datetime.date())
        return user

    def test_non_ajax_post_response(self):
        form_data = {
            'task_id': 0,
        }
        response = self.client.post(path=self.path, data=form_data)
        self.assertEqual(403, response.status_code)

    def test_tasks_retrieval(self):
        user = self.login_user()
        user.dayschedules.current_schedule.tasks.create(
            start_time=datetime.time(7, 0),
            end_time=datetime.time(8, 0),
            task_desc='Test task',
        )
        user.dayschedules.current_schedule.tasks.create(
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            task_desc='Test task 1',
        )
        user.dayschedules.current_schedule.tasks.create(
            start_time=datetime.time(11, 0),
            end_time=datetime.time(12, 0),
            task_desc='Test task 2',
        )
        user.dayschedules.current_schedule.tasks.create(
            start_time=datetime.time(13, 0),
            end_time=datetime.time(14, 0),
            task_desc='Test task 3',
        )
        response = self.client.post(
            path=self.path,
            data={},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(200, response.status_code)
        tasks_qs = user.dayschedules.current_schedule.tasks.all()
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
        data = response.json()
        self.assertEqual(data['TASKS'], serialized_tasks)
