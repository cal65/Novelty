from dash import dcc, html
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output, State
from netflix.plotting.plotting import plot_network, load_data
from netflix import data_munge as nd
import plotly.graph_objs as go
import plotly.io as pio
from networkx.readwrite import json_graph
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


@app.callback(
    [Output("figure-store", "data"),
     Output("network-data-store", "data")],
    [Input("usernameInput", "value")],
)
def initiate_data(username: str):
    df = load_data(username)
    G = nd.format_network(df)
    fig = plot_network(df, username)
    Gjson = json_graph.node_link_data(G)
    logger.info(f"Initiated with username {username} and fig: {fig['data'][0]['x'][0]}")
    return fig.to_json(), Gjson


app.layout = html.Div(
    [
        dcc.Input(id="usernameInput", style={"display": "none"}, value=""),
        dcc.Graph(
            id="network-graph",
            className="dash-frame-network",
            config={"scrollZoom": True},
            style={"width": "100%"},
        ),
        dcc.Store(id="network-data-store", data=None),
        dcc.Store(id="figure-store", data=None),
        dcc.Store(id="click-store", data=None),
    ]
)


@app.callback(
    [Output("network-graph", "figure"), Output("click-store", "data")],
    [Input("network-graph", "clickData"),
     Input("network-data-store", "data"),
     Input("figure-store", "data")],
    [State("network-graph", "figure"), State("click-store", "data")],
)
def update_figure(clickData, gData, figure_data, existing_figure, stored_click):
    if existing_figure is None and figure_data is not None:
        fig = pio.from_json(figure_data) #deserialize data stored in store
        return fig, stored_click
    else:
        fig = existing_figure

    if clickData:
        clicked_node = clickData["points"][0]["customdata"]
        node_name = clicked_node[0]
        logger.info(f"clicked node: {clicked_node}. stored_click: {stored_click}")
        G = json_graph.node_link_graph(gData)
        if node_name != stored_click:
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
            stored_click = node_name
        else:
            # Reset the opacity to default
            for trace in fig["data"]:
                if trace["mode"] == "markers":
                    trace["marker"]["opacity"] = 1

    return fig, stored_click


if __name__ == "__main__":
    app.run_server(debug=True)
