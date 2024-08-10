from dash import dcc, html
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output, State
from netflix.plotting.plotting import plot_network, load_data

external_stylesheets = [
    "/static/css/landing.css"  # This should be the relative URL as served by Django
]
app = DjangoDash("bacon_interactive", external_stylesheets=external_stylesheets)

username = 'ja'
df = load_data(username)

app.layout = html.Div([
    dcc.Graph(
        id='network-graph',
        config={'scrollZoom': True},
        figure=plot_network(df, username)
    )
])

@app.callback(
    Output('network-graph', 'figure'),
    [Input('network-graph', 'clickData')],
    [State('network-graph', 'figure')]
)
def update_figure(clickData, existing_figure):
    fig = existing_figure
    if clickData:
        clicked_node = clickData['points'][0]['text']
        node_names = [node['text'] for node in fig['data']]

        # Make all nodes transparent
        for trace in fig['data']:
            if 'text' in trace:
                trace['marker']['opacity'] = 0.1
        # Highlight the clicked node and its neighbors
        for trace in fig['data']:
            if 'text' in trace:
                if clicked_node in trace['text']:
                    trace['marker']['opacity'] = 1
                    neighbors = list(G.neighbors(clicked_node))
                    if clicked_node in neighbors:
                        trace['marker']['opacity'] = 1
                else:
                    trace['marker']['opacity'] = 0.1

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)