import pandas as pd
import sys
from google_answer import append_nationalities
from wikipedia import search_person_for_gender
import gender_guesser.detector as gender
from choose_nationality import choose_nationality
import logging

logging.basicConfig()
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# add the handler to the root logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(ch)


def guess_gender(author):
    d = gender.Detector()
    names = author.split(" ")
    first_name = names[0] if names is not None else ""
    gender_return = d.get_gender(
        first_name
    )  # this returns male, female, unknown or andy
    if gender_return not in ["male", "female"]:
        gender_return = search_person_for_gender(author)
    return gender_return


def create_artifact_addition(df, authors_database, author_col="Author"):
    """
    Take a dataframe with an author_col.
    Compare authors in dataframe with authors in database.
    Subset out the rows with authors not in database.
    Look up nationalities and genders for those authors
    Return dataframe with columns appended.
    """
    df.drop_duplicates(author_col, keep="first", inplace=True)
    df_addition = df[~df[author_col].isin(authors_database[author_col])]
    df_addition = append_nationalities(
        df_addition
    )  # this will add nationality1, nationality2 etc (given these Google results)
    df_addition = choose_nationality(df_addition)  # this will add country_chosen
    df_addition["gender_fixed"] = df_addition[author_col].apply(guess_gender)

    return df_addition


def update_artifact(df, author_col="Author", artifact_path="authors_database.csv"):
    authors_database = pd.read_csv(artifact_path)
    authors_addition = create_artifact_addition(df, authors_database, author_col)
    logger.info(
        "Adding " + str(len(authors_addition)) + " new rows to authors database"
    )
    df_return = pd.concat([authors_database, authors_addition])
    df_return.reset_index(drop=True, inplace=True)
    df_return.to_csv(artifact_path, index=False)


if __name__ == "__main__":
    file_path = sys.argv[1]
    df = pd.read_csv(file_path)
    update_artifact(df)
