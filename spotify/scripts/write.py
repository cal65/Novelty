import os
import sys
import argparse
import logging
import pandas as pd
import sqlalchemy as sa
import psycopg2


logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

post_pass = os.getenv("cal65_pass")


def get_tracks():
    query = f"""
    select 
    uri,
    name, 
    artist, 
    duration,
    popularity,
    release_date,
    genres,
    album,
    explicit,
    podcast
    from goodreads_spotifytracks 
    """

    conn = psycopg2.connect(
        host="localhost", database="goodreads", user="cal65", password=post_pass
    )
    try:
        df = pd.read_sql(query, con=conn)
        logger.info(f"Returning data from query with nrows {len(df)}")
        return df

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return


def process_for_db(df):
    df["genres"] = df["genres"].str.join(", ")
    df.drop(columns=["is_local"], inplace=True)
    df.columns = [c.lower() for c in df.columns]
    return df


if __name__ == "__main__":
    """
    Usage: python write.py file_path.pkl
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path")
    args = parser.parse_args()
    file_path = args.file_path
    df_pickle = pd.read_pickle(file_path)
    df_pickle = process_for_db(df_pickle)
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

    engine = sa.create_engine(
        "postgresql+psycopg2://cal65:"
        + os.environ["cal65_pass"]
        + "@127.0.0.1/goodreads"
    )

    df_existing = get_tracks()
    if len(df_existing) < 1:
        df_new = df_pickle.copy()
    else:
        df_new = df_pickle[~df_pickle["uri"].isin(df_existing["uri"])]

    df_new.to_sql("goodreads_spotifytracks", engine, if_exists="append", index=False)
    connection.close()
