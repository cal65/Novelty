import os
import pandas as pd
import numpy as np
import psycopg2
import matplotlib
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import calendar
import matplotlib.pyplot as plt
from matplotlib import dates
import seaborn as sns
import plotly.graph_objs as go
from datetime import timedelta


def split_title(title):
    primary = ""
    secondary = ""
    return primary, secondary


def plot_genres(df):
    # df should be already formatted, genres cleaned up
    # only tv shows or movies
    df_count = pd.DataFrame(
        df.groupby(["Name", "genre", "type"], as_index=False).size()
    )
    df_genre_count = pd.DataFrame(
        df.groupby("genre", as_index=False).size()
    ).sort_values("size")
    fig = go.Figure()
    df_shows = df_count.loc[df_count["type"] != "Movie"]
    for g in df_genre_count["genre"]:
        df_sub = df_shows.loc[df_shows["genre"] == g]

        fig.add_trace(
            go.Bar(
                x=df_sub["size"],
                y=df_sub["genre"],
                customdata=df_sub["Name"],
                text=df_sub["Name"],
                hovertemplate="Genre: %{y} <br> Title: %{customdata} <br> Count: %{x}",
                name=g,
                orientation="h",
                insidetextanchor="middle",
            )
        )
    fig.update_layout(barmode="stack", title="Netflix TV Genres")
