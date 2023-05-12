import os
from django.contrib import messages
from django.views.generic import View
from django.utils.http import is_safe_url
from django.shortcuts import render, redirect
from .forms import UserRegisterForm, LoginForm
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
import logging

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# function to create folder for user on registration 
def create_folder(username):
    path = username
    os.mkdir(path)


@csrf_exempt
def register(request):
    try:
        headers = request.headers["User-Agent"]
    except Exception:
        headers = ""
    logger.info(f"registration request with headers {headers}")

    if request.method == 'POST':
        next = request.GET['next']
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()

            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            path = 'goodreads/static/Graphs/{}'.format(username)
            try:
                create_folder(path)
            except:
                logger.info(f"Folder already exists for {username}")

            login(request, user)
            if next:
                return redirect(next)
            else:
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

# def password_reset(request):
#     return render(request, "registration/password_reset_form.html")
#
#
# def password_reset_confirm(request):
#     return render(request, "registration/password_reset_confirm.html")
#
#
# def password_reset_done(request):
#     return render(request, "registration/password_reset_done.html")
