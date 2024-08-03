import csv
import os
import sys
from datetime import datetime

import pandas as pd
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import template
from spotify.plotting.utils import objects_to_df, minute_conversion

from .models import (
    NetflixUsers,
    Books,
    ExportData,
    Authors,
    SpotifyTracks,
    NetflixTitles,
    NetflixGenres,
    NetflixActors,
)

sys.path.append("..")
sys.path.append("../spotify/")
from spotify import data_engineering as de
from spotify.plotting import plotting as splot

from netflix import data_munge as nd
from netflix.plotting import plotting as nplot

from .plotting import plotting as gplot

from .scripts.append_to_export import (
    convert_to_ExportData,
    convert_to_Authors,
    convert_to_Book,
)

import logging

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
register = template.Library()


def run_script_function(request):
    """
    Main script that generates and saves plots for a user
    """
    user = request.user
    logger.info(f"Running graphs for user {user} based on request {request.method}")
    gplot.main(user)


def index(request):
    next = request.POST.get("next", "/")
    if request.user.is_authenticated:
        base_auth_template = "goodreads/basefile.html"
    else:
        base_auth_template = "goodreads/base2.html"
    return render(request, "goodreads/home.html", {"basefile": base_auth_template})


def books_home(request):
    return render(request, "goodreads/books_home.html")


def music_home(request):
    return render(request, "spotify/music_home.html")


def about_this(request):
    return render(request, "goodreads/about_this.html")


def about_this_spotify(request):
    return render(request, "spotify/about_this.html")


def about_this_netflix(request):
    return render(request, "netflix/about_this.html")


def faq(request):
    return render(request, "goodreads/faq.html")


def gallery_books(request):
    logger.info(f"Books gallery requested for {request.headers['User-Agent']}")
    return render(request, "goodreads/gallery.html")


def gallery_music(request):
    logger.info(f"Spotify gallery requested for {request.headers['User-Agent']}")
    return render(request, "spotify/gallery.html")


def gallery_streaming(request):
    logger.info(
        f"Netflix gallery requested for request {request.headers['User-Agent']}"
    )
    return render(request, "netflix/gallery.html")


def gallery_geography(request):
    logger.info(
        f"geography gallery requested for request {request.headers['User-Agent']}"
    )
    return render(request, "geography/gallery.html")


@login_required(redirect_field_name="next", login_url="user-login")
def nationality_map_view(request):
    username = request.user
    nationality_map_url = "goodreads/static/Graphs/{}/author_map_{}.html".format(
        username, username
    )
    return render(
        request,
        "goodreads/nationality_map.html",
        {"nationality_map_url": nationality_map_url},
    )


@login_required(redirect_field_name="next", login_url="user-login")
def popularity_spectrum_view(request):
    username = request.user
    popularity_spectrum_url = "goodreads/static/Graphs/{}/read_heatmap_{}.html".format(
        username, username
    )
    return render(
        request,
        "goodreads/popularity_spectrum.html",
        {"popularity_spectrum_url": popularity_spectrum_url},
    )


@login_required(redirect_field_name="next", login_url="user-login")
def plots_view(request):
    username = request.user
    finish_plot_url = "Graphs/{}/goodreads_finish_plot_{}.html".format(
        username, username
    )
    nationality_map_url = "Graphs/{}/author_map_{}.html".format(username, username)
    popularity_spectrum_url = "Graphs/{}/goodreads_read_heatmap_{}.html".format(
        username, username
    )
    summary_plot_url = "Graphs/{}/goodreads_summary_{}.html".format(username, username)
    monthly_pages_read_url = "Graphs/{}/monthly_pages_read_{}.html".format(
        username, username
    )
    genre_diff_url = f"Graphs/{username}/goodreads_genre_diff_{username}.html"

    if "run_script_function" in request.POST:
        run_script_function(request)
    return render(
        request,
        "goodreads/plots.html",
        {
            "popularity_spectrum_url": popularity_spectrum_url,
            "finish_plot_url": finish_plot_url,
            "nationality_map_url": nationality_map_url,
            "summary_plot_url": summary_plot_url,
            "monthly_pages_read_url": monthly_pages_read_url,
            "genre_diff_url": genre_diff_url,
        },
    )


def runscript(request):
    logger.info(f"Running script with request method {request.method}")
    if request.method == "POST" and "runscript" in request.POST:
        run_script_function(request)

    return plots_view(request)


