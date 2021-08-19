import glob
import pandas as pd
from append_to_export import fix_date

files = glob.glob('data/*appended.csv')
[fix_date(file) for file in files]