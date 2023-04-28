import logging
import os
import sys
import glob
import pandas as pd
from pandas._testing import assert_frame_equal

sys.path.append("..")
from spotify.plotting import plotting as splot
from goodreads.plotting import plotting as gplot

logging.basicConfig()
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# add the handler to the root logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(ch)

test_df = pd.DataFrame(
    {
        "Author": ["J.K. Rowling", "LeBron James"],
        "Title": ["Harry Potter and the 8th Book", "How to Build a Superteam"],
    }
)


# def test_create_artifact_addition(artifact_path="authors_database.csv"):
#     authors_db = pd.read_csv(artifact_path)
#
#     artifact_addition = create_artifact_addition(
#         df=test_df, authors_database=authors_db
#     )
#     # J.K. Rowling should be in Authors database. LeBron James should not
#     assert artifact_addition.shape[0] == 1
#     # we should have one row of addition, LeBron James
#     assert artifact_addition["gender_fixed"].values == ["male"]
#     # LeBron is male
#     assert artifact_addition["Country.Chosen"].values == ["American"]
#     # LeBron is American

#
# def test_update_missing_data():
#     no_missing_data = pd.DataFrame(
#         {
#             "Title": ["A", "B", "C"],
#             "Author": ["La La", "Ba Ba", "Ra Ra"],
#             "Added_by": [99, 1029405, 3332859],
#         }
#     )
#     updated = update_missing_data(no_missing_data)
#     assert_frame_equal(no_missing_data, updated)



def test_goodreads_main():
    username = "test-olive"
    graph_dir = f"goodreads/static/Graphs/{username}"
    goodreads_files_raw = [f"monthly_pages_read_{username}.html", f"goodreads_summary_{username}.html",
                       f"finish_plot_{username}.html",
                       f"goodreads_genre_diff_{username}.html",
                       f"monthly_pages_read_{username}.html"]
    goodreads_files = [os.path.join(graph_dir, f) for f in goodreads_files_raw]
    for f in goodreads_files:
        os.remove(f)
    logger.info("Running goodreads plot")
    gplot.main(username)
    html_files = glob.glob(os.path.join(graph_dir, '*html'))
    assert(all([f in html_files for f in goodreads_files]))

def test_spotify_main():
    # my approach here is I've created a user named test-olive and loaded it with data
    username = "test-olive"
    graph_dir = f"goodreads/static/Graphs/{username}"

    spotify_files_raw = [f"overall_{username}.html", f"spotify_year_plot_{username}.html", f"spotify_daily_plot_{username}.html", f"spotify_popularity_plot_{username}.html",
                     f"spotify_genre_plot_{username}.html", f"spotify_top_songs_{username}.html"]
    spotify_files = [os.path.join(graph_dir, f) for f in spotify_files_raw]
    for f in spotify_files:
        os.remove(f)

    logger.info("Running spotify plot")
    splot.main(username)
    html_files = glob.glob(os.path.join(graph_dir, '*html'))
    assert(all([f in html_files for f in spotify_files]))
