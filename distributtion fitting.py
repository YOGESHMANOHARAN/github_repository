import pandas as pd
import numpy as np
import seaborn as sns
from fitter import Fitter, get_common_distributions,get_distributions

data = pd.read_excel(r"C:\Users\ymnharan\Documents\GitHub\github_repository\wind_m_s.xlsx",index_col= 'index')
distr_output = pd.DataFrame(columns=['date','fitting_distr'])
date_list=[]
dist_list=[]
hours = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
minutes= [0,15,30,45]
month=[1,2,3,4,5,6,7,8,9,10,11,12]
day=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
for i in range(0, 12):
    for j in range(0, 31):
        for k in range(0, 24):
            for l in range(0,4):
                try:
                    hour = f'{hours[k]:02d}'
                    minute = f'{minutes[l]:02d}'
                    time = hour+":"+minute
                    print(i,j,time)
                    step_1 = data.at_time(time)
                    step_2= step_1[step_1.index.month==month[i]]
                    step_3= step_2[step_2.index.day==day[j]]
                    solar_irrad = step_3
                    solar_irrad = step_3['v_z_y'].fillna(0).values
                    solar_dist = Fitter(solar_irrad,distributions=['gamma','lognorm','beta','burr','norm'])
                    solar_dist.fit()
                    solar_dist.summary()
                    solar_dist.get_best(method='sumsquare_error')
                    date_list.append(str(month[i]) + '/' + str(day[j]) + ' ' + time)
                    dist_list.append(solar_dist.get_best(method='sumsquare_error'))
                except:
                    if 2>>0:
                        print(day[j],month[i])
                        continue