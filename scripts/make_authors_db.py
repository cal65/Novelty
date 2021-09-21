import psycopg2
import os
from sqlalchemy import create_engine
import pandas as pd


def start():
    """ populate authors table in the PostgreSQL database"""
    try:
        connection = psycopg2.connect(user='cal65', password=os.environ['cal65_pass'], host="127.0.0.1", 
                                       port="5432", 
                                       database="goodreads")  

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connection is not None:
            connection.close()
    engine = create_engine('postgresql+psycopg2://cal65:'+os.environ['cal65_pass']+'@127.0.0.1/goodreads')
    authors_db = pd.read_csv('artifacts/authors_database.csv')
    authors_db = authors_db[['Author', 'gender_fixed', 'nationality1', 'nationality2', 'Country.Chosen']]
    authors_db.columns = ['author_name', 'gender', 'nationality1', 'nationality2', 'nationality_chosen']
    authors_db.to_sql('goodreads_authors', engine, if_exists='replace',index=False)
    connection.close()

if __name__ == "__main__":
    start()