def runscriptSpotify(request):
    username = request.user
    logger.info(f"Running Spotify script with request method {request.method}")
    if request.method == "POST" and "runscriptSpotify" in request.POST:
        splot.main(username)
        return HttpResponseRedirect("/music/plots/")

    return spot_plots_view(request)


def runscriptNetflix(request):
    username = request.user
    logger.info(f"Running Netflix script with request method {request.method}")
    if request.method == "POST" and "runscriptNetflix" in request.POST:
        nplot.main(username)
        return HttpResponseRedirect("/netflix/plots/")

    return netflix_plots_view(request)


def spot_text(request):
    username = request.user
    info_text_url = f"goodreads/static/Graphs/{username}/spotify_summary_{username}.txt"
    with open(info_text_url) as f:
        lines = f.readlines()
    f.close()
    info_text = "".join(lines)
    weekly_text_url = (
        f"goodreads/static/Graphs/{username}/spotify_weekly_{username}.txt"
    )
    with open(weekly_text_url) as f:
        lines2 = f.readlines()
    f.close()
    weekly_text = "".join(lines2)
    return JsonResponse({"info_text": info_text, "weekly_text": weekly_text})


@login_required(redirect_field_name="next", login_url="user-login")
def spot_plots_view(request):
    username = request.user

    overall_url = "Graphs/{}/spotify_overall_{}.html".format(username, username)
    popularity_url = "Graphs/{}/spotify_popularity_plot_{}.html".format(
        username, username
    )
    top_artists_url = "Graphs/{}/spotify_top_artists_plot_{}.html".format(
        username, username
    )
    daily_url = "Graphs/{}/spotify_daily_plot_{}.html".format(username, username)
    release_year_url = "Graphs/{}/spotify_year_plot_{}.html".format(username, username)
    genre_url = "Graphs/{}/spotify_genre_plot_{}.html".format(username, username)
    top_songs_url = "Graphs/{}/spotify_top_songs_{}.html".format(username, username)
    follower_heat_url = "Graphs/{}/spotify_follower_heat_{}.html".format(
        username, username
    )

    return render(
        request,
        "spotify/plots.html",
        {
            "overall_url": overall_url,
            "popularity_url": popularity_url,
            "top_artists_url": top_artists_url,
            "daily_url": daily_url,
            "release_year_url": release_year_url,
            "genre_url": genre_url,
            "top_songs_url": top_songs_url,
            "follower_heat_url": follower_heat_url,
        },
    )


def process_export_upload(df, date_col="Date_Read"):
    df.columns = df.columns.str.replace(
        r"[ .]", "_", regex=True
    )  # standard export comes in with spaces. R would turn these into dots
    logger.info(df.columns)
    df[date_col] = pd.to_datetime(df[date_col])
    df.columns = df.columns.str.lower()
    df["number_of_pages"].fillna(0, inplace=True)
    df["book_id"] = df["book_id"].astype(str)
    df["original_publication_year"] = df["original_publication_year"].fillna(
        df["year_published"]
    )
    df = df[pd.notnull(df["book_id"])]
    df["author"] = df["author"].str.strip()
    df["author"] = df["author"].replace(r"\s+", " ", regex=True)
    return df


def populateExportData(df, user):
    exportDataObjs = df.apply(
        lambda x: convert_to_ExportData(x, username=str(user)), axis=1
    )
    return exportDataObjs


def populateBooks(book_ids, user, wait=2, metrics=True):
    found = Books.objects.filter(book_id__in=book_ids).count()
    not_found = len(book_ids) - found
    now = datetime.now()
    for book_id in book_ids[:30]:
        status = convert_to_Book(book_id, wait=wait)
    if metrics:
        # output metrics
        write_metrics(user, time=now, found=found, not_found=not_found)


def populateAuthors(df):
    authors = df["author"].apply(convert_to_Authors)
    return authors


