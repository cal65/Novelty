import os
import sys

import pandas as pd
import re
import logging
import argparse
import functools
import psycopg2
from datetime import datetime

def preprocess(file_path, date_col='Date', title_col='Title'):
    df = pd.read_csv(file_path)
    df[date_col] = pd.to_datetime(df[date_col])
    title_values = df[title_col].str.split(':')
    df['Name'], df['Secondary'] = zip(*title_values)
    return df
