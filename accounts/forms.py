from django import forms as dj_forms
from django.core import exceptions
from django.contrib.auth import (forms as auth_forms,
                                 models as auth_models,
                                 password_validation)

from . import models as acc_models


class UserCreationForm(dj_forms.ModelForm):
    """A form for creating a User object with no extra data.

    This form creates a user from username, email and password.
    """
    error_messages = {
        'required': 'This field is required.',
        'email_unique': 'A user with that email already exists.',
    }
    password = dj_forms.CharField(
        label='Password',
        strip=False,
        widget=dj_forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    class Meta:
        model = auth_models.User
        fields = ('username', 'email', 'password')
        field_classes = {'username': auth_forms.UsernameField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['required'] = True

    def clean_email(self):
        """Validates that the provided email is unique.

        Raises:
             ValidationError: if there exist a user with the provided
                email.
        """
        email = self.cleaned_data.get('email')
        if email:
            email_qs = auth_models.User.objects.filter(email=email)
            if email_qs.exists():
                raise exceptions.ValidationError(self.error_messages['email_unique'])
        else:
            raise exceptions.ValidationError(self.error_messages['required'])
        return email

    def clean_password(self):
        """Validates that the provided password is valid.

        The algorithm used to check the password validity exists in
        `django.contrib.auth.password_validation.validate_password` function.
        Raises:
             ValidationError: if the given password is not valid.
        """
        password = self.cleaned_data.get('password')
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except exceptions.ValidationError as error:
                self.add_error('password', error)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserProfileForm(dj_forms.ModelForm):
    """A form for creating a User profile that stores user's extra data."""
    error_messages = {
        'required': 'This field is required.',
    }

    class Meta:
        model = acc_models.UserProfile
        fields = ['timezone']

    def clean_timezone(self):
        """Validates that the given timezone not an empty string or none.

        Raises:
             ValidationError: if the given timezone is empty or none.

        Notes:
            We do not have to check if the given timezone is valid because a
            `CharField` with choices does that check automatically and fields
            are cleaned before this method is called.
        """
        timezone = self.cleaned_data.get('timezone')
        if not timezone:
            raise exceptions.ValidationError(self.error_messages['required'])
        return timezone
