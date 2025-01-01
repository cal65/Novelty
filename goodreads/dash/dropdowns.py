from dash import dcc, html
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
from goodreads.plotting.plotting import (
    month_plot,
    format_month_plot,
    load_data,
    preprocess,
    create_read_plot_heatmap
)
import pandas as pd

external_stylesheets = [
    "/static/css/landing.css"  # This should be the relative URL as served by Django
]
app = DjangoDash("goodreads_dash", external_stylesheets=external_stylesheets)


@app.callback(
    [Output("stored-data", "data"), Output("stored-years", "years")],
    [
        Input(component_id="usernameInput", component_property="value"),
    ],
)
def initiate_data(username):
    df = load_data(username)
    df = preprocess(df)
    df = format_month_plot(df, date_col="date_read")
    all_years = df["year_read"].unique()
    return df.to_dict("records"), all_years


@app.callback(
    Output("month-plot", "figure"),
    [
        Input("stored-data", "data"),
        Input(component_id="yearDropdown", component_property="value"),
        Input(component_id="usernameInput", component_property="value"),
    ],
)
def graph_monthly(data, selected_years, username):
    df = pd.DataFrame(data)
    print(df.head())
    if "all" not in selected_years:
        df = df[df["year_read"].isin(selected_years)]
    month_fig = month_plot(
        df,
        username=username,
        date_col="date_read",
        page_col="number_of_pages",
        title_col="title_simple",
        author_gender_col="gender",
        format=False,
    )
    month_fig.update_layout(
        autosize=True,
        height=None,  # Default height; remove this to let Plotly manage it dynamically
        width=None,  # Default width; remove this to let Plotly manage it dynamically
        margin=dict(l=20, r=20, t=20, b=20),  # Adjust margins as needed
    )
    return month_fig


@app.callback(
    Output("yearDropdown", "options"),
    Input("stored-years", "years"),
)
def update_year_dropdown_options(stored_years):
    stored_years.sort()
    stored_years = stored_years[::-1]
    stored_years.append("all")
    if stored_years:
        return [{"label": str(year), "value": year} for year in stored_years]
    return []


app.layout = html.Div(
    [
        dcc.Input(id="usernameInput", style={"display": "none"}, value=" "),
        dcc.Dropdown(
            id="yearDropdown",
            options=[
                {"label": str(year), "value": year}
                for year in [
                    "all",
                    2024,
                ]
            ],
            multi=True,
            value="all",  # Default to all years
            placeholder="Select Year(s)",
        ),
        dcc.Store(id="stored-data"),
        dcc.Store(id="stored-years"),
        dcc.Graph(id="month-plot"),
    ]
)

if __name__ == "__main__":

    app.run_server(debug=True)
