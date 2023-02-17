import os
import sys
import requests

import pandas as pd
import numpy as np
import re
import logging
import argparse
import functools
import psycopg2
from datetime import datetime
import networkx as nx
import itertools


def preprocess(file_path, date_col="Date", title_col="Title"):
    df = pd.read_csv(file_path)
    df[date_col] = pd.to_datetime(df[date_col])
    title_values = df[title_col].str.split(":")
    names = []
    secondary = []
    for title in title_values:
        names.append(title[0])
        if len(title) > 1:
            secondary.append(title[1])
        else:
            secondary.append(None)
    df["Name"] = names
    df["Secondary"] = secondary
    return df


def process_kaggle(df):
    df["name"] = df["title"].apply(lambda x: x.split(":")[0])
    countries = df["country"].str.split(", ")
    df["country1"] = [c[0] if isinstance(c, list) else "" for c in countries]
    df["country2"] = [
        c[1] if (isinstance(c, list) and len(c) > 1) else "" for c in countries
    ]
    df["country3"] = [
        c[2] if (isinstance(c, list) and len(c) > 2) else "" for c in countries
    ]
    return df


def unique_non_null(s):
    uniques = s.dropna().unique()
    if len(uniques) < 1:
        return None
    return uniques


def unique_cast(df, name="name"):
    cast_df = pd.pivot_table(
        df, index=[name], values=["cast"], aggfunc=lambda x: unique_non_null(x)
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
                intersections[key] += [common_cast, key2]
        if not intersections[key]:
            intersections.pop(key)
    return intersections


def df_from_set(s):
    df = pd.DataFrame()
    for i in np.arange(0, len(s), 2):
        cast = list(s[i])
        media = s[i + 1]
        df = pd.concat([df, pd.DataFrame({"cast": cast, "show2": [media] * len(cast)})])
    return df


def create_cast_array(intersections):
    cast_array = []
    for k, v in intersections.items():
        df_temp = df_from_set(v)
        df_temp["show1"] = k
        cast_array.append(df_temp)
    cast_df = pd.concat(cast_array)
    return cast_df


def return_unmerged(df, ref_df, df_name_col="Name", ref_name_col="title"):
    """
    Given a Netflix export and a reference database (either actors or genres),
    return the shows that are not in the database
    """
    return list(set(df[df_name_col]).difference(set(ref_df[ref_name_col])))


rapid_api_url = "https://unogs-unogs-v1.p.rapidapi.com/"


def query_title(title: str):
    url = rapid_api_url + "search/titles"

    querystring = {"order_by": "date", "title": title}

    headers = {
        "X-RapidAPI-Key": os.environ["RAPID_API_NETFLIX"],
        "X-RapidAPI-Host": "unogs-unogs-v1.p.rapidapi.com",
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    results_all = response.json()["results"]
    if results_all is None:
        print(f"No response found for {title}")
        return
    results = results_all[0] # take first search
    series_results = pd.Series(results)
    return series_results


def get_actors(netflix_id):
    url = rapid_api_url + "search/people"

    querystring = {"person_type": "Actor", "netflix_id": netflix_id}
    headers = {
        "X-RapidAPI-Key": os.environ["RAPID_API_NETFLIX"],
        "X-RapidAPI-Host": "unogs-unogs-v1.p.rapidapi.com",
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    results = response.json()["results"]
    if results is None:
        print(f"No response found for {netflix_id}")
        return
    actors = [r["full_name"] for r in results]
    actors_df = pd.DataFrame({"netflix_id": [netflix_id], "actors": [actors]})
    return actors_df


def get_genres(netflix_id):
    url = "https://unogs-unogs-v1.p.rapidapi.com/title/genres"

    querystring = {"netflix_id": netflix_id}
    headers = {
        "X-RapidAPI-Key": os.environ["RAPID_API_NETFLIX"],
        "X-RapidAPI-Host": "unogs-unogs-v1.p.rapidapi.com",
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    results = response.json()["results"]
    if results is None:
        print(f"No genre response found for {netflix_id}")
        return
    genres = [r["genre"] for r in results]
    genres = ", ".join(genres)
    genre_df = pd.DataFrame({"netflix_id": [netflix_id], "genre": [genres]})
    return genre_df
