import sys
import pandas as pd
import re
import logging
import argparse

from append_to_export import append_scraping

logging.basicConfig()
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# add the handler to the root logger
logger = logging.getLogger(__name__)
logger.addHandler(ch)


def update_goodreads(df1, df2, index_column):
    """
    Takes df1, an existing dataframe, and df2, a new dataframe.
    The idea is df1 already has appended fields, but df2 may be more recent.
    Any changes in df2 should be reflected in df1
    Updates df1 on new df2 values
    """
    df2.columns = [c.replace(" ", ".") for c in df2.columns]
    # save all new books
    df2_new = df2[~df2[index_column].isin(df1[index_column])]
    df2_new.reset_index(inplace=True)
    logger.info("Adding " + str(len(df2_new)) + " new rows of data")
    # go over the old books that are in common with existing dataset
    df1.set_index(index_column, inplace=True)
    df2.set_index(index_column, inplace=True)
    df1.update(df2)
    df1.reset_index(inplace=True)
    df2_updated = append_scraping(df2_new)
    df2_updated.reset_index(inplace=True)
    df_updated = pd.concat([df1, df2_updated], ignore_index=True)
    return df_updated


if __name__ == "__main__":
    """
    Usage: python update_export.py existing_file_appended.csv new_file.csv
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path1")
    parser.add_argument("file_path2")
    args = parser.parse_args()
    file_path1, file_path2 = args.file_path1, args.file_path2
    df1 = pd.read_csv(file_path1)
    df2 = pd.read_csv(file_path2)
    df = update_goodreads(df1, df2, index_column="Book.Id")
    df.to_csv(file_path1, index=False)
