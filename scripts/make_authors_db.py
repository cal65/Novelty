import psycopg2
import os
from sqlalchemy import create_engine, insert
import pandas as pd


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
    finally:
        if connection is not None:
            connection.close()
    engine = create_engine(
        "postgresql+psycopg2://cal65:"
        + os.environ["cal65_pass"]
        + "@127.0.0.1/goodreads"
    )
    ## populate authors
    authors_db = pd.read_csv("artifacts/authors_sql_database.csv")
    authors_db = authors_db[
        ["Author", "gender_fixed", "nationality1", "nationality2", "Country.Chosen"]
    ]
    authors_db.columns = [
        "author_name",
        "gender",
        "nationality1",
        "nationality2",
        "nationality_chosen",
    ]
    authors_db.to_sql("goodreads_authors", engine, if_exists="replace", index=False)
    ## populate books
    books_db = pd.read_csv("artifacts/books_database.csv")
    books_db = books_db[
        [
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
        ]
    ]
    books_db.columns = [
            "book_id",
            "shelf1",
            "shelf2",
            "shelf3",
            "shelf4",
            "shelf5",
            "shelf6",
            "shelf7",
            "added_by",
            "to_reads",
        ]
    books_db.to_sql("goodreads_books", engine, if_exists="replace", index=False)
    connection.close()


if __name__ == "__main__":
    start()
