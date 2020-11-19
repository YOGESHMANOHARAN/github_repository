import pandas as pd
import os

# We should probably make this more object based ultimately, but I'm tired at the moment...

filename = 'test.xlsx'
resample_rate = '1min'

excel = pd.ExcelFile(filename)
sheet_names = excel.sheet_names

all_data = pd.DataFrame()
data = {}
for sheet in sheet_names:
    sheet_data = pd.read_excel(filename, sheet_name=sheet, index_col='Time/Date', parse_dates=True)
    sheet_data.resample(resample_rate)
    data[sheet] = sheet_data

