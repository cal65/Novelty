import pandas as pd
import numpy as np
from goodreads.models import *
from goodreads.scripts.append_to_export import append_scraping


def scrape_null(book_ids, n):
    for bid in book_ids[:n]:
        b = append_scraping(bid, wait=25)
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
