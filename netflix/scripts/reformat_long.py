import pandas as pd


def redate(df):
    df['Start Time'] = pd.to_datetime(df['Start Time'])
    df['Date'] = df['Start Time'].dt.date
    return df

def segment(df, user):
    df_return = df.loc[df['Profile Name'] == user]
    df_return = df_return.loc[pd.isnull(df_return['Supplemental Video Type'])]
    return df_return

