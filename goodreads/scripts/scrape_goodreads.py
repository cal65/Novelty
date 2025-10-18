from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import random
import time
import sys
import re
import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


cookies = {
    'ccsid': '162-6250125-6529944',
    'p': 'dkCKV365TjqNenOKY4VtqQ6sIm7CTPX-c9d94GhAzRXKWDHD',
    'likely_has_account': 'true',
    'allow_behavioral_targeting': 'true',
    'session-id': '135-9578339-3724526',
    'logged_out_browsing_page_count': '2',
    'srb_1': '0',
    'ubid-main': '133-4011406-7695433',
    'lc-main': 'en_US',
    'csm-hit': 'tb:28PZZBK444T48GAAWQ0H+b-4K51QZ90N1KMGMJX1EGE|1667883949756&t:1667883949756&adb:adblk_no',
    'srb_8': '0_ar',
    '__qca': 'P0-58208308-1679029998916',
    'locale': 'en',
    'ntvSession': '{"id":7105107,"placementID":1210536,"lastInteraction":1689465068498,"sessionStart":1689465068498,"sessionEndDate":1689490800000,"experiment":""}',
    'csm-sid': '269-3996257-5017812',
    'session-id-time': '2378177356l',
    'session-token': 'od3bAO9OYTy8DywKy+aMKtbRJARxFTJCRaQVdigNS66w2JXYE94wT9XLh4+rNCXpMjxzC5Bo06juZvfqQoDtO8EbB90m8cDnXZMZU20BezWgwngpTa0diz9uWKdWyGuTxpazjAIeimkw9bzX0cCuKRstzUuxfROUfP12u/p0a9zo/LIv1m3oV08dtuIiDeWq1GQJ2gwRDL51n7cmHAeVLhEx5NjGN8XdnYF6XMRbFYioA6HePRGmRgnC3o8ub6+2iFKqyg4I728EwELJh/fs7e8rJzQt7xiISJD2wKAynlurzNM4mrX2jr2MSCbIGH6H1+DlKKlFg1MZoDET5dj2ce2cWddxVyI25s3m2MrcmKl+FVM4DYiV4Tcaw3TTW0kD',
    'x-main': 'n9oyMq5CUQ9WbCvZjaUlyok7rXOnq0GEjBm2GCKy1NeJ1AqvlmoUdxalzQJEzDyI',
    'at-main': 'Atza|IwEBIMkjx-aTGd5k5nOkjWE2S50ghFqGwXFblgQVwqkLIK0PpWxkaYVh4LWhhqF7qP3bEFDHsQ8VS7vyBC8aHWvY47-Aef9fMP5aQ01xHNps59k6kvGGqoqG_Jm2mvZsKHzygEteaxC0K45nhUEsdIYZ-KMEQqxV_EsImxEkPmQ3860AaQ7DN9cCviswebYV8FYkIU3I4WLenkGiH7jIfFAi15_BlpSTMsGYft98wFpjb5pKFxRpIs91oQvD7tCfLVf3MwnGve3V_zcWcr_Ft-PbS1KD',
    'sess-at-main': '"L4X7nx1bEIpiwwD4dl1RnG+lCVmCeLZhDOTptos71YI="',
    '_session_id2': '709591c189ab49250a9d5e92eaf6ef6d',
    '__gads': 'ID=df0a6707150d114d:T=1670897981:RT=1690310731:S=ALNI_MZfGBQsHE3Vk7tICMIg8zJxLI8e8Q',
    '__gpi': 'UID=0000097ff616a3c7:T=1682402001:RT=1690310731:S=ALNI_MY4xLYySL-kyW09g_nl8AuOjCRIbQ',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    # 'Cookie': 'ccsid=981-7720517-4539359; p=dkCKV365TjqNenOKY4VtqQ6sIm7CTPX-c9d94GhAzRXKWDHD; likely_has_account=true; allow_behavioral_targeting=true; session-id=141-6452885-9687058; logged_out_browsing_page_count=2; srb_1=0; ubid-main=131-4250835-4161367; lc-main=en_US; csm-hit=tb:28PZZBK444T48GAAWQ0H+b-4K51QZ90N1KMGMJX1EGE|1667883949756&t:1667883949756&adb:adblk_no; srb_8=0_ar; __qca=P0-58208308-1679029998916; locale=en; ntvSession={"id":7105107,"placementID":1210536,"lastInteraction":1689465068498,"sessionStart":1689465068498,"sessionEndDate":1689490800000,"experiment":""}; csm-sid=269-3996257-5017812; session-id-time=2320515620l; session-token=Bll6D6eAe4nNvOkehUMOOiTy4c4dutA4SyuqLzIqhZ5cMhyT2bANWizk46rCLq+4aX5D5pqBvnIaX6QsPa56vc5gkxqXminijtEMeUbLF3qOik7AZPmfvytj6nPBPfT+t9A42Dp7xlKFAZnaVO+Foi21M9N3xAh3QCCPxdSAaPZkhowMHaJGGjttzEyUu2EUX1DMzy5acpvzFWv7UwT1gUzeFee0FrxSfSh8k0dQdkCZP6+7WRHUAIM3gV1xnOzb; x-main="4EosvwpQCoL@Zqhj7Zl8DtXYnjfXD7IkpvU@N8xOvXojNJjDQltTAFj8AHu9yDRf"; at-main=Atza|IwEBIMkjx-aTGd5k5nOkjWE2S50ghFqGwXFblgQVwqkLIK0PpWxkaYVh4LWhhqF7qP3bEFDHsQ8VS7vyBC8aHWvY47-Aef9fMP5aQ01xHNps59k6kvGGqoqG_Jm2mvZsKHzygEteaxC0K45nhUEsdIYZ-KMEQqxV_EsImxEkPmQ3860AaQ7DN9cCviswebYV8FYkIU3I4WLenkGiH7jIfFAi15_BlpSTMsGYft98wFpjb5pKFxRpIs91oQvD7tCfLVf3MwnGve3V_zcWcr_Ft-PbS1KD; sess-at-main="L4X7nx1bEIpiwwD4dl1RnG+lCVmCeLZhDOTptos71YI="; _session_id2=709591c189ab49250a9d5e92eaf6ef6d; __gads=ID=df0a6707150d114d:T=1670897981:RT=1690310731:S=ALNI_MZfGBQsHE3Vk7tICMIg8zJxLI8e8Q; __gpi=UID=0000097ff616a3c7:T=1682402001:RT=1690310731:S=ALNI_MY4xLYySL-kyW09g_nl8AuOjCRIbQ',
    'DNT': '1',
    'If-None-Match': 'W/"9404a63aaa98659fb1000399ea02cdf3"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

# response = requests.get('https://www.goodreads.com/book/stats/50175419', cookies=cookies, headers=headers)


def get_soup(url):
    try:
        page = requests.get(url, cookies=cookies, headers=headers, timeout=5)
    except Exception as e:
        logger.info(f"Error {e} in page requests")
        return None
    soup = BeautifulSoup(page.content, "html.parser")
    return soup

def get_scripts(soup):
    scripts = soup.find_all("script", string=re.compile("secondaryContributorEdges"))
    script = scripts[0].contents[0]
    return script

def iter_get(d, keys):
    for key in keys:
        try:
            d = d[key]
        except (KeyError, TypeError):
            return None
    return d

def get_genres(script):
    data = json.loads(script)
    d2 = iter_get(data, ['props', 'pageProps', 'apolloState'])
    if d2 is None:
        return None
    book_keys = [k for k in d2.keys() if k.startswith('Book')]
    # genre_keys = ['props', 'pageProps', 'apolloState', 'Book:kca://book/amzn1.gr.book.v1.L8xC_pyytbmWYVi8GFp1dA', 'bookGenres']
    genres_raw = iter_get(d2, [book_keys[0], 'bookGenres'])
    if genres_raw is None:
        return None
    genres = [g.get('genre').get('name') for g in genres_raw]
    return genres


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
    try:
        genre_divs = soup.find("div", {"data-testid": "genresList"})
        shelves = [g.text for g in genre_divs.findAll("a")]
    except Exception as e:
        logger.info(f"Exception {e} encountered for scraping genres")
        shelves = None

    try:
        title = soup.find("h1").text.replace("\n", "")
    except:
        title = None

    try:
        author = soup.find("span", {"data-testid": "name"}).text
        author = re.sub(pattern=r"\s+", repl=" ", string=author)
    except:
        author = None

    try:
        publish_info = details.find("p", {"data-testid": "publicationInfo"}).text
        publish_info = publish_info.replace("\n", "")
        publish_info = publish_info.replace("First published", "").strip()

    except:
        publish_info = None

    try:
        original_publication_year = int(re.match('.*?([0-9]+)$', publish_info).group(1))
    except:
        original_publication_year = None

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
    except Exception as e:
        numberOfPages = None
    time.sleep(wait)

    return {
        "title": title,
        "author": author,
        "publish_info": publish_info,
        "original_publication_year": original_publication_year,
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
        ratings_raw = stats[1]
        reviews_raw = stats[2]
        to_reads_raw = stats[3]
        added_by_raw = stats[4]
    except Exception as e:
        logger.info(f"Error {e} for {url}")
        return null_return
    ratings = re.findall(r"\d+", ratings_raw)
    reviews = re.findall(r"\d+", reviews_raw)
    to_reads = re.findall(r"\d+", to_reads_raw)
    to_reads = int("".join(to_reads))
    read = int("".join(ratings)) + int("".join(reviews))
    added_by = int("".join(re.findall(r"\d+", added_by_raw)))
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
