from django.core.management.base import BaseCommand

from goodreads.models import NetflixGenres, NetflixUsers, NetflixActors, Books, Authors
from netflix import data_munge as nd
import pandas as pd

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('domain', nargs='+', type=str)

    def handle(self, **options):
        if options["domain"] == 'Netflix':
            genres_null = NetflixGenres.objects.filter(genres__isnull=True)
            actors_null = NetflixActors.objects.filter(cast__isnull=True)
            i = 0
            j = 0
            if len(genres_null) > 0:
                print(f"looking up {len(genres_null)} genres")
                for g in genres_null:
                    result = nd.get_genres(g.netflix_id)
                    if result is not None:
                        g.genres = result['genres']
                        g.save()
                        i += 1
            if len(actors_null) > 0:
                print(f"looking up {len(actors_null)} genres")
                for a in actors_null:
                    nid = int(a.netflix_id)
                    result = nd.get_actors(nid)
                    if result is not None:
                        a.cast = ', '.join(result['actors'])
                        a.save()
                        j += 1
            print(f"Found {i} new genres and {j} new acting casts")
            df = pd.DataFrame.from_records(NetflixActors.objects.all().values())
            df.head().to_csv('debug.csv')