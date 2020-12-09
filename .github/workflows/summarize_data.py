from two_zone_fixed_eff_main import *
import pandas as pd
import os
import calendar
import numpy as np


def summarize_data(instance, data):
    demand_charge = [13, 25]
    summary = {}
    for zone in range(0, 2):
        summary[zone] = pd.DataFrame()
        summary[zone]['time'] = data.index
        points_per_hour = pd.to_timedelta('1h') / (data.index[1] - data.index[0])
        summary[zone]['Base Demand (kW)'] = [instance.base_electrical[zone, t] for t in range(0, len(data))]
        summary[zone]['SSW Demand (gpm)'] = [instance.SSW_demand[zone, t] for t in range(0, len(data))]
        summary[zone]['DSW Demand (gpm)'] = [instance.DSW_demand[zone, t] for t in range(0, len(data))]
        summary[zone]['Solar (kW)'] = [instance.solar[zone, t] for t in range(0, len(data))]
        summary[zone]['Curtailed Power (kW)'] = [instance.curtailedPower[zone, t].value for t in range(0, len(data))]
        summary[zone]['SSW Pumped (gpm)'] = [instance.SSW_pumped[zone, t].value for t in range(0, len(data))]
        summary[zone]['DSW Pumped (gpm)'] = [instance.DSW_pumped[zone, t].value for t in range(0, len(data))]
        summary[zone]['SSW Power (kW)'] = [instance.SSW_power[zone, t].value for t in range(0, len(data))]
        summary[zone]['DSW Power (kW)'] = [instance.DSW_power[zone, t].value for t in range(0, len(data))]
        summary[zone]['SSW Transfer Out (gpm)'] = [instance.transferSSW[zone, t].value for t in range(0, len(data))]
        summary[zone]['DSW Transfer Out (gpm)'] = [instance.transferDSW[zone, t].value for t in range(0, len(data))]
        summary[zone]['Charge (kW)'] = [instance.chargePower[zone, t].value for t in range(0, len(data))]
        summary[zone]['Discharge (kW)'] = [instance.dischargePower[zone, t].value for t in range(0, len(data))]
        summary[zone]['Purchased (kW)'] = [instance.purchasedPower[zone, t].value for t in range(0, len(data))]
        summary[zone]['State of Charge (kWh)'] = [instance.stateOfCharge[zone, t].value for t in range(0, len(data))]
        summary[zone]['Price (cents/kWh)'] = data.price.values
        summary[zone]['Purchased Energy Cost ($)'] = summary[zone]['Purchased (kW)'] \
                                                     * summary[zone]['Price (cents/kWh)'] \
                                                     / points_per_hour / 100
        summary[zone]['Peak Power(kW)'] = np.nan
        summary[zone].loc[summary[zone].index[0], 'Peak Power(kW)'] = value(instance.peak_power[zone])
        summary[zone]['Demand Charge ($)'] = summary[zone]['Peak Power(kW)'] * demand_charge[zone]


    return summary


# Read the relevant data
end = 2000
data_RC = pd.read_excel('research_campus_alt.xlsx',
                        index_col='Time/Date',
                        parse_dates=True)

data_FF = pd.read_excel('55inch_alt.xlsx',
                        index_col='Time/Date',
                        parse_dates=True)



def generate_folder_by_battery_size(kW_ES, kWh_ES):
    directory = os.getcwd() + '/{}kW - {}kWh/'.format(kW_ES, kWh_ES)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


# Run code

# months = list(set(data_RC.index.month))
months = [3]
for month in months:
    timeframe = '2019-{}'.format(month)
    all_data = [data_RC[timeframe], data_FF[timeframe]]
    kW_ES = 0
    kWh_ES = 0
    # Save summary[zone] of data to some filename
    try:
        instance, results = run_main(all_data[0], all_data[1], kWh_ES, kW_ES)
        folder = generate_folder_by_battery_size(kW_ES, kWh_ES)
        filename = '{} Summary.xlsx'.format(calendar.month_abbr[month])
        writer = pd.ExcelWriter(folder + filename)
        for zone in range(0, 2):
            zone_names = ['RC', '55in']
            summary = summarize_data(instance, all_data[zone])
            summary[zone].to_excel(writer,
                                   sheet_name=zone_names[zone],
                                   index=False)
        writer.save()
    except:
        print('passed')
        pass
