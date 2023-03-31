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


cookies = {
    "ccsid": "981-7720517-4539359",
    "p": "dkCKV365TjqNenOKY4VtqQ6sIm7CTPX-c9d94GhAzRXKWDHD",
    "likely_has_account": "true",
    "__utma": "250562704.423302064.1603340854.1621127507.1621198172.295",
    "allow_behavioral_targeting": "true",
    "session-id": "141-6452885-9687058",
    "logged_out_browsing_page_count": "2",
    "srb_1": "0",
    "ubid-main": "131-4250835-4161367",
    "lc-main": "en_US",
    "csm-hit": "tb:28PZZBK444T48GAAWQ0H+b-4K51QZ90N1KMGMJX1EGE|1667883949756&t:1667883949756&adb:adblk_no",
    "session-id-time": "2298605691l",
    "__gads": "ID=df0a6707150d114d:T=1670897981:S=ALNI_MZfGBQsHE3Vk7tICMIg8zJxLI8e8Q",
    "srb_8": "0_ar",
    "u": "wAw3MOakONnieoULVHt00uOWrYRoyYDZsk99mGcNYG0A06pv",
    "locale": "en",
    "csm-sid": "597-1753354-2882842",
    "_session_id2": "f7a5a1a7a6f2a35bdc0b8a0252624e2e",
    "__gpi": "UID=000004048f7baabd:T=1648685718:RT=1677827658:S=ALNI_MYxDQ7dAo3KLoXnssoo0UOLpKL7ow",
}

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    # 'Cookie': 'ccsid=981-7720517-4539359; p=dkCKV365TjqNenOKY4VtqQ6sIm7CTPX-c9d94GhAzRXKWDHD; likely_has_account=true; __utma=250562704.423302064.1603340854.1621127507.1621198172.295; allow_behavioral_targeting=true; session-id=141-6452885-9687058; logged_out_browsing_page_count=2; srb_1=0; ubid-main=131-4250835-4161367; lc-main=en_US; csm-hit=tb:28PZZBK444T48GAAWQ0H+b-4K51QZ90N1KMGMJX1EGE|1667883949756&t:1667883949756&adb:adblk_no; session-id-time=2298605691l; __gads=ID=df0a6707150d114d:T=1670897981:S=ALNI_MZfGBQsHE3Vk7tICMIg8zJxLI8e8Q; srb_8=0_ar; u=wAw3MOakONnieoULVHt00uOWrYRoyYDZsk99mGcNYG0A06pv; locale=en; csm-sid=597-1753354-2882842; _session_id2=f7a5a1a7a6f2a35bdc0b8a0252624e2e; __gpi=UID=000004048f7baabd:T=1648685718:RT=1677827658:S=ALNI_MYxDQ7dAo3KLoXnssoo0UOLpKL7ow',
    "DNT": "1",
    "If-None-Match": 'W/"accfd32b1ffcc24b9de5eaf56d15ccc4"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}

# response = requests.get('https://www.goodreads.com/book/stats/50175419', cookies=cookies, headers=headers)


def get_soup(url):
    try:
        page = requests.get(url, cookies=cookies, headers=headers, timeout=5)
    except requests.exceptions.ConnectionError:
        logger.info("Connection refused - too many requests")
        return None
    soup = BeautifulSoup(page.content, "html.parser")
    return soup


def get_stats(url, wait=0):
    """
    Mega block to pull Goodreads website contents using BeautifulSoup
    Extract numerous useful book info from the page
    Returns a dictionary of that extract
    """
    null_return = {
        "title": None,
        "author": None,
        "publish_info": None,
        "language": None,
        "rating": None,
        "shelf1": None,
        "shelf2": None,
        "shelf3": None,
        "shelf4": None,
        "shelf5": None,
        "shelf6": None,
        "shelf7": None,
        "original_title": None,
        "url": url,
        "number_of_pages": None,
    }
    logger.info(f"Initiating scrape for url {url}")
    soup = get_soup(url)
    if soup is None:
        logger.info("Connection refused - too many requests")
        return null_return

    details = soup.find("div", {"class": "FeaturedDetails"})
    genre_divs = soup.find("div", {"data-testid": "genresList"})
    shelves = [g.text for g in genre_divs.findAll("a")]

    try:
        title = soup.find("h1").text.replace("\n", "")
    except:
        title = None

    try:
        author = soup.find("span", {"data-testid": "name"}).text
    except:
        author = None

    try:
        publish_info = details.find("p", {"data-testid": "publicationInfo"}).text
        publish_info = publish_info.replace("\n", "")
        publish_info = publish_info.replace("First published", "").strip()
    except:
        publish_info = None

    try:
        language = soup.find("div", {"itemprop": "inLanguage"}).text
    except:
        language = None
    try:
        rating = soup.find("div", {"class": "RatingStatistics__rating"}).text
    except:
        rating = None
    try:
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
        numberOfPages_raw = details.find("p", {"data-testid": "pagesFormat"}).text
        numberOfPages = int(re.findall(r"\d+", numberOfPages_raw)[0])
    except:
        numberOfPages = None
    time.sleep(wait)

    return {
        "title": title,
        "author": author,
        "publish_info": publish_info,
        "language": language,
        "rating": rating,
        "shelf1": shelf1,
        "shelf2": shelf2,
        "shelf3": shelf3,
        "shelf4": shelf4,
        "shelf5": shelf5,
        "shelf6": shelf6,
        "shelf7": shelf7,
        "original_title": original_title,
        "url": url,
        "number_of_pages": numberOfPages,
    }


def get_read_stats(url):
    null_return = {
        "added_by": None,
        "to_reads": None,
    }
    soup = get_soup(url)
    if soup is None:
        logger.info("Connection refused for stats page - too many requests")
        return null_return

    stats_raw = soup.findAll("div", {"class": "infoBoxRowItem"})
    stats = [s.text.strip() for s in stats_raw]
    try:
        added_by_raw = stats[-1]
        to_reads_raw = stats[-2]
    except Exception as e:
        logger.info(f"Error {e} for {url}")
        return null_return
    added_by = re.findall("\d+", added_by_raw)
    to_reads = re.findall("\d+", to_reads_raw)

    return {
        "added_by": added_by,
        "to_reads": to_reads,
    }


def create_url(id):
    return "https://www.goodreads.com/book/show/" + str(id)


def read_goodreads_export(file_path):
    if file_path.endswith(".csv"):
        goodreads_data = pd.read_csv(file_path)
    elif file_path.endswith(".xlsx"):
        goodreads_data = pd.read_excel(file_path)
    return goodreads_data


def apply_added_by(urls, wait=4):
    stats_basic = [get_stats(url, wait=wait) for url in urls]
    url_stats = [url.replace("show", "stats") for url in urls]
    stats_read = [get_read_stats(url) for url in url_stats]
    goodreads_data = pd.concat(
        [pd.DataFrame(stats_basic), pd.DataFrame(stats_read)], axis=1
    )

    goodreads_data["date_published"] = (
        goodreads_data["Publish_info"]
        .str.split("by ")
        .apply(lambda x: x[0] if x is not None else None)
    )
    return goodreads_data


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
