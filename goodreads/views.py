import io
import os
import csv
import time
import pandas as pd
from .models import ExportData
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def run_script_function(request):
    user = request.user

    print('running python script')
    os.system('python goodreads/scripts/append_to_export.py goodreads/Graphs/{}/sample_export_{}.csv'.format(user, user))
    time.sleep(3)

    print('running R scripts')
    os.system('Rscript goodreads/scripts/runner.R goodreads/Graphs/{}/sample_export_{}_appended.csv {}'.format(user, user, user))


def py_script_function(request):
    user = request.user
    os.system('python goodreads/scripts/append_to_export.py goodreads/Graphs/{}/sample_export_{}.csv'.format(user, user))


def index(request):
    # print(user)
    if request.user.is_authenticated:
        base_auth_template = 'goodreads/basefile.html'
    else:
        base_auth_template = 'goodreads/base2.html'
    return render(request, 'goodreads/home.html', {'basefile': base_auth_template})


@login_required(redirect_field_name='next', login_url='user-login')
def finish_plot_view(request):
    username = request.user
    finish_plot_url = '{}/finish_plot_{}.jpeg'.format(username, username)
    return render(request, 'goodreads/finish_plot.html', {'finish_plot_url': finish_plot_url})


@login_required(redirect_field_name='next', login_url='user-login')
def nationality_map_view(request):
    username = request.user
    nationality_map_url = '{}/nationality_map_{}.jpeg'.format(username, username)
    return render(request, 'goodreads/nationality_map.html', {'nationality_map_url': nationality_map_url})


@login_required(redirect_field_name='next', login_url='user-login')
def popularity_spectrum_view(request):
    username = request.user
    popularity_spectrum_url = '{}/popularity_spectrum_{}.jpeg'.format(username, username)
    return render(request, 'goodreads/popularity_spectrum.html', {'popularity_spectrum_url': popularity_spectrum_url})


@login_required(redirect_field_name='next', login_url='user-login')
def summary_plot_view(request):
    username = request.user
    summary_plot_url = '{}/Summary_plot.jpeg'.format(username, username)
    return render(request, 'goodreads/summary_plot.html', {'summary_plot_url': summary_plot_url})
    
    
@login_required(redirect_field_name='next', login_url='user-login')
def yearly_pages_read_view(request):
    username = request.user
    yearly_pages_read_url = '{}/Yearly_pages_read_{}.jpeg'.format(username, username)
    return render(request, 'goodreads/yearly_pages_read.html', {'yearly_pages_read_url': yearly_pages_read_url})


def runscript(request):
    if request.method == 'POST' and 'runscript' in request.POST:
        run_script_function(request)
    
    if request.method == 'POST' and 'pythonscript' in request.POST:
        print('running python script')
        py_script_function(request)
    return render(request, 'goodreads/run.html')


@login_required(redirect_field_name='next', login_url='user-login')
def upload_view(request):
    template = "goodreads/csv_upload.html"

    # check if user has uploaded a csv file before running the analysis
    file_path = 'goodreads/Graphs/{}/sample_export_{}.csv'.format(request.user, request.user)
    if os.path.isfile(file_path):
        file_exists = True
    else:
        file_exists = False

    if request.method == 'GET':
        return render(request, template, {'file_exists': file_exists})
        
    # run analysis when user clicks on Analyze button
    if request.method == 'POST' and 'runscript' in request.POST:
        run_script_function(request)
        return render(request, template, {'file_exists': file_exists})
    
    # upload csv file
    csv_file = request.FILES['file']

    # check if file uploaded is csv
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'Wrong file format chosen. Please upload .csv file instead.')
        return render(request, template)

    # save csv file in database
    df = pd.read_csv(csv_file)
    df.columns = df.columns.str.replace(' |\.', '_') # standard export comes in with spaces. R would turn these into dots
    df['Number_of_Pages'].fillna(0, inplace=True)
    for row in df.itertuples():
        _, book = ExportData.objects.update_or_create(
                book_id=row.Book_Id, 
                title=row.Title, 
                author=row.Author,
                number_of_pages=row.Number_of_Pages,
                my_rating=row.My_Rating,
                original_publication_year=row.Original_Publication_Year
            )
    
    # save csv file to user's folder
    username = request.user
    try:
        df.to_csv('goodreads/Graphs/{}/sample_export_{}.csv'.format(username, username))
    except OSError:
        os.mkdir('goodreads/Graphs/{}'.format(username))
        df.to_csv('goodreads/Graphs/{}/sample_export_{}.csv'.format(username, username))

    return render(request, template, {'file_exists': file_exists})
    