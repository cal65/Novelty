from dash import dcc, html
import pandas as pd
import os
from goodreads.models import ExportData, BooksLists
from spotify.plotting.utils import objects_to_df
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goodreads_history.settings')
# django.setup()
# Initialize the Dash app
external_stylesheets = [
    "/static/css/landing.css"  # This should be the relative URL as served by Django
]
app = DjangoDash("checklist", external_stylesheets=external_stylesheets)
list_df = objects_to_df(
    BooksLists.objects.filter(
        list_name="New York Times Best Books of 21st Century"
    ).order_by("-rank")
)
list_df["title"] = list_df["title"].str.strip()
list_df["author"] = list_df["author"].str.strip()
list_df["title_author"] = list_df["title"] + " - " + list_df["author"]


def initiate_lists(list_name):
    df = objects_to_df(BooksLists.objects.filter(list_name=list_name).order_by("-rank"))
    df["title"] = df["title"].str.strip()
    df["author"] = df["author"].str.strip()
    df["title_author"] = df["title"] + " - " + df["author"]
    return df


def load_data(df, username):
    user_df = objects_to_df(
        ExportData.objects.filter(username=username, exclusive_shelf="read")
    )
    if len(user_df) == 0:
        df["username"] = None
        return df
    merged_df = pd.merge(df, user_df[["book_id", "username"]], on="book_id", how="left")
    merged_df = pd.pivot_table(merged_df, index=['title', 'author', 'rank', 'list_name'], values='username',
                   aggfunc=lambda x: any(pd.notnull(x))).reset_index()
    merged_df.sort_values("rank", ascending=False, inplace=True)
    merged_df['username'] = merged_df['username'].replace(False, None)
    merged_df["title_author"] = merged_df["title"] + " - " + merged_df["author"]
    ## logic to add in matches based on title and author matches
    return merged_df


@app.callback(
    Output(component_id="checklist", component_property="options"),
    Output(component_id="checklist", component_property="value"),
    [
        Input(component_id="list_selector", component_property="value"),
        Input("usernameInput", "value"),
    ],
)
def update_checklist(listname, username):
    df = initiate_lists(listname)
    list_merged = load_data(df, username)
    options = [
        {
            "label": html.Span(
                [html.B(str(100 - i) + ". "), t]
            ),  # bold number then title
            "value": t,
        }
        for i, t in enumerate(list_merged["title_author"])
    ]
    values = list_merged.loc[pd.notnull(list_merged["username"])]["title_author"].values
    return options, values


app.layout = html.Div(
    className="checklistContainer",
    children=[
        dcc.Input(id="usernameInput", style={"display": "none"}, value=" "),
        dcc.Dropdown(
            id="list_selector",
            options=[
                {
                    "label": list_name,
                    "value": list_name,
                }
                # iterate through unique BooksLists names
                for list_name in list(
                    BooksLists.objects.order_by()
                    .values_list("list_name", flat=True)
                    .distinct()
                )
            ],
            value="New York Times Best Books of 21st Century",  # default value
        ),
        html.Br(),
        dcc.Checklist(
            id="checklist",
            className="checklist",
            options=[
                {
                    "label": html.Span(
                        [html.B(str(100 - i) + ". "), t]
                    ),  # bold number then title
                    "value": t,
                }
                for i, t in enumerate(list_df["title_author"])
            ],
            value=[],
            labelStyle={"display": "block"},
        ),
        html.Div(id="output"),
    ],
)


if __name__ == "__main__":

    app.run_server(debug=True)
