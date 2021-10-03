from bs4 import BeautifulSoup
import requests
import pandas as pd
from pandas.api.types import is_string_dtype
import numpy as np
import json
import random
import time
import sys
import re
import gender_guesser.detector as gender
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_stats(url, wait=0):
    """
    Mega block to pull Goodreads website contents using BeautifulSoup
    Extract numerous useful book info from the page
    Returns a dictionary of that extract
    """
    null_return = {
        "Added_by": None,
        "To_reads": None,
        "Title": None,
        "Author": None,
        "Publish_info": None,
        "Language": None,
        "Rating": None,
        "Shelf1": None,
        "Shelf2": None,
        "Shelf3": None,
        "Shelf4": None,
        "Shelf5": None,
        "Shelf6": None,
        "Shelf7": None,
        "Original_title": None,
        "url": url,
        "numberOfPages": None,
    }

    try: 
        page = requests.get(url)
    except requests.exceptions.ConnectionError:
        logger.info("Connection refused - too many requests")
        return null_return
    soup = BeautifulSoup(page.content, "html.parser")

    scripts = soup.findAll("script")
    try:
        navig = scripts[18].string
    except IndexError as error:
        logger.info("Soup failed - index error - for url: " + url)
        return null_return
    except Exception as exception:
        logger.info(
            "Soup failed for url: " + url,
        )
        return null_return
    add_string = 'added by <span class=\\"value\\">'
    # crucial breaking line
    try:
        n = navig.find(add_string)
    except Exception as exception:
        print(str(exception) + " - for url: " + url)
        return null_return
    added_by_raw = navig[(n + len(add_string)) : (n + len(add_string) + 9)]
    added_by_parsed = re.findall("\d+", added_by_raw)  # extract numbers
    if len(added_by_parsed) > 0:
        added_by = int(added_by_parsed[0])  # first number found
    else:
        added_by = None

    to_read_string = "<\\/span> to-reads"
    n2 = navig.find(to_read_string)
    to_reads_raw = navig[(n2 - 8) : n2]
    to_reads_parsed = re.findall("\d+", to_reads_raw)
    if len(to_reads_parsed) > 0:
        to_reads = int(to_reads_parsed[0])
    else:
        to_reads = None

    try:
        title = soup.find("h1").text.replace("\n", "")
    except:
        title = None

    try:
        author = soup.find("span", {"itemprop": "name"}).text
    except:
        author = None

    try:
        publish_info = (
            soup.find("div", {"id": "details"}).findAll("div", {"class": "row"})[1].text
        )
        publish_info = publish_info.replace("\n", "")
        publish_info = publish_info.replace("Published", "").strip()
    except:
        publish_info = None

    try:
        language = soup.find("div", {"itemprop": "inLanguage"}).text
    except:
        language = None
    try:
        rating = soup.find("span", {"itemprop": "ratingValue"}).text.replace("\n", "")
    except:
        rating = None
    try:
        shelves = soup.findAll("a", {"class": "actionLinkLite bookPageGenreLink"})
        shelves = [shelf.text for shelf in shelves]
        shelves = pd.unique(
            shelves
        )  # because of the way Goodreads organizes this, there are some repeat shelves
        shelf1 = shelves[0] if len(shelves) > 0 else ""
        shelf2 = shelves[1] if len(shelves) > 1 else ""
        shelf3 = shelves[2] if len(shelves) > 2 else ""
        shelf4 = shelves[3] if len(shelves) > 3 else ""
        shelf5 = shelves[4] if len(shelves) > 4 else ""
        shelf6 = shelves[5] if len(shelves) > 5 else ""
        shelf7 = shelves[6] if len(shelves) > 6 else ""
    except:
        shelf1 = shelf2 = shelf3 = shelf4 = shelf5 = shelf6 = shelf7 = None

    try:
        original_title = soup.find("div", {"class": "infoBoxRowItem"}).text
    except:
        original_title = None
    try:
        numberOfPages = soup.find("span", {"itemprop": "numberOfPages"}).text.replace(
            "\n", ""
        )
    except:
        numberOfPages = None

    time.sleep(wait)

    return {
        "Added_by": added_by,
        "To_reads": to_reads,
        "Title": title,
        "Author": author,
        "Publish_info": publish_info,
        "Language": language,
        "Rating": rating,
        "Shelf1": shelf1,
        "Shelf2": shelf2,
        "Shelf3": shelf3,
        "Shelf4": shelf4,
        "Shelf5": shelf5,
        "Shelf6": shelf6,
        "Shelf7": shelf7,
        "Original_title": original_title,
        "url": url,
        "numberOfPages": numberOfPages,
    }


def create_url(id, name):

    return "https://www.goodreads.com/book/show/" + str(id)


def read_goodreads_export(file_path):
    if file_path.endswith(".csv"):
        goodreads_data = pd.read_csv(file_path)
    elif file_path.endswith(".xlsx"):
        goodreads_data = pd.read_excel(file_path)
    return goodreads_data


def return_urls(goodreads_data, id_col="Book.Id"):
    if not is_string_dtype(goodreads_data["Title"]):
        goodreads_data["Title"] = goodreads_data["Title"].astype(str)
    urls = goodreads_data.apply(lambda x: create_url(x[id_col], x["Title"]), axis=1)

    return urls


def apply_added_by(urls, wait=4):
    stats = [get_stats(url, wait=wait) for url in urls]
    goodreads_data = pd.DataFrame(stats)

    goodreads_data["date_published"] = (
        goodreads_data["Publish_info"]
        .str.split("by ")
        .apply(lambda x: x[0] if x is not None else None)
    )
    # gender
    goodreads_data = guess_gender(goodreads_data, gender_col="gender")
    # shelves
    return goodreads_data


def guess_gender(goodreads_data, gender_col="gender"):
    d = gender.Detector()
    goodreads_data["First.Name"] = [
        name[0] if name != "" else ""
        for name in goodreads_data["Author"].str.split(" ").fillna("")
    ]
    goodreads_data[gender_col] = [
        d.get_gender(name) for name in goodreads_data["First.Name"]
    ]
    return goodreads_data


def get_first_name(name):
    names = name.split(" ")
    if len(names) > 0:
        return names[0]
    else:
        return ""


def generate_random_urls(max, n, seed):
    random.seed(seed)
    start = 5
    random_samples = random.sample(list(np.arange(start, start + max)), n)
    urls = ["https://www.goodreads.com/book/show/" + str(r) for r in random_samples]

    return urls


if __name__ == "__main__":
    """
    python scrape_goodreads.py 67500000 25 999 export_goodreads.csv
    """
    urls = generate_random_urls(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    if len(sys.argv) >= 6:
        wait = int(sys.argv[5])
    else:
        wait = 3
    goodreads_data = apply_added_by(urls, wait=wait)
    try:
        existing = pd.read_csv(sys.argv[4])
        goodreads_data = pd.concat([existing, goodreads_data], axis=0)
    except:
        pass
    goodreads_data.to_csv(sys.argv[4], index=False)
