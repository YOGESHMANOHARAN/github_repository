from two_zone_main import *
import pandas as pd
import numpy as np

def summarize_data(instance, data):
    summary = {}
    for zone in range(0, 2):
        summary[zone] = pd.DataFrame()
        summary[zone]['time'] = data.index
        summary[zone]['Base Demand (kW)'] = [instance.base_electrical[zone, t] for t in range(0, len(data-1))]
        summary[zone]['SSW Demand (gpm)'] = [instance.SSW_demand[zone, t] for t in range(0, len(data-1))]
        summary[zone]['DSW Demand (gpm)'] = [instance.DSW_demand[zone, t] for t in range(0, len(data-1))]
        summary[zone]['Solar (kW)'] = [instance.solar[zone, t] for t in range(0, len(data-1))]
        summary[zone]['Curtailed Power (kW)'] = [instance.curtailedPower[zone, t].value for t in range(0, len(data-1))]
        summary[zone]['SSW Power (kW)'] = [instance.SSW_power[zone, t].value for t in range(0, len(data-1))]
        summary[zone]['DSW Power (kW)'] = [instance.DSW_power[zone, t].value for t in range(0, len(data-1))]
        summary[zone]['Charge (kW)'] = [instance.chargePower[zone, t].value for t in range(0, len(data-1))]
        summary[zone]['Discharge (kW)'] = [instance.dischargePower[zone, t].value for t in range(0, len(data-1))]
        summary[zone]['Purchased (kW)'] = [instance.purchasedPower[zone, t].value for t in range(0, len(data-1))]
        summary[zone]['State of Charge (kWh)'] = [instance.stateOfCharge[zone, t].value for t in range(0, len(data-1))]
        summary[zone]['Price ($/kWh)'] = data.price.values

    return summary


# Read the relevant data
data_RC = pd.read_excel('RC_data.xlsx')
data_RC['kW'] = 165
data_RC['price'] = 0.2979

data_FF = data_RC.copy()
data_FF['kW'] = 0
data_FF['price'] = 0.271
# Run code
end = 120
instance, results = run_main(data_RC[0:end], data_FF[0:end], 100, 100)

# Make summary[zone] of data
summary = summarize_data(instance, data_RC)

# Save summary[zone] of data to some filename
