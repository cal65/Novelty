import os
import sys
import pandas as pd
import re
import logging
import argparse
from datetime import datetime
sys.path.append("..")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "local_settings.py")
import django
from ..models import ExportData, Authors, Books
from . import scrape_goodreads

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_field_names(djangoClass):
    fields = djangoClass._meta.get_fields()
    f_names = [f.name for f in fields]
    return set(f_names)

def convert_to_ExportData(row, username):
    try:
        # check if ExportData table already has this book
        djangoObj = ExportData.objects.get(book_id=str(row.book_id), username=username)
        print('book found')
    except:
        print('book not found')
        djangoObj = ExportData()
    f_names = get_field_names(ExportData)
    common_fields = list(set(row.keys()).intersection(f_names))
    for f in common_fields:
        value = row.get(f)
        if pd.isnull(value):
            value = None
        setattr(djangoObj, f, value)
    djangoObj.username = username
    djangoObj.ts_updated = datetime.now()
    logger.info(f"Saving book {djangoObj.title}")
    djangoObj.save()
    return djangoObj


def clean_df(goodreads_data):
    goodreads_data.columns = [c.replace(" ", "_") for c in goodreads_data.columns]
    date_columns = [c for c in goodreads_data.columns if 'date' in c.lower()]
    for c in date_columns:
        goodreads_data[c] = pd.to_datetime(goodreads_data[c], errors='coerce')
        goodreads_data[c] = goodreads_data[[c]].astype(object).where(goodreads_data[[c]].notnull(), None)
    return goodreads_data

def append_scraping(book_id, wait):
    """
    Take data meant to be in the Goodreads export format
    Scrape additional fields and add them as columns
    """
    djangoBook = Books()
    book_fields = get_field_names(Books)
    url = scrape_goodreads.create_url(book_id)
    scraped_dict = scrape_goodreads.get_stats(url, wait=wait)
    for k, v in scraped_dict.items():
        if k in book_fields:
            setattr(djangoBook, k, v)
    djangoBook.save()
    return djangoBook


def database_append(book_id, username, wait=4):
    djangoExport = ExportData.objects.get(book_id=book_id, username=username)
    book_fields = get_field_names(Books)
    export_fields = get_field_names(ExportData)
    try:
        djangoBook = Books.objects.get(book_id=book_id)
    except:
        logger.info("Book not in database - must scrape")
        djangoBook = append_scraping(book_id, wait=wait)

    common_fields = book_fields.intersection(export_fields)
    for field in common_fields:
        setattr(djangoExport, field, getattr(djangoBook, field))
    djangoExport.save()
    logger.info(f"Book {djangoBook.book_id} updated in database")


def apply_append(file_path, username):
    goodreads_data = scrape_goodreads.read_goodreads_export(file_path)
    goodreads_data.apply(lambda x: convert_to_ExportData(x, username=username).save(), axis=1)
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
    date_columns = [c for c in df.columns if 'date' in c.lower()]
    for c in date_columns:
        df[c] = pd.to_datetime(df[c])
    df.to_csv(file_path, index=False)
    # return just for proof
    return df[["Title", "Date.Added", "Date.Read"]]


def merge_with_existing(df, db, id_col_df="Book.Id", id_col_db="Book.Id"):
    """
    df is a dataframe of a goodreads export (not yet appended)
    db is a dataframe of an existing library of goodreads books with only Book.Id and scraped columns (and unique)
    Merge the db fields into df, so as to save scraping time
    """
    df = pd.merge(df, db, left_on=id_col_df, right_on=id_col_db, how="left")
    return df


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
