import io
import os
import csv
import time
import pandas as pd
from .models import ExportData
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .scripts.append_to_export import convert_to_ExportData, database_append


def run_script_function(request):
    user = request.user

    print("running python script")
    os.system(
        f"python goodreads/scripts/append_to_export.py goodreads/Graphs/{user}/sample_export_{user}.csv --username {user} 3"
    )

    print("running R scripts")
    os.system("Rscript goodreads/scripts/runner.R {}".format(user))


def py_script_function(request):
    user = request.user
    os.system(
        "python goodreads/scripts/append_to_export.py goodreads/Graphs/{}/sample_export_{}.csv".format(
            user, user
        )
    )


def index(request):
    # print(user)
    if request.user.is_authenticated:
        base_auth_template = "goodreads/basefile.html"
    else:
        base_auth_template = "goodreads/base2.html"
    return render(request, "goodreads/home.html", {"basefile": base_auth_template})

def books_home(request):
    return render(request, "goodreads/books_home.html")

def about_this(request):
    return render(request, "goodreads/about_this.html")


@login_required(redirect_field_name="next", login_url="user-login")
def finish_plot_view(request):
    username = request.user
    finish_plot_url = "goodreads/Graphs/{}/finish_plot_{}.jpeg".format(
        username, username
    )
    return render(
        request, "goodreads/finish_plot.html", {"finish_plot_url": finish_plot_url}
    )


@login_required(redirect_field_name="next", login_url="user-login")
def nationality_map_view(request):
    username = request.user
    nationality_map_url = "goodreads/Graphs/{}/nationality_map_{}.jpeg".format(
        username, username
    )
    return render(
        request,
        "goodreads/nationality_map.html",
        {"nationality_map_url": nationality_map_url},
    )


@login_required(redirect_field_name="next", login_url="user-login")
def popularity_spectrum_view(request):
    username = request.user
    popularity_spectrum_url = (
        "goodreads/Graphs/{}/popularity_spectrum_{}.jpeg".format(username, username)
    )
    return render(
        request,
        "goodreads/popularity_spectrum.html",
        {"popularity_spectrum_url": popularity_spectrum_url},
    )


@login_required(redirect_field_name="next", login_url="user-login")
def summary_plot_view(request):
    username = request.user
    summary_plot_url = "{}/Summary_plot.jpeg".format(username, username)
    return render(
        request, "goodreads/summary_plot.html", {"summary_plot_url": summary_plot_url}
    )


@login_required(redirect_field_name="next", login_url="user-login")
def plots_view(request):
    username = request.user
    finish_plot_url = "Graphs/{}/finish_plot_{}.jpeg".format(
        username, username
    )
    nationality_map_url = "Graphs/{}/nationality_map_{}.jpeg".format(
        username, username
    )
    popularity_spectrum_url = (
        "Graphs/{}/popularity_spectrum_{}.jpeg".format(username, username)
    )
    summary_plot_url = "Graphs/{}/Summary_plot.jpeg".format(username, username)
    return render(
        request,
        "goodreads/plots.html",
        {
            "popularity_spectrum_url": popularity_spectrum_url,
            "finish_plot_url": finish_plot_url,
            "nationality_map_url": nationality_map_url,
            "summary_plot_url": summary_plot_url,
        },
    )


@login_required(redirect_field_name="next", login_url="user-login")
def yearly_pages_read_view(request):
    username = request.user
    yearly_pages_read_url = "{}/Yearly_pages_read_{}.jpeg".format(username, username)
    return render(
        request,
        "goodreads/yearly_pages_read.html",
        {"yearly_pages_read_url": yearly_pages_read_url},
    )


def runscript(request):
    if request.method == "POST" and "runscript" in request.POST:
        run_script_function(request)

    if request.method == "POST" and "pythonscript" in request.POST:
        print("running python script")
        py_script_function(request)
    return render(request, "goodreads/run.html")


def process_export_upload(df, date_col="Date_Read"):
    df.columns = df.columns.str.replace(
        " |\.", "_"
    )  # standard export comes in with spaces. R would turn these into dots
    df[date_col] = pd.to_datetime(df[date_col])
    df.columns = df.columns.str.lower()
    df["number_of_pages"].fillna(0, inplace=True)
    return df


@login_required(redirect_field_name="next", login_url="user-login")
def upload_view(request):
    template = "goodreads/csv_upload.html"
    user = request.user
    # check if user has uploaded a csv file before running the analysis
    file_path = "goodreads/Graphs/{}/sample_export_{}.csv".format(user, user)
    if os.path.isfile(file_path):
        file_exists = True
    else:
        file_exists = False

    if request.method == "GET":
        return render(request, template, {"file_exists": file_exists})

    # run analysis when user clicks on Analyze button
    if request.method == "POST" and "runscript" in request.POST:
        if os.path.isfile(file_path):
            run_script_function(request)
            return render(request, template, {"file_exists": file_exists})
        else:
            return render(request, template)

    # upload csv file
    csv_file = request.FILES["file"]

    # check if file uploaded is csv
    if not csv_file.name.endswith(".csv"):
        messages.error(
            request, "Wrong file format chosen. Please upload .csv file instead."
        )
        return render(request, template)

    # save csv file in database
    df = pd.read_csv(csv_file)
    df = process_export_upload(df)
    for _, row in df.iterrows():
        obj = convert_to_ExportData(row, str(user))
        # obj.create_or_update()
        database_append(str(obj.book_id), str(user))

    df.columns = df.columns.str.replace("_", ".")

    # save csv file to user's folder
    try:
        df.to_csv("goodreads/Graphs/{}/sample_export_{}.csv".format(user, user))
    except OSError:
        os.mkdir("goodreads/Graphs/{}".format(user))
        df.to_csv("goodreads/Graphs/{}/sample_export_{}.csv".format(user, user))

    return render(request, template, {"file_exists": file_exists})


### Geography
def geography(request):
    return render(request, "goodreads/geography.html")   
