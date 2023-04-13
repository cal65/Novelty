from django.contrib import admin
from django.urls import path, include
from users import views as user_views


urlpatterns = [
    path('register/', user_views.register, name='register'),
    path('login/', user_views.login_user, name='user-login'),
    # path('reset/', user_views.password_reset, name='password_reset'),
    # path('reset-done/', user_views.password_reset_done, name='password_reset_done'),
    # path('reset-confirm/', user_views.password_reset_confirm, name='password_reset_confirm'),
]