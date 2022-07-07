import os
import csv
import sys
from datetime import datetime
import pandas as pd
from multiprocessing import Pool, Process
import pyRserve
from .models import ExportData
import concurrent.futures
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages

sys.path.append("..")

from .plotting import plotting

from django.contrib.auth.decorators import login_required
from .scripts.append_to_export import convert_to_ExportData, convert_to_Authors, database_append

import logging

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_script_function(request):
    """
    Main script that generates and saves plots for a user
    """
    user = request.user
    logger.info(f"Running graphs for user {user} based on request {request.method}")
    plotting.main(user)


def py_script_function(request):
    user = request.user
    os.system(
        "python goodreads/scripts/append_to_export.py goodreads/static/Graphs/{}/export_{}.csv".format(
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
    finish_plot_url = "goodreads/static/Graphs/{}/finish_plot_{}.jpeg".format(
        username, username
    )
    return render(
        request, "goodreads/finish_plot.html", {"finish_plot_url": finish_plot_url}
    )


@login_required(redirect_field_name="next", login_url="user-login")
def nationality_map_view(request):
    username = request.user
    nationality_map_url = "goodreads/static/Graphs/{}/author_map_{}.html".format(
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
        "goodreads/static/Graphs/{}/popularity_spectrum_{}.jpeg".format(
            username, username
        )
    )
    return render(
        request,
        "goodreads/popularity_spectrum.html",
        {"popularity_spectrum_url": popularity_spectrum_url},
    )


@login_required(redirect_field_name="next", login_url="user-login")
def summary_plot_view(request):
    username = request.user
    summary_plot_url = "Graphs/{}/Summary_plot_{}.jpeg".format(username, username)
    return render(
        request, "goodreads/summary_plot.html", {"summary_plot_url": summary_plot_url}
    )


@login_required(redirect_field_name="next", login_url="user-login")
def plots_view(request):
    username = request.user
    finish_plot_url = "Graphs/{}/finish_plot_{}.jpeg".format(username, username)
    nationality_map_url = "Graphs/{}/author_map_{}.html".format(username, username)
    popularity_spectrum_url = "Graphs/{}/popularity_spectrum_{}.jpeg".format(
        username, username
    )
    summary_plot_url = "Graphs/{}/Summary_plot_{}.jpeg".format(username, username)

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


def insert_dataframe_into_database(df, user, wait=2, metrics=True):
    found = 0
    not_found = 0
    now = datetime.now()
    for _, row in df.iterrows():
        # save book csv info to exportdata table
        obj = convert_to_ExportData(row, str(user))
        # if book is not in books table, scrape it and save additional parameters
        status = database_append(obj, wait=wait)
        if metrics:
            if status == "found":
                found += 1
            else:
                not_found += 1
    if metrics:
        # output metrics
        write_metrics(user, time=now, found=found, not_found=not_found)


def insert_row_into_db(row, user, wait=2):
    # save row info to exportdata table
    obj = convert_to_ExportData(row, str(user))
    # if book is not in books table, scrape it and save additional parameters
    logger.info("Insert row - obj converted")
    status = database_append(obj, wait=wait)
    logger.info(f"insert row being called for {user} with status: {status}")

    return status


@login_required(redirect_field_name="next", login_url="user-login")
def upload_view(request):
    template = "goodreads/csv_upload.html"
    user = request.user
    logger.info(f"upload started for {user}")
    # check if user has uploaded a csv file before running the analysis

    if request.method == "GET":
        return render(request, template)

    # run analysis when user clicks on Analyze button
    if request.method == "POST" in request.POST:
        logger.info(f"Got running with request {request.method}")
        run_script_function(request)
        # when script finishes, move user to plots view
        return HttpResponseRedirect("/plots/")
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

    logger.info(f"starting database addition for {str(len(df))} rows")
    insert_dataframe_into_database(df, user, wait=3, metrics=True)

    # save csv file to user's folder
    try:
        df.to_csv("goodreads/static/Graphs/{}/export_{}.csv".format(user, user))
    except OSError:
        os.mkdir("goodreads/static/Graphs/{}".format(user))
        df.to_csv("goodreads/static/Graphs/{}/export_{}.csv".format(user, user))


    return render(request, template)


def write_metrics(user, time, found, not_found, file_path="metrics.csv"):
    time_now = datetime.now()
    fields = [user, time, time_now, found, not_found]
    with open(file_path, "a") as f:
        writer = csv.writer(f)
        writer.writerow(fields)


### Geography
def geography(request):
    return render(request, "goodreads/geography.html")
