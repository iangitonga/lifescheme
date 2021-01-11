import base64
import pytz
from django import conf, http, test, shortcuts
from django.contrib import messages
from django.core import mail, signing
from django.contrib.auth import models as auth_models
from django.utils import timezone

from accounts import signer, forms as acc_forms, models as acc_models, views as acc_views


VALID_USERNAME, INVALID_USERNAME = 'Testuser', '{}'
VALID_EMAIL, INVALID_EMAIL = 'testuser@gmail.com', 'testuser'
VALID_PASSWORD = 'Str0ngPa55w0rd'
SHORT_PASSWORD = 'short'

# This dictionary should be read-only since writing to it would not be safe if
# the tests were run in parallel(thread safety).
ERROR_MESSAGES = {
    'required': 'This field is required.',
    'invalid_username': 'Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ '
                        'characters.',
    'existing_username': 'A user with that username already exists.',
    'invalid_email': 'Enter a valid email address.',
    'existing_email': 'A user with that email already exists.',
    'short_password': 'This password is too short. It must contain at least 8 characters.',
    'invalid_timezone': 'Select a valid choice. invalid is not one of the available choices.',
}


class UserProfileModelTest(test.TestCase):
    """Tests `models.UserProfile` model.

    Test cases:
      - `TIMEZONE_CHOICES` contains expected data.
      - `datetime` method returns expected data.
    """
    def test_timezone_choices(self):
        # We cannot test `UserProfile.TIMEZONE_CHOICES` directly because it
        # gets exhausted in the `timezone` field when models module is
        # imported.
        expected_choices = sorted(pytz.common_timezones_set)
        # We convert to tuples since we cannot reliably compare pytz internal
        # types.
        expected_choices = tuple(expected_choices)
        actual_choices = tuple(acc_models.UserProfile.TIMEZONES)
        self.assertEqual(actual_choices, expected_choices)

    def test_datetime(self):
        tzname = 'Africa/Nairobi'
        # A user is not needed here.
        profile = acc_models.UserProfile(user=None, timezone=tzname)
        actual_datetime = profile.datetime
        expected_datetime = timezone.now().astimezone(pytz.timezone(tzname))
        # In this case, testing the date and time is irrelevant because it is
        # impossible for two datetimes to have the same timezone and yet have
        # different dates or time.
        self.assertEqual(actual_datetime.tzname(), expected_datetime.tzname())


class UserCreationFormTest(test.TestCase):
    """Tests `forms.UserCreationForm`.

    Test cases:
        - valid data is saved to db.
        - empty data causes expected form errors.
        - invalid data causes expected form errors.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form_class = acc_forms.UserCreationForm

    def test_valid_data(self):
        form_data = {'username': VALID_USERNAME, 'email': VALID_EMAIL, 'password': VALID_PASSWORD}
        form = self.form_class(form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, form_data)
        form.save()
        user = auth_models.User.objects.get(username=form_data['username'])
        self.assertEqual(user.email, form_data['email'])
        self.assertTrue(user.check_password(form_data['password']))

    def test_empty_data(self):
        form_data = {'username': '', 'email': '', 'password': ''}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        form_errors = form.errors
        self.assertEqual(form_errors['username'], [ERROR_MESSAGES['required']])
        self.assertEqual(form_errors['email'], [ERROR_MESSAGES['required']])
        self.assertEqual(form_errors['password'], [ERROR_MESSAGES['required']])

    def test_invalid_data(self):
        form_data = {'username': INVALID_USERNAME, 'email': INVALID_EMAIL, 'password': SHORT_PASSWORD}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        form_errors = form.errors
        self.assertEqual(form_errors['username'], [ERROR_MESSAGES['invalid_username']])
        self.assertEqual(form_errors['email'], [ERROR_MESSAGES['invalid_email']])
        self.assertEqual(form_errors['password'], [ERROR_MESSAGES['short_password']])

    def test_existing_username(self):
        form_data = {'username': VALID_USERNAME, 'email': VALID_EMAIL, 'password': VALID_PASSWORD}
        auth_models.User.objects.create(username=form_data['username'])
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        form_errors = form.errors
        self.assertEqual(form_errors['username'], [ERROR_MESSAGES['existing_username']])

    def test_existing_email(self):
        form_data = {'username': VALID_USERNAME, 'email': VALID_EMAIL, 'password': VALID_PASSWORD}
        auth_models.User.objects.create(username='Testuser1', email=VALID_EMAIL)
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        form_errors = form.errors
        self.assertEqual(form_errors['email'], [ERROR_MESSAGES['existing_email']])


class UserProfileFormTest(test.TestCase):
    """Tests `forms.UserProfileForm`.

    Test cases:
        - valid data causes no errors.
        - empty data causes expected form errors.
        - invalid data causes expected form errors.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form_class = acc_forms.UserProfileForm

    def test_valid_data(self):
        form_data = {'timezone': 'UTC'}
        form = self.form_class(form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, form_data)

    def test_empty_data(self):
        form_data = {'timezone': ''}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        form_errors = form.errors
        self.assertEqual(form_errors['timezone'], [self.form_class.error_messages['required']])

    def test_invalid_data(self):
        form_data = {'timezone': 'invalid'}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        form_errors = form.errors
        self.assertEqual(form_errors['timezone'], [ERROR_MESSAGES['invalid_timezone']])


