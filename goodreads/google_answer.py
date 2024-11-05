from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import sys
import logging
from .models import RefNationality
from spotify.plotting.utils import objects_to_df

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

S = requests.Session()

URL = "https://www.google.com/search?q="
nationality_dict = (
    objects_to_df(RefNationality.objects.all())
    .set_index("region")["nationality"]
    .to_dict()
)
nationality_dict["United States"] = "American"
nationality_dict["England"] = "English"
nationalities = set(nationality_dict.values())
regions = set(nationality_dict.keys())


def get_search_url(name):
    name = str(name)
    return URL + name.replace(" ", "+") + "+author+nationality"


def get_soup(url):
    headers = {
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
    }
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")
    return soup


def get_result(soup):
    raw_results = soup.findAll("div", {"class": "BNeawe iBp4i AP7Wnd"})
    if len(raw_results) == 0:
        # this result is less likely to be a straight nationality
        raw_results = soup.findAll("span", {"class": "FCUp0c rQMQod"})
    elif len(raw_results) == 0:
        raw_results = soup.findAll("span", {"class": "BNeawe tAd8D AP7Wnd"})
    elif len(raw_results) == 0:
        raw_results = soup.findAll("div", {"class": "BNeawe tAd8D AP7Wnd"})
    elif len(raw_results) == 0:
        raw_results = soup.findAll("div", {"class": "BNeawe deIvCb AP7Wnd"})
    elif len(raw_results) == 0:
        raw_results = soup.findAll("div", {"class": "BNeawe s3v9rd AP7Wnd"})

    results = []
    for raw in raw_results:
        children = raw.findChildren("a", recursive=True)
        if len(children) > 1:
            for child in children:
                results.append(child.get("aria-label"))
        else:
            texts = raw.text.split("-")
            if "People also ask" in texts:
                texts.remove("People also ask")
            for text in texts:
                if text not in ["Images", "People also ask"]:
                    result = text_to_national(text)
                    if result is not None:
                        results.append(result)
            if len(results) == 0:
                texts_space = raw.text.split(" ")
                texts_space = [t for t in texts_space if t not in set(["People", "also", "ask"])]
                for text in texts_space:
                    result = text_to_national(text)
                    if result is not None:
                        results.append(result)
    results = [r for r in results if r is not None]
    return results


def text_to_national(text):
    if text in ["Images", "People also ask"]:
        return None
    if text in nationalities:
        # if it's a nationality, add
        return text
    elif text in regions:
        # if it's a region, add the associated nationality
        return nationality_dict[text]
    elif "California" in text:
        return "American"
    elif "British" in text:
        return "British"
    else:
        logger.info(f"Unrecognized text: {text}")


def lookup_author_nationality(author):
    url = get_search_url(author)
    soup = get_soup(url)
    answers = get_result(soup)
    answers = [
        answer.replace("Nationality: ", "") for answer in answers if answer is not None
    ]
    answers = [
        answer.split(", ") for answer in answers
    ]  # sometimes we get "American, British" as a response
    answers = [a for answer in answers for a in answer]  # flatten list
    answers = pd.unique(answers)
    if len(answers) == 0:
        logger.info("No results found for " + str(author))
    return answers


def listlen(data):
    return len(data) if isinstance(data, np.ndarray) else 1


def convert_nats_list_to_df(nats_list):
    max_nat = max([listlen(n) for n in nats_list])
    columns = ["author"] + ["nationality_" + str(i) for i in np.arange(1, max_nat + 1)]
    output_dicts = []
    for nationality in nats_list:
        # create a dictionary with keys nationality1, nationality2 etc.
        indiv_dict = {}
        for i in np.arange(0, max_nat):
            c = "nationality" + str(i + 1)
            if i < len(nationality):
                indiv_dict[c] = [nationality[i]]
            else:
                indiv_dict[c] = [None]
        # combine dicts as dataframes
        output_dicts.append(pd.DataFrame(indiv_dict))
    return pd.concat(output_dicts).reset_index(drop=True)


def append_nationalities(df, author_col="Author"):
    nats_list = df[author_col].apply(lookup_author_nationality)
    nats_df = convert_nats_list_to_df(nats_list)
    return pd.concat([df.reset_index(drop=True), nats_df], axis=1)


def lookup_unfound(df, nationality_col="nationality1", author_col="Author"):
    # for a file without the base schema
    if nationality_col not in df.columns:
        return append_nationalities(df)
    # for a file with the nationality column
    df_found = df[(pd.notnull(df[nationality_col])) & (df[nationality_col] != "")]
    df_unfound = df[(pd.isnull(df[nationality_col])) | (df[nationality_col] == "")]
    df_unfound = df_unfound[
        [
            c
            for c in df_unfound.columns
            if ("nationality" not in c) and (nationality_col not in c)
        ]
    ]
    if len(df_unfound) > 0:
        logger.info(
            "Looking up author nationalities for " + str(len(df_unfound)) + " authors"
        )
        df_unfound = append_nationalities(df_unfound)
        df_return = pd.concat([df_found, df_unfound])
    else:
        df_return = df_found

    return df_return


if __name__ == "__main__":
    file_path = sys.argv[1]
    df = pd.read_csv(file_path)
    lookup_unfound(df).to_csv(file_path, index=False)
