import pandas as pd
import os
import psycopg2
from sqlalchemy import create_engine
import argparse
from datetime import datetime

def process_kaggle(df):
    df['name'] = df['title'].apply(lambda x: x.split(':')[0])
    countries = df['country'].str.split(', ')
    df['country1'] = [c[0] if isinstance(c, list) else '' for c in countries]
    df['country2'] = [c[1] if (isinstance(c, list) and len(c) > 1) else '' for c in countries]
    df['country3'] = [c[2] if (isinstance(c, list) and len(c) > 2) else '' for c in countries]
    return df

def export_to_csv(df, export_file_name = "kaggle_processed.csv"):
    export_cols = ['title', 'name', 'type', 'director',
                   'cast', 'date_added', 'release_year', 'rating',
                   'duration', 'country1', 'country2', 'country3',
                   'listed_in', 'description', 'ts_updated']
    df['ts_updated'] = datetime.now()
    df[export_cols].to_csv(export_file_name)
    return df[export_cols]

def write_to_db(df):
    try:
        connection = psycopg2.connect(
            user="cal65",
            password=os.environ["cal65_pass"],
            host="127.0.0.1",
            port="5432",
            database="goodreads",
        )

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    engine = create_engine(
        "postgresql+psycopg2://cal65:"
        + os.environ["cal65_pass"]
        + "@127.0.0.1/goodreads"
    )
    df.to_sql("goodreads_netflixtitles", engine, if_exists="append", index=False)
    connection.close()

def main(file_path):
    df = pd.read_csv(file_path)
    df = process_kaggle(df)
    df = export_to_csv(df)
    write_to_db(df)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--filepath",
        dest="filepath",
        help="The csv file to read from",
    )
    args = parser.parse_args()
    filepath = args.filepath
    main(filepath)