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

def load_streaming(username):
    return get_data(userdata_query(username))


def main(username):
    df = get_data(tracks_query(username))
    logger.info(f"Spotify data read with {len(df)} rows \n : {df.head()}")
    df = preprocess(df)