import os
import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)
import pandas as pd
import psycopg2
from plotnine import *

from .models import ExportData

post_pass = os.getenv("cal65_pass")


def get_data(user):
    conn = psycopg2.connect(
        host="localhost", database="goodreads", user="cal65", password=post_pass
    )
    query = f"""
    select id, book_id, title, author, number_of_pages,
    my_rating, average_rating, original_publication_year,
    shelf1, shelf2, shelf3, shelf4, shelf5, shelf6, shelf7,
    date_read, exclusive_shelf, added_by, to_reads,
    gender, nationality1, nationality2, nationality_chosen
    from goodreads_exportdata e left join goodreads_authors as a 
    on e.author = a.author_name where e.username = '{user}'
    """
    try:
        df = pd.read_sql(query, con=conn)
        return df
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return


def preprocess(df):
    gender_dict = {"mostly_male": "male", "mostly_female": "female"}
    df["gender"] = df["gender"].map(gender_dict).fillna(df["gender"])
    df["date_read"] = pd.to_datetime(df["date_read"])
    df["title_simple"] = df["title"].str.replace(":.*", "")
    df["title_simple"] = df["title_simple"].str.replace("\\(.*\\)", "")
    return df


def narrative(df):
    shelf_columns = [s for s in df.columns if s.startswith("shelf")]
    df["narrative"] = df[shelf_columns].apply(
        lambda x: "Nonfiction" if "Nonfiction" in x.values else "Fiction", axis=1
    )
    return df


def read_percentage(df):
    # It seems sometimes the "added by" value is off by a factor of 10. When the
    # number of people listing the book as "to read" is larger than total added by, multiply by 10
    df.loc[df["to_reads"] > df["added_by"], "added_by"] = (
        df.loc[df["to_reads"] > df["added_by"], "added_by"] * 10
    )
    df["read"] = df["added_by"] - df["to_reads"]
    df["read_percentage"] = df["read"] / df["added_by"]
    return df


def run_all(df):
    df = read_percentage(narrative(preprocess(df)))
    return df

def generate_labels(breaks):
    if len(breaks) == 2:
        return [f"{breaks[0]} - {breaks[1]}"]
    else:
        return [f"{breaks[0]} - {breaks[1]}"] + generate_labels(breaks[1:])


def read_plot(df, name, read_col, title_col, min_break=3, plot=F, plot_name ='popularity_spectrum_', date_col='date_read', start_year=None):
    max_read = int(df[read_col].max())
    df = df[pd.notnull(df[read_col])]
    if start_year is not None:
        df = df[df[date_col].dt.year >= start_year]
    max_digits = len(str(max_read))
    digit_range = list(range(min_break, max_digits+1))
    breaks = [0] + [10**d for d in digit_range]
    df['title_length'] = df[title_col].apply(lambda x: len(x))
    # order title text by popularity
    df.sort_values(by='read', inplace=True)
    df[title_col] = df[title_col].astype('category')
    # ['0 - 1,000', '1,000 - 10,000', '10,000 - 100,000', '100,000 - 1,000,000'] using fancy local-aware f:, hack
    labels = generate_labels([f"{b:,}" for b in breaks])
    # adding obscure and bestsellers commentary
    labels[0] = f"{labels[0]} \n Obscure"
    labels[-1] = f"{labels[-1]} \n Bestsellers"
    df['strats'] = pd.cut(df[read_col], bins = breaks, labels = labels, include_lowest = True)
    text_sizes = pd.pivot_table(df, index='strats', aggfunc={'title_length': lambda x: 120/max(x)})
    text_sizes.rename(columns = {'title_length': 'text_size'}, inplace=True)
    df = pd.merge(df, text_sizes, on='strats', how='left')
    (ggplot(df, aes('strats', 'title_simple'))
    + aes(fill='narrative')
    + geom_tile() 
    + geom_text(aes(label='title_simple', size='text_size')) 
    + facet_wrap('strats', scales='free', nrow=1)
    + scale_fill_manual(values = ['mediumvioletred', 'darkolivegreen'])
    + scale_size_continuous(guide = False, range=[4, 6])
    + xlab('Number of Readers')
    + ylab('Title')
    + theme(axis_text_y = element_blank())
    )

read_plot <- function(df, 
                      name, 
                      read_col, 
                      title_col, 
                      min_break = 3, 
                      plot=F, 
                      plot_name = 'popularity_spectrum_',
                      date_col='date_read',
                      start_year=NA){
  
  
  ggplot(df, aes(x=strats, y=get(title_col))) +
    geom_tile(aes(fill=Narrative), color='black') +
    geom_text(aes(label = get(title_col), size = text_size)) +
    facet_wrap(strats ~ ., scales='free', nrow=1) +
    scale_fill_manual(values = c('hotpink2', 'darkolivegreen')) +
    scale_size_continuous(guide = "none", range=c(2, 5)) +
    xlab('Number of Readers') + 
    ylab('Title') +
    ggtitle(paste0('Readership Spectrum - ', name)) +
    theme(axis.text.y = element_blank(),
          plot.title = element_text(hjust=0.5),
          panel.background = element_blank())
  if (plot){
    ggsave(paste0('Novelty/goodreads/static/Graphs/', name, '/', plot_name, name, '.jpeg'), width = 16, height=15)
  }
}    
