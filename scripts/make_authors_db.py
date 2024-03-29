import psycopg2
import os
from sqlalchemy import create_engine, insert
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
    df = pd.read_csv(csv_file_path, encoding="ISO-8859-1")
    df.to_sql(table, engine, if_exists="append", index=False)
    connection.close()


def start():
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
    authors_db = pd.read_csv("artifacts/authors_sql_database.csv")
    authors_db["ts_updated"] = datetime.now()
    authors_db.to_sql("goodreads_authors", engine, if_exists="replace", index=False)
    ## populate books
    books_db = pd.read_csv("artifacts/books_database.csv")
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
        "Narrative",
    ]
    rename_cols = [c.lower().replace(".", "_") for c in book_cols]
    books_db = books_db[book_cols].rename(columns=dict(zip(book_cols, rename_cols)))
    books_db["book_id"] = books_db["book_id"].astype(str)
    books_db["ts_updated"] = datetime.now()
    books_db.to_sql("goodreads_books", engine, if_exists="replace", index=False)

    ## populat refnationalities
    nationalities_db = pd.read_csv("artifacts/world_regions_dict.csv", encoding='unicode_escape')
    nationalities_db.to_sql(
        "goodreads_refnationality", engine, if_exists="replace", index=False
    )
    connection.close()


if __name__ == "__main__":
    start()
