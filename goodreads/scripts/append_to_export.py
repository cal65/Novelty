import scrape_goodreads
import sys
import pandas as pd
import re
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def append_scraping(goodreads_data):
    goodreads_data.columns = [c.replace(" ", ".") for c in goodreads_data.columns]
    urls = scrape_goodreads.return_urls(goodreads_data)
    scraped_df = scrape_goodreads.apply_added_by(urls)
    scraped_df.drop(columns=["Title", "Author", "Publish_info"], inplace=True)
    goodreads_data_merged = pd.concat([goodreads_data, scraped_df], axis=1)
    return goodreads_data_merged


def apply_append(file_path):
    goodreads_data = scrape_goodreads.read_goodreads_export(file_path)
    return append_scraping(goodreads_data)


def add_to_existing_export(file_path_existing, file_path_new):
    existing = scrape_goodreads.read_goodreads_export(file_path_existing)
    new = scrape_goodreads.read_goodreads_export(file_path_new)
    diff_titles = set(new["Title"]).difference(existing["Title"]).tolist()
    diff = new[new["Title"].isin(diff_titles)]
    diff_scraped = append_scraping(diff)
    return diff_scraped


def update_goodreads(df1, df2, index_column):
    """
    Takes df1, an existing dataframe, and df2, a new dataframe.
    The idea is df1 already has appended fields, but df2 may be more recent.
    Any changes in df2 should be reflected in df1
    Updates df1 on new df2 values
    """
    df2.columns = [c.replace(" ", ".") for c in df2.columns]
    # save all new books
    df2_unupdated = df2[~df2[index_column].isin(df1[index_column])]
    # go over the old books that are in common with existing dataset
    df1.set_index(index_column, inplace=True)
    df2.set_index(index_column, inplace=True)
    df1.update(df2)
    df1.reset_index(inplace=True)
    df2_updated = append_scraping(df2_unupdated)
    df_updated = pd.concat([df1, df2_updated])
    return df_updated


def update_missing_data(df, wait=1):
    df_missing = df[pd.isnull(df["Added_by"])]
    if len(df_missing) > 0:
        logger.info("Updating " + str(len(df_missing.shape)) + " missing rows of data")
        urls = scrape_goodreads.return_urls(df_missing)
        scraped_missing = scrape_goodreads.apply_added_by(urls, wait=wait)
        scraped_missing.index = df_missing.index
        df.update(scraped_missing)
    else:
        logger.info("No data needs updating")
    return df


def fix_date(file_path):
    df = pd.read_csv(file_path)
    df["Date.Added"] = pd.to_datetime(df["Date.Added"])
    df["Date.Read"] = pd.to_datetime(df["Date.Read"])
    df.to_csv(file_path, index=False)
    # return just for proof
    return df[["Title", "Date.Added", "Date.Read"]]


if __name__ == "__main__":
    file_path = sys.argv[1]
    export_path = re.sub(".csv|.xlsx", "_appended.csv", file_path)
    apply_append(file_path).to_csv(export_path, index=False)
    fix_date(export_path)
