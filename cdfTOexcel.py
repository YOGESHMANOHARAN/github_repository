import glob
import pandas as pd
import numpy as np
from netCDF4 import Dataset
import xarray as xr
import datetime
import time
file_list=glob.glob(r"C:\Users\ymnharan\Documents\GitHub\github_repository\STOCHASTIC DATA\wind_data\**",recursive=True)
ran = range(1,len(file_list))
date = pd.date_range('2005-01-01 00:00:00','2020-12-31 23:45:00', freq="30T")
resultdf=pd.DataFrame(index=date)
resultdf['v_z']=0.000
empty_df= pd.DataFrame()
year_h = range(2005,2021)
for i,h in zip (ran,year_h):
    file = xr.open_dataset(file_list[i], decode_times=False)
    numpy_data = file.as_numpy()
    if 'v_z'in file:
         cdf2Dataframe =numpy_data['v_z'].dropna('time').to_dataframe()
         cdf2Dataframe= cdf2Dataframe.reset_index(level=[0,1])
         cdf2Dataframe= cdf2Dataframe[cdf2Dataframe['z']==150]
         cdf2Dataframe = cdf2Dataframe[['time', 'v_z']]
         cdf2Dataframe = cdf2Dataframe.rename(columns={'time': 'time_seconds'})
         cdf2Dataframe['date'] = 'Nan'
         for l in range(len(cdf2Dataframe)):
          cdf2Dataframe['date'].iloc[l] = time.strftime('%m/%d/' + str(h) + ' %H:%M:%S',time.gmtime(cdf2Dataframe['time_seconds'].iloc[l]))
         cdf2Dataframe = cdf2Dataframe.set_index('date')
         del cdf2Dataframe['time_seconds']
         empty_df = pd.concat([empty_df, cdf2Dataframe])
         print(i,h)
    else:
         cdf2Dataframe = numpy_data['v_wind_h'].dropna('time').to_dataframe()
         cdf2Dataframe = cdf2Dataframe.reset_index(level=[0, 1])
         cdf2Dataframe = cdf2Dataframe[cdf2Dataframe['height'] == 150]
         cdf2Dataframe = cdf2Dataframe[['time', 'v_wind_h']]
         cdf2Dataframe = cdf2Dataframe.rename(columns={'time':'time_seconds'})
         cdf2Dataframe = cdf2Dataframe.rename(columns={'v_wind_h': 'v_z'})
         cdf2Dataframe['date'] = 'Nan'
         for l in range(len(cdf2Dataframe)):
             cdf2Dataframe['date'].iloc[l] = time.strftime('%m/%d/' + str(h) + ' %H:%M:%S',time.gmtime(cdf2Dataframe['time_seconds'].iloc[l]))
         cdf2Dataframe = cdf2Dataframe.set_index('date')
         del cdf2Dataframe['time_seconds']
         empty_df = pd.concat([empty_df, cdf2Dataframe])
         print(i, h)

resultdf=pd.merge(resultdf,empty_df,left_index=True, right_index=True, how= 'outer')
resultdf.index = pd.to_datetime(resultdf.index)
resultdf = resultdf.sort_index()
resultdf= resultdf.resample('15T').mean().ffill()
resultdf=resultdf.reset_index([0])
# resultdf['index']=resultdf['index'].astype(str)
# resultdf4['date'] = 'Nan'
# resultdf4['date']= resultdf4['index'].str[5:19]
# resultdf = resultdf[['date','v_z_y']]
# resultdf = resultdf.set_index('date')
# resultdf.to_excel('wind_m_s.xlsx')
#
# #####negative wind speed to positive wind speed#########
# for i in range(len(resultdf4)):
#     c=resultdf4['v_z_y'][i]
#     if c<0:
#         resultdf4['v_z_y'][i]=resultdf4['v_z_y'][i]*-1
#     else:
#         print('no')