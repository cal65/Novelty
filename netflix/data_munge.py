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

def preprocess(file_path, date_col='Date', title_col='Title'):
    df = pd.read_csv(file_path)
    df[date_col] = pd.to_datetime(df[date_col])
    title_values = df[title_col].str.split(':')
    df['Name'] = [t[0] for t in title_values]
    df['Secondary'] = ['' if len(t) < 2 else t[1] for t in title_values]

    return df

def plot(df):
    fig = px.scatter(df, x='Date', y='Name', color='country')
    fig.update_layout(yaxis=dict(tickmode='linear'))
    fig.update_layout(legend=dict(
        yanchor="top",
        xanchor="center",
    ))
    fig.show()

def unique_non_null(s):
    uniques = s.dropna().unique()
    if len(uniques) < 1:
        return None
    return uniques

def unique_cast(df):
    cast_df = pd.pivot_table(df, index=['Name'], values=['cast'], aggfunc=lambda x: unique_non_null(x))
    # the unique aggfunc can return a string or a list
    joined_arrays = cast_df[cast_df['cast'].apply(
        lambda x: isinstance(x, np.ndarray))]['cast'].apply(lambda x: ', '.join(x))
    # for the list, join them into one string
    cast_df.loc[cast_df['cast'].apply(
        lambda x: isinstance(x, np.ndarray)), 'cast'] = joined_arrays
    # split the strings into an array then turn into a set
    cast_df['cast_set'] = cast_df['cast'].str.split(', ').apply(set)
    cast_df.drop(columns=['cast'], inplace=True)
    cast_dict = cast_df.T.to_dict('records')[0]
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
