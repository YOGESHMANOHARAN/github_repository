import pandas as pd
import numpy as np
import glob
import os
contents= np.random.randn(70,2)
index1 = pd.MultiIndex.from_product([[0.74,0.76,0.78,0.80,0.82,0.847,0.86],[1,2,3,4,5,6,7,8,9,10]])
# column_solar= pd.MultiIndex.from_product([['solar'],['RC Bat kw','55" Bat kW','RC Bat kwh','55" Bat kWh','overall 10 yr cost','RC_Maxpeakpower','ff_Maxpeakpower','RC_curtailed_power','ff_curtailed_power','RC_purchased_power','ff_purchased_power','RC_Entire_demand','RC_solar','RC_Wind','RC_renewable_generation']])
# column_solar= pd.MultiIndex.from_product([['solar'],['RC_charge','RC_discharge','ff_charge','ff_discharge']])
column_solar= pd.MultiIndex.from_product([['solar'],['RC_Entire_demand', 'ff_Entire_demand']])
k=0
# ####### ESS_SOLAR_####
# ESS_SOLAR_E2020B2020 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_Sensitivity_study_only_ESS_solar\E2020_eff\_$156_kW_$408_kWh\**\*.xlsx', recursive=True)
# ESS_SOLAR_E2020B2030 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_Sensitivity_study_only_ESS_solar\E2020_eff\_$126_kW_$285_kWh\**\*.xlsx', recursive=True)
# ESS_SOLAR_E2030B2020 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_Sensitivity_study_only_ESS_solar\ELECTRICITY_2030.394]_eff\ $156_kW_$408_kWh\**\*.xlsx', recursive=True)
# ESS_SOLAR_E2030B2030 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_Sensitivity_study_only_ESS_solar\ELECTRICITY_2030.394]_eff\ $126_kW_$285_kWh\**\*.xlsx', recursive=True)
# ##############
#
# #######ESS_WIND_###
# ESS_WIND_E2020B2020 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_sensitivity_study_only_ESS_WIND\ELECTRICITY_2020.27]_eff\ $156_kW_$408_kWh\**\*.xlsx', recursive=True)
# ESS_WIND_E2020B2030 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_sensitivity_study_only_ESS_WIND\ELECTRICITY_2020.27]_eff\ $126_kW_$285_kWh\**\*.xlsx', recursive=True)
# ESS_WIND_E2030B2020 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_sensitivity_study_only_ESS_WIND\ELECTRICITY_2030.394]_eff\ $156_kW_$408_kWh\**\*.xlsx', recursive=True)
# ESS_WIND_E2030B2030 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_sensitivity_study_only_ESS_WIND\ELECTRICITY_2030.394]_eff\ $126_kW_$285_kWh\**\*.xlsx', recursive=True)
#
# ##########DSM_SOLAR_###################
# DSM_SOLAR_E2020B2020 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_Sensitivity_study_ly_DSM_solar\ELECTRICITY_2020.27]_eff\ $156_kW_$408_kWh\**\*.xlsx', recursive=True)
# # DSM_SOLAR_E2020B2030 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_Sensitivity_study_ly_DSM_solar\ELECTRICITY_2020.27]_eff\ $126_kW_$285_kWh\**\*.xlsx', recursive=True)
# DSM_SOLAR_E2030B2020 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_Sensitivity_study_ly_DSM_solar\ELECTRICITY_2030.394]_eff\ $156_kW_$408_kWh\**\*.xlsx', recursive=True)
# # DSM_SOLAR_E2030B2030 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_Sensitivity_study_ly_DSM_solar\ELECTRICITY_2030.394]_eff\ $126_kW_$285_kWh\**\*.xlsx', recursive=True)
# ##############
#
# ####### DSM_WIND_   #######
# DSM_WIND_E2020B2020 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_Sensitivity_study_ly_DSM_wind_\ELECTRICITY_2020.27]_eff\ $156_kW_$408_kWh\**\*.xlsx', recursive=True)
# # DSM_WIND_E2020B2030 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_Sensitivity_study_ly_DSM_wind_\ELECTRICITY_2020.27]_eff\ $126_kW_$285_kWh\**\*.xlsx', recursive=True)
# DSM_WIND_E2030B2020 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_Sensitivity_study_ly_DSM_wind_\ELECTRICITY_2030.394]_eff\ $156_kW_$408_kWh\**\*.xlsx', recursive=True)
# # DSM_WIND_E2030B2030 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\New_Sensitivity_study_ly_DSM_wind_\ELECTRICITY_2030.394]_eff\ $126_kW_$285_kWh\**\*.xlsx', recursive=True)

