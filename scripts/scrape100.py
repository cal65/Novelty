from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import re
import sys


def scrape100(url_ending, save_path):
    url = "https://www.goodreads.com/list/show/" + url_ending
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    titles_raw = soup.findAll("a", {"class": "bookTitle"})
    titles = [book.get("href") for book in titles_raw]
    book_ids = [re.findall("\d+", title)[0] for title in titles]
    title_strings = [re.findall("[^.]+$", title)[0] for title in titles]
    title_strings = [
        title[re.search("-", title).end() :] if "-" in title else title
        for title in title_strings
    ]
    title_strings = [title.replace("_", " ") for title in title_strings]
    title_strings = [title.replace("-", " ") for title in title_strings]
    title_strings = [title.title() for title in title_strings]
    title_strings = [title.replace(" S ", "'s ") for title in title_strings]
    df = pd.DataFrame(
        {"Title.Raw": titles, "Book.Id": book_ids, "Title": title_strings}
    )
    df["Index"] = range(1, 101)
    df["Facet"] = (
        ["A"] * 25 + ["B"] * 25 + ["C"] * 25 + ["D"] * 25
    )  # for graphing purposes
    df.to_csv(save_path, index=False)


if __name__ == "__main__":
    """
    Usage: python scrape100.py url_ending
    """
    url_ending = sys.argv[1]
    save_path = sys.argv[2]
    scrape100(url_ending, save_path)