def upload_goodreads(request):
    user = request.user
    csv_file = request.FILES["file"]
    # save csv file in database
    logger.info(f"Goodreads upload started for {user}")
    df = pd.read_csv(csv_file)
    if not os.path.exists(f"goodreads/static/Graphs/{user}"):
        os.mkdir(f"goodreads/static/Graphs/{user}")
    df.to_csv(f"goodreads/static/Graphs/{user}/export_{user}.csv")
    df = process_export_upload(df)
    logger.info(f"starting export table addition for {user} with {str(len(df))} rows")
    exportDataObjs = populateExportData(df, user)
    exportNew_ids = [
        e.book_id
        for e in exportDataObjs
        if not Books.objects.filter(book_id=e.book_id).exists()
    ]
    logger.info(f"starting authors table addition")
    populateAuthors(df)
    return JsonResponse({"book_ids": exportNew_ids})


def insert_goodreads(request):
    template = "goodreads/csv_upload.html"
    book_ids = request.POST.getlist("book_ids[]")
    user = request.user
    newN = len(book_ids)
    logger.info(f"starting books table addition for {newN} new books")
    populateBooks(book_ids, user, wait=3, metrics=True)
    return render(request, template)


@login_required(redirect_field_name="next", login_url="user-login")
def upload_view_goodreads(request):
    template = "goodreads/csv_upload.html"
    # check if user has uploaded a csv file before running the analysis
    if request.method == "GET":
        return render(request, template)

    # run analysis when user clicks on Analyze button
    if request.method == "POST" and "runscript" in request.POST:
        logger.info(
            f"Got running with request {request.method} and post {request.POST}"
        )
        run_script_function(request)
        # when script finishes, move user to plots view
        return HttpResponseRedirect("/books/plots/")
    else:
        return render(request, template)

    return render(request, template)


@login_required(redirect_field_name="next", login_url="user-login")
def upload_view_spotify(request):
    user = request.user
    logger.info(f"The request looks like: {request}, {type(request)}")
    # return
    template = "spotify/json_upload_spotify.html"
    if request.method == "POST" and "runscriptSpotify" in request.POST:
        logger.info(
            f"Got running with spotify request {request.method} and post {request.POST}"
        )
        runscriptSpotify(request)
        # when script finishes, move user to plots view
        return HttpResponseRedirect("music/plots/")
    return render(request, template)


def upload_spotify(request):
    user = request.user
    graphs_path = f"goodreads/static/Graphs/{user}"
    json_file = request.FILES["file"]
    logger.info(f"Spotify upload started for {user}")
    df = pd.read_json(json_file)
    file_path = f"goodreads/static/Graphs/{user}/spotify_{user}.csv"
    df.to_csv(file_path, index=False)
    if not os.path.exists(graphs_path):
        os.mkdir(graphs_path)
    # change columns from endTime to endtime etc.
    df = de.lowercase_cols(df)
    # detect if upload format is of full Spotify export format
    if "ip_addr_decrypted" in df.columns:
        df = splot.preprocess_new(df)
    # load up the existing data in database for this user
    loaded_df = splot.load_data(user)
    # if there is existing data, dedupe with new data
    if len(loaded_df) > 0:
        loaded_df["endtime"] = pd.to_datetime(loaded_df["endtime"], utc=True)
        df["endtime"] = pd.to_datetime(df["endtime"], utc=True)
        logger.info(
            f"df: {df['endtime'].values[:5]}, \nloaded_df: {loaded_df['endtime'].values[:5]}"
        )
        # new here means new to the user
        df_new = pd.concat([df, loaded_df, loaded_df]).drop_duplicates(
            keep=False
        )  # nifty line to keep just new data
    else:
        df_new = df
    new_lines = str(len(df_new))
    if len(df_new) < 1:
        logger.info(f"No new data for user {user}")
        return JsonResponse({"tracknames": [0], "artistnames": [0], "msplayed": [0]})
    populateSpotifyStreaming(df_new, user)
    # save csv file in database
    file_path = f"goodreads/static/Graphs/{user}/spotify_{user}_{new_lines}.csv"
    df_new.to_csv(file_path, index=False)
    df_unmerged = de.get_unmerged(
        df_new, track_col="trackname", artist_col="artistname"
    )
    logger.info(
        f"Search uri & track data for {len(df_unmerged)} tracks out of original {len(df)} unique tracks"
    )
    return JsonResponse(
        {
            "tracknames": df_unmerged["trackname"].tolist(),
            "artistnames": df_unmerged["artistname"].tolist(),
            "msplayed": df_unmerged["msplayed"].tolist(),
        }
    )


