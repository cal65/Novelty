import sys
import os
import pandas as pd
import logging
import signal
import spotipy
from spotipy.oauth2 import SpotifyOAuth

sys.path.append("../goodreads")

from goodreads.models import SpotifyStreaming, SpotifyTracks

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

SPOTIPY_CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
SPOTIPY_CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
os.environ["SPOTIPY_CLIENT_ID"] = os.environ["SPOTIFY_CLIENT_ID"]
os.environ["SPOTIPY_CLIENT_SECRET"] = os.environ["SPOTIFY_CLIENT_SECRET"]
os.environ["SPOTIPY_REDIRECT_URI"] = "http://localhost:1410/"
scope = ["user-library-read", "user-read-recently-played"]

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))


class Timeout:
    """Timeout class using ALARM signal."""

    class Timeout(Exception):
        pass

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)  # disable alarm

    def raise_timeout(self, *args):
        raise Timeout.Timeout()


def convert_to_SpotifyStreaming(row, username):
    """
    Take a row from a Spotify export and write it to database
    """
    djangoSpotifyStreaming = SpotifyStreaming()
    djangoSpotifyStreaming.endtime = row["endTime"]
    djangoSpotifyStreaming.artistname = row["artistName"]
    djangoSpotifyStreaming.trackname = row["trackName"]
    djangoSpotifyStreaming.msplayed = row["msPlayed"]
    djangoSpotifyStreaming.username = username
    djangoSpotifyStreaming.save()
    return djangoSpotifyStreaming

def lowercase_cols(df):
    df = df.copy()
    df.columns = [col.lower() for col in df.columns]
    return df

def identify_new():
    return

def get_historical_track_info_from_id(
    track_id: str, trackName: str, artistName: str, searchType: str = "track"
):
    """
    output: series with uri, name, artist, duration (min), popularity, release date, genres, album
    """
    empty_series = pd.Series(
        {
            "uri": None,
            "name": trackName,
            "artist": artistName,
            "duration": None,
            "popularity": None,
            "release_date": "",
            "explicit": False,
            "is_local": None,
            "genres": [],
            "trackName": trackName,
            "artistName": artistName,
            "podcast": False,
        }
    )
    if track_id is None:
        empty_series["uri"] = str(hash(trackName + artistName))
        return empty_series
    else:
        try:
            with Timeout(6):
                if searchType == "track":
                    track_info_dict = sp.track(track_id)
                    track_info_series = pd.Series(
                        {
                            "uri": track_id,
                            "name": track_info_dict["name"],
                            "artist": track_info_dict["artists"][0]["name"],
                            "duration": track_info_dict["duration_ms"] / ms_per_minute,
                            "popularity": track_info_dict["popularity"],
                            "release_date": track_info_dict["album"]["release_date"],
                            "genres": sp.artist(track_info_dict["artists"][0]["id"])[
                                "genres"
                            ],
                            "album": track_info_dict["album"]["name"],
                            "explicit": track_info_dict["explicit"],
                            "trackName": trackName,
                            "artistName": artistName,
                            "podcast": False,
                        }
                    )
                elif searchType == "show":
                    track_info_dict = sp.show(track_id)
                    track_info_series = pd.Series(
                        {
                            "uri": track_id,
                            "name": track_info_dict["name"],
                            "artist": track_info_dict["publisher"],
                            "duration": None,
                            "popularity": None,
                            "release_date": None,
                            "genres": None,
                            "album": None,
                            "explicit": track_info_dict["explicit"],
                            "trackName": trackName,
                            "artistName": artistName,
                            "podcast": True,
                        }
                    )
        except Exception as e:
            logger.info(f"Error {e} for {track_id}")
            return None

    return track_info_series


def search_by_names(trackName: str, artistName: str, searchType: str = "track") -> str:
    """
    input: trackName, artistName
    output: id
    """

    if (not isinstance(trackName, str)) | (not isinstance(artistName, str)):
        raise TypeError

    try:
        with Timeout(6):
            search_items = sp.search(
                trackName + " " + artistName, type=searchType, limit=3
            )[f"{searchType}s"]["items"]
            # searchType could be track or show, and the resulting dictionary will have "tracks" or "shows"
    except:
        logger.info(f"Time out error for {trackName} and {artistName}")
        return None

    if len(search_items) < 1:
        logger.info(
            "No match found for " + trackName + ", " + artistName + " and " + searchType
        )
        return None

    # call get_historical_track_info which takes a search dictionary and returns the results
    uri = search_items[0]["id"]

    return uri


def get_audio(uris):
    audio_fts = []
    for uid in uris:
        if uid is not None:
            try:
                with Timeout(3):
                    feat = sp.audio_features(uid)[0]
            except:
                print(f"Time out error for {uid}")
        audio_fts.append(pd.Series(feat))
    return audio_fts


def merge_tracks(
    data,
    track_df,
    d_artist="artistName",
    d_song="trackname",
    t_artist="artistName",
    t_song="trackname",
):
    """
    One of the first steps in the pipeline. Merge data import with existing searched tracks on artist and song names
    """
    data = data[[d_artist, d_song, "msPlayed"]]  # no need to keep the other columns
    data = pd.pivot_table(
        data, index=[d_artist, d_song], values="msPlayed", aggfunc=sum
    ).reset_index()
    tracks_merged = pd.merge(
        data,
        track_df,
        left_on=[d_artist, d_song],
        right_on=[t_artist, t_song],
        how="left",
    )

    return tracks_merged

