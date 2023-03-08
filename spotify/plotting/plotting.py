import os
import pandas as pd
import numpy as np
from pandas.api.types import is_numeric_dtype
from pandas.api.types import CategoricalDtype
import psycopg2
import matplotlib
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import calendar
import matplotlib.pyplot as plt
from matplotlib import dates
import seaborn as sns
import plotly.graph_objs as go
from datetime import timedelta

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

standard_layout = dict(title_x=0.5,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
)

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
    genre_chosen,
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
    df["endtime"] = pd.to_datetime(df["endtime"], utc=True)
    df["endtime"] = df["endtime"].dt.tz_convert("US/Pacific")
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
    fig.update_layout(standard_layout)
    return fig


def get_top(df, column, n):
    return df[column].value_counts().index[:n]


def simplify_genre(genre_list):
    replace_list = [
        "pop",
        "mellow",
        "funk",
        "indie",
        "rap",
        "house",
        "rock",
        "hip hop",
        "reggae",
        "soul",
        "r&b",
    ]
    for genre in replace_list:
        genre_list = [genre if genre in g else g for g in genre_list]
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


def format_new_songs(df, time_col="endtime", index_cols=["artistname", "trackname"]):
    first_df = pd.pivot_table(
        data=df, index=index_cols, values=time_col, aggfunc="first"
    ).reset_index()
    first_df["first"] = True

    new_df = pd.merge(df, first_df, on=index_cols + [time_col], how="left")
    return new_df


def count_new(
    df,
    date_col="date",
    win=7,
):
    ## df should be new df
    df["first"] = df["first"].fillna(0)
    total_df = pd.pivot_table(
        df, index=[date_col], values="minutes", aggfunc=sum
    ).reset_index()
    new_df = pd.pivot_table(
        df[df["first"] == True], index=[date_col], values="minutes", aggfunc=sum
    ).reset_index()
    count_first_df = pd.pivot_table(df, index=date_col, values="first", aggfunc=sum)
    new_df.rename(columns={"minutes": "minutes_first"}, inplace=True)
    count_new_df = pd.merge(total_df, new_df, on=date_col, how="outer")
    count_new_df = pd.merge(count_new_df, count_first_df, on=date_col, how="outer")

    count_new_df = fill_date(count_new_df, date_col=date_col)
    count_new_df["minutes"] = count_new_df["minutes"].fillna(0)
    count_new_df["minutes_first"] = count_new_df["minutes_first"].fillna(0)
    count_new_df["rolling_first"] = count_new_df["minutes_first"].rolling(win).mean()
    return count_new_df


def plot_new(count_new_df, date_col="date", firsts_col="first", win=7):
    fig = go.Figure(
        [go.Bar(x=count_new_df[date_col], y=count_new_df[firsts_col], name="New Songs")]
    )
    fig.add_trace(
        go.Scatter(
            x=count_new_df[date_col],
            y=count_new_df[f"rolling_{firsts_col}"],
            mode="lines",
            line=go.scatter.Line(color="purple"),
            name=f"New Songs - {win} Day Rolling",
        )
    )
    fig.update_layout(
        title="New Songs",
        yaxis=dict(
            title="New Songs",
        ),
    )
    fig.update_layout(standard_layout)
    return fig


def write_new_info(df):
    new_df = format_new_songs(
        df, time_col="endtime", index_cols=["artistname", "trackname"]
    )
    count_news = count_new(new_df)
    max_new = count_news.loc[np.argmax(count_news["rolling_first"])]

    d1 = max_new["date"]
    d2 = d1 - timedelta(days=4)
    new_songs = new_df.loc[(new_df["date"] <= d2) & (new_df["date"] >= d2)]
    new_songs = new_songs.loc[new_songs["first"] == True]
    sample_df = new_songs.sample(5)
    songs = [
        f"{song} by {artist}"
        for song, artist in zip(sample_df["trackname"], sample_df["artistname"])
    ]
    text = f"You listened to the most new songs around {max_new['date'].date()},"
    text += f"such as {songs[0]}, {songs[1]} and {songs[2]}."

    return text


def plot_overall(df_sum, date_col="date", minutes_col="minutes", win=7, podcast=True):
    fig = go.Figure()
    if podcast:
        for p in [True, False]:
            df_sum_sub = df_sum[df_sum["podcast"] == p]
            fig.add_trace(
                go.Bar(
                    x=df_sum_sub[date_col],
                    y=df_sum_sub[minutes_col],
                    name="Daily Minutes",
                )
            )
    else:
        fig.add_trace(
            go.Bar(x=df_sum[date_col], y=df_sum[minutes_col], name="Daily Minutes")
        )
    fig.add_trace(
        go.Scatter(
            x=df_sum[date_col],
            y=df_sum["rolling_average"],
            mode="lines",
            line=go.scatter.Line(color="red"),
            name=f"{win} Day Rolling Average",
        )
    )
    fig.update_layout(
        title="Overall Consumption",
        yaxis=dict(
            title="Minutes",
        ),
    )
    return fig


