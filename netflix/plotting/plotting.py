import os
import pandas as pd
import numpy as np
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
import networkx as nx
import plotly.express as px
import logging

from goodreads.models import NetflixGenres, NetflixUsers, NetflixActors
from spotify.plotting.plotting import standard_layout
import netflix.data_munge as nd

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def plot_genres(df, username, title_type):
    # df should be already formatted, genres cleaned up
    # only tv shows or movies
    df_count = pd.DataFrame(
        df.groupby(["name", "genre_chosen", "title_type"], as_index=False).size()
    )
    df_genre_count = pd.DataFrame(
        df.groupby("genre_chosen", as_index=False).size()
    ).sort_values("size")
    fig = go.Figure()
    df_shows = df_count.loc[df_count["title_type"] == title_type]
    for g in df_genre_count["genre_chosen"]:
        df_sub = df_shows.loc[df_shows["genre_chosen"] == g]

        fig.add_trace(
            go.Bar(
                x=df_sub["size"],
                y=df_sub["genre_chosen"],
                customdata=df_sub["name"],
                text=df_sub["name"],
                hovertemplate="Genre: %{y} <br> Title: %{customdata} <br> Count: %{x}",
                name=g,
                orientation="h",
                insidetextanchor="middle",
            )
        )
    fig.update_layout(barmode="stack", title=f"Netflix Genres - {username} - {title_type.capitalize()}")
    fig.update_layout(standard_layout)
    return fig


genres_hierarchy = ['Sci-Fi & Fantasy', 'Stand-up Comedy', 'Mexican', 'Korean', 'British', 'Musicals',
                   'Mystery', 'Indian', 'Science & Nature', 'Documentaries', 'Historical Dramas', 'Japanese',
                    'Crime Action & Adventure', 'Anime', 'Docuseries', 'Kids', 'Dramas', 'Horror',
                    'LGBTQ', "International", 'Reality']


def simplify_genres(genres):
    genres_list = genres.split(', ')
    stop_words = ['TV', 'Shows', 'Programmes', 'Movies', "&#39;'", "&#39;", 'Films', 'Series']
    genre_mapper = {'for ages 5 to 7': 'Kids',
                    'Kids for ages 8 to 10': 'Kids',
                    'for ages 8 to 10': 'Kids',
                    'Kids & Family': 'Kids',
                    'Late Night Comedies': 'Comedies',
                    'Action Thrillers': 'Action & Adventure',
                    'Independent Dramas': 'Dramas',
                    'Social Issue Dramas': 'Dramas',
                    'Mysteries': 'Mystery',
                    'Comedy': 'Comedies',
                    'LGBTQ Dramas': 'LGBTQ',
                    'Supernatural Thrillers': 'Thrillers',
                    'Drama': 'Dramas',
                    'Sitcoms': 'Comedies',
                    'Stand-Up Comedy & Talk ': 'Stand-up Comedy',
                    'Family Sci-Fi & Fantasy': 'Sci-Fi & Fantasy',
                    'Spoofs & Satires': 'Comedies',
                    'Kids  for ages 11 to 12': 'Kids',
                    "Kids'": "Kids"}
    for w in stop_words:
        genres_list = [g.replace(w, '').strip() for g in genres_list]

    genres_list = [genre_mapper[g] if g in genre_mapper.keys() else g for g in genres_list]
    for g in genres_list:
        if g in genres_hierarchy:
            return g
    return genres_list[0]


def plot_timeline(df, username):
    fig = go.Figure()
    series_df = df.loc[df['title_type'] == 'series']
    series_df = pd.pivot_table(series_df, index=['name', 'date'],
                               values=['season', 'episode', 'genre_chosen', 'netflix_id', 'username'],
                               aggfunc={'season': 'first', 'episode': 'first',
                                        'genre_chosen': 'first', 'netflix_id': 'first',
                                        'username': len}).reset_index()
    for i, genre in enumerate(series_df['genre_chosen'].unique()):
        g_df = series_df.loc[series_df['genre_chosen'] == genre]
        for j, nid in enumerate(g_df['netflix_id'].unique()):
            s_df = g_df.loc[g_df['netflix_id'] == nid]
            fig.add_trace(
                go.Scatter(x=s_df['date'],
                           y=s_df['name'],
                           mode='lines+markers',
                           marker=dict(color=i,
                                       size=s_df['username'] * 5),
                           # line=dict(color=i),
                           customdata=s_df['season'],
                           name=genre,
                           text=s_df['episode'],
                           hovertemplate="date: %{x} <br>name: %{y} - <br>%{customdata} <br>%{text}",
                           legendgroup=genre,
                           showlegend=j == 0)
            )
    fig.update_layout(
        yaxis=dict(
            tickfont=dict(size=9),
            title='Show Name',
            tickmode='linear'
        ),
        height=len(series_df['name'].unique()) * 12,
        title=f"Netflix Timeline Plot - {username}")
    fig.update_layout(standard_layout)
    return fig


def plot_network(df, username):
    G = nd.format_network(df)
    pos = nx.kamada_kawai_layout(G, scale=.2)
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
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))
    color_mapper = {n: int(n in pd.unique(df['title'].unique())) for n in G.nodes()}
    node_values = [int(n in pd.unique(df['title'].unique())) for n in G.nodes()]
    node_names = list(G.nodes)
    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(G.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        node_text.append(f'{node_names[node]}<br> # of connections: {str(len(adjacencies[1]))}')

    node_trace.marker.color = node_values
    node_trace.text = node_text
    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title=f'Netflix Actors Network Graph - {username}',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        annotations=[dict(
                            text="Kevin Bacon visualization",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002)],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    fig.update_layout(standard_layout)
    return fig


def save_fig(fig, file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    fig.write_html(file=file_path)


def main(username):
    """
    df has been through pipeline steps already
    """
    df = pd.DataFrame.from_records(NetflixUsers.objects.filter(username=username).values())
    df = nd.pipeline_steps(df)
    nids = df['netflix_id'][pd.notnull(df['netflix_id'])].unique().astype(int)
    genres_df = pd.DataFrame.from_records(NetflixGenres.objects.filter(
        netflix_id__in=nids).values())
    genres_df['genres'] = genres_df['genres'].fillna('')
    logger.info("Simplifying genres")
    genres_df['genre_chosen'] = genres_df['genres'].apply(simplify_genres)
    df_merged = pd.merge(df, genres_df, on='netflix_id', how='left')
    fig_plotline = plot_timeline(df_merged, username)
    save_fig(fig_plotline, f"goodreads/static/Graphs/{username}/netflix_timeline_{username}.html")
    fig_genres_s = plot_genres(df_merged, username, 'series')
    save_fig(fig_genres_s, f"goodreads/static/Graphs/{username}/netflix_genres_{username}_series.html")
    fig_genres_m = plot_genres(df_merged, username, 'movie')
    save_fig(fig_genres_m, f"goodreads/static/Graphs/{username}/netflix_genres_{username}_movie.html")
    actors_df = pd.DataFrame.from_records(NetflixActors.objects.filter(
        netflix_id__in=nids).values())
    df_network = pd.merge(df_merged, actors_df, on='netflix_id', how='left').drop_duplicates(subset='name')
    fig_network = plot_network(df_network, username)
    save_fig(fig_network, f"goodreads/static/Graphs/{username}/netflix_network_{username}.html")
    df_network.to_csv(f"goodreads/static/Graphs/{username}/netflix_process_{username}.csv", index=False)
