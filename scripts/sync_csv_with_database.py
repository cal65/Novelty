import psycopg2
import os
from sqlalchemy import create_engine, insert
import pandas as pd
from datetime import datetime
import logging

from goodreads.models import ExportData, Books, Authors
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


def create_Books_object(row):
    f_names = get_field_names(Books)
    common_fields = list(set(row.keys()).intersection(f_names))
    try:
        Books.objects.get(book_id=row.book_id)
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
    return djangoBook


def sync_books(books_df):
    # todo write check on column schema
    books_df.columns = [c.lower() for c in books_df.columns]
    books_df.rename(columns={"book.id": "book_id"}, inplace=True)
    for _, row in books_df.iterrows():
        create_Books_object(row)
