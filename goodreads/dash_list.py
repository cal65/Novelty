from dash import dcc, html
import pandas as pd
import os
from spotify.plotting.utils import objects_to_df
from django_plotly_dash import DjangoDash

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goodreads_history.settings')
# django.setup()
# Initialize the Dash app
external_stylesheets = [
    '/static/css/landing.css'  # This should be the relative URL as served by Django
]
app = DjangoDash('checklist',  external_stylesheets=external_stylesheets)

def load_data(username='cal'):
    from goodreads.models import ExportData, BooksLists
    list_df = objects_to_df(BooksLists.objects.filter(list_name="New York Times Best Books of 21st Century"))
    list_df['title'] = list_df['title'].str.strip()
    list_df['author'] = list_df['author'].str.strip()
    list_df['title_author'] = list_df['title'] + ' - ' + list_df['author']
    user_df = objects_to_df(ExportData.objects.filter(username=username))
    df = pd.merge(list_df, user_df[['book_id', 'username']], on='book_id', how='left')
    return df

list_merged = load_data(username='cal')

app.layout = html.Div(
            className='checklistContainer',
            children=[
                dcc.Checklist(
                    id='checklist',
                    className='checklist',
                    options=[{'label': html.Span([html.B(str(100-i) + '. '), t]),
                              'value': t} for i, t in enumerate(list_merged['title_author'])],
                    value=list_merged.loc[pd.notnull(list_merged['username'])]['title_author'].values,
                    labelStyle={'display': 'block'}
                ),
                html.Div(id='output')
            ]
)

if __name__ == '__main__':

    app.run_server(debug=True)