def format_artist_day(
    df, artist_col="artistname", date_col="date", minutes_col="minutes", n=5
):
    top_artists = get_top(df, artist_col, n)
    df = df[df[artist_col].isin(top_artists)]
    df_artist_day = pd.pivot_table(
        df, index=[artist_col, date_col], values=minutes_col, aggfunc=sum
    ).reset_index()
    df_artist_day.columns = [artist_col, date_col, minutes_col]

    return df_artist_day


def plot_top_artists(df, artist_col="artistname", n=5):
    artist_df = format_artist_day(df)
    unique_artists = pd.unique(artist_df[artist_col])
    a_dfs = []
    for a in unique_artists:
        a_df = artist_df.loc[artist_df.loc[:, artist_col] == a, :]
        a_df = fill_date(a_df, "date")
        a_df[artist_col] = a
        a_df["minutes"] = a_df["minutes"].fillna(0)
        a_dfs.append(a_df)
    artist_df = pd.concat(a_dfs)
    fig = go.Figure()

    # Add traces
    for a in unique_artists[:n]:
        a_df = artist_df[artist_df[artist_col] == a]
        fig.add_trace(
            go.Scatter(x=a_df["date"], y=a_df["minutes"], name=a, mode="lines+markers")
        )
    fig.update_layout(standard_layout)
    return fig


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
    plot.set(ylim=(-1, ylim_99), xlabel="Day of Week")
    for label in plot.get_xticklabels():
        label.set_visible(True)
    figure = plot.get_figure()
    plt.close()
    return figure


def format_one_hit_wonder(music_df, artist_col="artistname", song_col="trackname"):
    artist_summary = pd.pivot_table(
        music_df,
        index=[artist_col],
        values=[song_col, "msplayed"],
        aggfunc={song_col: lambda x: len(pd.unique(x)), "msplayed": sum},
    ).reset_index()
    artist_summary.rename(columns={song_col: "unique_tracks"}, inplace=True)
    artist_summary.sort_values("msplayed", ascending=False, inplace=True)
    one_hit_wonders = artist_summary[artist_summary["unique_tracks"] == 1]
    return one_hit_wonders


def plot_one_hit_wonders(
    music_df, granularity="month", artist_col="artistname", song_col="trackname", n=4
):
    one_hit_wonders_df = format_one_hit_wonder(music_df, artist_col=artist_col)
    one_hit_artists = one_hit_wonders_df[artist_col][:n]
    m = music_df[music_df[artist_col].isin(one_hit_artists)]
    m_pivotted = format_group_granular(
        m, granularity=granularity, index_cols=[artist_col, song_col]
    )
    m_pivotted["hit"] = m_pivotted[song_col] + " - " + m_pivotted[artist_col]

    dates = m_pivotted["date"].unique()
    dates.sort()
    m_pivotted["date_cat"] = pd.Categorical(
        m_pivotted["date"], categories=dates, ordered=True
    )

    plot = sns.FacetGrid(m_pivotted, row="hit", aspect=3, sharex=True)
    plot.map_dataframe(sns.barplot, x="date_cat", y="minutes")

    plot.set_titles(col_template="One Hit Wonders")
    # the axis labels are terrible, fix
    labels = plot.axes[n - 1][0].get_xticklabels()
    plot.set_xticklabels([format_datetime(d) for d in dates], rotation=30)

    figure = plot.fig
    plt.close()
    return plot


def format_datetime(date):
    ts = pd.to_datetime(str(date))
    return ts.strftime("%b %Y")


def format_group_granular(
    df, granularity, index_cols, time_col="endtime", minutes_col="minutes"
):
    df = df.copy()
    if granularity == "week":
        df["segment"] = df[time_col].dt.week
    elif granularity == "month":
        df["segment"] = df[time_col].dt.month
    else:
        raise Exception("granularity must be one of day, week, month or year")
    df["year"] = df[time_col].dt.year

    m_pivotted = pd.pivot_table(
        df, index=index_cols + ["segment", "year"], values=minutes_col, aggfunc=sum
    ).reset_index()

    if granularity == "month":
        m_pivotted["date"] = pd.to_datetime(
            m_pivotted["year"].astype(str)
            + "-"
            + m_pivotted["segment"].astype(str)
            + "-15"
        )

    return m_pivotted


