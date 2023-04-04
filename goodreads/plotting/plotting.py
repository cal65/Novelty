import os
import warnings
import argparse
import geopandas as gpd

from netflix.plotting.plotting import save_fig

warnings.simplefilter(action="ignore", category=FutureWarning)
import pandas as pd
import numpy as np
from pandas.api.types import is_numeric_dtype, CategoricalDtype

import psycopg2
import matplotlib
from plotnine import *
import patchworklib as pw
from mizani.formatters import percent_format
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots

from spotify.plotting.plotting import standard_layout
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
    e.id, e.book_id, e.title, e.author, e.number_of_pages,
    e.my_rating, e.average_rating, e.original_publication_year,
    e.date_read, e.exclusive_shelf, 
    b.shelf1, b.shelf2, b.shelf3, b.shelf4, b.shelf5, b.shelf6, b.shelf7,
    b.added_by, b.to_reads,
    a.gender, a.nationality1, a.nationality2, a.nationality_chosen
    from goodreads_exportdata e 
    left join goodreads_authors as a 
    on e.author = a.author_name
    left join goodreads_books as b
    on e.book_id = b.book_id
    where e.username = '{username}'
    """
    return query


def preprocess(df):
    gender_dict = {"mostly_male": "male", "mostly_female": "female"}
    df["gender"] = df["gender"].map(gender_dict).fillna(df["gender"])
    df["date_read"] = pd.to_datetime(df["date_read"])
    df["title_simple"] = df["title"].str.replace(":.*", "")
    df["title_simple"] = df["title_simple"].str.replace("\\(.*\\)", "")
    return df


def narrative(df):
    shelf_columns = [s for s in df.columns if s.startswith("shelf")]
    df["narrative"] = df[shelf_columns].apply(
        lambda x: "Nonfiction" if "Nonfiction" in x.values else "Fiction", axis=1
    )
    return df


def read_percentage(df):
    # It seems sometimes the "added by" value is off by a factor of 10. When the
    # number of people listing the book as "to read" is larger than total added by, multiply by 10
    df.loc[df["to_reads"] > df["added_by"], "added_by"] = (
        df.loc[df["to_reads"] > df["added_by"], "added_by"] * 10
    )
    df["read"] = df["added_by"] - df["to_reads"]
    df["read_percentage"] = df["read"] / df["added_by"]
    return df


def run_all(df):
    df = read_percentage(narrative(preprocess(df)))
    return df


def generate_labels(breaks):
    if len(breaks) == 2:
        return [f"{breaks[0]} - {breaks[1]}"]
    else:
        return [f"{breaks[0]} - {breaks[1]}"] + generate_labels(breaks[1:])


def read_plot_munge(
    df,
    read_col="read",
    title_col="title_simple",
    min_break=3,
    date_col="date_read",
    start_year=2010,
):
    df = df[pd.notnull(df[read_col])]
    if len(df) == 0:
        return df
    if start_year is not None:
        df = df[df[date_col].dt.year >= start_year]
    max_read = int(df[read_col].max())
    max_digits = len(str(max_read))
    digit_range = list(range(min_break, max_digits + 1))
    breaks = [0] + [10**d for d in digit_range]
    df["title_length"] = df[title_col].apply(lambda x: len(x))
    # order title text by popularity
    df.sort_values(by="read", inplace=True)
    df[title_col] = df[title_col].astype("category")
    # ['0 - 1,000', '1,000 - 10,000', '10,000 - 100,000', '100,000 - 1,000,000'] using fancy local-aware f:, hack
    break_labels = generate_labels([f"{b:,}" for b in breaks])
    # adding obscure and bestsellers commentary
    break_labels[0] = f"{break_labels[0]} \n Obscure"
    break_labels[-1] = f"{break_labels[-1]} \n Bestsellers"
    df["strats"] = pd.cut(
        df[read_col], bins=breaks, labels=break_labels, include_lowest=True
    )
    # logging
    strats_count = df["strats"].value_counts()
    logger.info(f"debugging read plot munge: {strats_count}")
    return df


def read_plot(
    df,
    name,
    read_col="read",
    title_col="title_simple",
    min_break=3,
    plot_name="popularity_spectrum_",
    date_col="date_read",
    start_year=None,
):
    df = read_plot_munge(
        df,
        read_col=read_col,
        title_col=title_col,
        min_break=min_break,
        date_col=date_col,
        start_year=start_year,
    )

    p = (
        ggplot(df, aes("strats", "title_simple"))
        + aes(fill="narrative")
        + geom_tile()
        + geom_text(aes(label="title_simple", size="text_size"))
        + facet_wrap("strats", scales="free", nrow=1)
        + scale_fill_manual(values=["mediumvioletred", "darkolivegreen"])
        + scale_size_continuous(guide=False, range=[7, 10])
        + xlab("Number of Readers")
        + ylab("Title")
        + ggtitle(f"Readership Spectrum - {name}")
        + theme_light()
        + theme(
            axis_text_y=element_blank(),
            plot_title=element_text(hjust=0.5),
            panel_background=element_blank(),
        )
    )
    p.save(
        f"goodreads/static/Graphs/{name}/{plot_name}{name}.jpeg",
        width=16,
        height=15,
        dpi=300,
    )


def factorize(series):
    # order numeric series from low to high
    uniques = pd.unique(series)
    if is_numeric_dtype(series):
        uniques = sorted(uniques)

    # take a series, return it as an ordered category typed series
    cat_type = CategoricalDtype(categories=uniques, ordered=True)
    series = series.astype(cat_type)
    return series


def finish_plot(
    df,
    name,
    exclusive_shelf="exclusive_shelf",
    read_col="read_percentage",
    title_col="title_simple",
    n=10,
    plot_name="finish_plot_",
):
    df[exclusive_shelf] = df[exclusive_shelf].replace(
        {"currently-reading": "unread", "to-read": "unread"}
    )
    df_read = df.sort_values(read_col)
    df_read = df_read[pd.notnull(df[read_col])]
    # have a duplicate data problem occasionally with multiple book versions
    df_read = df_read.drop_duplicates(subset=title_col)
    # keep only bottom n
    df_read_n = (
        df_read.groupby(exclusive_shelf)
        .apply(lambda x: x.head(n))
        .reset_index(drop=True)
    )

    cat_type = CategoricalDtype(
        categories=pd.unique(df_read_n[title_col]), ordered=True
    )
    df_read_n[title_col] = df_read_n[title_col].astype(cat_type)
    df_read_n["read_half"] = df_read_n[read_col] / 2
    df_read_n["display_text"] = df_read_n.apply(
        lambda x: f"{int(x['read'])} / {int(x['added_by'])}", axis=1
    )
    logger.info(
        f"Debugging df_read_n: {df_read_n[[title_col, read_col, exclusive_shelf]].sample(2)}"
    )
    p = (
        ggplot(df_read_n, aes(x=title_col))
        + geom_col(aes(y=1), fill="darkblue")
        + geom_col(aes(y=read_col), fill="darkred")
        + geom_text(
            aes(y="read_half", label="display_text"),
            size=n * 3 / 5,
            color="white",
            ha="left",
        )
        + facet_grid("exclusive_shelf ~ .", scales="free", space="free")
        + ylim(0, 1)
        + xlab("Title")
        + ylab("Reading Percentage")
        + scale_y_continuous(labels=percent_format())
        + coord_flip()
        + ggtitle("Least Finished Reads")
        + theme(plot_title=element_text(hjust=0.5), panel_background=element_blank())
    )
    p.save(
        f"goodreads/static/Graphs/{name}/{plot_name}{name}.jpeg",
        width=12,
        height=8,
        dpi=300,
    )


def gender_bar_plot(df, gender_col="gender", narrative_col="narrative"):
    # ignore nones
    df_gender = pd.DataFrame(
        df.groupby([gender_col, narrative_col], as_index=False).size()
    )
    traces = []
    for g in df_gender[gender_col].unique():
        df_g = df_gender.loc[df_gender[gender_col] == g]
        traces.append(
            go.Bar(
                x=df_g["size"],
                y=df_g[narrative_col],
                orientation="h",
                hovertemplate="<b>Type:</b> %{y}<br><b>Count:</b> %{x}",
                name=g,
            )
        )
    return traces


def publication_histogram(df, date_col="original_publication_year", start_year=1800):
    df_recent = df[df[date_col] > start_year]
    n_bins = int(max(len(df_recent) / 10, 10))
    return go.Histogram(
        x=df_recent[date_col],
        nbinsx=n_bins,
        customdata=df_recent["title_simple"],
        hovertemplate="%{customdata}",
        showlegend=False,
    )


def plot_longest_books(
    df,
    n=15,
    pages_col="number_of_pages",
    title_col="title_simple",
    my_rating_col="my_rating",
):
    highest = df[pd.notnull(df[pages_col])].sort_values(pages_col).tail(n)
    highest[title_col] = factorize(highest[title_col])
    return go.Bar(
        x=highest[pages_col],
        y=highest[title_col],
        orientation="h",
        hovertemplate="<b>Title:</b> %{y}<br><b>Number of Pages:</b> %{x}",
        showlegend=False,
    )


def genre_bar_plot(df, n_shelves=4, min_count=3):
    """
    Because genres are stored in multiple columns starting with 'shelf', to plot them we need to melt the shelves
    Currently 7 shelves are stored, but including them all can lead to a busy graph
    Default is to only show top 4
    """

    def create_melted_genre_df(df):
        shelf_columns = [s for s in df.columns if s.startswith("shelf")]
        genre_df = df[shelf_columns]
        genre_df_m = pd.melt(genre_df, value_name="Shelf")
        genre_df_m = genre_df_m[
            ~genre_df_m["Shelf"].isin(["Fiction", "Nonfiction", ""])
        ]
        genre_df_m = genre_df_m[pd.notnull(genre_df_m["Shelf"])]
        return genre_df_m

    genre_df_m = create_melted_genre_df(df)
    genre_df_m["shelf_number"] = (
        genre_df_m["variable"].str.replace("shelf", "").astype(int)
    )
    genre_df_m = genre_df_m[genre_df_m["shelf_number"] <= n_shelves]
    shelf_table_df = pd.DataFrame(genre_df_m["Shelf"].value_counts()).reset_index()
    shelf_table_df.columns = ["Shelf", "Count"]
    shelf_table_df.sort_values("Count", ascending=False, inplace=True)
    shelf_table_df["Shelf"] = factorize(shelf_table_df["Shelf"])

    # manual adjustment for smaller datasets
    if len(df) < 75:
        min_count = 1

    plot_df = shelf_table_df[shelf_table_df["Count"] > min_count]
    plot_df = plot_df.head(30)

    if len(plot_df) > 3:
        return go.Bar(
            x=plot_df["Count"],
            y=plot_df["Shelf"],
            orientation="h",
            hovertemplate="<b>Shelf:</b> %{y}<br><b>Count:</b> %{x}",
            showlegend=False,
        )
    else:
        logger.info(f"length of eligible data is too small, only {len(plot_df)} rows")
        return None


def summary_plot(
    df,
    username,
    date_col="original_publication_year",
    start_year=1800,
    gender_col="gender",
    narrative_col="narrative",
    pages_col="number_of_pages",
    title_col="title_simple",
    my_rating_col="my_rating",
    n_shelves=4,
    min_count=3,
):
    """
    Call 4 distinct plot generators. Load them up into a 2x2 grid. Save and return figure.
    """
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Gender Summary",
            "Publication Dates",
            "Longest Books",
            "Genres",
        ),
    )

    gender_traces = gender_bar_plot(df, gender_col="gender")
    for trace in gender_traces:
        fig.add_trace(trace, row=1, col=1)

    fig.add_trace(
        publication_histogram(df, date_col=date_col, start_year=start_year),
        row=1,
        col=2,
    )

    fig.add_trace(
        plot_longest_books(df),
        row=2,
        col=1,
    )

    fig.add_trace(genre_bar_plot(df, n_shelves=4, min_count=2), row=2, col=2)
    fig.update_layout(standard_layout)

    return fig


def load_map():
    world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    region_query = """
    select * from goodreads_refnationality
    """
    region_df = get_data(region_query)
    if len(region_df) == 0:
        logger.error("No region data queried")
    country_mapper = {
        "England": "United Kingdom",
        "Bosnia": "Bosnia and Herz.",
        "Dominican Republic": "Dominican Rep.",
    }
    region_df["region"] = region_df["region"].replace(country_mapper)
    region_dict = region_df.set_index("region").to_dict()["nationality"]
    world["nationality"] = world["name"].map(region_dict)
    return world


def join_titles(titles, limit=3):
    return ", ".join(titles[: min(len(titles), limit)])


def return_nationality_count(
    df,
    nationality_col="nationality_chosen",
    title_col="title_simple",
    author_col="author",
    limit=3,
):
    nationality_count = (
        pd.pivot_table(
            df,
            index=nationality_col,
            values=[title_col, author_col],
            aggfunc=[len, lambda x: join_titles(x, limit)],
        )
        .reindex(columns=[title_col, author_col], level=1)
        .reset_index()
    )
    nationality_count.columns = [
        nationality_col,
        "count",
        "count2",
        title_col,
        author_col,
    ]

    return nationality_count


def merge_map_data(world_df, nationality_count, nationality_col):
    if len(world_df) == 0:
        return world_df
    world_df = pd.merge(
        world_df,
        nationality_count,
        how="left",
        left_on="nationality",
        right_on=nationality_col,
    )
    logger.info(
        f"Map data merged with {len(pd.unique(world_df['nationality']))} unique nationalities"
    )
    return world_df


def bokeh_world_plot(world_df, username):
    from bokeh.plotting import figure, output_file, save
    from bokeh.models import (
        ColorBar,
        GeoJSONDataSource,
        HoverTool,
        LogColorMapper,
    )
    from bokeh.palettes import brewer

    output_file(
        filename=f"goodreads/static/Graphs/{username}/author_map_{username}.html",
        title=f"Author Map - {username}",
    )
    palette = brewer["OrRd"][8]
    palette = palette[
        ::-1
    ]  # reverse order of colors so higher values have darker colors
    color_mapper = LogColorMapper(palette=palette, low=1, high=world_df["count"].max())
    # Create color bar.
    color_bar = ColorBar(
        color_mapper=color_mapper,
        label_standoff=8,
        width=500,
        height=20,
        border_line_color=None,
        location=(0, 0),
        orientation="horizontal",
        # major_label_overrides = tick_labels
    )
    p = figure(
        title=f"Author Nationality Map - {username}",
        toolbar_location="below",
        tools="pan, wheel_zoom, box_zoom, reset",
    )
    # Add patch renderer to figure.
    geosource = GeoJSONDataSource(geojson=world_df.to_json())
    author_map = p.patches(
        "xs",
        "ys",
        source=geosource,
        fill_color={"field": "count", "transform": color_mapper},
        line_color="gray",
        line_width=0.25,
        fill_alpha=1,
    )
    # Create hover tool
    p.add_tools(
        HoverTool(
            renderers=[author_map],
            tooltips=[
                ("Country", "@name"),
                ("Author Count", "@count"),
                ("Titles", "@title_simple"),
                ("Authors", "@author"),
            ],
        )
    )

    p.add_layout(color_bar, "below")

    save(p)


def create_read_plot_heatmap(
    df,
    username,
    read_col="read",
    title_col="title_simple",
    min_break=3,
    date_col="date_read",
    start_year=None,
):
    df = read_plot_munge(
        df,
        read_col=read_col,
        title_col=title_col,
        min_break=min_break,
        date_col=date_col,
        start_year=start_year,
    )
    strats = pd.unique(df["strats"])
    df["narrative_int"] = df["narrative"].map({"Fiction": 1, "Nonfiction": 0})
    df["hover_text"] = df.apply(
        lambda x: f"Readers: {'{:,.0f}'.format(x.read)} <br> Title: {x.title_simple} <br> Author: {x.author}",
        axis=1,
    )
    df.to_csv("debugging_heatmap.csv", index=False)
    fig = make_subplots(
        rows=1,
        cols=len(strats),
        horizontal_spacing=0.015,
        column_widths=[3] * len(strats),
    )
    heatmaps = []
    for i in range(len(strats)):
        r_strat = df[df["strats"] == strats[i]]
        heatmaps.append(
            ff.create_annotated_heatmap(
                x=[strats[i]],
                z=[[r] for r in r_strat["narrative_int"]],
                annotation_text=[[r] for r in r_strat["title_simple"]],
                text=[[r] for r in r_strat["hover_text"]],
                hoverinfo="text",
                colorscale="geyser",
                font_colors=["black", "black"],
            )
        )
        heatmaps[i].layout.width = 300
        fig.add_trace(heatmaps[i].data[0], row=1, col=i + 1)

        annotations = heatmaps[i].layout.annotations
        for k in range(len(annotations)):
            annotations[k]["xref"] = f"x{i + 1}"
            annotations[k]["yref"] = f"y{i + 1}"
        for ano in annotations:
            fig.add_annotation(ano)

        if i == 0:
            fig.update_layout(yaxis=dict(visible=False, categoryorder="array"))
        else:
            fig.layout[f"yaxis{i + 1}"] = dict(visible=False, categoryorder="array")

    fig.update_layout(
        title="Popularity Spectrum",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(standard_layout)

    filename = f"goodreads/static/Graphs/{username}/read_heatmap_{username}.html"
    fig.write_html(file=filename)
    return fig


def month_plot(
    df, username, date_col, page_col, title_col, author_gender_col, lims=None
):
    filename = f"goodreads/static/Graphs/{username}/monthly_pages_read_{username}.html"
    df["year_read"] = df[date_col].dt.year
    df["month_read"] = df[date_col].dt.month
    logger.info(
        f"Starting Monthly pages read plot for data with \
    years {pd.unique(df['year_read'])}"
    )
    df = df[pd.notnull(df["year_read"])]
    if len(df) < 3:
        logger.info("Not enough date data to plot month plot")
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=[5],
                y=[0],
                text="Not Enough Data with Date Read Inputted to Plot",
                width=5,
            )
        )
        fig.write_html(file=filename)

    if lims is not None:
        df = df[(df["year_read"] >= lims[0]) & (df["year_read"] <= lims[1])]

    n_years = len(pd.unique(df["year_read"]))

    df["color"] = df[author_gender_col].map(
        {"female": "lightsalmon", "male": "deepskyblue", "other": "green"}
    )
    df["text"] = df["text"] = (
        df[title_col] + "<br>" + df["author"] + "<br>" + df[date_col].astype(str)
    )
    fig = make_subplots(rows=n_years, cols=1, shared_xaxes=True, vertical_spacing=0.01)
    for i, year in enumerate(sorted(pd.unique(df["year_read"]))):
        df_year = df[df["year_read"] == year]
        df_month_totals = pd.pivot_table(
            df_year, index="month_read", values=page_col, aggfunc=sum
        )
        fig.add_trace(
            go.Bar(
                x=df_year["month_read"],
                y=df_year[page_col],
                marker_color=df_year["color"],
                hovertext=df_year["text"],
                text=df_year["author"],
                textposition="inside",
                textangle=0,
                textfont=dict(size=8),
                width=1,
            ),
            row=i + 1,
            col=1,
        )
        fig.add_annotation(
            x=12,
            y=max(df_month_totals[page_col]),
            text=str(int(year)),
            xref=f"x{i+1}",
            yref=f"y{i+1}",
            showarrow=False,
        )
    fig.update_layout(
        showlegend=False,
        title_text=f"Month Breakdown - {username}",
        title_x=0.5,
        height=n_years * 125,
        uniformtext_minsize=6,
        uniformtext_mode="hide",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(
        tickvals=np.arange(1, 13),
        showgrid=False,
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor="black",
    )
    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor="black")

    fig["layout"][f"xaxis{n_years}"]["title"] = {"text": "Month"}

    fig.write_html(file=filename)

    return fig


def main(username):
    df = get_data(userdata_query(username))
    logger.info(f"Data read with {len(df)} rows \n : {df.head()}")
    df = run_all(df)
    read_df = df[
        df["exclusive_shelf"] == "read"
    ]  # ignore the books that haven't been read
    try:
        fig_summary = summary_plot(read_df, username)
        save_fig(
            fig_summary,
            f"goodreads/static/Graphs/{username}/goodreads_summary_{username}.html",
        )
    except Exception as exception:
        logger.info(" summary plot failed: " + str(exception))
    create_read_plot_heatmap(df=read_df, username=username)
    finish_plot(df, username)
    # world map plotting
    world_df = load_map()
    nationality_count = return_nationality_count(read_df)
    world_df = merge_map_data(
        world_df, nationality_count, nationality_col="nationality_chosen"
    )
    bokeh_world_plot(world_df, username)
    month_plot(
        read_df,
        username,
        date_col="date_read",
        page_col="number_of_pages",
        title_col="title",
        author_gender_col="gender",
        lims=[2012, 2022],
    )


if __name__ == "__main__":
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--username",
        dest="username",
        help="The username which data is queried from goodreads.exportbooks",
    )
    args = parser.parse_args()
    username = args.username
    main(username)
