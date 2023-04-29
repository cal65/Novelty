import os


standard_layout = dict(
    title_x=0.5,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showline=True, linecolor="rgb(36,36,36)"),
    yaxis=dict(showline=True, linecolor="rgb(36,36,36)"),
    font=dict(family="Courier New"),
)

def save_fig(fig, file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    fig.write_html(file=file_path)