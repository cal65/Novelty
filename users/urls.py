from django.contrib import admin
from django.urls import path, include
from users import views as user_views


urlpatterns = [
    path('register/', user_views.register, name='register'),
    path('login/', user_views.login_user, name='user-login'),
]