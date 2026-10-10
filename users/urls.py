from django.urls import path
from django.contrib.auth import views as d_views

from . import views
from users.forms import MyLoginForm


urlpatterns = [
    # path('login/', views.login_view, name="login_view"),
    path('login/', d_views.LoginView.as_view(
        template_name='users/login.html',
        form_class=MyLoginForm
    ), name="login_view"),
    path('logout/', views.logout_view, name="logout_view"),
    path('new/', views.signup_view, name="create_user_view"),
    path('api/createpin/', views.create_pin_view, name="create_pin_view"),
    # path('api/createuser/', views.signup_handler, name="create_user_view"),
]