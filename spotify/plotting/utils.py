import os

import pandas as pd

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


def objects_to_df(objects):
    df = pd.DataFrame.from_records(objects.values())
    return df


def write_text(filename, texts):
    if isinstance(texts, list):
        text = "\n\n".join(texts)
    elif texts is None:
        text = ""
    else:
        text = texts
    with open(filename, "w") as f:
        f.write(text)

def minute_conversion(m):
    """
    Given float, return minutes and seconds
    """
    minutes = int(m)
    seconds = int((m-minutes)*60)
    if seconds < 10:
        seconds_str = f"0{str(seconds)}"
    else:
        seconds_str = str(seconds)
    if minutes == 0:
        minutes_str = ""
    else:
        minutes_str = str(minutes)
    time_str = f"{minutes_str}:{seconds_str}"
    return time_str