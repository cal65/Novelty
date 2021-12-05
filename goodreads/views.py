import io
import os
import csv
import time
from datetime import datetime
import pandas as pd
import csv
from .models import ExportData
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .scripts.append_to_export import convert_to_ExportData, database_append

import logging

logging.basicConfig(filename="logs.txt", filemode="a", level=logging.INFO)
logger = logging.getLogger(__name__)


def run_script_function(request):
    user = request.user
    logger.info(f"Running graphs for user {user} based on request {request.method}")
    os.system("Rscript goodreads/scripts/runner.R {}".format(user))


def py_script_function(request):
    user = request.user
    os.system(
        "python goodreads/scripts/append_to_export.py goodreads/Graphs/{}/export_{}.csv".format(
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


def faq(request):
    return render(request, "goodreads/faq.html")


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
    popularity_spectrum_url = "goodreads/Graphs/{}/popularity_spectrum_{}.jpeg".format(
        username, username
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
    finish_plot_url = "Graphs/{}/finish_plot_{}.jpeg".format(username, username)
    nationality_map_url = "Graphs/{}/nationality_map_{}.jpeg".format(username, username)
    popularity_spectrum_url = "Graphs/{}/popularity_spectrum_{}.jpeg".format(
        username, username
    )
    summary_plot_url = "Graphs/{}/Summary_plot.jpeg".format(username, username)

    if "run_script_function" in request.POST:
        run_script_function(request)
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
    logger.info(f"Running script with request method {request.method}")
    if request.method == "POST" and "runscript" in request.POST:
        run_script_function(request)

    if request.method == "POST" and "pythonscript" in request.POST:
        logger.info("running python script")
        py_script_function(request)
    return plots_view(request)


def process_export_upload(df, date_col="Date_Read"):
    df.columns = df.columns.str.replace(
        " |\.", "_"
    )  # standard export comes in with spaces. R would turn these into dots
    df[date_col] = pd.to_datetime(df[date_col])
    df.columns = df.columns.str.lower()
    df["number_of_pages"].fillna(0, inplace=True)
    df["book_id"] = df["book_id"].astype(str)
    df = df[pd.notnull(df["book_id"])]
    return df


@login_required(redirect_field_name="next", login_url="user-login")
def upload_view(request):
    template = "goodreads/csv_upload.html"
    user = request.user
    logger.info(f"upload started for {user}")
    # check if user has uploaded a csv file before running the analysis
    file_path = "goodreads/Graphs/{}/export_{}.csv".format(user, user)
    if os.path.isfile(file_path):
        file_exists = True
    else:
        file_exists = False

    if request.method == "GET":
        return render(request, template, {"file_exists": file_exists})

    # run analysis when user clicks on Analyze button
    if request.method == "POST" and "runscript" in request.POST:
        if os.path.isfile(file_path):
            logger.info(f"Got running with request {request.method}")
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

    # saving metrics
    found = 0
    not_found = 0
    now = datetime.now()
    logger.info(f"starting database addition for {str(len(df))} rows")
    for _, row in df.iterrows():
        obj = convert_to_ExportData(row, str(user))
        status = database_append(str(obj.book_id), str(user))
        if status == "found":
            found += 1
        else:
            not_found += 1

    df.columns = df.columns.str.replace("_", ".")

    # output metrics
    write_metrics(user, time=now, found=found, not_found=not_found)

    # save csv file to user's folder
    try:
        df.to_csv("goodreads/Graphs/{}/export_{}.csv".format(user, user))
    except OSError:
        os.mkdir("goodreads/Graphs/{}".format(user))
        df.to_csv("goodreads/Graphs/{}/export_{}.csv".format(user, user))

    return render(request, template, {"file_exists": file_exists})


def write_metrics(user, time, found, not_found, file_path="metrics.csv"):
    time_now = datetime.now()
    fields = [user, time, time_now, found, not_found]
    with open(file_path, "a") as f:
        writer = csv.writer(f)
        writer.writerow(fields)


### Geography
def geography(request):
    return render(request, "goodreads/geography.html")
