import os
import sys

import pandas as pd
import re
import logging
import argparse
import functools
import psycopg2
from datetime import datetime

sys.path.append("..")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "local_settings.py")
from ..models import ExportData, Authors, Books
from . import scrape_goodreads
import gender_guesser.detector as gender_detector
from .. import google_answer
from . import wikipedia

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

post_pass = os.getenv("cal65_pass")


def get_field_names(djangoClass):
    fields = djangoClass._meta.get_fields()
    f_names = [f.name for f in fields]
    return set(f_names)


def convert_to_ExportData(row, username):
    """
    Take a row from a goodreads export
    """
    new = False
    try:
        # check if ExportData table already has this book
        djangoExport = ExportData.objects.get(
            book_id=str(row.book_id), username=username
        )
    except:
        djangoExport = ExportData()
        logger.info(f"convert to export data - new book id {row.book_id}")
        new = True

    f_names = get_field_names(ExportData)
    common_fields = list(set(row.keys()).intersection(f_names))

    for f in common_fields:
        value = row.get(f)
        existing_value = getattr(djangoExport, f)
        if pd.isnull(value):
            value = None
        # check if this data is different from what has been existing
        setattr(djangoExport, f, value)
        if value != existing_value:
            if not new:
                logger.info(
                    f"updating djangoExport {row.title} for field {f} from {existing_value} to value {value}"
                )
                # update ExportsData table with updated book
                djangoExport.save()
    if new:
        djangoExport.username = username
        djangoExport.ts_updated = datetime.now()
        # update ExportsData table with new book
        djangoExport.save()

    return djangoExport


def convert_to_Authors(row):
    name = row.author
    if Authors.objects.filter(author_name=name).exists():
        return
    else:
        djangoObj = Authors()
        djangoObj.author_name = name
        djangoObj.gender = lookup_gender(name)
        nationalities = lookup_nationality(name)

        if len(nationalities) > 0:
            djangoObj.nationality1 = nationalities[0]
        elif (
            len(nationalities) > 1
        ):  # too lazy to figure out if there's a more elegant way to do this
            djangoObj.nationality2 = nationalities[1]
        else:
            djangoObj.nationality1 = ""

        logger.info(f"Saving new author {djangoObj.author_name}")
        djangoObj.save()
        return djangoObj


def lookup_gender(name):
    # gender
    first_name = get_first_name(name)
    gender = guess_gender(first_name)
    # outcomes from this package can be male, female, andy, or unknown
    if gender not in ["male", "female"]:
        gender = wikipedia.search_person_for_gender(name)
    # gender will now be either male, female or unknown
    return gender


def get_first_name(name):
    names = name.split(" ")
    if len(names) > 0:
        return names[0]
    else:
        return ""


def guess_gender(name):
    d = gender_detector.Detector()
    gender = d.get_gender(name)

    return gender


def lookup_nationality(name):
    nationalities = google_answer.lookup_author_nationality(name)
    return nationalities


def nationality_counts(df):
    """
    return count of all nationalities in authors table in order to choose the least common one
    """
    nationality_cols = [n for n in df.columns if "nationality" in n]
    nationality_series = [df[c] for c in nationality_cols]
    nationalities_all = functools.reduce(lambda a, b: a.append(b), nationality_series)
    counts_df = pd.DataFrame(nationalities_all.value_counts())
    counts_df.columns = ["Count"]
    count_dict = counts_df.to_dict()["Count"]
    return count_dict


def query_authors():
    conn = psycopg2.connect(
        host="localhost", database="goodreads", user="cal65", password=post_pass
    )
    query = f"""
    select * from goodreads_authors
    """
    try:
        df = pd.read_sql(query, con=conn)
        logger.info(f"Returning data from query with nrows {len(df)}")
        return df
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return


def clean_df(goodreads_data):
    goodreads_data.columns = [c.replace(" ", "_") for c in goodreads_data.columns]
    date_columns = [c for c in goodreads_data.columns if "date" in c.lower()]
    for c in date_columns:
        goodreads_data[c] = pd.to_datetime(goodreads_data[c], errors="coerce")
        goodreads_data[c] = (
            goodreads_data[[c]]
            .astype(object)
            .where(goodreads_data[[c]].notnull(), None)
        )
    return goodreads_data


