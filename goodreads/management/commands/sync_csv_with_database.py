from django.core.management.base import BaseCommand

import argparse
import sys
import os
import pandas as pd
import logging
import django
from spotify.plotting.plotting import objects_to_df

sys.path.append("../..")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "local_settings.py")

from goodreads.models import Books, Authors, SpotifyTracks, NetflixTitles
from goodreads.scripts.append_to_export import (
    convert_to_ExportData,
    convert_to_Book,
    convert_to_Authors,
    get_field_names,
)

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

django.setup()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)
        parser.add_argument("domain", type=str)

    def handle(self, **options):
        df = pd.read_csv(options["file_path"])
        if options["domain"] == "Spotify":
            sync_df(df, "SpotifyStreaming")
        elif options["domain"] == "Books":
            sync_books(df)


def create_Books_object(row):
    f_names = get_field_names(Books)
    common_fields = list(set(row.keys()).intersection(f_names))
    try:
        djangoBook = Books.objects.get(book_id=row.book_id)
    except:
        djangoBook = Books()
    for f in common_fields:
        value = row.get(f)
        existing_value = getattr(djangoBook, f)
        if pd.isnull(value):
            value = None
        if value != getattr(djangoBook, f):
            logger.info(
                f"updating djangoBook {row.title} for field {f} from {existing_value} to value {value}"
            )
            setattr(djangoBook, f, value)
            # update ExportsData table with updated book
        djangoBook.save()
    return djangoBook


def get_field_names(djangoClass):
    fields = djangoClass._meta.get_fields()
    f_names = [f.name for f in fields]
    return set(f_names)


def sync_books(books_df):
    # todo write check on column schema
    books_df.columns = [c.lower() for c in books_df.columns]
    books_df.rename(columns={"book.id": "book_id"}, inplace=True)
    for _, row in books_df.iterrows():
        create_Books_object(row)


def sync_authors(authors_df):
    for _, row in authors_df.iterrows():
        try:
            a = Authors.objects.get(author_name=row.author_name)
        except Exception as e:
            a = Authors()
        a.gender = row.gender
        a.nationality1 = row.nationality1
        a.nationality2 = row.nationality2
        a.nationality_chosen = row.nationality_chosen
        a.save()
        print(a.__dict__)
    return


def export_authors_missing():
    authors = Authors.objects.filter(nationality_chosen="") | Authors.objects.filter(
        gender="unknown"
    )
    authors_df = objects_to_df(authors)
    authors_df.to_csv("artifacts/authors_export.csv", index=False)


def sync_df(df, schema):
    if schema == "SpotifyTracks":
        df["release_date"] = pd.to_datetime(df["release_date"])
        fields = get_field_names(SpotifyTracks)
        for _, row in df.iterrows():
            try:
                a = SpotifyTracks.objects.filter(artistname=row.artistname).get(
                    trackname=row.trackname
                )
            except Exception as e:
                a = SpotifyTracks()
            for field in fields:
                setattr(a, field, row.get(field))
            print(a.__dict__)
            a.save()
    elif schema == "NetflixTitles":
        fields = get_field_names(NetflixTitles)
    return


if __name__ == "__main__":
    """
    Usage: python append_to_export.py filepath.csv
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path")

    args = parser.parse_args()
    file_path = args.file_path
    books_df = pd.read_csv(file_path)
    # to do: check schema
    sync_books(books_df)
