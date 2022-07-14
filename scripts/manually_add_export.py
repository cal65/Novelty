import psycopg2
import os
from sqlalchemy import create_engine, insert
import argparse
import pandas as pd
from datetime import datetime

def populate_table_from_csv(csv_file_path, table, database="goodreads"):
    """ populate table in the PostgreSQL database"""
    try:
        connection = psycopg2.connect(
            user="cal65",
            password=os.environ["cal65_pass"],
            host="127.0.0.1",
            port="5432",
            database=database,
        )

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    engine = create_engine(
        "postgresql+psycopg2://cal65:"
        + os.environ["cal65_pass"]
        + "@127.0.0.1/goodreads"
    )
    df = pd.read_csv(csv_file_path, encoding = "ISO-8859-1")
    df.to_sql(table, engine, if_exists="replace", index=False)
    connection.close()


def start(file_path, username):
    """ populate authors table in the PostgreSQL database"""
    try:
        connection = psycopg2.connect(
            user="cal65",
            password=os.environ["cal65_pass"],
            host="127.0.0.1",
            port="5432",
            database="goodreads",
        )

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    engine = create_engine(
        "postgresql+psycopg2://cal65:"
        + os.environ["cal65_pass"]
        + "@127.0.0.1/goodreads"
    )

    ## populate authors
    ## populate books
    books = pd.read_csv(file_path)
    books_db['Book.Id'] = books_db['Book.Id'].astype(str)

    book_cols = [
            "Book.Id",
            "Shelf1",
            "Shelf2",
            "Shelf3",
            "Shelf4",
            "Shelf5",
            "Shelf6",
            "Shelf7",
            "Added_by",
            "To_reads",
            "Narrative"
        ]
    rename_cols = [c.lower().replace('.', '_') for c in book_cols]   
    books_db = books[book_cols].rename(columns=dict(zip(book_cols, rename_cols)))
    books_db['ts_updated'] = datetime.now()
    books_db.to_sql("goodreads_books", engine, if_exists="replace", index=False)

    books.columns = [c.lower().replace('.', '_') for c in books.columns]  
    exportdata_cols = ['book_id', 'title', 'author', 'number_of_pages', 'my_rating', 'average_rating',
    'original_publication_year', 'date_read', 'exclusive_shelf']
    books['ts_updated'] = datetime.now()
    books['username'] = username
    books[exportdata_cols].to_sql("goodreads_exportdata", engine, if_exists="replace", index=False)
    connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", help="The path to a books csv file")
    parser.add_argument("username", help="name of user")
    args = parser.parse_args()
    file_path = args.file_path
    username = args.username
    start(file_path, username)
