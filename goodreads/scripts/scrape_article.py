from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import random
import time
import sys


def ids_from_article(url):
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    links_raw = soup.findAll('i')
    a_refs = [link.find('a') for link in links_raw]
    a_refs = [a for a in a_refs if a is not None]
    links = [a.attrs['href'] for a in a_refs]
    book_ids = [link.split('/')[-1].split('-')[0] for link in links]
    return book_ids
