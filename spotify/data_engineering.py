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



def convert_to_SpotifyStreaming(row, username):
    """
    Take a row from a Spotify export and write it to database
    """
    djangoSpotifyStreaming = SpotifyStreaming()
    djangoSpotifyStreaming.endtime = row["endTime"]
    djangoSpotifyStreaming.artistname = row["artistName"]
    djangoSpotifyStreaming.trackname = row["trackName"]
    djangoSpotifyStreaming.msplayed = row["msPlayed"]
    djangoSpotifyStreaming.username = username
    djangoSpotifyStreaming.save()
    return djangoSpotifyStreaming
