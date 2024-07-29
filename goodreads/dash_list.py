from dash import dcc, html
import pandas as pd
import os
from django_plotly_dash import DjangoDash

# Initialize the Dash app
external_stylesheets = [
    '/static/css/landing.css'  # This should be the relative URL as served by Django
]
app = DjangoDash('checklist',  external_stylesheets=external_stylesheets)

df = pd.read_csv('artifacts/nyt_merged.csv')
df['title_author'] = df['rank'].astype(str) + '. ' + df['title'] + ' - ' + df['author']

app.layout = html.Div(
            className='checklistContainer',
            children=[
                dcc.Checklist(
                    id='checklist',
                    className='checklist',
                    options=[{'label': i, 'value': i} for i in df['title_author']],
                    value=[],
                    labelStyle={'display': 'block'}
                ),
                html.Div(id='output')
            ]
)

if __name__ == '__main__':

    app.run_server(debug=True)