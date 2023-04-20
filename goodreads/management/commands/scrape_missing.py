from django.core.management.base import BaseCommand

from goodreads.models import NetflixGenres, NetflixUsers, NetflixActors, Books, Authors
from netflix import data_munge as nd
from goodreads.scripts.append_to_export import append_scraping
import pandas as pd
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
            genres_null = NetflixGenres.objects.filter(genres__isnull=True)
            actors_null = NetflixActors.objects.filter(cast__isnull=True)
            i = 0
            j = 0
            if len(genres_null) > 0:
                print(f"looking up {len(genres_null)} genres")
                for g in genres_null:
                    result = nd.get_genres(g.netflix_id)
                    if result is not None:
                        g.genres = result["genres"]
                        g.save()
                        i += 1
            if len(actors_null) > 0:
                self.stdout.write(f"looking up {len(actors_null)} genres")
                for a in actors_null:
                    nid = int(a.netflix_id)
                    result = nd.get_actors(nid)
                    if result is not None:
                        a.cast = ", ".join(result["actors"])
                        a.save()
                        j += 1
            print(f"Found {i} new genres and {j} new acting casts")
            df = pd.DataFrame.from_records(NetflixActors.objects.all().values())
            df.head().to_csv("debug.csv")
        if options["domain"] == "Goodreads":
            books_null = Books.objects.filter(added_by__isnull=True)
            authors_null = Authors.objects.filter(nationality_chosen__isnull=True)
            self.stdout.write(f"scraping {len(books_null)} books")
            for b in books_null:
                b = append_scraping(b.book_id, wait=3)
                b.save()