####### ESS_DSM_SOLAR_ #######
ESS_DSM_SOLAR_E2020B2020 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\Sensitivity_study_for_ESS_DSM_SOLAR\ELECTRICITY_2020.27]_eff\ $156_kW_$408_kWh\**\*.xlsx', recursive=True)
ESS_DSM_SOLAR_E2020B2030 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\Sensitivity_study_for_ESS_DSM_SOLAR\ELECTRICITY_2020.27]_eff\ $126_kW_$285_kWh\**\*.xlsx', recursive=True)
ESS_DSM_SOLAR_E2030B2020 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\Sensitivity_study_for_ESS_DSM_SOLAR\ELECTRICITY_2030.394]_eff\ $156_kW_$408_kWh\**\*.xlsx', recursive=True)
ESS_DSM_SOLAR_E2030B2030 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\Sensitivity_study_for_ESS_DSM_SOLAR\ELECTRICITY_2030.394]_eff\ $126_kW_$285_kWh\**\*.xlsx', recursive=True)

######ESS_DSM_WIND_##########
ESS_DSM_WIND_E2020B2020 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\Sensitivity_study_for_ESS_DSM_WIND\0.29, 0.27_eff\ $156_kW_$408_kWh\**\*.xlsx', recursive=True)
ESS_DSM_WIND_E2020B2030 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\Sensitivity_study_for_ESS_DSM_WIND\0.29, 0.27_eff\ $126_kW_$285_kWh\**\*.xlsx', recursive=True)
ESS_DSM_WIND_E2030B2020 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\Sensitivity_study_for_ESS_DSM_WIND\0.424, 0.394_eff\ $156_kW_$408_kWh\**\*.xlsx', recursive=True)
ESS_DSM_WIND_E2030B2030 = glob.glob(r'C:\Users\ymnharan\Documents\GitHub\github_repository\second_try_for_journal_paper\Sensitivity_study_for_ESS_DSM_WIND\0.424, 0.394_eff\ $126_kW_$285_kWh\**\*.xlsx', recursive=True)

# # list_files = [ESS_SOLAR_E2020B2020,ESS_SOLAR_E2020B2030,ESS_SOLAR_E2030B2020,ESS_SOLAR_E2030B2030,ESS_WIND_E2020B2020,ESS_WIND_E2020B2030,ESS_WIND_E2030B2020,\
# ESS_WIND_E2030B2030,DSM_SOLAR_E2020B2020,DSM_SOLAR_E2030B2020,DSM_WIND_E2020B2020,DSM_WIND_E2030B2020\
# ,ESS_DSM_SOLAR_E2020B2020,ESS_DSM_SOLAR_E2020B2030,ESS_DSM_SOLAR_E2030B2020,ESS_DSM_SOLAR_E2030B2030,\
# ESS_DSM_WIND_E2020B2020,ESS_DSM_WIND_E2020B2030,ESS_DSM_WIND_E2030B2020,ESS_DSM_WIND_E2030B2030]
list_files = [ESS_DSM_SOLAR_E2020B2020,ESS_DSM_SOLAR_E2020B2030,ESS_DSM_SOLAR_E2030B2020,ESS_DSM_SOLAR_E2030B2030,\
ESS_DSM_WIND_E2020B2020,ESS_DSM_WIND_E2020B2030,ESS_DSM_WIND_E2030B2020,ESS_DSM_WIND_E2030B2030]

