import os
from django.contrib import messages
from django.views.generic import View
from django.utils.http import is_safe_url
from django.shortcuts import render, redirect
from .forms import UserRegisterForm, LoginForm
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import authenticate, login, logout


# function to create folder for user on registration 
def create_folder(username):
    path = username
    os.mkdir(path)


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()

            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            path = 'goodreads/Graphs/{}'.format(username)
            create_folder(path)

            return redirect('user-login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


def login_user(request):
    logout(request)
    username = password = ''
    form = LoginForm

    next = ""
    if request.GET:  
        next = request.GET['next']
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        # user = authenticate(request=request, username=username, password=password)
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                if next == "":
                    return redirect('index-view')
                elif not is_safe_url(
                        url=next,
                        allowed_hosts={request.get_host()},
                        require_https=request.is_secure()):
                    return redirect('user-login')
                else:
                    return redirect(next)
        else:
            messages.warning(request, "The username or password is incorrect.")
            return redirect('user-login')

    context = {'form': form, 'next': next}
    return render(request, 'users/login.html', context)

