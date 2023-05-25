import datetime
import os
import pandas as pd
import numpy as np
import psycopg2
import matplotlib
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import calendar
from datetime import date, timedelta
import matplotlib.pyplot as plt
from scipy.stats import norm
from statsmodels.stats.weightstats import ztest
import seaborn as sns
import plotly.graph_objs as go
from sklearn import linear_model as lm

from spotify.plotting.utils import standard_layout
import spotify.data_engineering as de
import logging

from goodreads.models import SpotifyStreaming, SpotifyTracks

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


def tracks_all_query():
    query = f""" 
        select 
        artistname, 
        trackname, 
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
        from goodreads_spotifytracks tracks
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


def format_song_day(df, artist_col, song_col, date_col, n=15):
    df_song_day = pd.DataFrame(
        df.groupby([artist_col, song_col, date_col], as_index=False).size()
    )
    df_song_day.rename(columns={"size": "n"}, inplace=True)
    top_songs_df = pd.DataFrame(
        df.groupby([artist_col, song_col], as_index=False).size()
    )
    top_songs_df.sort_values("size", ascending=False, inplace=True)
    top_songs_df = top_songs_df.head(n)
    logger.info(f"top songs: {top_songs_df}")
    df_song_day_select = df_song_day[
        (df_song_day[artist_col].isin(top_songs_df[artist_col]))
        & (df_song_day[song_col].isin(top_songs_df[song_col]))
    ]
    return df_song_day_select


def plot_song_day(df, artist_col, song_col, date_col):
    df_song = format_song_day(
        df=df, artist_col=artist_col, song_col=song_col, date_col=date_col
    )
    df_song["combined"] = "<b>" + df_song[song_col] + "</b><br>" + df_song[artist_col]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_song[date_col],
            y=df_song["combined"],
            customdata=df_song[artist_col],
            text=df_song["n"],
            mode="markers",
            marker={"size": np.sqrt(df_song["n"]) * 4},
            name=None,
            hovertemplate="%{y}<br>%{x}<br>Plays: %{text}<extra></extra>",
        )
    )

    fig.update_layout(
        showlegend=False,
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
    df["first"] = df["first"].fillna(False)
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
        [
            go.Bar(
                x=count_new_df[date_col],
                y=count_new_df[firsts_col],
                hovertemplate="%{x}<br><b>New Songs: </b>%{y}<extra></extra>",
                name="New Songs",
            )
        ]
    )
    fig.add_trace(
        go.Scatter(
            x=count_new_df[date_col],
            y=count_new_df[f"rolling_{firsts_col}"].round(1),
            mode="lines",
            line=go.scatter.Line(color="purple"),
            hovertemplate="%{x}<br><b>New Songs: </b>%{y}<br>(Rolling Average)<extra></extra>",
            name=f"New Songs - {win} Day Rolling",
        )
    )
    fig.update_layout(
        title="New Songs",
        yaxis=dict(
            title="Minutes",
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
    new_songs = new_df.loc[(new_df["date"] <= d1) & (new_df["date"] >= d2)]
    new_songs = new_songs.loc[new_songs["first"] == True]
    sample_df = new_songs.sample(5)
    songs = [
        f"{song} by {artist}"
        for song, artist in zip(sample_df["trackname"], sample_df["artistname"])
    ]
    text = f"You listened to the most new songs around {max_new['date'].date()}, "
    text += f"such as <b>{songs[0]}</b>, <b>{songs[1]}</b> and <b>{songs[2]}</b>."

    return text


def write_week_text(df_wday):
    wday_avg = pd.pivot_table(
        df_wday, index="day_of_week", values="minutes", aggfunc=np.mean
    ).reset_index()
    day_high = wday_avg["day_of_week"][np.argmax(wday_avg["minutes"])]
    day_low = wday_avg["day_of_week"][np.argmin(wday_avg["minutes"])]
    minutes_high = df_wday.loc[df_wday["day_of_week"] == day_high]
    minutes_low = df_wday.loc[df_wday["day_of_week"] == day_low]
    av_high = round(minutes_high["minutes"].mean())
    av_low = round(minutes_low["minutes"].mean())
    text_week = f"You listen to the most music on <b>{day_high}</b> and the least on <b>{day_low}</b>, "
    alpha = ztest(minutes_high["minutes"], minutes_low["minutes"], 0)[1]
    if alpha > 0.05:
        text_week += "but the difference between them is not statistically significant."
    else:
        text_week += f"with an average of <b>{av_high}</b> and <b>{av_low}</b> minutes respectively."

    return text_week


def plot_overall(df_sum, date_col="date", minutes_col="minutes", win=7, podcast=True):
    """
    Timeline plot with a bar chart for a date column, plus a rolling average line of window win
    """
    df_sum[minutes_col] = df_sum[minutes_col].round(1)
    fig = go.Figure()
    if podcast:
        for p in [True, False]:
            df_sum_sub = df_sum[df_sum["podcast"] == p]
            fig.add_trace(
                go.Bar(
                    x=df_sum_sub[date_col],
                    y=df_sum_sub[minutes_col],
                    name="Daily Minutes",
                    hovertemplate="<b>Date: </b>%{x}<br><b>Minutes: </b>%{y}<extra></extra>",
                    showlegend=False,
                )
            )
    else:
        fig.add_trace(
            go.Bar(
                x=df_sum[date_col],
                y=df_sum[minutes_col],
                hovertemplate="<b>Date: </b>%{x}<br><b>Minutes: </b>%{y}<extra></extra>",
                name="Daily Minutes",
                showlegend=False,
            )
        )
    fig.add_trace(
        go.Scatter(
            x=df_sum[date_col],
            y=df_sum["rolling_average"],
            mode="lines",
            line=go.scatter.Line(color="red"),
            hovertemplate="<b>Date: </b>%{x}<br><b>Minutes (Rolling Average):</b> %{y}<extra></extra>",
            name=f"{win} Day Rolling Average",
        )
    )
    fig.update_layout(
        title="Overall Consumption",
        yaxis=dict(
            title="Minutes",
        ),
        hovermode="x unified",
    )
    fig.update_layout(standard_layout)
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
    df_artist_day[date_col] = pd.to_datetime(df_artist_day[date_col])

    return df_artist_day


def format_artist_list_day(
    df,
    artist_list,
    artist_col="artistname",
    date_col="date",
    minutes_col="minutes",
    other=False,
):
    """
    Different unction from `format_artist_day`
    This one takes a list of artists to keep, which should come from get_top_artists_range
    It calculates minutes played for all those artists, and lumps everything else into "Other"
    """
    df = df.copy()
    if artist_list is not None:
        if other:
            df[artist_col] = [
                name if name in artist_list else "Other" for name in df[artist_col]
            ]
        else:
            df = df.loc[df[artist_col].isin(artist_list)]
    df_artist_day = pd.pivot_table(
        df, index=[artist_col, date_col], values=minutes_col, aggfunc=sum
    ).reset_index()
    df_artist_day.columns = [artist_col, date_col, minutes_col]
    df_artist_day[date_col] = pd.to_datetime(df_artist_day[date_col])

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


def get_top_artist_date(
    df,
    date_start,
    date_end,
    date_col="date",
    artist_col="artistname",
    minutes_col="duration",
):
    df[date_col] = pd.to_datetime(df[date_col])
    sub_df = df[(df[date_col] >= date_start) & (df[date_col] <= date_end)]
    sub_df_pivot = pd.pivot_table(
        sub_df, index=[artist_col], values=minutes_col, aggfunc=sum
    ).reset_index()
    if len(sub_df_pivot) < 1:
        # there may be no music listened in this period
        return sub_df_pivot
    sub_df_pivot.sort_values(by=minutes_col, ascending=False, inplace=True)
    sub_df_pivot = sub_df_pivot.head(1)
    sub_df_pivot["date_start"] = date_start
    sub_df_pivot["date_end"] = date_end
    sub_df_pivot["date_start"] = sub_df_pivot["date_start"].dt.date
    sub_df_pivot["date_end"] = sub_df_pivot["date_end"].dt.date
    return sub_df_pivot


def get_top_artists_range(df, periods, artist_col="artistname"):
    df = df.copy()
    df = df.loc[df[artist_col] != "Other"]
    date_range = pd.date_range(
        start=df["date"].min(), end=df["date"].max(), periods=periods
    )
    moments = []
    for i in range(0, len(date_range) - 1):
        moments.append(
            get_top_artist_date(
                df, date_start=date_range[i], date_end=date_range[i + 1]
            )
        )
    moments_df = pd.concat(moments)
    moments_df.reset_index(drop=True, inplace=True)

    def mid_date(d1, d2):
        return pd.to_datetime(pd.Series([d1, d2])).mean()

    moments_df["date_mid"] = moments_df.apply(
        lambda x: mid_date(x["date_start"], x["date_end"]), axis=1
    )
    return moments_df


def sunday_of_calenderweek(year, week):
    first = date(year, 1, 1)
    base = 0 if first.isocalendar()[1] == 0 else 7
    return first + timedelta(days=base - first.isocalendar()[2] + 7 * (week - 1))


def flatten_adjacent(df, date_col="date_start"):
    """
    Recursive function complementing get_top_artists_range
    Reduces the dataframe if multiple adjacent periods are dominated by the same artist
    """
    if len(df) <= 1:
        return df
    else:
        start_date = df[date_col].values[0]
        if df["artistname"].values[0] == df["artistname"].values[1]:
            df = df[1:]
            df[date_col].values[0] = start_date
            return flatten_adjacent(df)
        else:
            return pd.concat([df.head(1), flatten_adjacent(df[1:])])


def plot_top_artists_over_time(df, periods=10):
    """
    For now, keep periods <= 10
    """
    artists_range_df = get_top_artists_range(df, periods=periods)
    artists_range_df = flatten_adjacent(artists_range_df)
    artist_list = artists_range_df["artistname"].unique()

    artist_df = format_artist_list_day(df, artist_list=artist_list)
    artist_df_week = format_group_granular(
        artist_df, granularity="week", index_cols=["artistname"], time_col="date"
    )

    fig = go.Figure()
    art_palette = {}

    for i, a in enumerate(artist_df_week["artistname"].unique()):
        # assign a color to each artist
        art_palette[a] = px.colors.qualitative.Plotly[i]
        a_df = artist_df_week.loc[artist_df_week["artistname"] == a]
        fig.add_trace(
            go.Bar(
                x=a_df["date"],
                y=a_df["minutes"].round(1),
                customdata=a_df["artistname"],
                width=60 * 60 * 24 * 7 * 1000,
                name=a,
                hovertemplate="%{customdata}<br><b>Total Minutes:</b> %{y}<extra></extra> ",
                marker=dict(color=art_palette[a]),
            )
        )
    fig.update_layout(
        barmode="stack", xaxis=dict(title="Date"), yaxis=dict(title="Minutes")
    )
    full_fig = fig.full_figure_for_development()
    yrange = full_fig.layout.yaxis.range
    for i, row in artists_range_df.iterrows():
        ## y_annot has some above line and some below line
        a = row["artistname"]
        y_annot = yrange[1] * (1 + 0.10 * (-1) ** i)
        fig.add_trace(
            go.Scatter(
                x=[row["date_start"], row["date_end"]],
                y=[yrange[1], yrange[1]],
                mode="lines",
                text=row["artistname"],
                customdata=[row["artistname"]],
                hovertemplate="<b>Date:</b> %{x}<br>%{customdata}<extra></extra> ",
                marker=dict(color=art_palette[a]),
                showlegend=False,
            )
        )
        fig.add_annotation(
            x=row["date_mid"],
            y=y_annot,
            text=row["artistname"],
            showarrow=False,
            font=dict(color=art_palette[a]),
        )

    fig.update_layout(standard_layout)
    return fig


def format_weekly(df, date_col="date"):
    d = dict(enumerate(calendar.day_name))
    df_wday = pd.pivot_table(
        df, index=date_col, values="minutes", aggfunc=sum
    ).reset_index()
    df_wday[date_col] = pd.to_datetime(df_wday[date_col])
    df_wday["wday"] = df_wday["date"].dt.weekday
    df_wday["day_of_week"] = df_wday["wday"].map(d)
    return df_wday


def plot_weekly(df, date_col="date"):
    df_wday = format_weekly(df, date_col=date_col)
    df_wday.sort_values('wday', inplace=True)
    # weekly boxplot
    fig = go.Figure()
    for day in df_wday["day_of_week"].unique():
        df_day = df_wday.loc[df_wday["day_of_week"] == day]
        fig.add_trace(go.Box(y=df_day["minutes"].round(1), name=day, showlegend=False))
    fig.update_layout(standard_layout)
    return fig


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
    music_df,
    granularity="month",
    artist_col="artistname",
    song_col="trackname",
    time_col="endtime",
    n=4,
):
    one_hit_wonders_df = format_one_hit_wonder(music_df, artist_col=artist_col)
    one_hit_artists = one_hit_wonders_df[artist_col][:n]
    m = music_df[music_df[artist_col].isin(one_hit_artists)]
    m_pivotted = format_group_granular(
        m, granularity=granularity, index_cols=[artist_col, song_col]
    )
    m_pivotted["hit"] = m_pivotted[song_col] + " - " + m_pivotted[artist_col]
    m_pivotted["date"] = m_pivotted[time_col].dt.date
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
    """
    Group granular time data into a larger time segment, ie from days to weeks
    Returns df with column names [index_cols, 'segment', 'year', minutes_col, time_col]
    """
    df = df.copy()
    if granularity == "week":
        df["segment"] = df[time_col].dt.isocalendar().week
    elif granularity == "month":
        df["segment"] = df[time_col].dt.month
    else:
        raise Exception("granularity must be one of day, week, month or year")
    # all granularities also need the year
    df["year"] = df[time_col].dt.year

    m_pivotted = pd.pivot_table(
        df, index=index_cols + ["segment", "year"], values=minutes_col, aggfunc=sum
    ).reset_index()

    segment_df = pd.pivot_table(
        df, index=["segment", "year"], values=time_col, aggfunc=min
    ).reset_index()
    m_pivotted = pd.merge(m_pivotted, segment_df, on=["segment", "year"])

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
            hovertemplate="<b>Year:</b> %{x}<br> <b>Total minutes:</b> %{y}<extra></extra>",
            name="Minutes - Total",
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Bar(
            x=years_df[feature_col],
            y=years_df[minutes_col],
            customdata=years_df[index_col],
            hovertemplate="<b>Year:</b> %{x}<br><b>Top artist:</b> %{customdata}<extra></extra>",
            name="Minutes - Top Artist",
        )
    )
    fig.update_layout(
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
            hovertemplate="<b>Genre:</b> %{y} <br><b>Total Minutes:</b> %{x}<extra></extra>",
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
            hovertemplate="<b>Top artist:</b> %{customdata[0]} <br><b>Minutes:</b> %{customdata[1]} <extra></extra>",
            orientation="h",
            name="Minutes - Top Artist",
        )
    )
    fig.update_layout(
        barmode="overlay",
        xaxis=dict(title="Minutes"),
        yaxis=dict(title="Genre"),
    )
    fig.update_layout(standard_layout)

    return fig


def create_normal_line(
    value_series,
    start=0,
    end=100,
    mean=50,
    sd=19,
):
    """
    Given a series, fit a normal distribution curve to it. Designed to complement popularity plot
    """
    normal_array = norm.pdf(np.arange(start, end), mean, sd) * value_series.sum()

    return normal_array


def plot_popularity(
    df, minutes_col="minutes", track_col="trackname", artist_col="artistname"
):
    df = df.copy()
    df = df.loc[df["popularity"] > 0]
    df["song"] = df[track_col] + " - " + df[artist_col]
    df_agg = get_max_agg(
        df, feature_col="popularity", minutes_col=minutes_col, index_col="song"
    )
    pop_agg_dict = df_agg.set_index("popularity")["song"].to_dict()
    pop = pd.pivot_table(
        df, index="popularity", values=minutes_col, aggfunc=sum
    ).reset_index()
    pop["song"] = pop["popularity"].map(pop_agg_dict)
    # create a normal distribution line, scaled to this plot
    normal_array = create_normal_line(pop["minutes"])
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=pop["popularity"],
            y=round(pop["minutes"]),
            customdata=pop["song"],
            hovertemplate="Popularity: %{x} <br>Total Minutes: %{y} <br>Top Track: %{customdata}<extra></extra>",
            name="Minutes - Total",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=np.arange(0, 100),
            y=normal_array,
            mode="lines",
            name="Normal Distribution",
            hoverinfo="none",
        )
    )
    fig.update_layout(
        title="Popularity",
        title_x=0.5,
        xaxis_title="Popularity (Spotify calculation)",
        yaxis_title="Count",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
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

    df_period["time_of_day"] = pd.to_datetime(
        df_period["time_period"], format="%H:%M:%S"
    )
    full_day = np.arange(
        datetime.datetime(1900, 1, 1),
        datetime.datetime(1900, 1, 2),
        timedelta(minutes=15),
    ).astype(datetime.datetime)
    full_day_df = pd.DataFrame(
        {
            "time_of_day": np.tile(full_day, 2),
            "weekend": np.repeat([True, False], len(full_day)),
        }
    )
    df_period = pd.merge(
        full_day_df, df_period, on=["time_of_day", "weekend"], how="left"
    )
    df_period = pd.merge(df_period, weekend_count, on="weekend")
    df_period["minutes"] = df_period["minutes"].fillna(0)
    df_period["minutes_scaled"] = df_period["minutes"] / df_period["date"]
    df_period["time_period"] = df_period["time_of_day"].dt.time
    df_period["time_minute"] = (
        df_period["time_of_day"].dt.hour * 60 + df_period["time_of_day"].dt.minute
    )
    return df_period


def plot_daily(df, date_col="endtime"):
    daily_df = format_daily(df, date_col=date_col)
    fig = go.Figure()
    weekend_df = daily_df.loc[daily_df["weekend"] == True]
    weekday_df = daily_df.loc[daily_df["weekend"] == False]
    fig.add_trace(
        go.Scatter(
            x=weekend_df["time_of_day"],
            y=weekend_df["minutes_scaled"],
            customdata=weekend_df["time_period"],
            hovertemplate="Weekend<br>Time: <b>%{customdata}</b><extra></extra>",
            name="Weekend",
            line=dict(color="firebrick", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=weekday_df["time_of_day"],
            y=weekday_df["minutes_scaled"],
            customdata=weekday_df["time_period"],
            hovertemplate="Weekday<br>Time: <b>%{customdata}</b><extra></extra>",
            name="Weekday",
            line=dict(color="blue", width=2),
        )
    )
    fig.update_layout(
        xaxis=dict(
            ticktext=pd.unique(daily_df["time_period"]),
            tickformat="%H:%M:%S",
            type="date",
            title="Time",
        ),
        yaxis=dict(title="Usage", tickformat=",.0%"),
    )
    fig.update_layout(standard_layout)
    return fig


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
    text = f"Your most skipped tracks are <b>{skippedTracks[0]}</b> (skipped {skipped[0]} out of {played[0]}) and "
    text += f"<b>{skippedTracks[1]}</b> ({skipped[1]} out of {played[1]})."
    return text


def format_last_listened(df, index_cols=["artistname", "trackname", "uri"]):
    last_listen_df = pd.pivot_table(
        df, index=index_cols, values="endtime", aggfunc=[len, max]
    ).reset_index()
    last_listen_df.columns = index_cols + ["n", "last_listened"]
    last_listen_df["days_since"] = (
        last_listen_df["last_listened"].max() - last_listen_df["last_listened"]
    ).dt.days
    return last_listen_df


def write_last_listened(df):
    last_listen_df = format_last_listened(
        df, index_cols=["artistname", "trackname", "uri"]
    )
    # get rid of single listens for regression purposes
    last_listen_df = last_listen_df.loc[last_listen_df["n"] > 1]
    last_listen_df.reset_index(drop=True, inplace=True)
    x = last_listen_df["days_since"].values.reshape(-1, 1)
    # take log
    last_listen_df["y"] = np.log(last_listen_df["n"])
    # fit regression of days_since ~ log(n)
    lm1 = lm.LinearRegression().fit(x, last_listen_df["y"])
    last_listen_df["predictions"] = lm1.predict(x)
    last_listen_df["residuals"] = last_listen_df["y"] - lm1.predict(x)
    # which song is the biggest outlier?
    # let's say it hasn't been listened to in at least 7 days
    last_sub_df = last_listen_df.loc[last_listen_df["days_since"] >= 7]
    if len(last_sub_df) > 0:
        song_i = np.argmax(last_sub_df["residuals"])
        forgotten_song = last_sub_df.iloc[song_i]
    else:
        # if there are no songs over a week, unlikely scenario
        song_i = np.argmax(last_listen_df["residuals"])
        forgotten_song = last_listen_df.iloc[song_i]

    text = f"You listened to <b>{forgotten_song['trackname']}</b> by {forgotten_song['artistname']} {forgotten_song['n']} times in this period."
    text += (
        f"  However you haven't listened to it in {forgotten_song['days_since']} days."
    )
    return text


def multiplot_overall(df):
    df_sums = sum_days(df, podcast=True)
    new_df = format_new_songs(
        df, time_col="endtime", index_cols=["artistname", "trackname"]
    )
    count_news = count_new(new_df)

    fig = make_subplots(
        3,
        1,
        subplot_titles=["Volume Timeline", "New Songs", "Weekday Usage"],
        shared_xaxes=True,
        vertical_spacing=0.08,
    )
    overall = [
        plot_overall(df_sums, podcast=True),
        plot_new(count_news),
        plot_weekly(df),
    ]
    for i, figure in enumerate(overall):
        for trace in range(len(figure["data"])):
            fig.add_trace(figure["data"][trace], row=i + 1, col=1)
            fig.update_yaxes(title_text="Minutes", row=i + 1, col=1)

        for annotation in figure.select_annotations():
            fig.add_annotation(annotation, row=i + 1, col=1)
    fig.update_layout(standard_layout)
    fig.update_xaxes(showline=True, linecolor="rgb(36,36,36)")
    fig.update_yaxes(showline=True, linecolor="rgb(36,36,36)")
    fig.update_layout(
        xaxis_showticklabels=True,
        xaxis2_showticklabels=True,
        showlegend=False,
    )
    return fig


def write_text(filename, texts):
    if isinstance(texts, list):
        text = "\n\n".join(texts)
    else:
        text = texts
    with open(filename, "w") as f:
        f.write(text)


def objects_to_df(objects):
    df = pd.DataFrame.from_records(objects.values())
    return df


def load_data(username):
    user_df = objects_to_df(SpotifyStreaming.objects.filter(username=username))
    tracks_df = objects_to_df(
        SpotifyTracks.objects.filter(
            artistname__in=user_df["artistname"], trackname__in=user_df["trackname"]
        )
    )
    df = pd.merge(user_df, tracks_df, on=["artistname", "trackname"], how="left")
    logger.info(
        f"Spotify data read for {username} with {len(df)} rows \n : {df.head()}"
    )
    df = preprocess(df)
    return df


def main(username):
    df = load_data(username)
    path = f"goodreads/static/Graphs/{username}"
    if not (os.path.exists(path) and os.path.isdir(path)):
        os.mkdir(path)

    fig_overall = multiplot_overall(df)
    fig_overall.write_html(
        f"goodreads/static/Graphs/{username}/spotify_overall_{username}.html"
    )

    fig_year = plot_years(
        df, feature_col="release_year", minutes_col="minutes", index_col="artistname"
    )
    fig_year.write_html(
        f"goodreads/static/Graphs/{username}/spotify_year_plot_{username}.html"
    )

    fig_top_artists = plot_top_artists_over_time(df)
    fig_top_artists.write_html(
        f"goodreads/static/Graphs/{username}/spotify_top_artists_plot_{username}.html"
    )
    fig_daily = plot_daily(df)
    fig_daily.write_html(
        f"goodreads/static/Graphs/{username}/spotify_daily_plot_{username}.html"
    )

    fig_popularity = plot_popularity(df)
    fig_popularity.write_html(
        f"goodreads/static/Graphs/{username}/spotify_popularity_plot_{username}.html"
    )

    fig_genre = plot_genres(df, genre_col="genre_chosen", n=25)
    fig_genre.write_html(
        f"goodreads/static/Graphs/{username}/spotify_genre_plot_{username}.html"
    )

    fig_songs = plot_song_day(
        df, artist_col="artistname", song_col="trackname", date_col="date"
    )
    fig_songs.write_html(
        f"goodreads/static/Graphs/{username}/spotify_top_songs_{username}.html"
    )

    write_text(
        filename=f"goodreads/static/Graphs/{username}/spotify_summary_{username}.txt",
        texts=[write_new_info(df), write_skips_summary(df), write_last_listened(df)],
    )

    write_text(
        filename=f"goodreads/static/Graphs/{username}/spotify_weekly_{username}.txt",
        texts=[write_week_text(format_weekly(df, date_col="date"))],
    )
