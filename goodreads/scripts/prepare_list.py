import sys
import pandas as pd
from spotify.plotting.utils import objects_to_df
from goodreads.models import ExportData
from django.db.models import Q
from goodreads.plotting.plotting import simplify_titles


def convert_to_list(file_path, new_file_path):
    df = pd.read_csv(file_path)
    books_list = objects_to_df(ExportData.objects.filter(Q(title__in=df['Title']) | Q(book_id__in=df['Book.Id'])))
    books_list = books_list[['book_id', 'title', 'author']].drop_duplicates()
    df = simplify_titles(df, title_col='Title')
    books_list = simplify_titles(books_list, title_col='title')
    df['title_simple'] = df['title_simple'].str.lower()
    books_list['title_simple'] = books_list['title_simple'].str.lower()
    rank_dict = df.set_index('title_simple')['Index'].to_dict()
    books_list['rank'] = books_list['title_simple'].map(rank_dict)
    shortest_titles = books_list.groupby('rank')['title'].apply(lambda x: min(x, key=len))
    books_list['title'] = books_list['rank'].map(shortest_titles)
    books_list = simplify_titles(books_list, title_col='title')
    books_list['title'] = books_list['title_simple']
    books_list.to_csv(new_file_path)


if __name__ == "__main__":
    file_path = sys.argv[1]
    new_file_path = sys.argv[2]
    convert_to_list(file_path, new_file_path)