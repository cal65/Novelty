import pandas as pd
import numpy as np
from spotify.plotting.plotting import objects_to_df
from goodreads.models import NetflixGenres
from netflix.plotting import plotting as nplot


def group_person(df):
    df_group = pd.pivot_table(
        df, index=["name", "title_type", "netflix_id"], values=["episode"], aggfunc=len
    )
    return df_group


def combine_people(df1, df2, name1, name2):
    combined_shows = pd.concat([df1, df2], axis=1).reset_index()
    combined_shows.columns = ["name", "title_type", "netflix_id", name1, name2]
    genres_df = objects_to_df(NetflixGenres.objects.all())
    combined_shows = pd.merge(combined_shows, genres_df, on="netflix_id", how="left")
    return combined_shows


genre_numerical_mapper = {
    "Reality": -1,
    "Dramas": 1,
    "Comedies": -0.7,
    "Stand-Up Comedy": -0.5,
    "Documentaries": 0.6,
    "Docuseries": 0.9,
    "Mystery": -0.1,
    "British": -0.2,
    "Korean": 0,
    "Romantic Comedies": -0.4,
    "Sci-Fi & Fantasy": 0.1,
    "Crime": 1,
    "Horror": 0.4,
    "Action & Adventure": 0.3,
    "International": 0,
    "Romantic": -0.2,
    "": 0,
    "Crime Action & Adventure": 0.3,
    "Kids": -0.8,
    "Thrillers": 0.9,
    "Stand-Up Comedy & Talk": -0.1,
    "Special Interest": 0,
    "Anime": -0.2,
}


def post_combination(combined_shows, name1, name2):
    combined_shows["genre_chosen"] = combined_shows["genres"].apply(
        nplot.simplify_genres
    )
    combined_shows["both"] = pd.notnull(combined_shows[name1]) & pd.notnull(
        combined_shows[name2]
    )
    combined_shows["genre_num"] = (
        combined_shows["genre_chosen"].map(genre_numerical_mapper).fillna(0)
    )
    return combined_shows
