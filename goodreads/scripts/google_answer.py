from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

S = requests.Session()

URL = "https://www.google.com/search?q="


def get_search_url(name):
    name = str(name)
    return URL + name.replace(" ", "+") + "+nationality"


def get_soup(url):
    headers = {
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
    }
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")
    return soup


def get_result(soup):
    raw_results = soup.findAll("div", {"data-attrid": "kc:/people/person:nationality"})
    results = []
    for raw in raw_results:
        children = raw.findChildren("a", recursive=True)
        if len(children) > 1:
            for child in children:
                results.append(child.get("aria-label"))
        else:
            results.append(raw.text)
    return results


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
        print("No results found for " + str(author))
    return answers


def listlen(data):
    return len(data) if isinstance(data, np.ndarray) else 1


def convert_nats_list_to_df(nats_list):
    max_nat = max([listlen(n) for n in nats_list])
    columns = ["author"] + ["nationality_" + str(i) for i in np.arange(1, max_nat + 1)]
    output_dicts = []
    for nationality in nats_list:
        output_dict = {}
        for i in np.arange(0, max_nat):
            c = "nationality" + str(i + 1)
            if i < len(nationality):
                output_dict[c] = [nationality[i]]
            else:
                output_dict[c] = [None]
        output_dicts.append(pd.DataFrame(output_dict))
    return pd.concat(output_dicts).reset_index(drop=True)


def append_nationalities(df, author_col="Author"):
    nats_list = df[author_col].apply(lookup_author_nationality)
    nats_df = convert_nats_list_to_df(nats_list)
    return pd.concat([df.reset_index(drop=True), nats_df], axis=1)


def lookup_unfound(df, nationality_col="nationality_1", author_col="Author"):
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