def append_scraping(book_id, wait):
    """
    Take data meant to be in the Goodreads export format
    Scrape additional fields and add them as columns
    """
    djangoBook = Books()
    book_fields = get_field_names(Books)
    url = scrape_goodreads.create_url(str(book_id))
    scraped_dict = scrape_goodreads.get_stats(url, wait=wait)
    url_stats = url.replace("show", "stats")
    stats_dict = scrape_goodreads.get_read_stats(url_stats)
    scraped_dict.update(stats_dict)
    for k, v in scraped_dict.items():
        if k in book_fields:
            setattr(djangoBook, k, v)
    djangoBook.book_id = book_id
    return djangoBook


def convert_to_Book(djangoExport, wait=2):
    """
    If book is in books table, return status "found"
    If book is not in books table, scrape it, add the scraped fields to the books table, return status "not found"
    Add the scraped fields to the exportdata table
    Save to user goodreads exportdata table
    """
    book_id = djangoExport.book_id

    if Books.objects.filter(book_id=book_id).exists():
        status = "found"
        return status
    else:
        logger.info(f"{djangoExport.title} not in database - must scrape")
        djangoBook = append_scraping(book_id, wait=wait)
        status = "not found"
        djangoBook.save()
        logger.info(f"Book {djangoBook.book_id} updated in books table")
    return status


def apply_append(file_path, username):
    goodreads_data = scrape_goodreads.read_goodreads_export(file_path)
    goodreads_data.apply(
        lambda x: convert_to_ExportData(x, username=username).save(), axis=1
    )
    return append_scraping(goodreads_data)


def add_to_existing_export(file_path_existing, file_path_new):
    existing = scrape_goodreads.read_goodreads_export(file_path_existing)
    new = scrape_goodreads.read_goodreads_export(file_path_new)
    diff_titles = set(new["Title"]).difference(existing["Title"]).tolist()
    diff = new[new["Title"].isin(diff_titles)]
    diff_scraped = append_scraping(diff)
    return diff_scraped


def update_goodreads(df1, df2, index_column):
    """
    Takes df1, an existing dataframe, and df2, a new dataframe.
    The idea is df1 already has appended fields, but df2 may be more recent.
    Any changes in df2 should be reflected in df1
    Updates df1 on new df2 values
    """
    df2.columns = [c.replace(" ", ".") for c in df2.columns]
    # save all new books
    df2_new = df2[~df2[index_column].isin(df1[index_column])]
    logger.info("Adding " + str(len(df2_new)) + " new rows of data")
    # go over the old books that are in common with existing dataset
    df1.set_index(index_column, inplace=True)
    df2.set_index(index_column, inplace=True)
    df1.update(df2)
    df1.reset_index(inplace=True)
    df2_updated = append_scraping(df2_new)
    df_updated = pd.concat([df1, df2_updated])
    return df_updated


def update_missing_data(df, wait=4):
    """
    This function is for incomplete appends, when rows failed due to timeouts
    """
    df_missing = df[
        pd.isnull(df["Added_by"])
    ]  # this is a scraped field that is often missing
    if len(df_missing) > 0:
        logger.info("Updating " + str(len(df_missing)) + " missing rows of data")
        urls = scrape_goodreads.return_urls(df_missing)
        scraped_missing = scrape_goodreads.apply_added_by(urls, wait=wait)
        scraped_missing.index = df_missing.index
        df.update(scraped_missing)
    else:
        logger.info("No data needs updating")
    return df


def fix_date(file_path):
    """
    In passing csvs back and forth between R and Python, different defaults in reading date columns can be problematic
    This function ensures that the csv in a file path has the Date.Added and Date.Read columns in datetime
    """
    df = pd.read_csv(file_path)
    date_columns = [c for c in df.columns if "date" in c.lower()]
    for c in date_columns:
        df[c] = pd.to_datetime(df[c])
    df.to_csv(file_path, index=False)
    # return just for proof
    return df[["Title", "Date.Added", "Date.Read"]]


if __name__ == "__main__":
    """
    Usage: python append_to_export.py filepath.csv --username [--update] [wait]
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path")
    parser.add_argument(
        "--username",
        dest="username",
        help="The username which will be stored in goodreads.exportbooks",
    )
    parser.add_argument(
        "--update",
        dest="update",
        action="store_true",
        help="Mode - default none = apply append",
    )
    parser.add_argument("wait")
    args = parser.parse_args()
    file_path = args.file_path
    username = args.username
    update = args.update
    wait = int(args.wait)
    export_path = re.sub(".csv|.xlsx", "_appended.csv", file_path)
    if update is False:
        apply_append(file_path, username).to_csv(export_path, index=False)
        fix_date(export_path)
    elif update is True:
        df = pd.read_csv(file_path)
        df = update_missing_data(df, wait)
        df.to_csv(file_path, index=False)
