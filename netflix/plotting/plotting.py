import os
import warnings
import argparse
import geopandas as gpd

warnings.simplefilter(action="ignore", category=FutureWarning)
import pandas as pd
import numpy as np
import psycopg2
import matplotlib
from plotnine import *
import patchworklib as pw
from mizani.formatters import percent_format
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots

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

def get_data(query):
    conn = psycopg2.connect(
        host="localhost", database="goodreads", user="cal65", password=post_pass
    )
    try:
        df = pd.read_sql(query, con=conn)
        logger.info(f"Returning data from query with nrows {len(df)}")
        return df
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return

def refdata_query():
    query = f"""
    select 
    t.name, t.type, t.director, t.cast, t.date_added, t.release_year, t.rating,
    t.duration, t.country1, t.country2, t.country3, t.listed_in
    from goodreads_netflixtitles t 
    """
    return query