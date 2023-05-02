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
    def handle(self, **options):
        users_goodreads = list(ExportData.objects.order_by().values_list('username', flat=True).distinct())
        for user in users_goodreads:
            gplot.main(user)
        users_spotify = list(SpotifyStreaming.objects.order_by().values_list('username', flat=True).distinct())
        for user in users_spotify:
            splot.main(user)
        users_netflix = list(NetflixUsers.objects.order_by().values_list('username', flat=True).distinct())
        for user in users_netflix:
            nplot.main(user)

