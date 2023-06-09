from django.core.management.base import BaseCommand

from goodreads.models import ExportData, NetflixUsers, SpotifyStreaming
from goodreads.plotting import plotting as gplot
from spotify.plotting import plotting as splot
from netflix.plotting import plotting as nplot
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
        parser.add_argument(
            "domain",
            type=str,
            help="Optional domain of either Goodreads, Spotify, Netflix, indicates run plots for just that domain.",
        )

    def handle(self, **options):
        domain = (
            options["domain"]
            if options["domain"] is not None
            else ["Goodreads", "Spotify", "Netflix"]
        )

        if "Goodreads" in domain:
            users_goodreads = list(
                ExportData.objects.order_by()
                .values_list("username", flat=True)
                .distinct()
            )
            print(f"Running goodreads for {len(users_goodreads)} users")
            for user in users_goodreads:
                gplot.main(user)

        if "Spotify" in domain:
            users_spotify = list(
                SpotifyStreaming.objects.order_by()
                .values_list("username", flat=True)
                .distinct()
            )
            print(f"Running spotify for {len(users_spotify)} users")
            for user in users_spotify:
                splot.main(user)

        if "Netflix" in domain:
            users_netflix = list(
                NetflixUsers.objects.order_by()
                .values_list("username", flat=True)
                .distinct()
            )
            print(f"Running netflix for {len(users_netflix)} users")
            for user in users_netflix:
                try:
                    nplot.main(user)
                except Exception as e:
                    print(f"Exception {e} for user {user}")
