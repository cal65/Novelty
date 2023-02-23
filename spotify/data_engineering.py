import sys
import os
import plotly.graph_objs as go
import pandas as pd
import calendar
import matplotlib.pyplot as plt
from matplotlib import dates
import seaborn as sns
import logging

sys.path.append("../goodreads")

from goodreads.models import SpotifyStreaming, SpotifyTracks

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
ms_per_minute = 60 * 1000


def preprocess(df):
    df["endTime"] = pd.to_datetime(df["endTime"])
    df["endTime"] = df["endTime"].dt.tz_localize("utc").dt.tz_convert("US/Pacific")
    df["date"] = df["endTime"].dt.date
    df["minutes"] = df["msPlayed"] / ms_per_minute

    # processing for merged data
    if "release_year" not in df.columns:
        df["release_year"] = pd.to_numeric(
            df["release_date"].str[:4], downcast="integer"
        )
    df["genre_chosen"] = df["genre_chosen"].fillna("")
    df["genre_simplified"] = simplify_genre(df["genre_chosen"])

    return df


def simplify_genre(genre_list):
    replace_list = [
        "pop",
        "mellow",
        "funk",
        "indie",
        "rap",
        "house",
        "rock",
        "hip hop",
        "reggae",
        "soul",
        "r&b",
    ]
    for genre in replace_list:
        genre_list = [genre if genre in g else g for g in genre_list]
    return genre_list


def convert_to_SpotifyStreaming(row, username):
    """
    Take a row from a Spotify export and write it to database
    """
    djangoSpotifyStreaming = SpotifyStreaming()
    djangoSpotifyStreaming.endTime = row["endTime"]
    djangoSpotifyStreaming.artistName = row["artistName"]
    djangoSpotifyStreaming.trackName = row["trackName"]
    djangoSpotifyStreaming.msPlayed = row["msPlayed"]
    djangoSpotifyStreaming.username = username
    djangoSpotifyStreaming.save()
    return djangoSpotifyStreaming
