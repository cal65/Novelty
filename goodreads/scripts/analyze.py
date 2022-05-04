import os
import warnings
import argparse

warnings.simplefilter(action="ignore", category=FutureWarning)
import pandas as pd
import numpy as np
import psycopg2
from plotnine import *
import patchworklib as pw

from pandas.api.types import CategoricalDtype

from .models import ExportData

post_pass = os.getenv("cal65_pass")


def get_data(username):
    conn = psycopg2.connect(
        host="localhost", database="goodreads", user="cal65", password=post_pass
    )
    query = f"""
    select id, book_id, title, author, number_of_pages,
    my_rating, average_rating, original_publication_year,
    shelf1, shelf2, shelf3, shelf4, shelf5, shelf6, shelf7,
    date_read, exclusive_shelf, added_by, to_reads,
    gender, nationality1, nationality2, nationality_chosen
    from goodreads_exportdata e left join goodreads_authors as a 
    on e.author = a.author_name where e.username = '{username}'
    """
    try:
        df = pd.read_sql(query, con=conn)
        return df
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return


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
    max_read = int(df[read_col].max())
    df = df[pd.notnull(df[read_col])]
    if start_year is not None:
        df = df[df[date_col].dt.year >= start_year]
    max_digits = len(str(max_read))
    digit_range = list(range(min_break, max_digits + 1))
    breaks = [0] + [10 ** d for d in digit_range]
    df["title_length"] = df[title_col].apply(lambda x: len(x))
    # order title text by popularity
    df.sort_values(by="read", inplace=True)
    df[title_col] = df[title_col].astype("category")
    # ['0 - 1,000', '1,000 - 10,000', '10,000 - 100,000', '100,000 - 1,000,000'] using fancy local-aware f:, hack
    labels = generate_labels([f"{b:,}" for b in breaks])
    # adding obscure and bestsellers commentary
    labels[0] = f"{labels[0]} \n Obscure"
    labels[-1] = f"{labels[-1]} \n Bestsellers"
    df["strats"] = pd.cut(df[read_col], bins=breaks, labels=labels, include_lowest=True)
    text_sizes = pd.pivot_table(
        df, index="strats", aggfunc={"title_length": lambda x: 120 / max(x)}
    )
    text_sizes.rename(columns={"title_length": "text_size"}, inplace=True)
    df = pd.merge(df, text_sizes, on="strats", how="left")
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
        f"goodreads/Graphs/{name}/{plot_name}{name}.jpeg", width=16, height=15, dpi=300
    )


def factorize(series):
    # take a series, return it as an ordered category typed series
    cat_type = CategoricalDtype(categories=pd.unique(series), ordered=True)
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
        lambda x: f"{x['read']} / {x['added_by']}", axis=1
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
        + coord_flip()
        + ggtitle("Least Finished Reads")
        + theme(plot_title=element_text(hjust=0.5), panel_background=element_blank())
    )
    p.save(
        f"goodreads/Graphs/{name}/{plot_name}{name}.jpeg", width=12, height=8, dpi=300
    )


def gender_bar_plot(df, username, gender_col="gender", narrative_col="narrative"):
    p = (
        ggplot(df)
        + geom_bar(aes(x=narrative_col, fill=gender_col), position=position_dodge())
        + xlab("")
        + scale_fill_manual(
            name="Gender",
            values={"male": "blue", "female": "red", "other": "green"},
            drop=False,
        )
        + coord_flip()
        + theme_classic()
        + theme(
            legend_position="bottom",
            plot_title=element_text(hjust=1),
            axis_text=element_text(size=12),
        )
        + ggtitle("Summary Plots  ")
    )
    return p


def publication_histogram(df, date_col="original_publication_year", start_year=1800):
    df_recent = df[df[date_col] > start_year]
    n_bins = max(len(df_recent) / 10, 10)
    p = (
        ggplot(df_recent)
        + geom_histogram(aes(x=date_col), fill="black", bins=n_bins)
        + theme_classic()
        + xlab("Year of Publication")
        + ylab("Count")
    )
    return p


def plot_longest_books(
    df,
    n=15,
    pages_col="number_of_pages",
    title_col="title_simple",
    my_rating_col="my_rating",
):
    highest = df[pd.notnull(df[pages_col])].sort_values(pages_col).tail(n)
    highest[title_col] = factorize(highest[title_col])
    highest[my_rating_col] = factorize(highest[my_rating_col])
    p = (
        ggplot(highest, aes(x=title_col))
        + geom_col(aes(y=pages_col, fill=my_rating_col))
        + geom_text(aes(y=pages_col, label=pages_col), ha="right")
        + xlab("")
        + ylab("Number of Pages")
        + scale_fill_brewer(palette="Blues", name="Your Rating", type="seq")
        + coord_flip()
    )
    return p


def genre_bar_plot(df, n_shelves=4, min_count=2):
    def create_melted_genre_df(df):
        shelf_columns = [s for s in df.columns if s.startswith("shelf")]
        genre_df = df[shelf_columns]
        genre_df_m = pd.melt(df[shelf_columns], value_name="Shelf")
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
    shelf_table_df.sort_values("Count", inplace=True)
    shelf_table_df["Shelf"] = factorize(shelf_table_df["Shelf"])
    p = (
        ggplot(shelf_table_df[shelf_table_df["Count"] > min_count])
        + geom_col(aes(x="Shelf", y="Count"), color="black", fill="red")
        + coord_flip()
        + theme_classic()
        + ylab("Number of Books")
        + theme(plot_title=element_text(hjust=0.5))
    )
    return p


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
    min_count=2,
):
    p1 = gender_bar_plot(
        df, username, gender_col=gender_col, narrative_col=narrative_col
    )
    p2 = publication_histogram(df, date_col=date_col, start_year=start_year)
    p3 = plot_longest_books(
        df, n=15, pages_col=pages_col, title_col=title_col, my_rating_col=my_rating_col
    )
    p4 = genre_bar_plot(df, n_shelves=n_shelves, min_count=min_count)

    p1 = pw.load_ggplot(p1, figsize=(4, 3))
    p2 = pw.load_ggplot(p2, figsize=(4, 3))
    p3 = pw.load_ggplot(p3, figsize=(4, 3))
    p4 = pw.load_ggplot(p4, figsize=(4, 3))

    p1234 = (p1 | p2 ) / (p3 | p4)
    p1234.savefig(
        f"goodreads/Graphs/{username}/summary_plot_{name}.jpeg",
        dpi=300,
        width=12,
        height=8,
    )

    return p1234


if __name__ == "__main__":
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--username",
        dest="username",
        help="The username which data is queried from goodreads.exportbooks",
    )
    df = get_data(username)
    df = run_all(df)
    summary_plot(df, username)
    read_plot(df, username)
    finish_plot(df, username)
