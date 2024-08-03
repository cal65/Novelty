from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from users import views as user_views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('register/', user_views.register, name='register'),
    path('login/', user_views.login_user, name='user-login'),
    path('accounts/', include('allauth.urls')),
    path('logout', LogoutView.as_view(http_method_names=['post']), name='logout'),
    path('', TemplateView.as_view(template_name="index.html")),
    # path('reset/', user_views.password_reset, name='password_reset'),
    # path('reset-done/', user_views.password_reset_done, name='password_reset_done'),
    # path('reset-confirm/', user_views.password_reset_confirm, name='password_reset_confirm'),
]