import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import networkx as nx
import plotly.express as px
import plotly
import logging

from goodreads.models import NetflixGenres, NetflixUsers, NetflixActors
from goodreads.plotting.plotting import split_title
from spotify.plotting.utils import standard_layout, save_fig
import netflix.data_munge as nd

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

palette = plotly.colors.qualitative.Plotly


def load_data(username):
    """
    Given a username, return their streaming history merged with titles data
    """
    df = pd.DataFrame.from_records(
        NetflixUsers.objects.filter(username=username).values()
    )
    df = nd.pipeline_steps(df)
    return df


def plot_genres(df, username, title_type, genre_col = "genre_chosen"):
    # df should be already formatted, genres cleaned up
    # only tv shows or movies
    df_count = pd.DataFrame(
        df.groupby(["name", "genre_chosen", "title_type"], as_index=False).size()
    )
    df_genre_count = pd.DataFrame(
        df.groupby(genre_col, as_index=False).size()
    ).sort_values("size")
    fig = go.Figure()
    df_shows = df_count.loc[df_count["title_type"] == title_type]
    for i, g in enumerate(df_genre_count[genre_col]):
        df_sub = df_shows.loc[df_shows[genre_col] == g]
        df_sub[genre_col] = '<b>' + df_sub[genre_col] + '</b>'
        fig.add_trace(
            go.Bar(
                x=df_sub["size"],
                y=df_sub["genre_chosen"],
                customdata=df_sub["name"],
                text=df_sub["name"],
                hovertemplate="Genre: <b>%{y}</b><br>Title: <b>%{customdata}</b> <br>Count: <b>%{x}</b><extra></extra>",
                name=g,
                orientation="h",
                insidetextanchor="middle",
            )
        )
    fig.update_layout(
        barmode="stack",
        xaxis_title="Number of Shows",
    )
    fig.update_layout(standard_layout)
    return fig


genres_hierarchy = [
    "Sci-Fi & Fantasy",
    "Stand-up Comedy",
    "Mexican",
    "Korean",
    "Comedies",
    "Food & Travel",
    "Musicals",
    "Mystery",
    "Indian",
    "Science & Nature",
    "Documentaries",
    "Historical Dramas",
    "Anime",
    "Japanese",
    "Crime Action & Adventure",
    "Docuseries",
    "Kids",
    "Dramas",
    "Horror",
    "LGBTQ",
    "Reality",
    "British",
    "Chinese",
]


def reduce_genre(genre):
    if genre is None:
        return ""
    stop_words = [
        "TV",
        "Shows",
        "Programmes",
        "Movies",
        "&#39;'",
        "&#39;",
        "Films",
        "Series",
        "Features",
    ]
    genre_mapper = {
        "for ages 5 to 7": "Kids",
        "Kids for ages 8 to 10": "Kids",
        "for ages 8 to 10": "Kids",
        "Kids & Family": "Kids",
        "Children & Family": "Kids",
        "Late Night Comedies": "Comedies",
        "Action Thrillers": "Action & Adventure",
        "Independent Dramas": "Dramas",
        "Social Issue Dramas": "Dramas",
        "Mysteries": "Mystery",
        "Comedy": "Comedies",
        "LGBTQ Dramas": "LGBTQ",
        "Supernatural Thrillers": "Thrillers",
        "Drama": "Dramas",
        "Sitcoms": "Comedies",
        "Stand-Up Comedy & Talk": "Stand-Up Comedy",
        "Stand-up Comedy": "Stand-Up Comedy",
        "Family Sci-Fi & Fantasy": "Sci-Fi & Fantasy",
        "Spoofs & Satires": "Comedies",
        "Kids  for ages 11 to 12": "Kids",
        "Kids'": "Kids",
        "Cult Comedies": "Comedies",
        "Music & Musicals": "Musicals",
    }
    for w in stop_words:
        genre = genre.replace(w, "")
    genre = (", ").join([g.strip() for g in genre.split(", ")])

    genre = genre_mapper[genre] if genre in genre_mapper.keys() else genre
    return genre


def simplify_genres(genres):
    """
    Takes a string that could be split by comma
    """

    genres_list = genres.split(", ")
    genres_list = [reduce_genre(g) for g in genres_list]

    # iterate through the hierarchy established
    for g in genres_hierarchy:
        if g in genres_list:
            return g
    # if no match in the hierarchy, take top item
    return genres_list[0]


