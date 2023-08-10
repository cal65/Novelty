import os
import sys

import numpy as np
import pandas as pd
import logging
import functools
import psycopg2
from datetime import datetime

sys.path.append("..")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "local_settings.py")
from ..models import ExportData, Authors, Books, RefNationality
from . import scrape_goodreads
import gender_guesser.detector as gender_detector
from .. import google_answer
from . import wikipedia
from spotify.plotting.utils import objects_to_df

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
            book_id=str(row['book_id']), username=username
        )
    except Exception as e:
        djangoExport = ExportData()
        new = True

    f_names = get_field_names(ExportData)
    common_fields = list(set(row.keys()).intersection(f_names))

    for f in common_fields:
        value = row[f]
        existing_value = getattr(djangoExport, f)
        if pd.isnull(value):
            value = None
        # check if this data is different from what has been existing
        setattr(djangoExport, f, value)
        if value != existing_value:
            if not new:
                logger.info(
                    f"updating djangoExport {row['title']} for field {f} from {existing_value} to value {value}"
                )
                # update ExportsData table with updated book
                djangoExport.save()
    if new:
        djangoExport.username = username
        djangoExport.ts_updated = datetime.now()
        # update ExportsData table with new book
        djangoExport.save()

    return djangoExport


def convert_to_Authors(name):
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

        djangoObj.nationality_chosen = djangoObj.nationality1  # TODO: Fix
        logger.info(f"Saving new author {djangoObj.author_name}")
        djangoObj.save()
        return djangoObj


def lookup_gender(name):
    # gender
    first_name = get_first_name(name)
    gender = guess_gender(first_name)
    logger.info(f"Guessed gender for {name}, got {gender}")
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


def choose_nationality():
    authors = Authors.objects.all()
    count_dict = nationality_counts(objects_to_df(authors))
    regions = objects_to_df(RefNationality.objects.all())

    def _choose_a(author):
        if pd.isnull(author.nationality2):
            # shortcut, if nationality 2 is NA, they are all NA
            author.nationality_chosen = author.nationality1
            author.save()
            return
        else:
            nationalities = [author.nationality1, author.nationality2]
            counts = [
                count_dict.get(n) if n in regions["nationality"].values else np.nan
                for n in nationalities
            ]
            if (len(counts) > 0) and (not all(pd.isnull(counts))):
                author.nationality_chosen = nationalities[np.nanargmin(counts)]
                author.save()
                return
            else:
                return None

    for a in authors:
        _choose_a(a)
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
    scraped_dict = scrape_bid(book_id, wait=wait)
    for k, v in scraped_dict.items():
        if k in book_fields:
            setattr(djangoBook, k, v)
    djangoBook.book_id = book_id
    return djangoBook


def scrape_bid(book_id, wait):
    url = scrape_goodreads.create_url(str(book_id))
    scraped_dict = scrape_goodreads.get_stats(url, wait=wait)
    url_stats = url.replace("show", "stats")
    stats_dict = scrape_goodreads.get_read_stats(url_stats)
    scraped_dict.update(stats_dict)
    scraped_dict.update({"book_id": book_id})
    return scraped_dict

def convert_to_Book(book_id, wait=2):
    """
    If book is in books table, return status "found"
    If book is not in books table, scrape it, add the scraped fields to the books table, return status "not found"
    Add the scraped fields to the exportdata table
    Save to user goodreads exportdata table
    """

    if Books.objects.filter(book_id=book_id).exists():
        status = "found"
        return status
    else:
        logger.info(f"{book_id} not in database - must scrape")
        djangoBook = append_scraping(book_id, wait=wait)
        status = "not found"
        djangoBook.save()
        logger.info(f"Book {djangoBook.book_id} updated in books table")
    return status
