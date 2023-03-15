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
import matplotlib.pyplot as plt

from goodreads.models import NetflixUsers

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


rapid_api_url = "https://unogs-unogs-v1.p.rapidapi.com/"
post_pass = os.getenv("cal65_pass")


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
    title, date, username
    from goodreads_netflixuser
    where username = '{username}'
    """
    return query

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



def query_title(title: str, type=None):
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
    url = rapid_api_url + "title/genres"

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


def get_details(netflix_id):
    url = rapid_api_url + "title/details"

    querystring = {"netflix_id": netflix_id}
    headers = {
        "X-RapidAPI-Key": os.environ["RAPID_API_NETFLIX"],
        "X-RapidAPI-Host": "unogs-unogs-v1.p.rapidapi.com",
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    results = response.json()
    if results is None:
        print(f"No genre response found for {netflix_id}")
        return
    # details_df = pd.DataFrame({"netflix_id": [netflix_id], "genre": [genres]})
    return results

def get_deleted(title):
    url = rapid_api_url + "search/deleted"
    querystring = {"title": title}
    headers = {
        "X-RapidAPI-Key": os.environ["RAPID_API_NETFLIX"],
        "X-RapidAPI-Host": "unogs-unogs-v1.p.rapidapi.com",
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    results_all = response.json()['results']
    if results_all is None:
        print(f"No response found for {title}")
        return
    results = results_all[0]
    if 'netflix_id' in results.keys():
        return results['netflix_id']
    else:
        return

def format_network(df):
    cast_dict = unique_cast(df, name='title')
    intersections = return_intersections(cast_dict)
    cast_df = create_cast_array(intersections)
    cast_df_m = pd.melt(cast_df, id_vars=['show1'])
    cast_df_m = cast_df_m[cast_df_m['variable'] == 'cast']
    G = nx.from_pandas_edgelist(cast_df_m,
                                source='show1', target='value', edge_attr='variable')
    return G

def plot_network(G, cast_df):
    pos = nx.kamada_kawai_layout(G, scale=.2)
    # colors
    color_mapper = {n: int(n in pd.unique(cast_df['show1'])) for n in G.nodes()}
    cm2 = {1: 'red', 0: 'blue'}
    # position of text
    pos_moved = pos.copy()
    for k, v in pos_moved.items():
        pos_moved[k] = pos_moved[k] + [0, .005]
    f, ax = plt.subplots(figsize=(30, 30))
    plt.style.use('ggplot')

    nodes = nx.draw_networkx_nodes(G, pos, node_color=[cm2[c] for c in color_mapper.values()],
                                   alpha=0.8)
    nodes.set_edgecolor('k')
    nx.draw_networkx_labels(G, pos_moved, font_size=15, alpha=0.8)

    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.2)
    return f

def ingest_netflix(df, user):
    """
    See what was in the database for the user. Delete what was there.
    Replace with this new one
    """
    NetflixUsers.objects.filter(username=user).delete()

    for row in df.iterrows():
        netflix_Entry = NetflixUsers()
        netflix_Entry.title = row["title"]
        netflix_Entry.date = row["date"]
        netflix_Entry.username = user
        netflix_Entry.save()
    return