def format_timeline(df, values=["season", "episode", "genre_chosen", "netflix_id"]):
    agg_dict = {v: "first" for v in values}
    agg_dict.update({"username": len})
    daily_df = pd.pivot_table(
        df,
        index=["name", "date"],
        values=values,
        aggfunc=agg_dict,
    ).reset_index()
    return daily_df


def plot_timeline(df, username):
    fig = go.Figure()
    series_df = df.loc[df["title_type"] == "series"]
    series_df = format_timeline(
        series_df,
        values=["season", "episode", "genre_chosen", "netflix_id", "username"],
    )
    # wrap names to deal with titles that are too long and ruin the plot
    series_df["name_short"] = series_df["name"].apply(lambda x: split_title(x, 40))
    # order by top genre
    genres = list(series_df["genre_chosen"].value_counts().index)
    n_palette = len(palette)
    if len(genres) > n_palette:
        other_genres = {k: "Other" for k in list(genres[(n_palette - 1) :])}
        series_df["genre_chosen_truncated"] = (
            series_df["genre_chosen"]
            .map(other_genres)
            .fillna(series_df["genre_chosen"])
        )
        genres = genres[:n_palette] + ["Other"]

    for i, genre in enumerate(genres):
        g_df = series_df.loc[series_df["genre_chosen"] == genre]
        for j, nid in enumerate(g_df["netflix_id"].unique()):
            s_df = g_df.loc[g_df["netflix_id"] == nid]
            fig.add_trace(
                go.Scatter(
                    x=s_df["date"],
                    y=s_df["name_short"],
                    mode="lines+markers",
                    marker=dict(color=palette[i], size=s_df["username"] * 5),
                    line=dict(dash="dash", color="rgba(0, 0, 0, 0.3)"),
                    customdata=np.stack(
                        (s_df["season"], s_df["username"], s_df["name"]), axis=-1
                    ),
                    name=genre,
                    text=s_df["episode"],
                    hovertemplate="<b>Date:</b> %{x} <br><b>Name:</b> %{customdata[2]} <br>%{customdata[0]}<br><b>Count:</b> %{customdata[1]}<extra></extra>",
                    legendgroup=genre,
                    showlegend=j == 0,
                )
            )
    fig.update_layout(
        yaxis=dict(tickfont=dict(size=9), title="Show Name", tickmode="linear"),
        xaxis=dict(title="Date"),
        height=len(series_df["name"].unique()) * 12,
    )
    fig.update_layout(standard_layout)
    return fig


def plot_hist(df, username):
    from scipy.stats import mode

    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year
    df_hist = pd.pivot_table(
        df,
        index=["month", "year", "title_type"],
        values=["name"],
        aggfunc=[len, lambda x: mode(x)[0]],
    ).reset_index()
    df_hist.columns = ["month", "year", "title_type", "n", "Top Show"]
    df_hist["segment"] = (
        df_hist["year"].astype(str) + "-" + df_hist["month"].astype(str)
    )
    fig = go.Figure()
    for t in df_hist["title_type"].unique():
        df_plot = df_hist.loc[df_hist["title_type"] == t]
        if t == "series":
            hovert = (
                "<b>Time:</b> %{x}<br><b>Top Show:</b> %{customdata}<extra></extra>"
            )
        else:
            hovert = "<b>Time:</b> %{x}<br><b>Movie:</b> %{customdata}<extra></extra>"
        fig.add_trace(
            go.Bar(
                x=df_plot["segment"],
                y=df_plot["n"],
                customdata=df_plot["Top Show"],
                hovertemplate=hovert,
                name=t,
            )
        )
    fig.update_layout(
        barmode="stack",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Count"),
    )
    fig.update_layout(standard_layout)
    return fig


