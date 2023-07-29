import os
import requests
import pandas as pd
import numpy as np
import logging
import psycopg2
import networkx as nx
import matplotlib.pyplot as plt

from goodreads.models import NetflixUsers, NetflixTitles, NetflixGenres, NetflixActors

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
        logger.error(error)
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
    """ """
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
        logger.info(f"No response found for {title}")
        return
    results = results_all[0]  # take first search
    series_results = pd.Series(results)
    series_results["title"] = series_results["title"].replace("&#39;", "'")
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
        logger.info(f"No response found for {netflix_id}")
        return
    actors = ', '.join([r["full_name"] for r in results])
    actors_results = pd.Series({"netflix_id": netflix_id, "actors": actors})
    return actors_results


def get_genres(netflix_id):
    url = rapid_api_url + "title/genres"

    querystring = {"netflix_id": netflix_id}
    headers = {
        "X-RapidAPI-Key": os.environ["RAPID_API_NETFLIX"],
        "X-RapidAPI-Host": "unogs-unogs-v1.p.rapidapi.com",
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    if not response.ok:
        logger.info(f"No genre response found for {netflix_id}")
        return

    results = response.json()["results"]
    if results is None:
        logger.info(f"No genre response found for {netflix_id}")
        return
    genres = [r["genre"] for r in results]
    genres = ", ".join(genres)
    genres = genres.replace("&#39;", "'")
    genre_results = pd.Series({"netflix_id": netflix_id, "genres": genres})
    return genre_results


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
        logger.info(f"No genre response found for {netflix_id}")
        return
    try:
        results["title"] = results["title"].replace("&#39;", "'")
    except Exception as e:
        logger.info(
            f"Exception {e} encountered for id {netflix_id} and {results.keys()}"
        )
    return pd.Series(results)


def get_deleted(title):
    url = rapid_api_url + "search/deleted"
    querystring = {"title": title}
    headers = {
        "X-RapidAPI-Key": os.environ["RAPID_API_NETFLIX"],
        "X-RapidAPI-Host": "unogs-unogs-v1.p.rapidapi.com",
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    results_all = response.json()["results"]
    if results_all is None:
        logger.info(f"No response found for {title}")
        return
    results = results_all[0]
    if "netflix_id" in results.keys():
        return results["netflix_id"]
    else:
        return


def format_network(df, title_col="name"):
    cast_dict = unique_cast(df, name=title_col)
    intersections = return_intersections(cast_dict)
    cast_df = create_cast_array(intersections)
    cast_df_m = pd.melt(cast_df, id_vars=["show1"])
    cast_df_m = cast_df_m[cast_df_m["variable"] == "cast"]
    G = nx.from_pandas_edgelist(
        cast_df_m, source="show1", target="value", edge_attr="variable"
    )
    return G


def plot_network(graph, cast_df):
    pos = nx.kamada_kawai_layout(graph, scale=0.2)
    # colors
    color_mapper = {n: int(n in pd.unique(cast_df["show1"])) for n in graph.nodes()}
    cm2 = {1: "red", 0: "blue"}
    # position of text
    pos_moved = pos.copy()
    for k, v in pos_moved.items():
        pos_moved[k] = pos_moved[k] + [0, 0.005]
    f, ax = plt.subplots(figsize=(30, 30))
    plt.style.use("ggplot")

    nodes = nx.draw_networkx_nodes(
        graph, pos, node_color=[cm2[c] for c in color_mapper.values()], alpha=0.8
    )
    nodes.set_edgecolor("k")
    nx.draw_networkx_labels(graph, pos_moved, font_size=15, alpha=0.8)

    nx.draw_networkx_edges(graph, pos, width=1.0, alpha=0.2)
    return f


def ingest_netflix(df, user):
    """
    See what was in the database for the user. Delete what was there.
    Replace with this new one
    """
    NetflixUsers.objects.filter(username=user).delete()

    for i, row in df.iterrows():
        netflix_Entry = NetflixUsers()
        netflix_Entry.title = row["title"]
        netflix_Entry.date = row["date"]
        netflix_Entry.username = user
        netflix_Entry.save()
    return


def codify_title(title):
    splits = title.split(":")
    splits = [s.strip() for s in splits]
    seas_words = ("Season", "Book", "Chapter", "Volume", "Part", "Collection")
    season_bool = [(t.startswith(seas_words)) | ("Series" in t) for t in splits]
    episode_bool = [t.startswith("Episode") for t in splits]

    # exception 1: Stranger Things:
    if splits[0] == "Stranger Things":
        name = splits[0]
        if len(splits) > 2:
            season = splits[-3]
            episode = ": ".join(splits[-2:])
        else:
            season = ""
            episode = ""
    elif any(season_bool):
        season_index = season_bool.index(True)
        season = splits[season_index]
        if season_index > 1:
            name = ": ".join(splits[:season_index])
        else:
            name = splits[0]
        if (len(splits) - season_index) > 1:
            episode = ": ".join(splits[season_index + 1 :])
        else:
            episode = splits[-1]
    elif any(episode_bool):
        episode_index = episode_bool.index(True)
        # this will apply the colon join only if episode index is not last  index
        episode = ": ".join(splits[episode_index:])
        if len(splits) > 2:
            name = splits[0]
            season = splits[1]
        else:
            name = splits[0]
            season = ""
    elif len(splits) == 2:
        name = splits[0]
        season = ""
        episode = splits[1]
    elif len(splits) == 1:
        name = title
        season = ""
        episode = ""
    elif len(splits) == 3:
        name = splits[0]
        season = splits[1]
        episode = splits[2]
    else:
        name = ": ".join(splits[:-1])
        season = ""
        episode = splits[-1]
    return pd.Series({"name": name, "season": season, "episode": episode})


def net_merge(df, titles_df, left, right, ids, how="inner"):
    df = df.copy()
    if ids is not None:
        df = df.loc[~df["id"].isin(ids)]
    df = pd.merge(
        df, titles_df, left_on=left, right_on=right, suffixes=("", "_remove"), how=how
    )
    df.drop([c for c in df.columns if "remove" in c], axis=1, inplace=True)
    return df


def reformat_special(df, user):
    """
    Special reformat function for different Netflix export.
    This occurs when a Netflix download returns an error.
    """
    df = df.copy()
    df = df.loc[df["Profile Name"] == user]
    df = df.loc[df["Latest Bookmark"] != "Not latest view"]
    df["Start Time"] = pd.to_datetime(df["Start Time"])
    df["Date"] = df["Start Time"].dt.date
    return df


def pipeline_steps(df):
    """
    Full pipeline given df from netflix export csv
    Step 1: Merge based on the raw title in Netflix export with database titles
    Step 2: Merge based on the stem of the title in export with database titles
    Step 3: Merge based on the stem of the title in export with stem of title in database
    """
    df = df.copy()
    df = df[df["title"] != " "]
    df = df[pd.notnull(df["title"])]
    df.reset_index(drop=True, inplace=True)
    df["id"] = np.arange(0, len(df))
    df["date"] = pd.to_datetime(df["date"])
    # split the raw Netflix show title into Name, Season and Episode. Add new columns
    split_titles_df = pd.DataFrame([codify_title(t) for t in df["title"]])
    df = pd.concat([df, split_titles_df], axis=1)
    titles_df = pd.DataFrame.from_records(NetflixTitles.objects.all().values())

    # match title with full title. This gets movies and comedy specials
    step1 = net_merge(df, titles_df, left="title", right="title", ids=None)
    # match cleared out name with title. This matches TV shows
    step2 = net_merge(df, titles_df, left="name", right="title", ids=step1["id"])
    # match the rest
    step1_2_ids = pd.unique(step1["id"].append(step2["id"]))
    titles_df["name"] = titles_df["title"].apply(lambda x: x.split(":")[0])
    step3 = net_merge(
        df, titles_df, left="name", right="name", ids=step1_2_ids, how="left"
    )
    df_concat = pd.concat([step1, step2, step3], axis=0).sort_values("id")
    return df_concat


def save_titles(series_results):
    nt = NetflixTitles()
    nt.title = series_results["title"]
    nt.netflix_id = series_results["netflix_id"]
    nt.title_type = series_results["title_type"]
    nt.release_year = series_results["year"]
    nt.default_image = series_results.get("default_image", series_results.get("img", ""))
    alt_votes = series_results.get("alt_votes", '')
    nt.alt_votes = 0 if alt_votes == "" else alt_votes
    nt.save()
    return nt


def save_actors(actors_results):
    na = NetflixActors()
    if actors_results is not None:
        na.netflix_id = actors_results["netflix_id"]
        na.cast = actors_results["actors"]
        na.save()
    return na


def save_genres(genre_results):
    ng = NetflixGenres()
    if genre_results is not None:
        try:
            ng.netflix_id = genre_results["netflix_id"]
            ng.genres = genre_results["genres"]
            ng.save()
        except Exception as e:
            logger.info(f"Complete fail {e} for results {genre_results}")
            return None
    return ng


def actors_and_genres(netflix_id):
    actors_results = get_actors(netflix_id)
    if actors_results is not None:
        save_actors(actors_results)
    #
    genre_results = get_genres(netflix_id)
    if genre_results is not None:
        save_genres(genre_results)
    return


def lookup_and_insert(title):
    series_results = query_title(title)
    if series_results is None:
        deleted_id = get_deleted(title)
        series_results = get_details(deleted_id)
    # add line if string difference is too far elif series_result['title']

    if (series_results is None) | ('netflix_id' not in series_results.keys()):
        logger.info(f"No active or deleted Netflix info found for {title}")
        return

    netflix_id = series_results["netflix_id"]
    logger.info(f"Saving result of {title} having queried {series_results['title']}")
    save_titles(series_results)
    #
    actors_and_genres(netflix_id)

    return