def insert_spotify(request):
    user = request.user
    template = "spotify/json_upload_spotify.html"
    artistnames = request.POST.getlist("artistnames[]")
    tracknames = request.POST.getlist("tracknames[]")
    msplayed = request.POST.getlist("msplayed[]")
    logger.info(f"starting spotify tracks api calls for {user}")
    de.update_tracks(artistnames, tracknames, msplayed)
    return render(request, template, {"hasData": True})


def populateSpotifyStreaming(df, user):
    logger.info(f"spotify df {df.head()}")
    # if 'uri' in df.columns:
    #     print("something") Add in some logic to deal with newer export
    spotifyStreamingObjs = df.apply(
        lambda x: de.convert_to_SpotifyStreaming(x, username=str(user)),
        axis=1,
    )
    return spotifyStreamingObjs


@login_required(redirect_field_name="next", login_url="user-login")
def upload_view_netflix(request):
    user = request.user
    # check whether user has data
    q = NetflixUsers.objects.filter(username=user).values()
    hasData = len(q) > 0
    if request.method == "POST":
        logger.info(f"The request looks like: {request}, {request.POST}")
    template = "netflix/csv_upload_netflix.html"
    # Analyze
    if request.method == "POST" and "runscriptNetflix" in request.POST:
        logger.info(
            f"Got running with Netflix request {request.method} and post {request.POST}"
        )
        runscriptNetflix(request)
        # when script finishes, move user to plots view
        return HttpResponseRedirect("/netflix/plots/")
    return render(request, template, {"hasData": hasData})


