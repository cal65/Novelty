from bs4 import BeautifulSoup
import requests
import pandas as pd
import sys
import logging

logging.basicConfig()
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# add the handler to the root logger
logger = logging.getLogger(__name__)
logger.addHandler(ch)

S = requests.Session()

URL = "https://en.wikipedia.org/w/api.php"
PARAMS = {
    "action": "opensearch",
    "namespace": "0",
    "search": "Placeholder",
    "limit": "1",
    "format": "json",
}


def grab_first_result(search_term):
    PARAMS["search"] = search_term
    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()
    try:
        first_result = DATA[-1][0]
    except:
        logger.info("No Wikipedia page found for: " + search_term)
        return "No result"
    return first_result


def eval_page(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    paragraphs = soup.findAll("p")
    return paragraphs


def search_paragraph_for_gender(paragraph):
    words = paragraph.split(" ")
    # counter = [0, 0, 0]
    for word in words:
        if word.lower() in ["he", "his", "him"]:
            return "male"
        elif word.lower() in ["she", "her", "hers"]:
            return "female"
        # elif word.lower() in ["they", "them", "theirs"]:
        #     return "non-binary"
    return None


def search_raw_page_for_gender(paragraphs):
    for paragraph_raw in paragraphs:
        gender = search_paragraph_for_gender(paragraph_raw.text)
        if gender:
            return gender
    return "unknown"


def search_person_for_gender(person):
    result = grab_first_result(person)
    if result == "No result":
        gender = "unknown"
    else:
        paragraphs = eval_page(result)
        gender = search_raw_page_for_gender(paragraphs)
    return gender


def evaluate_file(csv, fix_col="gender_fixed", name_col="Author"):
    df = pd.read_csv(csv)
    authors = df.loc[~(df[fix_col].isin(["male", "female", "non-binary"])), name_col]
    genders = [search_person_for_gender(author) for author in authors]
    df.loc[~(df[fix_col].isin(["male", "female", "non-binary"])), fix_col] = genders
    logger.info("Updating genders for " + str(len(genders)) + " authors")
    return df


if __name__ == "__main__":
    file_path = sys.argv[1]
    evaluate_file(file_path).to_csv(file_path, index=False)
