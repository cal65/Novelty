from dash import dcc, html
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output, State
from netflix.plotting.plotting import plot_network, load_data
from netflix import data_munge as nd
import logging

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

external_stylesheets = [
    "/static/css/landing.css"  # This should be the relative URL as served by Django
]
app = DjangoDash("bacon_interactive", external_stylesheets=external_stylesheets)

username = "ja"
df = load_data(username)
G = nd.format_network(df)

app.layout = html.Div(
    className="checklistContainer",
    children=[
        dcc.Graph(
            id="network-graph",
            className="dash-frame",
            config={"scrollZoom": True},
            figure=plot_network(df, username),
            style={"width": "100%"},
        )
    ],
)


@app.callback(
    Output("network-graph", "figure"),
    [Input("network-graph", "clickData")],
    [State("network-graph", "figure")],
)
def update_figure(clickData, existing_figure):
    fig = existing_figure
    if clickData:
        logger.info(clickData)
        clicked_node = clickData["points"][0]["customdata"]
        node_name = clicked_node[0]

        # Highlight the clicked node and its neighbors
        for trace in fig["data"]:
            if trace["mode"] == "markers":
                # Make an array of 0.1 and 1, with 1 being the clicked node
                node_names = [n[0] for n in trace["customdata"]]
                # Find the neighbors and change those to a middle opacity
                neighbors = set(G.neighbors(node_name))
                opacity_array = [
                    1 if nn == node_name else 0.7 if nn in neighbors else 0.1
                    for nn in node_names
                ]
                trace["marker"]["opacity"] = opacity_array

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
