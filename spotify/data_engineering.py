import sys
import os
import pandas as pd
import logging
import signal
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

sys.path.append("../goodreads")

from goodreads.models import SpotifyStreaming, SpotifyTracks
from spotify.plotting import plotting as splot

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

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET
    )
)

ms_per_minute = 60 * 1000


# class Timeout:
#     """Timeout class using ALARM signal."""
#
#     class Timeout(Exception):
#         pass
#
#     def __init__(self, sec):
#         self.sec = sec
#
#     def __enter__(self):
#         signal.signal(signal.SIGALRM, self.raise_timeout)
#         signal.alarm(self.sec)
#
#     def __exit__(self, *args):
#         signal.alarm(0)  # disable alarm
#
#     def raise_timeout(self, *args):
#         raise Timeout.Timeout()


def convert_to_SpotifyStreaming(row, username):
    """
    Take a row from a Spotify export after its columns have been made lowercase and write it to database
    """
    djangoSpotifyStreaming = SpotifyStreaming()
    djangoSpotifyStreaming.endtime = row["endtime"]
    djangoSpotifyStreaming.artistname = row["artistname"][:250]
    djangoSpotifyStreaming.trackname = row["trackname"][:250]
    djangoSpotifyStreaming.msplayed = row["msplayed"]
    djangoSpotifyStreaming.username = username
    djangoSpotifyStreaming.save()
    return djangoSpotifyStreaming


def convert_to_SpotifyTrack(track_series):
    djangoSpotifyTrack = SpotifyTracks()
    djangoSpotifyTrack.uri = track_series["uri"]
    djangoSpotifyTrack.name = track_series["name"][:250]
    djangoSpotifyTrack.artist = track_series["artist"][:250]
    djangoSpotifyTrack.duration = track_series["duration"]
    djangoSpotifyTrack.popularity = track_series["popularity"]
    djangoSpotifyTrack.release_date = track_series["release_date"]
    djangoSpotifyTrack.genres = track_series["genres"]
    djangoSpotifyTrack.album = track_series["album"]
    djangoSpotifyTrack.explicit = track_series["explicit"]
    djangoSpotifyTrack.trackname = track_series["trackname"]
    djangoSpotifyTrack.artistname = track_series["artistname"]
    djangoSpotifyTrack.podcast = track_series["podcast"]
    djangoSpotifyTrack.genre_chosen = track_series["genre_chosen"]
    djangoSpotifyTrack.save()
    return djangoSpotifyTrack


def lowercase_cols(df):
    df = df.copy()
    df.columns = [col.lower() for col in df.columns]
    return df


def identify_new(df, track_df, track_col="trackname", artist_col="artistname"):
    df = lowercase_cols(df)
    tracks_merged = merge_tracks(
        df,
        track_df,
        d_artist=artist_col,
        d_song=track_col,
        t_artist=artist_col,
        t_song=track_col,
    )
    logger.info(f"tracks merged looks like {tracks_merged.head()}")
    df_unmerged = tracks_merged.loc[pd.isnull(tracks_merged["uri"])]
    return df_unmerged


def get_historical_track_info_from_id(
    track_id: str, trackname: str, artistname: str, searchType: str = "track"
):
    """
    output: series with uri, name, artist, duration (min), popularity, release date, genres, album
    """
    empty_series = pd.Series(
        {
            "uri": None,
            "name": trackname,
            "artist": artistname,
            "duration": 0,
            "popularity": 0,
            "release_date": "",
            "explicit": False,
            "genres": [],
            "album": "",
            "trackname": trackname,
            "artistname": artistname,
            "podcast": False,
            "genre_chosen": "",
        }
    )
    if track_id is None:
        empty_series["uri"] = str(hash(trackname + artistname))
        return empty_series
    else:
        try:
            if True:  # with Timeout(6):
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
                            "trackname": trackname,
                            "artistname": artistname,
                            "podcast": False,
                            "genre_chosen": "",
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
                            "trackname": trackname,
                            "artistname": artistname,
                            "podcast": True,
                            "genre_chosen": "",
                        }
                    )
        except Exception as e:
            logger.info(f"Error {e} for {track_id}")
            return None

    return track_info_series


def search_by_names(trackname: str, artistname: str, searchType: str = "track") -> str:
    """
    input: trackName, artistName
    output: id
    """

    if (not isinstance(trackname, str)) | (not isinstance(artistname, str)):
        raise TypeError

    try:
        # with Timeout(6):
        search_items = sp.search(
            trackname + " " + artistname, type=searchType, limit=3
        )[f"{searchType}s"]["items"]
        # searchType could be track or show, and the resulting dictionary will have "tracks" or "shows"
    except Exception as e:
        logger.info(f"Error {e} for {trackname} and {artistname}")
        return None

    if len(search_items) < 1 or search_items is None:
        logger.info(
            "No match found for " + trackname + ", " + artistname + " and " + searchType
        )
        return None
    try:
        # call get_historical_track_info which takes a search dictionary and returns the results
        uri = search_items[0]["id"]
    except Exception as e:
        logger.info(f"Error {e} for {trackname} and {artistname}")
        return None

    return uri


def get_audio(uris):
    audio_fts = []
    for uid in uris:
        if uid is not None:
            try:
                if True:  # with Timeout(3):
                    feat = sp.audio_features(uid)[0]
            except:
                print(f"Time out error for {uid}")
        audio_fts.append(pd.Series(feat))
    return audio_fts


def merge_tracks(
    data,
    track_df,
    d_artist="artistname",
    d_song="trackname",
    t_artist="artistname",
    t_song="trackname",
):
    """
    One of the first steps in the pipeline. Merge data import with existing searched tracks on artist and song names
    """
    data = data[[d_artist, d_song, "msplayed"]]  # no need to keep the other columns
    data.drop_duplicates(subset=[d_artist, d_song], inplace=True)
    tracks_merged = pd.merge(
        data,
        track_df,
        left_on=[d_artist, d_song],
        right_on=[t_artist, t_song],
        how="left",
    )

    return tracks_merged


def update_tracks(df, track_col="trackname", artist_col="artistname"):
    df = df.drop_duplicates(subset=[track_col, artist_col])
    track_df = splot.get_data(splot.tracks_all_query())
    df_unmerged = identify_new(df, track_df)
    logger.info(
        f"Search uri & track data for {len(df_unmerged)} tracks out of original {len(df)} unique tracks"
    )
    for i, row in df_unmerged.iterrows():
        # crude test for podcast show vs track
        if row["msplayed"] > ms_per_minute * 10:
            uri = search_by_names(row[track_col], row[artist_col], searchType="show")
            track_info_series = get_historical_track_info_from_id(
                uri, row[track_col], row[artist_col], searchType="show"
            )
            convert_to_SpotifyTrack(track_info_series)
        else:
            uri = search_by_names(row[track_col], row[artist_col], searchType="track")
            track_info_series = get_historical_track_info_from_id(
                uri, row[track_col], row[artist_col], searchType="track"
            )
            convert_to_SpotifyTrack(track_info_series)

    logger.info("Spotify uploads completed")

    return