class BaseViewTest(test.TestCase):
    """Tests `views.BaseView`.

    Test cases:
        - get method raises Http404 error.
        - post method raises Http404 error.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.view_class = acc_views.BaseView

    def test_get_raises_http404(self):
        # Since this is a unit test and the methods we are testing do nothing
        # with the request we pass to them we can use `None` as the request.
        request = None
        view = self.view_class()
        with self.assertRaises(http.Http404):
            view.get(request)

    def test_post_raises_http404(self):
        request = None
        view = self.view_class()
        with self.assertRaises(http.Http404):
            view.post(request)


class SignerTest(test.TestCase):
    """Tests `signer.Signer`.

    Test cases:
        - sign method raises an exception when its value is not a
          string.
        - sign method signs and timestamps value and its urlsafe.
        - unsign method raises an exception when its value is not a
          string.
        - unsign method raises an exception when max_age is not an
          int or is a negative number.
        - unsign method unsigns a timestamped value.
    """

    def test_sign_non_string(self):
        dummy = object()
        err_msg = f"'signed_value' must be a string not {type(dummy)}"
        with self.assertRaisesMessage(TypeError, err_msg):
            signer.SIGNER.sign(dummy)

    def test_sign_is_correct(self):
        # Due to timing between two signings, we cannot reliably test two
        # timestamped signed values.
        value = 'TestSigner'
        signed = signing.Signer().sign(value)
        expected_signed = base64.urlsafe_b64encode(bytes(signed, encoding='utf')).decode()
        actual_signed = signer.SIGNER.sign(value)
        self.assertIsInstance(actual_signed, str)
        self.assertNotEqual(actual_signed, expected_signed)

    def test_unsign_non_string(self):
        dummy = object()
        err_msg = f"'signed_value' must be a string not {type(dummy)}"
        with self.assertRaisesMessage(TypeError, err_msg):
            signer.SIGNER.unsign(dummy, 0)

    def test_unsign_max_age_non_int(self):
        err_msg = f"'max_age' must be a string not {type('max')}"
        with self.assertRaisesMessage(TypeError, err_msg):
            signer.SIGNER.unsign('dummy', 'max')

    def test_unsign_max_age_negative(self):
        err_msg = f"The given max_age, {-5}, is a negative value"
        with self.assertRaisesMessage(ValueError, err_msg):
            signer.SIGNER.unsign('dummy', -5)

    def test_unsign_expired(self):
        value = 'TestSigner'
        signed = signing.TimestampSigner().sign(value)
        signed = base64.urlsafe_b64encode(bytes(signed, encoding='utf')).decode()
        with self.assertRaises(signing.SignatureExpired):
            signer.SIGNER.unsign(signed, 0)

    def test_unsign_is_correct(self):
        value = 'TestSigner'
        signed = signing.TimestampSigner().sign(value)
        signed = base64.urlsafe_b64encode(bytes(signed, encoding='utf'))
        signed = signed.decode()
        actual = signer.SIGNER.unsign(signed, 5)
        self.assertIsInstance(actual, str)
        self.assertEqual(actual, value)

    def test_unsign_max_age_none(self):
        value = 'TestSigner'
        signed = signing.TimestampSigner().sign(value)
        signed = base64.urlsafe_b64encode(bytes(signed, encoding='utf'))
        signed = signed.decode()
        actual = signer.SIGNER.unsign(signed)
        self.assertIsInstance(actual, str)
        self.assertEqual(actual, value)


class UserRegistrationViewTest(test.TestCase):
    """Tests `views.UserSignupView`.

    Test cases:
        - GET request is Ok and has expected context data and template.
        - Non-ajax POST request has correct response.
        - POST request with valid data saves user.
        - POST request with empty forms has correct response.
        - POST request with invalid data in forms has correct response.
        - POST request confirmation email sending failed has correct response.???
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.path_name = '/signup/'

    def setUp(self):
        super().setUp()
        # Empty the dummy mail outbox.
        mail.outbox = []

    def test_get(self):
        response = self.client.get(self.path_name)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'accounts/user_signup.html')
        self.assertIn('USER_CREATION_FORM', response.context)
        self.assertIn('USER_PROFILE_FORM', response.context)
        self.assertIsInstance(
            response.context['USER_CREATION_FORM'],
            acc_forms.UserCreationForm,
        )
        self.assertIsInstance(
            response.context['USER_PROFILE_FORM'],
            acc_forms.UserProfileForm,
        )

    def test_post_valid_data(self):
        form_data = {
            'username': VALID_USERNAME,
            'email': VALID_EMAIL,
            'password': VALID_PASSWORD,
            'timezone': 'UTC',
        }
        with self.settings(
                EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
        ):
            response = self.client.post(self.path_name, form_data)
        self.assertEqual(response.status_code, 302)
        user = auth_models.User.objects.get(username=form_data['username'])
        self.assertEqual(user.email, form_data['email'])
        self.assertTrue(user.check_password(form_data['password']))
        self.assertEqual(user.profile.timezone, form_data['timezone'])
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, conf.settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(mail.outbox[0].to, [form_data['email']])
        self.assertEqual(mail.outbox[0].subject, 'Lifescheme password confirmation')

    def test_post_empty_forms(self):
        form_data = {
            'username': '',
            'email': '',
            'password': '',
            'timezone': '',
        }
        response = self.client.post(self.path_name, form_data)
        self.assertEqual(response.status_code, 200)
        creation_form_errors = response.context['USER_CREATION_FORM'].errors
        profile_form_errors = response.context['USER_PROFILE_FORM'].errors
        self.assertEqual(creation_form_errors['username'], [ERROR_MESSAGES['required']])
        self.assertEqual(creation_form_errors['email'], [ERROR_MESSAGES['required']])
        self.assertEqual(creation_form_errors['password'], [ERROR_MESSAGES['required']])
        self.assertEqual(profile_form_errors['timezone'], [ERROR_MESSAGES['required']])

    def test_post_invalid_data_in_forms(self):
        form_data = {
            'username': INVALID_USERNAME,
            'email': INVALID_EMAIL,
            'password': SHORT_PASSWORD,
            'timezone': 'invalid',
        }
        response = self.client.post(self.path_name, form_data)
        self.assertEqual(response.status_code, 200)
        creation_form_errors = response.context['USER_CREATION_FORM'].errors
        profile_form_errors = response.context['USER_PROFILE_FORM'].errors
        self.assertEqual(creation_form_errors['username'], [ERROR_MESSAGES['invalid_username']])
        self.assertEqual(creation_form_errors['email'], [ERROR_MESSAGES['invalid_email']])
        self.assertEqual(creation_form_errors['password'], [ERROR_MESSAGES['short_password']])
        self.assertEqual(profile_form_errors['timezone'], [ERROR_MESSAGES['invalid_timezone']])

    def test_post_existing_email_and_username(self):
        auth_models.User.objects.create(username=VALID_USERNAME, email=VALID_EMAIL)
        form_data = {
            'username': VALID_USERNAME,
            'email': VALID_EMAIL,
        }
        response = self.client.post(self.path_name, form_data)
        self.assertEqual(response.status_code, 200)
        creation_form_errors = response.context['USER_CREATION_FORM'].errors
        self.assertEqual(creation_form_errors['username'], [ERROR_MESSAGES['existing_username']])
        self.assertEqual(creation_form_errors['email'], [ERROR_MESSAGES['existing_email']])


class UserActivationViewTest(test.TestCase):
    """Tests `views.UserActivationView`.

    Test Cases:
        - GET request with valid token.
        - GET request with authenticated user.
        - GET request with an invalid token.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.path_name = shortcuts.reverse('accounts:user-account-activator')

    def test_valid_token(self):
        user = auth_models.User.objects.create(username=VALID_USERNAME, is_active=False)
        self.assertFalse(user.is_active)
        token = signer.SIGNER.sign(user.username)
        response = self.client.get(f'{self.path_name}?t={token}')
        message_storage = messages.get_messages(response.wsgi_request)
        messages_tup = tuple(iter(message_storage))
        self.assertEqual(len(messages_tup), 1)
        m = 'Your account has been confirmed successfully. You can now sign in using your account details.'
        self.assertEqual(messages_tup[0].message, m)
        # Check the redirect.
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user(self):
        user = auth_models.User.objects.create(username=VALID_USERNAME, password=VALID_PASSWORD)
        self.client.force_login(user)
        response = self.client.get(self.path_name)
        self.assertEqual(response.status_code, 302)

    def test_invalid_token(self):
        response = self.client.get(self.path_name)
        self.assertEqual(response.status_code, 404)
