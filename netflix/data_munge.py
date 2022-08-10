import os
import sys

import pandas as pd
import numpy as np
import re
import logging
import argparse
import functools
import psycopg2
import plotly.express as px
from datetime import datetime
from plotting.plotting import get_data, refdata_query

import logging

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def preprocess(file_path, date_col="Date", title_col="Title"):
    df = pd.read_csv(file_path)
    df[date_col] = pd.to_datetime(df[date_col])
    title_values = df[title_col].str.split(":")
    df.columns = [c.lower() for c in df.columns]
    df["name"] = [t[0] for t in title_values]
    df["secondary"] = ["" if len(t) < 2 else t[1] for t in title_values]

    return df


def plot(df, username):
    fig = px.scatter(df, x="date", y="name", color="country1")
    unique_titles = pd.unique(df['title'])
    fig.update_layout(yaxis=dict(tickmode="linear"))
    fig.update_layout(
        legend=dict(
            yanchor="top",
            xanchor="center",
        ),
        height=len(unique_titles) * 3
    )
    fig.show()
    file_path = f"static/Graphs/{username}/shows_plot_{username}.html"
    save_fig(fig, file_path)


def unique_non_null(s):
    uniques = s.dropna().unique()
    if len(uniques) < 1:
        return None
    return uniques


def unique_cast(df):
    cast_df = pd.pivot_table(
        df, index=["name"], values=["cast"], aggfunc=lambda x: unique_non_null(x)
    )
    # the unique aggfunc can return a string or a list
    joined_arrays = cast_df[cast_df["cast"].apply(lambda x: isinstance(x, np.ndarray))][
        "cast"
    ].apply(lambda x: ", ".join(x))
    # for the list, join them into one string
    cast_df.loc[
        cast_df["cast"].apply(lambda x: isinstance(x, np.ndarray)), "cast"
    ] = joined_arrays
    # split the strings into an array then turn into a set
    cast_df["cast_set"] = cast_df["cast"].str.split(", ").apply(set)
    cast_df.drop(columns=["cast"], inplace=True)
    cast_dict = cast_df.T.to_dict("records")[0]
    return cast_dict


def return_intersections(cast_dict):
    keys = cast_dict.keys()
    intersections = {}
    for key in keys:
        other_keys = [k for k in keys if k != key]
        cast = cast_dict[key]
        intersections[key] = []
        for key2 in other_keys:
            common_cast = cast.intersection(cast_dict[key2])
            if len(common_cast) > 0:
                intersections[key] += common_cast
    return intersections

def save_fig(fig, file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    fig.write_html(file=file_path)

def main(file_path, username):
    df = preprocess(file_path)
    netflix_ref = get_data(refdata_query())
    df = pd.merge(df, netflix_ref, on='name')
    plot(df, username)
    cast_dict = unique_cast(df)
    intersection = return_intersections(cast_dict)
    logger.info(f"intersections: {intersection}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file_path",
        action="store",
        type=str,
        help="The csv filepath to read from",
    )
    parser.add_argument(
        "--username",
        dest="username",
        help="The username which data is queried from goodreads.netflixusers",
    )

    args = parser.parse_args()
    file_path = args.file_path
    username = args.username

    main(file_path, username)