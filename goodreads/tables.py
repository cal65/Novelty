from django.core.cache import cache
from spotify.plotting.utils import objects_to_df
from goodreads.plotting import plotting as gplot
import pandas as pd
from django.db.models.functions import Length


from .models import (
    NetflixUsers,
    Books,
    ExportData,
    Authors,
    SpotifyTracks,
    NetflixTitles,
    NetflixGenres,
    NetflixActors,
)

import time
import logging

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_explore_books_table():
    t0 = time.time()
    books_df = objects_to_df(Books.objects.filter(added_by__gt=1))
    export_df = objects_to_df(
        ExportData.objects.annotate(title_len=Length("title"))
        .filter(title_len__gt=1)
        .values("book_id", "title", "author")
        .distinct()
    )
    good_df = pd.merge(books_df, export_df, how="left", on="book_id")
    logger.info(f"good_df merged: {round(time.time() - t0, 2)}")
    authors_df = objects_to_df(
        Authors.objects.filter(author_name__in=export_df["author"].unique()).values(
            "author_name", "gender", "nationality_chosen"
        )
    )
    authors_df.rename(columns={"author_name": "author"}, inplace=True)
    # drop a few authors that aren't books
    authors_df = authors_df.loc[authors_df["author"] != "NOT A BOOK"]
    good_df = pd.merge(good_df, authors_df, on="author", how="left")
    good_df["author"] = good_df["author"].fillna("")
    good_df = gplot.run_all(good_df)
    logger.info(f"pre genre join: {round(time.time() - t0, 2)}")
    good_df = gplot.genre_join(good_df)
    edf = pd.pivot_table(
        good_df,
        index=["title_simple", "author", "nationality_chosen", "gender"],
        values=[
            "number_of_pages",
            "original_publication_year",
            "read",
            "narrative",
            "shelves",
        ],
        aggfunc={
            "number_of_pages": max,
            "original_publication_year": max,
            "read": max,
            "narrative": "first",
            "shelves": "first",
        },
    ).reset_index()
    logger.info(f"edf pivoted: {round(time.time() - t0, 2)}")
    edf["read"] = edf["read"].fillna(0)
    edf = edf.fillna("")
    edf.sort_values("read", ascending=False, inplace=True)
    return edf


def get_explore_streaming():
    title_df = objects_to_df(NetflixTitles.objects.filter(netflix_id__isnull=False))
    genres_df = objects_to_df(NetflixGenres.objects.all())
    actors_df = objects_to_df(NetflixActors.objects.all())
    stream_df = pd.merge(title_df, genres_df, on="netflix_id", how="left")
    stream_df = pd.merge(stream_df, actors_df, on="netflix_id", how="left")
    # turn comma separated cast into array, keep only n people for performance reasons
    stream_df = df_str_to_array(stream_df, col='genres')
    stream_df = df_str_to_array(stream_df, col='cast')
    return stream_df


def df_str_to_array(df, col, n=15):
    df[col].fillna("", inplace=True)
    df[col] = df[col].apply(lambda x: x.split(",")[:n])
    # add space to the first value to make consistent but cast could be None
    df[col] = df[col].apply(
        lambda x: [" " + y if i == 0 else y for i, y in enumerate(x)]
    )
    return df