def plot_network(df, username):
    G = nd.format_network(df)
    pos = nx.kamada_kawai_layout(G, scale=0.3)
    show_names = df["name"].unique()
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
        showlegend=False,
    )

    node_x = []
    node_y = []
    show_bool = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        show_bool.append(node in show_names)

    node_df = pd.DataFrame(
        {
            "x": node_x,
            "y": node_y,
            "names": list(G.nodes),
            "n": [len(adjacencies[1]) for adjacencies in G.adjacency()],
        }
    )
    node_df["type"] = [
        "show" if name in show_names else "actor" for name in node_df["names"]
    ]

    fig = go.Figure()
    fig.add_trace(edge_trace)
    for i, t in enumerate(["show", "actor"]):
        n_df = node_df.loc[node_df["type"] == t]
        if t == "show":
            marker_dict = dict(size=10, line_width=2, color=palette[i])
        else:
            marker_dict = dict(
                size=n_df["n"] * 5,
                line_width=2,
                color=palette[i],
            )
        fig.add_trace(
            go.Scatter(
                x=n_df["x"],
                y=n_df["y"],
                mode="markers",
                marker=marker_dict,
                customdata=np.stack((n_df["names"], n_df["n"]), axis=-1),
                name=t,
                hovertemplate="<b>%{customdata[0]}</b><br># of connections: %{customdata[1]}<extra></extra>",
            )
        )

    fig.update_layout(
        titlefont_size=16,
        hovermode="closest",
        margin=dict(b=20, l=5, r=5, t=40),
        annotations=[
            dict(
                text="Kevin Bacon visualization",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.005,
                y=-0.002,
            )
        ],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
    fig.update_layout(standard_layout)
    return fig


def find_max(username):
    """
    Given user, find the day and show and number of the max binge day
    """
    df = load_data(username)
    daily_df = format_timeline(df, values=["username"])
    return_max = daily_df.iloc[np.argmax(daily_df["username"])]
    return_max["date"] = return_max["date"].date()
    return return_max


def plot_comparison(combined_plot, name1, name2):
    fig = go.Figure()
    pal = ["#636EFA", "#AB63FA", "#EF553B"]
    xm = 0
    for i, p in enumerate([name1, "both", name2]):
        combined_shows_p = combined_plot.loc[combined_plot["person"] == p]
        combined_shows_p["genre_ranked"] = combined_shows_p["genre_num"].rank(
            method="first"
        )
        index_max = combined_shows_p["group_index"].max()
        fig.add_trace(
            go.Scatter(
                x=(
                    combined_shows_p["group_index"]
                    / combined_shows_p["group_index_max"]
                )
                * index_max
                + xm
                + 10 * i,
                y=combined_shows_p["genre_num"] * 25 + combined_shows_p["rand"] / 5,
                text=combined_shows_p["name"],
                textposition="bottom center",
                mode="markers+text",
                customdata=combined_shows_p["n"],
                marker=dict(size=3 * np.sqrt(combined_shows_p["n"]) + 3, color=pal[i]),
                textfont=dict(
                    family="Courier New, monospace",
                    size=8,  # Set the font size here
                    color="RebeccaPurple",
                ),
                hovertemplate="<b>%{text}</b><br>Episodes Watched: %{customdata}<br><extra></extra>",
                name=p,
            )
        )
        xm += index_max
    fig.update_layout(
        yaxis=dict(title="Intensity"),
        xaxis=dict(visible=False),
        title="Comparison Plot",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def main(username):
    """
    df has been through pipeline steps already
    """
    df = load_data(username)
    nids = df["netflix_id"][pd.notnull(df["netflix_id"])].unique().astype(int)
    genres_df = pd.DataFrame.from_records(
        NetflixGenres.objects.filter(netflix_id__in=nids).values()
    )
    genres_df["genres"] = genres_df["genres"].fillna("")
    logger.info("Simplifying genres")
    genres_df["genre_chosen"] = genres_df["genres"].apply(simplify_genres)
    df_merged = pd.merge(df, genres_df, on="netflix_id", how="left")
    fig_plotline = plot_timeline(df_merged, username)
    save_fig(
        fig_plotline,
        f"goodreads/static/Graphs/{username}/netflix_timeline_{username}.html",
    )
    fig_genres_s = plot_genres(df_merged, username, "series")
    save_fig(
        fig_genres_s,
        f"goodreads/static/Graphs/{username}/netflix_genres_{username}_series.html",
    )
    fig_genres_m = plot_genres(df_merged, username, "movie")
    save_fig(
        fig_genres_m,
        f"goodreads/static/Graphs/{username}/netflix_genres_{username}_movie.html",
    )
    fig_hist = plot_hist(df_merged, username)
    save_fig(
        fig_hist,
        f"goodreads/static/Graphs/{username}/netflix_histogram_{username}.html",
    )
    actors_df = pd.DataFrame.from_records(
        NetflixActors.objects.filter(netflix_id__in=nids).values()
    )
    df_network = pd.merge(
        df_merged, actors_df, on="netflix_id", how="left"
    ).drop_duplicates(subset="name")
    fig_network = plot_network(df_network, username)
    save_fig(
        fig_network,
        f"goodreads/static/Graphs/{username}/netflix_network_{username}.html",
    )
    df_network.to_csv(
        f"goodreads/static/Graphs/{username}/netflix_process_{username}.csv",
        index=False,
    )
