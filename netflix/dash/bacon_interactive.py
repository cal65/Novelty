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
    [
        dcc.Graph(
            id="network-graph",
            className="dash-frame-network",
            config={"scrollZoom": True},
            figure=plot_network(df, username),
            style={"width": "100%"},
        ),
        dcc.Store(id="click-store", data=None),
    ]
)


@app.callback(
    [Output("network-graph", "figure"), Output("click-store", "data")],
    [Input("network-graph", "clickData")],
    [State("network-graph", "figure"), State("click-store", "data")],
)
def update_figure(clickData, existing_figure, stored_click):
    fig = existing_figure
    if clickData:
        clicked_node = clickData["points"][0]["customdata"]
        node_name = clicked_node[0]
        logger.info(f"clickData: {clickData}. stored_click: {stored_click}")
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
