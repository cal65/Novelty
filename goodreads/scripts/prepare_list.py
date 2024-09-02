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
    rank_dict = df.set_index('title_simple')['Index'].to_dict()
    books_list['rank'] = books_list['title_simple'].map(rank_dict)
    books_list.to_csv(new_file_path)