# list_files_names=['ESS_SOLAR_E2020B2020','ESS_SOLAR_E2020B2030','ESS_SOLAR_E2030B2020','ESS_SOLAR_E2030B2030','ESS_WIND_E2020B2020','ESS_WIND_E2020B2030','ESS_WIND_E2030B2020',\
# 'ESS_WIND_E2030B2030','DSM_SOLAR_E2020B2020','DSM_SOLAR_E2030B2020','DSM_WIND_E2020B2020','DSM_WIND_E2030B2020'\
# ,'ESS_DSM_SOLAR_E2020B2020','ESS_DSM_SOLAR_E2020B2030','ESS_DSM_SOLAR_E2030B2020','ESS_DSM_SOLAR_E2030B2030',\
# 'ESS_DSM_WIND_E2020B2020','ESS_DSM_WIND_E2020B2030','ESS_DSM_WIND_E2030B2020','ESS_DSM_WIND_E2030B2030']
list_files_names=[ 'ESS_DSM_SOLAR_E2020B2020','ESS_DSM_SOLAR_E2020B2030','ESS_DSM_SOLAR_E2030B2020','ESS_DSM_SOLAR_E2030B2030',\
'ESS_DSM_WIND_E2020B2020','ESS_DSM_WIND_E2020B2030','ESS_DSM_WIND_E2030B2020','ESS_DSM_WIND_E2030B2030']
table = pd.DataFrame(contents, index=index1, columns=column_solar)

for (j,table_name) in zip(list_files, list_files_names):
    name = table_name
    xl_name = table_name
    for i in j:
        print(i)
        excel_file = pd.read_excel(i, sheet_name=[0,1,2], index_col=0)
        excel_file[0] = excel_file[0].iloc[0:35712]
        excel_file[1] = excel_file[1].iloc[0:35712]
        # RC_Maxpeakpower = excel_file[0]['RC peak power'].max()
        # ff_Maxpeakpower = excel_file[1]['FF peak power'].max()
        # RC_curtailed_power = sum(excel_file[0]['power_curatiled'])
        # ff_curtailed_power = sum(excel_file[1]['power_curatiled'])
        # RC_purchased_power = sum(excel_file[0]['RC Purchased'])
        # ff_purchased_power = sum(excel_file[1]['FF Purchased'])
        RC_Entire_demand = sum(excel_file[0]['RC Demand'])+sum(excel_file[0]['RC SSW pumpPower'])+\
                                                   sum(excel_file[0]['RC DSW pumpPower'])
        ff_Entire_demand = sum(excel_file[1]['FF Demand']) + sum(excel_file[1]['FF SSW pumpPower']) + \
                           sum(excel_file[1]['FF DSW pumpPower'])
        # RC_solar=sum(excel_file[0]['RC Solar'])
        # RC_Wind=sum(excel_file[0]['RC wind'])
        # RC_renewable_generation =RC_solar-RC_Wind
        # RC_charge = sum(excel_file[0]['RC Charge'])
        # ff_charge = sum(excel_file[1]['FF Charge'])
        # RC_discharge= sum(excel_file[0]['RC Discharge'])
        # ff_discharge = sum(excel_file[1]['FF Discharge'])
        # list = [RC_Maxpeakpower,ff_Maxpeakpower,RC_curtailed_power,ff_curtailed_power,RC_purchased_power,ff_purchased_power,RC_Entire_demand,RC_solar,RC_Wind,RC_renewable_generation]
        list =[RC_Entire_demand, ff_Entire_demand]
        # bat_size_cost=excel_file[2].iloc[0]
        df = pd.Series(list)
        # appendingrow = bat_size_cost.append(df)
        table.iloc[k] = df
        k += 1
        print(k)


    def generate_write_folder(folder,variable_eff_folder):
        write_folder = os.getcwd() + variable_eff_folder + folder
        return write_folder


    folder = '/ ${}_'.format(xl_name)
    variable_eff_folder = '/results_excel_folder_DEMAND'
    write_folder = generate_write_folder(folder,variable_eff_folder)

    if not os.path.exists(write_folder):
        os.makedirs(write_folder)
    excel_filename = variable_eff_folder + '_' + 's_' + xl_name
    filename = '{}.xlsx'.format(excel_filename)
    writer = pd.ExcelWriter(write_folder + filename)
    table.to_excel(writer)
    writer.save()
    k=0


# 'C:\\Users\\ymnharan\\Documents\\GitHub\\github_repository\\second try for journal paper\\New_Sensitivity_study_only_ESS_solar\\[0.29, 0.27]_eff\\$156_kW_$408_kWh\\**\\*.xlsx'
# print(E2020B2020)
# print(name)

