from django import conf, http, shortcuts, views as dj_views
from django.contrib import messages
from django.contrib.auth import models as auth_models, views as auth_views
from django.core import mail, signing

from . import forms as acc_forms, signer


class UserSigninView(auth_views.LoginView):
    template_name = 'accounts/user_signin.html'


class UserSignoutView(auth_views.LogoutView):
    pass


class BaseView(dj_views.View):
    """The base class for other views."""
    def get(self, request, *args, **kwargs):
        """Processes a HTTP GET request and returns the appropriate response.

        Args:
            request: A `HttpRequest` object representing the request.
            *args: Arbitrary arguments.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A `HttpResponse` or `JsonResponse` object.
        Raises:
            Http404: If not overridden in a subclass.
        """
        raise http.Http404

    def post(self, request, *args, **kwargs):
        """Processes a HTTP POST request and returns the appropriate response.

        Args:
            request: A `HttpRequest` object representing the request.
            *args: Arbitrary arguments.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A `HttpResponse` or `JsonResponse`  object.
        Raises:
            Http404: If not overridden in a subclass.
        """
        raise http.Http404


class UserSignupView(BaseView):
    """Saves and deactivates a user."""
    template_name = 'accounts/user_signup.html'

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data()
        return shortcuts.render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        filled_creation_form = acc_forms.UserCreationForm(request.POST)
        filled_profile_form = acc_forms.UserProfileForm(request.POST)
        if filled_creation_form.is_valid() and filled_profile_form.is_valid():
            user = filled_creation_form.save()
            if self.send_confirmation_email(user):
                user.is_active = False
                user.save(update_fields=['is_active'])
                filled_profile_form.instance.user = user
                filled_profile_form.save()
                link = shortcuts.reverse('accounts:user-account-creation-success')
                token = signer.SIGNER.sign(user.email)
                redirect_link = f'{link}?t={token}'
                return shortcuts.redirect(redirect_link)
            else:
                user.delete()
                context_data = {
                    'USER_CREATION_FORM': filled_creation_form,
                    'USER_PROFILE_FORM': filled_profile_form,
                    'ERROR': True,
                }
                return shortcuts.render(
                    request,
                    self.template_name,
                    context_data,
                )
        else:
            # Here, we extract error messages directly instead of using
            # <form>.errors which returns error messages wrapped in html.
            form_errors = {
                **self.extract_form_errors(filled_creation_form),
                **self.extract_form_errors(filled_profile_form),
            }
            context_data = {
                'USER_CREATION_FORM': filled_creation_form,
                'USER_PROFILE_FORM': filled_profile_form,
                'FORM_ERRORS': form_errors,
            }
            return shortcuts.render(
                request,
                self.template_name,
                context_data,
            )

    def extract_form_errors(self, form):
        """Returns a `dict` where each key is a field name and its value is
        a list of the error messages gotten from that field.

        This method is useful when you want to bypass Django default mechanism
         of wrapping form error messages in HTML.
        Args
            form - An instance or a subclass of `django.forms.Form`.
        """
        form_errors = {}
        for field, error_list in form.errors.items():
            field_errors = []
            for error in error_list.data:
                if error.params is not None:
                    field_errors.append(error.message % error.params)
                else:
                    field_errors.append(error.message)
            form_errors[field] = field_errors
        return form_errors

    def get_context_data(self):
        data = {
            'USER_CREATION_FORM': acc_forms.UserCreationForm(),
            'USER_PROFILE_FORM': acc_forms.UserProfileForm(),
        }
        return data

    def send_confirmation_email(self, user):
        # This try/except allows this view to return a response even if the
        # email could not be sent. However, an exception will never occur
        # unless a connection issue arises with sending the email.
        try:
            protocol = 'https' if self.request.is_secure() else 'http'
            domain = self.request.get_host()
            token = signer.SIGNER.sign(user.username)
            path = shortcuts.reverse('accounts:user-account-activator')
            link = f'{protocol}://{domain}{path}?t={token}'
            mail_subject = 'Lifescheme password confirmation'
            mail_message = f'Hello {user.username}, follow this link to confirm your email. {link}'
            mail.send_mail(
                subject=mail_subject,
                message=mail_message,
                from_email=conf.settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return True
        except Exception:
            return False


class UserAccountCreationSuccessView(BaseView):
    """Shows the user a success message after creating an account."""
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return shortcuts.redirect('/')
        token = request.GET.get('t')
        try:
            email = signer.SIGNER.unsign(token)
            success_message = (
                f'A confirmation email has been sent to {email}.'
                ' Please click the link in that email to confirm your account.'
            )
            messages.success(request, success_message)
            return shortcuts.render(request, 'accounts/user_account_creation_success.html')
        except (TypeError, ValueError, signing.SignatureExpired, signer.SigningError):
            raise http.Http404


class UserAccountActivationView(BaseView):
    """Activates a deactivated user account."""
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return shortcuts.redirect(shortcuts.reverse('accounts:user-signin'))
        token = request.GET.get('t')
        try:
            username = signer.SIGNER.unsign(token)
            user = auth_models.User.objects.get(username=username)
            user.is_active = True
            user.save(update_fields=['is_active'])
            success_message = (
                'Your account has been confirmed successfully. You can now sign in'
                ' using your account details.'
            )
            messages.success(request, success_message)
            return shortcuts.redirect(shortcuts.reverse('accounts:user-signin'))
        except (TypeError, ValueError, signing.SignatureExpired, signer.SigningError):
            raise http.Http404
