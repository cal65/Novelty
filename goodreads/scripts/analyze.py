import os
import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)
import pandas as pd
import psycopg2

from .models import ExportData

post_pass = os.getenv("cal65_pass")


def get_data(user):
    conn = psycopg2.connect(
        host="localhost", database="goodreads", user="cal65", password=post_pass
    )
    query = f"""
    select id, book_id, title, author, number_of_pages,
    my_rating, average_rating, original_publication_year,
    shelf1, shelf2, shelf3, shelf4, shelf5, shelf6, shelf7,
    date_read, exclusive_shelf, added_by, to_reads,
    gender, nationality1, nationality2, nationality_chosen
    from goodreads_exportdata e left join goodreads_authors as a 
    on e.author = a.author_name where e.username = '{user}'
    """
    try:
        df = pd.read_sql(query, con=conn)
        return df
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return


def preprocess(df):
    gender_dict = {"mostly_male": "male", "mostly_female": "female"}
    df["gender"] = df["gender"].map(gender_dict).fillna(df["gender"])
    df["date_read"] = pd.to_datetime(df["date_read"])
    df["title_simple"] = df["title"].str.replace(":.*", "")
    df["title_simple"] = df["title_simple"].str.replace("\\(.*\\)", "")
    return df


def narrative(df):
    shelf_columns = [s for s in df.columns if s.startswith("shelf")]
    df["narrative"] = df[shelf_columns].apply(
        lambda x: "Nonfiction" if "Nonfiction" in x.values else "Fiction", axis=1
    )
    return df


def read_percentage(df):
    # It seems sometimes the "added by" value is off by a factor of 10. When the
    # number of people listing the book as "to read" is larger than total added by, multiply by 10
    df.iloc[df["to_reads"] > df["added_by"], "added_by"] = (
        df.iloc[df["to_reads"] > df["added_by"], "added_by"] * 10
    )
    df["read"] = df["added_by"] - df["to_reads"]
    df["read_percentage"] = df["read"] / df["added_by"]
    return df


def run_all(df):
    df = read_percentage(narrative(preprocess(df)))
    return df
