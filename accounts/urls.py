from django import http, urls, shortcuts

from . import views as acc_views

app_name = 'accounts'


def home(request):
    return shortcuts.render(request, 'accounts/homepage.html')


urlpatterns = [
    urls.path('', home),
    urls.path('signin/', acc_views.UserSigninView.as_view(), name='user-signin'),
    urls.path('signout/', acc_views.UserSignoutView.as_view(), name='user-signout'),
    urls.path('signup/', acc_views.UserSignupView.as_view(), name='user-signup'),
    urls.path(
        'account-creation-success/',
        acc_views.UserAccountCreationSuccessView.as_view(),
        name='user-account-creation-success'
    ),
    urls.path(
        'activate-account/',
        acc_views.UserAccountActivationView.as_view(),
        name='user-account-activator',
    ),
]

