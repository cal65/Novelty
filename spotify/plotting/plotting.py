import os
import warnings
import argparse
import geopandas as gpd

warnings.simplefilter(action="ignore", category=FutureWarning)
import pandas as pd
import numpy as np
from pandas.api.types import is_numeric_dtype
import psycopg2
import matplotlib
import seaborn as sns
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import calendar
import matplotlib.pyplot as plt
from matplotlib import dates
import seaborn as sns
import plotly.graph_objs as go


from pandas.api.types import CategoricalDtype

import logging

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

post_pass = os.getenv("cal65_pass")
matplotlib.pyplot.switch_backend("Agg")

ms_per_minute = 60 * 1000


def get_data(query, database="goodreads"):
    conn = psycopg2.connect(
        host="localhost", database=database, user="cal65", password=post_pass
    )
    try:
        df = pd.read_sql(query, con=conn)
        logger.info(f"Returning data from query with nrows {len(df)}")
        return df
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return


def userdata_query(username):
    query = f"""
    select 
    endtime, artistname, trackname, msplayed
    from goodreads_spotifystreaming 
    where username = '{username}'
    """
    return query


def tracks_query(username):
    query = f""" 
    select 
    endtime, 
    stream.artistname, 
    stream.trackname, 
    msplayed,
    uri,
    name, 
    artist, 
    duration,
    popularity,
    release_date,
    genres,
    album,
    explicit,
    podcast
    from goodreads_spotifystreaming stream 
    left join goodreads_spotifytracks tracks
    on stream.artistname = tracks.artistname
    and stream.trackname = tracks.trackname
    where  stream.username = '{username}'
    """
    return query


def preprocess(df):
    df["endtime"] = pd.to_datetime(df["endtime"])
    df["endtime"] = df["endtime"].dt.tz_localize("utc").dt.tz_convert("US/Pacific")
    df["date"] = df["endtime"].dt.date
    df["minutes"] = df["msplayed"] / ms_per_minute

    # processing for merged data
    if "release_year" not in df.columns:
        df["release_year"] = pd.to_numeric(
            df["release_date"].str[:4], downcast="integer"
        )
    df["genre_chosen"] = df["genre_chosen"].fillna("")
    df["genre_simplified"] = simplify_genre(df["genre_chosen"])

    df["played_ratio"] = df["minutes"] / df["duration"]

    return df


def format_song_day(df, artist_col, song_col, date_col):
    df_song_day = pd.DataFrame(
        df.groupby([artist_col, song_col, date_col]).size()
    ).reset_index()
    df_song_day.rename(columns={0: "n"}, inplace=True)
    top_artists = df[artist_col].value_counts().index[:10]
    df_song_day_select = df_song_day[df_song_day[artist_col].isin(top_artists)]
    return df_song_day_select


def plot_song_day(df, artist_col, song_col, date_col):
    num_songs = len(pd.unique(df[song_col]))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[date_col],
            y=df[song_col] + ", " + df[artist_col],
            text=df["n"],
            mode="markers",
            marker={"size": df["n"] * num_songs / 5, "color": "DarkRed"},
            hovertemplate="name: %{y} <br>number: %{text} <br> date: %{x} <extra></extra>",
        )
    )

    fig.update_layout(
        title="Song Plays",
        width=2000,
        height=max(
            500, min(num_songs * 20, 3000)
        ),  # ensure that the plot is between 100 and 3000
        showlegend=True,
    )
    return fig


def get_top(df, column, n):
    return df[column].value_counts().index[:n]



def simplify_genre(genre_list):
    replace_list = ["pop", "mellow", "funk", "indie", "rap", "house", "rock", "hip hop", "reggae", "soul", "r&b"]
    for genre in replace_list:
        genre_list = [genre if genre in g else g for g in genre_list ]
    return genre_list


def fill_date(df, date_col):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    date_full = pd.date_range(df[date_col].min(), df[date_col].max())
    df = pd.merge(pd.DataFrame({date_col: date_full}), df, on=date_col, how="left")
    return df


def sum_days(df, date_col="date", minutes_col="minutes", win=7, podcast=True):
    if podcast:
        df_sum = pd.pivot_table(
            df, index=[date_col, "podcast"], values=minutes_col, aggfunc=sum
        ).reset_index()
    else:
        df_sum = pd.pivot_table(
            df, index=date_col, values=minutes_col, aggfunc=sum
        ).reset_index()
    # date filling
    df_sum[date_col] = pd.to_datetime(df_sum[date_col])
    df_sum = fill_date(df=df_sum, date_col=date_col)
    df_sum[minutes_col] = df_sum[minutes_col].fillna(0)
    # rolling average
    df_sum["rolling_average"] = (
        df_sum[minutes_col].rolling(window=win, min_periods=1).mean()
    )
    df_sum["rolling_average"] = df_sum["rolling_average"].round(2)
    if podcast:
        df_sum["podcast"] = df_sum["podcast"].fillna(False)
    return df_sum


def new_songs(df, time_col="endtime", index_cols=["artistname", "trackname"]):
    first_df = pd.pivot_table(
        data=df, index=index_cols, values=time_col, aggfunc="first"
    ).reset_index()
    first_df["first"] = True

    df = pd.merge(df, first_df, on=index_cols + [time_col], how="left")
    return df


