from django.core.management.base import BaseCommand

from goodreads.models import (
    NetflixTitles,
    NetflixGenres,
    NetflixUsers,
    NetflixActors,
    Books,
    Authors,
    SpotifyStreaming,
    SpotifyTracks,
)
from netflix import data_munge as nd
from spotify.plotting.plotting import objects_to_df
from goodreads.scripts.append_to_export import append_scraping
from spotify import data_engineering as de
import pandas as pd
import numpy as np


def get_dupes(nid):
    netflix_titles = objects_to_df(NetflixTitles.objects.all())
    titles = netflix_titles.loc[netflix_titles["netflix_id"] == nid].title.to_list()
    print(netflix_titles.loc[netflix_titles["netflix_id"] == nid])
    return titles


def reconcile_titles(nid, titles):
    correct_title = nd.get_details(int(nid)).title
    if correct_title not in titles:
        print(f"The title {correct_title} is not in your titles list")
    else:
        titles.remove(correct_title)
    correct_ids = []
    for t in titles:
        cid = nd.get_deleted(t)
        if cid is None:
            print(f"No response for {t}")
            next
        correct_ids.append(cid)
        nt = NetflixTitles.objects.filter(title=t).update(netflix_id=cid)
        print(f"{t} updated in database")
    return correct_ids
