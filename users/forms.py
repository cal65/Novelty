from django import forms
from django.contrib.auth.models import User
from django.forms import TextInput, EmailInput, PasswordInput
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


# class UserRegisterForm(UserCreationForm):
#     email = forms.EmailField()

#     class Meta:
#         model = User
#         fields = ['username', 'email', 'password1', 'password2']
#         widgets = {
#             'username': TextInput(attrs={
#                 'class': "form-control",
#                 'style': 'max-width: 400px;',
#                 }),
#             'email': EmailInput(attrs={
#                 'class': "form-control",
#                 'style': 'max-width: 400px;',
#                 }),
#             'password1': PasswordInput(attrs={
#                 'class': "form-control",
#                 'style': 'max-width: 400px;',
#                 }),
#             'password2': PasswordInput(attrs={
#                 'class': "form-control",
#                 'style': 'max-width: 400px;',
#                 }),
#         }
class UserRegisterForm(UserCreationForm):
    username = forms.CharField(widget=(forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 400px;',})))
    email=forms.EmailField(widget=(forms.EmailInput(attrs={'class': 'form-control', 'style': 'width: 400px;'})), max_length=64, help_text='Enter a valid email address')
    password1=forms.CharField(widget=(forms.PasswordInput(attrs={'class': 'form-control', 'style': 'width: 400px;'})))
    password2=forms.CharField(widget=(forms.PasswordInput(attrs={'class': 'form-control', 'style': 'width: 400px;'})))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2',)


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", required=True, max_length=30,
                           widget=forms.TextInput(attrs={
                               'class': 'form-control',
                               'name': 'username'}))
    password = forms.CharField(label="Password", required=True, max_length=30,
                           widget=forms.PasswordInput(attrs={
                               'class': 'form-control',
                               'name': 'password'}))
