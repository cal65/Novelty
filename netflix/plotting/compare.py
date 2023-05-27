import pandas as pd
import numpy as np
from spotify.plotting.plotting import objects_to_df
from goodreads.models import NetflixGenres

def group_person(df):
    df_group = pd.pivot_table(df,
                           index=['name', 'title_type', 'netflix_id'],
                           values = ['episode'], aggfunc=len)
    return df_group

def combine_people(df1, df2):
    combined_shows = pd.concat([df1, df2], axis=1).reset_index()
    combined_shows.columns = ['name', 'title_type', 'netflix_id', 'n_jenny', 'n_cal']
    genres_df = objects_to_df(NetflixGenres.objects.all())
    combined_shows = pd.merge(combined_shows, genres_df, on='netflix_id', how='left')
    return combined_shows