@register.simple_tag
def upload_netflix(request):
    logger.info(f"upload Netflix with request path {request.path}")
    user = request.user
    csv_file = request.FILES["file"]
    # save csv file in database
    df = pd.read_csv(csv_file)
    if not os.path.exists(f"goodreads/static/Graphs/{user}"):
        os.mkdir(f"goodreads/static/Graphs/{user}")
    df.to_csv(f"goodreads/static/Graphs/{user}/netflix_history_{user}.csv")
    df.columns = [c.lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    # load up the existing data in database for this user
    logger.info(f"starting {user} Netflix table addition for {len(df)} rows")
    nd.ingest_netflix(df, user)
    logger.info(f"Netflix ingestion complete")
    df = nd.pipeline_steps(df=df)
    logger.info(df.head())
    df_unmerged = df.loc[pd.isnull(df["netflix_id"])]
    n_miss = len(df_unmerged["name"].unique())
    logger.info(f"Number of unmerged shows {n_miss}")
    return JsonResponse(
        {"names": df_unmerged["name"].unique().tolist(), "n_missing": n_miss}
    )


def insert_netflix(request):
    logger.info(f"insert netflix request looks like {request.POST.dict()}")
    names = request.POST.getlist("names[]")
    template = "netflix/csv_upload_netflix.html"
    for name in names:
        nd.lookup_and_insert(name)
        logger.info(f"Ingestion completed for {name}")
    return render(request, template, {"hasData": True})


@login_required(redirect_field_name="next", login_url="user-login")
def netflix_plots_view(request):
    username = request.user

    timeline_url = "Graphs/{}/netflix_timeline_{}.html".format(username, username)
    histogram_url = "Graphs/{}/netflix_histogram_{}.html".format(username, username)
    release_year_url = "Graphs/{}/netflix_year_plot_{}.html".format(username, username)
    genre_series_url = "Graphs/{}/netflix_genres_{}_series.html".format(
        username, username
    )
    genre_movie_url = "Graphs/{}/netflix_genres_{}_movie.html".format(
        username, username
    )
    network_url = "Graphs/{}/netflix_network_{}.html".format(username, username)
    max_binge = nplot.find_max(username)

    return render(
        request,
        "netflix/plots.html",
        {
            "timeline_url": timeline_url,
            "genre_series_url": genre_series_url,
            "genre_movie_url": genre_movie_url,
            "histogram_url": histogram_url,
            "network_url": network_url,
            "binge_show": max_binge.get("name", ""),
            "binge_date": max_binge.get("date", ""),
            "binge_n": max_binge.get("username", ""),
        },
    )


def write_metrics(user, time, found, not_found, file_path="metrics.csv"):
    time_now = datetime.now()
    fields = [user, time, time_now, found, not_found]
    with open(file_path, "a") as f:
        writer = csv.writer(f)
        writer.writerow(fields)


### Geography
def geography(request):
    return render(request, "geography/geography.html")


def streaming(request):
    return render(request, "netflix/streaming_home.html")


def comments(request):
    return render(request, "comments.html")


def post_comment(request):
    comment = request.POST.get("comment", "")
    next = request.POST.get("next", "/")
    logger.info(str(comment))
    # when script finishes, move user to plots view
    if next:
        logger.info(next)
        HttpResponseRedirect(next)
    return HttpResponseRedirect("/")


@login_required(redirect_field_name="next", login_url="user-login")
def netflix_compare_view(request):
    return render(request, "netflix/compare.html")


def netflix_compare_func(request):
    """ """
    from django.templatetags.static import static

    user1 = str(request.user)
    user2 = request.POST.get("user2", "")
    user2 = str(user2).strip()
    logger.info(f"netflix compare func called for {user1} and {user2}")
    fig, similarity = nplot.compare(user1, user2)
    if fig:
        compare_url = f"Graphs/{user1}/netflix_comparison_{user1}_{user2}.html"
        fig.write_html(f"goodreads/static/{compare_url}")
        # because netflix_compare_view does not pass in any url paths, we do it here
        # it's still easiest to use the static files framework, and it's necessary to use the static function
        # the request build_absolute_uri function makes it an absolute path, because in the html file
        # we can't just use the {% static url %} pattern
        return JsonResponse(
            {
                "compare_url": request.build_absolute_uri(static(compare_url)),
                "success": True,
                "similarity": similarity,
            }
        )
    else:
        logger.info(f"{user2} does not have Netflix data")
        return JsonResponse({"compare_url": "", "success": False, "similarity": 0})


def good_text(request):
    username = request.user
    small_text_url = (
        f"goodreads/static/Graphs/{username}/goodreads_small_{username}.txt"
    )
    with open(small_text_url) as f:
        lines = f.readlines()
    f.close()
    small_nations = "".join(lines)

    return JsonResponse({"small_nations": small_nations})


@login_required(redirect_field_name="next", login_url="user-login")
def view_data_books(request):
    return render(request, "goodreads/books_view_data.html")


def load_data_books(request):
    username = request.user
    logger.info(f"Loading data for {username}")
    user_df = gplot.load_data(username)
    df = gplot.run_all(user_df)
    df.drop(columns=["id", "ts_updated", "title", "book_id"], inplace=True)
    df["read_percentage"] = round(df["read_percentage"] * 100, 1)
    df = gplot.genre_join(df)
    html_cols = [
        "title_simple",
        "author",
        "exclusive_shelf",
        "date_read",
        "shelves",
        "narrative",
        "nationality_chosen",
        "read",
        "read_percentage",
    ]
    df = df.fillna("")
    df.sort_values("date_read", inplace=True)
    df["date_read"] = df["date_read"].dt.date
    reading_table = df[html_cols].to_dict(orient="records")
    logger.info(f"reading table: {reading_table[:4]}")
    return JsonResponse(reading_table, safe=False)


@login_required(redirect_field_name="next", login_url="user-login")
def view_data_music(request):
    return render(request, "spotify/view_data.html")


def load_data_music(request):
    username = request.user
    df = splot.load_data(username)
    df["minutes"] = df["minutes"].round(2)
    df["duration"] = df["duration"].round(2)
    df["played_ratio"] = round(df["played_ratio"] * 100, 1)
    html_cols = [
        "date",
        "artistname",
        "trackname",
        "genres",
        "album",
        "podcast",
        "minutes",
        "duration",
        "release_date",
        "popularity",
    ]
    df = df.fillna("")
    music_table = df[html_cols].to_dict(orient="records")
    logger.info(f"music table: {music_table[:4]}")
    return JsonResponse(music_table, safe=False)


@login_required(redirect_field_name="next", login_url="user-login")
def view_data_streaming(request):
    return render(request, "netflix/view_data.html")


def load_data_streaming(request):
    username = request.user
    logger.info(f"Loading data for {username}")
    df = nplot.load_data(username)
    html_cols = [
        "date",
        "title",
        "title_type",
        "director",
        "genres",
        "cast",
    ]
    df = df.fillna("")
    streaming_table = df[html_cols].to_dict(orient="records")
    logger.info(f"streaming table called")
    return JsonResponse(streaming_table, safe=False)


def explore_data_books(request):
    books_df = objects_to_df(Books.objects.all())
    books_df["book_id"] = pd.to_numeric(books_df["book_id"]).astype(int)
    books_df.sort_values("book_id", inplace=True)
    export_df = objects_to_df(ExportData.objects.all())
    export_df["book_id"] = export_df["book_id"].astype(float).astype(int)

    authors_df = objects_to_df(Authors.objects.all())
    good_df = pd.merge(books_df, export_df, how="left", on="book_id")
    authors_df.rename(columns={"author_name": "author"}, inplace=True)
    authors_df.drop(columns="ts_updated", inplace=True)
    # drop a few authors that aren't books
    authors_df = authors_df.loc[authors_df["author"] != "NOT A BOOK"]
    good_df = pd.merge(good_df, authors_df, on="author", how="left")
    good_df["author"] = good_df["author"].fillna("")
    good_df = gplot.run_all(good_df)
    good_df = gplot.genre_join(good_df)
    edf = pd.pivot_table(
        good_df,
        index=["title_simple", "author", "nationality_chosen", "gender"],
        values=[
            "number_of_pages",
            "original_publication_year",
            "read",
            "narrative",
            "shelves",
        ],
        aggfunc={
            "number_of_pages": max,
            "original_publication_year": max,
            "read": max,
            "narrative": "first",
            "shelves": "first",
        },
    ).reset_index()
    edf["read"] = edf["read"].fillna(0)
    edf = edf.fillna("")
    edf = edf.loc[edf["title_simple"].str.len() > 1]
    edf.sort_values("read", ascending=False, inplace=True)
    html_cols = [
        "title_simple",
        "author",
        "gender",
        "nationality_chosen",
        "original_publication_year",
        "read",
        "narrative",
        "shelves",
        "number_of_pages",
    ]
    read_table = edf[html_cols].to_dict(orient="records")
    logger.info(f"reading table: {read_table[:4]}")
    return JsonResponse(read_table, safe=False)


def view_explore_books(request):
    return render(request, "goodreads/explore_data.html")


def explore_data_music(request):
    stream_df = objects_to_df(SpotifyTracks.objects.all())
    # artists = objects_to_df(SpotifyArtists.objects.all())
    stream_df["time_str"] = stream_df["duration"].fillna(0).apply(minute_conversion)
    html_cols = [
        "artistname",
        "trackname",
        "genres",
        "album",
        "podcast",
        "time_str",
        "release_date",
        "popularity",
    ]
    stream_df = stream_df.fillna("")
    music_table = stream_df[html_cols].to_dict(orient="records")
    logger.info(f"music exploration called")
    return JsonResponse(music_table, safe=False)


def view_explore_music(request):
    return render(request, "spotify/explore_data.html")


def view_explore_streaming(request):
    return render(request, "netflix/explore_data.html")


def explore_data_streaming(request):
    title_df = objects_to_df(NetflixTitles.objects.filter(netflix_id__isnull=False))
    genres_df = objects_to_df(NetflixGenres.objects.all())
    actors_df = objects_to_df(NetflixActors.objects.all())
    stream_df = pd.merge(title_df, genres_df, on="netflix_id", how="left")
    stream_df = pd.merge(stream_df, actors_df, on="netflix_id", how="left")
    # turn comma separated cast into array, keep only ten people for performance reasons
    stream_df["cast"].fillna("", inplace=True)
    stream_df["cast"] = stream_df["cast"].apply(lambda x: x.split(",")[:10])
    # add space to the first value to make consistent but cast could be None
    stream_df["cast"] = stream_df["cast"].apply(
        lambda x: [" " + y if i == 0 else y for i, y in enumerate(x)]
    )
    html_cols = [
        "title",
        "release_year",
        "title_type",
        "alt_votes",
        "genres",
        "cast",
        "director",
    ]
    stream_df = stream_df.fillna("")
    stream_table = stream_df[html_cols].to_dict(orient="records")
    logger.info(f"netflix exploration called")
    return JsonResponse(stream_table, safe=False)


def load_lists(request):
    username = request.user
    # context has to contain a dictionary that gets passed to the dash app
    context = {"dash_context": {"usernameInput": {"value": str(username)}}}
    logger.info(f"Context: {context}")
    return render(request, "goodreads/lists.html", context=context)
