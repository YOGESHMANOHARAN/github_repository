import pandas as pd
import numpy as np

xl_file = pd.read_excel('solar data 10 year.xlsx', sheet_name= 'Sheet53' ,usecols= [0,1])
xl_file= xl_file.loc[0:35039]

date = pd.date_range(start='2021-05-05 00:00',end='2021-07-31 23:55',freq='5T')
