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
import logging

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("domain", type=str)

    def handle(self, **options):
        if options["domain"] == "Netflix":
            netflix_titles = objects_to_df(NetflixTitles.objects.all())
            genres_null = NetflixGenres.objects.filter(genres__isnull=True)
            actors_null = NetflixActors.objects.filter(cast__isnull=True)
            i = 0
            j = 0
            if len(genres_null) > 0:
                self.stdout.write(f"looking up {len(genres_null)} genres")
                for g in genres_null:
                    result = nd.get_genres(g.netflix_id)
                    if result is not None:
                        g.genres = result["genres"]
                        g.save()
                        i += 1
            if len(actors_null) > 0:
                self.stdout.write(f"looking up {len(actors_null)} acting casts")
                for a in actors_null:
                    nid = int(a.netflix_id)
                    result = nd.get_actors(nid)
                    if result is not None:
                        a.cast = ", ".join(result["actors"])
                        a.save()
                        j += 1
            self.stdout.write(f"Found {i} new genres and {j} new acting casts")
            genre_ids = NetflixGenres.objects.values("netflix_id")
            genre_ids = objects_to_df(genre_ids)["netflix_id"].astype(int)
            netflix_ids = netflix_titles.loc[np.isfinite(netflix_titles["netflix_id"])][
                "netflix_id"
            ].astype(int, errors="ignore")
            genres_missing_ids = list(set(netflix_ids).difference(set(genre_ids)))
            k = 0
            for nid in genres_missing_ids:
                n = nd.save_genres(nid)
                if n:
                    k += 1
            self.stdout.write(f"Scraped {k} genres out of {len(genres_missing_ids)} that weren't in the database.")

        elif options["domain"] == "Goodreads":
            books_null = Books.objects.filter(added_by__isnull=True)
            authors_null = Authors.objects.filter(nationality_chosen__isnull=True)
            self.stdout.write(f"scraping {len(books_null)} books")
            for b in books_null:
                b = append_scraping(b.book_id, wait=3)
                b.save()
        elif options["domain"] == "Spotify":
            streamed = objects_to_df(SpotifyStreaming.objects.all())
            de.update_tracks(streamed)
        elif options["domain"] is None:
            print("No domain specified")
        else:
            d = options["domain"]
            print(f"Bad domain {d} entered.")
