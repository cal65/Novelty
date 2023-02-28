import os
import warnings
import argparse
import geopandas as gpd

warnings.simplefilter(action="ignore", category=FutureWarning)
import pandas as pd
import numpy as np
from pandas.api.types import is_numeric_dtype
import psycopg2
import matplotlib
import seaborn as sns
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots


from pandas.api.types import CategoricalDtype

import logging

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

post_pass = os.getenv("cal65_pass")
matplotlib.pyplot.switch_backend("Agg")

ms_per_minute = 60 * 1000

def get_data(query, database="goodreads"):
    conn = psycopg2.connect(
        host="localhost", database=database, user="cal65", password=post_pass
    )
    try:
        df = pd.read_sql(query, con=conn)
        logger.info(f"Returning data from query with nrows {len(df)}")
        return df
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return


def userdata_query(username):
    query = f"""
    select 
    endTime, artistName, trackName, msPlayed
    from goodreads_spotifyStreaming 
    where username = '{username}'
    """
    return query

def tracks_query(username):
    query = f""" 
    select 
    endTime, 
    stream.artistName, 
    stream.trackName, 
    msPlayed,
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
    from goodreads_spotifyStreaming stream 
    left join goodreads_spotifytracks tracks
    on stream.artistName = tracks.artistName
    and stream.trackName = tracks.trackName
    where  stream.username = '{username}'
    """
    return query
def preprocess(df):
    df["endTime"] = pd.to_datetime(df["endTime"])
    df['endTime'] = df['endTime'].dt.tz_localize('utc').dt.tz_convert('US/Pacific')
    df["date"] = df["endTime"].dt.date
    df["minutes"] = df["msPlayed"] / ms_per_minute

    # processing for merged data
    if "release_year" not in df.columns:
        df["release_year"] = pd.to_numeric(
            df["release_date"].str[:4], downcast="integer"
        )
    df['genre_chosen'] = df['genre_chosen'].fillna('')
    df['genre_simplified'] = simplify_genre(df['genre_chosen'])

    df['played_ratio'] = df['minutes'] / df['duration']

    return df


def format_song_day(df, artist_col, song_col, date_col):
    df_song_day = pd.DataFrame(
        df.groupby([artist_col, song_col, date_col]).size()
    ).reset_index()
    df_song_day.rename(columns={0: "n"}, inplace=True)
    top_artists = df[artist_col].value_counts().index[:10]
    df_song_day_select = df_song_day[df_song_day[artist_col].isin(top_artists)]
    return df_song_day_select


def plot_song_day(df, artist_col, song_col, date_col):
    num_songs = len(pd.unique(df[song_col]))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[date_col],
            y=df[song_col] + ", " + df[artist_col],
            text=df["n"],
            mode="markers",
            marker={"size": df["n"] * num_songs / 5, "color": "DarkRed"},
            hovertemplate="name: %{y} <br>number: %{text} <br> date: %{x} <extra></extra>",
        )
    )

    fig.update_layout(
        title="Song Plays",
        width=2000,
        height=max(
            500, min(num_songs * 20, 3000)
        ),  # ensure that the plot is between 100 and 3000
        showlegend=True,
    )
    return fig


def get_top(df, column, n):
    return df[column].value_counts().index[:n]


def load_streaming(username):
    return get_data(userdata_query(username))


def main(username):
    df = get_data(tracks_query(username))
    logger.info(f"Spotify data read with {len(df)} rows \n : {df.head()}")
    df = preprocess(df)