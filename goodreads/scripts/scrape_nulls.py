import pandas as pd
import numpy as np
from goodreads.models import *
from goodreads.scripts.append_to_export import append_scraping
from spotify.plotting.utils import objects_to_df


def scrape_null(book_ids, n, wait=10):
    for bid in book_ids[:n]:
        b = append_scraping(bid, wait=wait)
        b.save()
        print(b.added_by)


def get_missing_books():
    export_all = ExportData.objects.all()
    books_all = Books.objects.all()
    books_ids = [b.book_id for b in books_all]
    missing_ids = [e.book_id for e in export_all if e.book_id not in books_ids]
    print(len(missing_ids))
    return missing_ids


def get_nulls():
    books_null = Books.objects.filter(added_by__isnull=True)
    print(len(books_null))
    null_ids = [b.book_id for b in books_null]
    return null_ids


def reading_percentage():
    books_df = objects_to_df(Books.objects.all())
    books_df["reading_percentage"] = (
        books_df["added_by"] - books_df["to_reads"]
    ) / books_df["added_by"]
    books_df["date"] = books_df["ts_updated"].dt.date
    export_df = objects_to_df(ExportData.objects.all())
    export_df = pd.pivot_table(
        export_df,
        index="book_id",
        values=["title", "author", "username"],
        aggfunc=lambda x: x.head(1),
    )
    books_df = pd.merge(books_df, export_df, on="book_id", how="left")
    return books_df
