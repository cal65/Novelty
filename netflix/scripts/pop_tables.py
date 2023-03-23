import psycopg2
import os
from sqlalchemy import create_engine, insert
import pandas as pd
from datetime import datetime


def populate_table_from_csv(csv_file_path, table, database="goodreads"):
    """populate table in the PostgreSQL database"""
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
    """populate authors table in the PostgreSQL database"""
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
    ## populate genres
    genres = pd.read_csv("artifacts/genres_data.csv")
    genres.to_sql("goodreads_netflixgenres", engine, if_exists="replace", index=False)

    ## populate actors
    actors = pd.read_csv("artifacts/actors_data.csv")
    actors = actors[["netflix_id", "cast"]]
    actors.to_sql("goodreads_netflixactors", engine, if_exists="replace", index=False)

    netflix_titles = pd.read_csv("artifacts/netflix_titles.csv")
    netflix_titles
    netflix_titles.to_sql('goodreads_netflixtitles', engine, if_exists="replace", index=False)

    connection.close()


if __name__ == "__main__":
    start()
