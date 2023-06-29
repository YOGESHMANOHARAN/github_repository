import glob
import pandas as pd
import numpy as np
from netCDF4 import Dataset
import xarray as xr
import datetime
import time
file_list=glob.glob(r"C:\Users\ymnharan\Documents\GitHub\github_repository\STOCHASTIC DATA\solar data\**",recursive=True)
ran = range(1,len(file_list))
date = pd.date_range('2005-01-01 00:00:00','2020-12-31 23:59:00', freq="1T")
resultdf=pd.DataFrame(index=date)
resultdf['down_short_diffuse_hemisp']=0.000
empty_df= pd.DataFrame()
for i in ran:
    try:
        file = xr.open_dataset(file_list[i], decode_times=False)
        numpy_data = file.as_numpy()
        date_str = file_list[i][-19:-15] + '/' + file_list[i][-15:-13] + '/' + file_list[i][-13:-11] + ' ' + file_list[i][-10:-8] + ':' + file_list[i][-9:-7] + ':' + file_list[i][-7:-5]
        cdf2Dataframe =numpy_data['down_short_diffuse_hemisp'].to_dataframe()
        df_date = pd.date_range(date_str, periods=1440, freq="1T")
        cdf2Dataframe['df_date'] = df_date
        cdf2Dataframe = cdf2Dataframe.set_index('df_date')
        empty_df = pd.concat([empty_df, cdf2Dataframe])
        print(i)
    except:
        if 2>>0:
            print('this file'+file_list[i])
            continue


resultdf=pd.merge(resultdf,empty_df,left_index=True, right_index=True, how= 'outer')
resultdf=resultdf[['down_short_diffuse_hemisp_y']]
resultdf= resultdf.resample('15T').mean().ffill()
# resultdf.index = pd.to_datetime(resultdf.index)
# resultdf = resultdf.sort_index()
# resultdf= resultdf.resample('15T').mean().ffill()
resultdf=resultdf.reset_index([0])
# resultdf['index']=resultdf['index'].astype(str)
# resultdf['date'] = 'Nan'
# resultdf['date']= resultdf4['index'].str[5:19]
resultdf = resultdf[['date','down_short_diffuse_hemisp_y']]
resultdf = resultdf.set_index('date')
resultdf.to_excel('solar_irradiation_w_m2.xlsx')