def load_streaming(username):
    return get_data(userdata_query(username))


def get_max_agg(df, feature_col, minutes_col, index_col):
    """
    Get the dataframe where there is the max aggregated by column, and the value of which max for an index_col
    """
    col_df = pd.pivot_table(
        data=df, index=[feature_col, index_col], values=minutes_col, aggfunc=sum
    ).reset_index()
    col_max = pd.pivot_table(
        col_df, index=[feature_col], values=minutes_col, aggfunc=max
    ).reset_index()
    col_max = pd.merge(col_max, col_df, on=[feature_col, minutes_col])
    return col_max


def format_years(
    df, feature_col="release_year", minutes_col="minutes", index_col="artistname"
):
    years_df = pd.pivot_table(
        data=df, index=feature_col, values=minutes_col, aggfunc=sum
    ).reset_index()
    years_df[minutes_col] = years_df[minutes_col].round(1)
    years_df.rename(columns={minutes_col: "minutes_total"}, inplace=True)
    years_max = get_max_agg(
        df, feature_col=feature_col, minutes_col=minutes_col, index_col=index_col
    )
    years_go = pd.merge(years_df, years_max, on=feature_col)

    return years_go


def plot_years(
    df, feature_col="release_year", minutes_col="minutes", index_col="artistname"
):
    years_df = format_years(df, feature_col=feature_col, minutes_col=minutes_col)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=years_df[feature_col],
            y=years_df["minutes_total"],
            hovertemplate="Year: %{x} <br> total minutes: %{y}",
            name="Minutes - Total",
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Bar(
            x=years_df[feature_col],
            y=years_df[minutes_col],
            customdata=years_df[index_col],
            hovertemplate="top artist: %{customdata}",
            name="Minutes - Top Artist",
        )
    )
    fig.update_layout(
        title="Release Year Distribution",
        barmode="overlay",
        xaxis=dict(title="Release Year"),
        yaxis=dict(title="Minutes"),
    )
    fig.update_layout(standard_layout)

    return fig


def format_genres(df, genre_col, minutes_col="minutes", n=20):
    genres_df = pd.pivot_table(
        data=df, index=genre_col, values=minutes_col, aggfunc=sum
    ).reset_index()
    genres_df[minutes_col] = genres_df[minutes_col].round(1)
    genres_df.rename(columns={minutes_col: "minutes_total"}, inplace=True)
    genres_df.sort_values("minutes_total", ascending=False, inplace=True)
    # keep only top n and remove blanks
    genres_df = genres_df[genres_df[genre_col] != ""][:n]

    genre_artist_df = pd.pivot_table(
        data=df, index=[genre_col, "artistname"], values=minutes_col, aggfunc=sum
    ).reset_index()
    genres_max = pd.pivot_table(
        genre_artist_df, index=[genre_col], values=minutes_col, aggfunc=max
    ).reset_index()
    genres_max = pd.merge(genres_max, genre_artist_df, on=[genre_col, minutes_col])
    genres_max[minutes_col] = genres_max[minutes_col].round(1)
    genre_go = pd.merge(genres_df, genres_max, on=genre_col)
    return genre_go


def plot_genres(df, genre_col, minutes_col="minutes", n=20):
    genre_df = format_genres(df, genre_col=genre_col, minutes_col=minutes_col, n=n)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=genre_df["minutes_total"],
            y=genre_df[genre_col],
            hovertemplate="genre: %{y} <br> total minutes: %{x}",
            orientation="h",
            name="Minutes - Total",
        )
    )
    fig.add_trace(
        go.Bar(
            x=genre_df[minutes_col],
            y=genre_df[genre_col],
            customdata=np.stack(
                (genre_df["artistname"], genre_df[minutes_col]), axis=-1
            ),
            hovertemplate="top artist: %{customdata[0]} <br>number of minutes: %{customdata[1]} <extra></extra>",
            orientation="h",
            name="Minutes - Top Artist",
        )
    )
    fig.update_layout(
        title="Most Listened to Genres",
        barmode="overlay",
        xaxis=dict(title="Minutes"),
        yaxis=dict(title="Genre"),
    )
    fig.update_layout(standard_layout)

    return fig