def count_new(
        df,
        date_col="date",
        time_col="endtime",
        index_cols=["artistname", "trackname"],
        win=7,
):
    df = new_songs(df, time_col=time_col, index_cols=index_cols)
    df["first"] = df["first"].fillna(0)
    total_df = pd.pivot_table(
        df, index=[date_col], values="minutes", aggfunc=sum
    ).reset_index()
    new_df = pd.pivot_table(
        df[df["first"] == True], index=[date_col], values="minutes", aggfunc=sum
    ).reset_index()
    count_first_df = pd.pivot_table(df, index=date_col, values="first", aggfunc=sum)
    new_df.rename(columns={'minutes': 'minutes_first'}, inplace=True)
    count_new_df = pd.merge(total_df, new_df, on=date_col, how='outer')
    count_new_df = pd.merge(count_new_df, count_first_df, on=date_col, how='outer')

    count_new_df = fill_date(count_new_df, date_col=date_col)
    count_new_df["minutes"] = count_new_df["minutes"].fillna(0)
    count_new_df["minutes_first"] = count_new_df["minutes_first"].fillna(0)
    count_new_df["rolling_first"] = count_new_df["minutes_first"].rolling(win).mean()
    return count_new_df


def load_streaming(username):
    return get_data(userdata_query(username))


def year_plot(df):
    release_year_df = pd.DataFrame(df["release_year"].value_counts()).reset_index()
    release_year_df.columns = ["release_year", "count"]
    release_year_df["release_year"] = release_year_df["release_year"].astype(int)

    sns.set(rc={"figure.figsize": (11.7, 8.27)})
    plot = sns.barplot(data=release_year_df, x="release_year", y="count")
    for ind, label in enumerate(plot.get_xticklabels()):
        if ind % 10 == 0:  # every 10th label is kept
            label.set_visible(True)
        else:
            label.set_visible(False)
    plot.set(title="Release Year Distribution")
    figure = plot.get_figure()
    plt.close()
    return figure


def plot_genres(df, genre_col, n=20):
    genres_df = pd.DataFrame(df[genre_col].value_counts()).reset_index()
    genres_df.rename(columns={"index": "genre", genre_col: "listens"}, inplace=True)
    genres_df = genres_df[genres_df["genre"] != ""]
    plot = sns.barplot(data=genres_df[:n], y="genre", x="listens")
    plot.set(title="Most Listened to Genres")
    figure = plot.get_figure()
    plt.close()
    return figure


def plot_popularity(df, bins=50):
    plot = sns.histplot(
        data=df[df["podcast"] == False], x="popularity", weights="minutes", bins=bins
    )
    plot.set(title="Song Popularity")
    figure = plot.get_figure()
    plt.close()
    return figure


def format_daily(df, date_col="endtime"):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df["wday"] = pd.to_datetime(df["date"]).dt.weekday
    df["weekend"] = df["wday"].isin([5, 6])
    df["time_of_day"] = pd.to_datetime("2000-01-01 " + df[date_col].dt.time.astype(str))
    df["time_period"] = df["time_of_day"].dt.round("15min").dt.time
    weekend_count = (
        df[["date", "weekend"]]
        .drop_duplicates()
        .groupby("weekend")
        .count()
        .reset_index()
    )
    df_period = pd.pivot_table(
        df, index=["time_period", "weekend"], values="minutes", aggfunc=sum
    ).reset_index()
    df_period = pd.merge(df_period, weekend_count, on="weekend")
    df_period["minutes_scaled"] = df_period["minutes"] / df_period["date"]
    return df_period


def plot_daily(df, date_col="endtime"):
    df_period = format_daily(df, date_col=date_col)
    plot = sns.barplot(
        data=df_period, x="time_period", y="minutes_scaled", hue="weekend"
    )
    for ind, label in enumerate(plot.get_xticklabels()):
        if ind % 10 == 0:  # every 10th label is kept
            label.set_visible(True)
        else:
            label.set_visible(False)
    figure = plot.get_figure()
    plt.close()
    return figure


def plot_weekly(df, date_col="date"):
    d = dict(enumerate(calendar.day_name))
    df_wday = pd.pivot_table(
        df, index=date_col, values="minutes", aggfunc=sum
    ).reset_index()
    df_wday[date_col] = pd.to_datetime(df_wday[date_col])
    df_wday["wday"] = df_wday["date"].dt.weekday
    df_wday["day_of_week"] = df_wday["wday"].map(d)
    ylim_99 = df_wday["minutes"].quantile(0.99)  # an extreme outlier can ruin the plot
    plot = sns.boxplot(data=df_wday, x="day_of_week", y="minutes", order=d.values())
    plot.set(ylim=(-1, ylim_99))
    for label in plot.get_xticklabels():
        label.set_visible(True)
    figure = plot.get_figure()
    plt.close()
    return figure


def main(username):
    df = get_data(tracks_query(username))
    logger.info(f"Spotify data read with {len(df)} rows \n : {df.head()}")
    df = preprocess(df)
    os.mkdirs(f"goodreads/static/Graphs/{username}")
    df_sums = sum_days(df, podcast=True)
    count_news = count_new(df)
    fig = year_plot(df)
    fig.savefig(f"goodreads/static/Graphs/{username}/spotify_year_plot_{username}.jpeg")

    fig.savefig(f"../graphs/{username}/year_plot_{username}.jpeg")
    fig_weekly = plot_weekly(df)
    fig_weekly.savefig(f"../graphs/{username}/spotify_weekday_plot_{username}.jpeg")

    # fig_popularity = plot_popularity(df, bins=50)
    # fig_popularity.savefig(f"goodreads/static/Graphs/{username}/spotify_popularity_plot_{username}.jpeg")
    #
    # fig = make_subplots(3, 1)
    # overall = [
    #     plot_overall(df_sums, podcast=True),
    #     plot_new(count_news),
    #     plot_top_artists(music_data),
    # ]
    # for i, figure in enumerate(overall):
    #     for trace in range(len(figure["data"])):
    #         fig.append_trace(figure["data"][trace], row=i + 1, col=1)
    # fig.write_html(f"../graphs/{name}/overall_{name}.html")