def plot_popularity(
    df, minutes_col="minutes", track_col="trackname", artist_col="artistname"
):
    df = df.copy()
    df["song"] = df[track_col] + " - " + df[artist_col]
    df_agg = get_max_agg(
        df, feature_col="popularity", minutes_col=minutes_col, index_col="song"
    )
    pop_agg_dict = df_agg.set_index("popularity")["song"].to_dict()
    pop = pd.pivot_table(
        df, index="popularity", values=minutes_col, aggfunc=sum
    ).reset_index()
    pop["song"] = pop["popularity"].map(pop_agg_dict)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=pop["popularity"],
            y=round(pop["minutes"]),
            customdata=pop["song"],
            hovertemplate="Popularity: %{x} <br> Total Minutes: %{y} <br> Top Track: %{customdata}",
            name="Minutes - Total",
        )
    )
    fig.update_layout(
        title="Popularity",
        title_x=0.5,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


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
    plot.set(ylim=(-1, ylim_99), xlabel="Day of Week")
    for label in plot.get_xticklabels():
        label.set_visible(True)
    figure = plot.get_figure()
    plt.close()
    return figure


def format_skips(df, ratio_limit=0.4, n=5):
    df["skipped"] = df["played_ratio"] < ratio_limit
    skipped_songs_df = pd.pivot_table(
        df.loc[df["skipped"] == True],
        index=["trackname", "artistname"],
        values="uri",
        aggfunc=len,
    ).sort_values("uri", ascending=False)
    skipped_songs_df.rename(columns={"uri": "skips"}, inplace=True)
    total = pd.DataFrame(df.groupby(["trackname", "artistname"]).size())
    skipped_merged = total.join(skipped_songs_df).reset_index()
    skipped_merged.rename(columns={0: "n"}, inplace=True)
    skipped_merged["skips"] = skipped_merged["skips"].fillna(0)
    skipped_merged["ratio"] = skipped_merged["skips"] / skipped_merged["n"]
    skipped_merged.sort_values("ratio", ascending=False, inplace=True)
    skipped_select = skipped_merged[skipped_merged["n"] >= n]
    return skipped_select.head(5)


def write_skips_summary(df, track_col="trackname", artist_col="artistname"):
    skips_df = format_skips(df)
    skippedTracks: object = (
        skips_df[track_col].values[:2] + " by " + skips_df[artist_col].values[:2]
    )
    played = skips_df["n"].values[:2].astype(int)
    skipped = skips_df["skips"].values[:2].astype(int)
    text = f"Your most skipped tracks are {skippedTracks[0]} and {skippedTracks[1]} which you "
    text += f"skipped {skipped[0]} out of {played[0]}  and {skipped[1]} times out of {played[1]} respectively."
    return text


def write_text(filename, texts):
    if isinstance(texts, list):
        text = "\n".join(texts)
    else:
        text = texts
    with open(filename, "w") as f:
        f.write(text)


def main(username):
    df = get_data(tracks_query(username))
    logger.info(f"Spotify data read with {len(df)} rows \n : {df.head()}")
    df = preprocess(df)
    path = f"goodreads/static/Graphs/{username}"
    if not (os.path.exists(path) and os.path.isdir(path)):
        os.mkdir(path)
    df_sums = sum_days(df, podcast=True)
    new_df = format_new_songs(
        df, time_col="endtime", index_cols=["artistname", "trackname"]
    )
    count_news = count_new(new_df)

    fig = make_subplots(3, 1)
    overall = [
        plot_overall(df_sums, podcast=True),
        plot_new(count_news),
        plot_top_artists(df),
    ]
    for i, figure in enumerate(overall):
        for trace in range(len(figure["data"])):
            fig.append_trace(figure["data"][trace], row=i + 1, col=1)
    fig.write_html(f"goodreads/static/Graphs/{username}/overall_{username}.html")

    fig_year = plot_years(
        df, feature_col="release_year", minutes_col="minutes", index_col="artistname"
    )
    fig_year.write_html(
        f"goodreads/static/Graphs/{username}/spotify_year_plot_{username}.html"
    )

    fig_weekly = plot_weekly(df)
    fig_weekly.savefig(
        f"goodreads/static/Graphs/{username}/spotify_weekday_plot_{username}.jpeg"
    )

    fig_popularity = plot_popularity(df)
    fig_popularity.write_html(
        f"goodreads/static/Graphs/{username}/spotify_popularity_plot_{username}.html"
    )

    fig_genre = plot_genres(df, genre_col="genre_chosen")
    fig_genre.write_html(
        f"goodreads/static/Graphs/{username}/spotify_genre_plot_{username}.html"
    )

    write_text(
        filename=f"goodreads/static/Graphs/{username}/spotify_summary_{username}.txt",
        texts=[write_new_info(df), write_skips_summary(df)],
    )
