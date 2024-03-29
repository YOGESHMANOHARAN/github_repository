from pyomo.environ import *
from pyomo.opt import SolverFactory
import pandas as pd
import numpy as np
from gurobipy import *
import os
import shutil
from pyomo.core import Constraint, Var, value
from pyomo.util.infeasible import log_infeasible_constraints
from math import fabs
import logging
from file_generating_code import *

logger = logging.getLogger('pyomo.solver')

ESmin = 1000
ESmax = 10000
SOCmax = 70000
transferMax = 0
model = AbstractModel()
model.zone = RangeSet(0, 1)
kWh_price = [0.31, 0.29]
kW_price = [13, 25]
#pump_Mainten = {0: 104577, 1: 56000}
solar_increment = 1
air_density = 1.2  # kg/m**3
blade_length = 17.06  # m
wind_tur_eff = 0.42
wind_increment = 0

# SSW_pump_max_gpm = 13800
# DSW_pump_max_gpm = 19500

####   numpy files for the solar and other demands and other information #####

solar_rad = [np.load('SOLAR_RADIATION.npy'), np.load('SOLAR_RADIATION.npy')]
base_demand = [np.load('Building_demand_RC.npy'), np.load('Building_demand_FF.npy')]
SSW_demand = [np.load('SSW_demand_RC.npy'), np.load('SSW_demand_FF.npy')]
DSW_demand = [np.load('DSW_demand_RC.npy'), np.load('DSW_demand_FF.npy')]
wind_speed_data = [np.load('WIND_SPEED.npy'), np.load('WIND_SPEED.npy')]
wind_del = [np.load('wind_del.npy'), np.load('wind_del.npy')]
wind_beta = [np.load('wind_beta.npy'), np.load('wind_beta.npy')]
solar_std = [np.load('solar_radia_stnd.npy'), np.load('solar_radia_stnd.npy')]
solar_mean= [np.load('solar_radia_mn.npy'), np.load('solar_radia_mn.npy')]
envtemp = [np.load('envTemp1.npy'), np.load('envTemp1.npy')]

# SSW_points = [pd.read_excel('linear_eff_RC.xlsx',sheet_name='SSW'),pd.read_excel('linear_eff_55.xlsx',sheet_name='SSW')]
# DSW_points = [pd.read_excel('linear_eff_RC.xlsx',sheet_name='DSW'),pd.read_excel('linear_eff_55.xlsx',sheet_name='DSW')]

# end_time = len(solar[0][0]) - 1
end_time=23
model.time = RangeSet(0, 23)
Battery_cost_kw = 126
Battery_cost_kwh = 285
final_month =3
initial_month = 0
model.month = RangeSet(initial_month, final_month)
# model.month= 0

# region Define max power and flow from each section

# PmaxSSW = 100
Pmaxff = 50000
# PmaxDSW = 200
# maxFlowSSW = 100000
# maxFlowDSW = 100000
maxFlowff = 100000
solarMax = solar_rad[0].max()
# print(solarMax)

# SOCmax = 1000  # Maximum state-of-charge in kWh
charge_eff = 0.84
discharge_eff = 0.84
Pmax = 100
dt = 15 / 60  #### Need to calculate this for different time steps
convec_coeff = 10  #### convective heat transfer coefficient ( w/m^2 k)

bat_area = 1.38  ## meter^2
battery_mass = 210000  ## grams
specific_heat_cap = 1  ### j/g.K
emissivity = 0.84
sigma = 5.67 * 10 ** -8
Pmax = 100
dt = 15 / 60  # Need to calculate this for different time steps
solar_eff = 0.65
Solarpanel_area = 1.95
# endregion

########## coefficients of pump efficiency equation #######

A2_SSW = {0: -0.0000001, 1: -0.0000000939}

A1_SSW = {0: 0.0149, 1: 0.0205}

A0_SSW = {0: 10.5, 1: 1.3521}

A2_DSW = {0: -0.0000001, 1: 0.00000001}

A1_DSW = {0: 0.0162, 1: 0.0185}

A0_DSW = {0: 11.202, 1: 11.952}

###### maximum capacity of each pump #####

SSW_pump_max_gpm = {0: 8900, 1: 17100}
DSW_pump_max_gpm = {0: 14000, 1: 20400}

###### Example of how to manage multiple pumps per pump station #####

# max_num_pumps = 5
# model.pump = RangeSet(1, max_num_pumps)
model.SSW_pumpOn = Var(model.zone, model.month, model.time, domain=Binary)
model.DSW_pumpOn = Var(model.zone, model.month, model.time, domain=Binary)


# region Initialize input data
# def Solar(model, zone, month, time):
#     # print(zone, month, time)
#     return solar[zone][month - 1, time]
# model.solar = Param(model.zone, model.month, model.time, initialize=Solar)


def Base_demand(model, zone, month, time):
    return base_demand[zone][month , time]
model.base_electrical = Param(model.zone, model.month, model.time, initialize=Base_demand)


def SSW1_demand(model, zone, month, time):
    return SSW_demand[zone][month, time]
model.SSW_demand = Param(model.zone, model.month, model.time, initialize=SSW1_demand)

def DSW1_demand(model, zone, month, time):
    return DSW_demand[zone][month, time]
model.DSW_demand = Param(model.zone, model.month, model.time, initialize=DSW1_demand)

def EnvTemp(model, zone, month, time):
    return (envtemp[zone][month, time] - 32) * (5 / 9) + 273.15
model.envTemp = Param(model.zone, model.month, model.time, initialize=EnvTemp)

def solar_radiation(model,zone,month,time):
    return (solar_rad[zone][month, time])
model.solar_rad = Param(model.zone, model.month, model.time, initialize=solar_radiation)

def solar_radiation_mean(model,zone,month,time):
    return (solar_mean[zone][month, time])
model.solar_mean = Param(model.zone, model.month, model.time, initialize=solar_radiation_mean)
    
def solar_radiation_std(model,zone,month,time):
    return (solar_std[zone][month, time])
model.solar_std = Param(model.zone, model.month, model.time, initialize=solar_radiation_std)

def wind_speed(model,zone,month,time):
    return (wind_speed_data[zone][month, time])
model.wind_speed = Param(model.zone, model.month, model.time, initialize=wind_speed)

def wind_speed_del(model,zone,month,time):
    return (wind_del[zone][month, time])
model.wind_del = Param(model.zone, model.month, model.time, initialize=wind_speed_del)

def wind_speed_beta(model,zone,month,time):
    return (wind_beta[zone][month, time])
model.wind_beta = Param(model.zone, model.month, model.time, initialize=wind_speed_beta)

# region Declare Variable
model.SSW_pumpPower = Var(model.zone, model.month, model.time, domain=NonNegativeReals,bounds=(0, Pmaxff))
model.DSW_pumpPower = Var(model.zone, model.month, model.time, domain=NonNegativeReals,bounds=(0, Pmaxff))
model.peak_power = Var(model.zone, model.month, domain=NonNegativeReals, bounds=(0, Pmaxff))
model.wind_pow = Var(model.zone,model.month,model.time,domain=NonNegativeReals)
model.uncertainity_windSpeed = Var(model.zone,model.month,model.time,domain=NonNegativeReals)
model.solar = Var(model.zone,model.month,model.time,domain=NonNegativeReals)
model.uncertainity_solar_gen = Var(model.zone,model.month,model.time,domain=NonNegativeReals)
model.SSW_pumped = Var(model.zone, model.month, model.time, domain=NonNegativeReals,bounds=(0, maxFlowff))
model.DSW_pumped = Var(model.zone, model.month, model.time, domain=NonNegativeReals,bounds=(0, maxFlowff))
model.transferSSW = Var(model.zone, model.month, model.time, domain=Reals,bounds=(-transferMax, transferMax))
model.transferDSW = Var(model.zone, model.month, model.time, domain=Reals,bounds=(-transferMax, transferMax))
model.chargePower = Var(model.zone, model.month, model.time, domain=NonNegativeReals,bounds=(0, ESmax))
model.dischargePower = Var(model.zone, model.month, model.time, domain=NonNegativeReals,bounds=(0, ESmax))
model.purchasedPower = Var(model.zone, model.month, model.time, domain=NonNegativeReals,bounds=(0, Pmaxff))
model.stateOfCharge = Var(model.zone, model.month, model.time, domain=NonNegativeReals,bounds=(0, SOCmax))
model.curtailedPower = Var(model.zone, model.month, model.time, domain=NonNegativeReals,bounds=(0, 100000))
model.installed_capacity_kw = Var(model.zone, domain=NonNegativeReals, bounds=(ESmin, ESmax))
model.installed_capacity_kwh = Var(model.zone, domain=NonNegativeReals,bounds=(ESmin, ESmax * 6))
model.bat_temp = Var(model.zone, model.month, model.time, domain=NonNegativeReals)
model.bat_temp_conve = Var(model.zone, model.month, model.time, domain=NonNegativeReals)
model.bat_temp_gen = Var(model.zone, model.month, model.time, domain=NonNegativeReals)
model.battery_temperature = Var(model.zone, model.month, model.time, domain=NonNegativeReals)
model.gamma = Var(model.zone, model.month, model.time, domain=Binary)


# 1 model.on_off = Var(model.zone, model.month, model.time, domain=Binary)

def SSW_gpm_to_pump_power(model, zone, month, time):
    return model.SSW_pumpPower[zone, month, time] == A2_SSW[zone] * model.SSW_pumped[zone, month, time] * \
           model.SSW_pumped[zone, month, time] \
           + A1_SSW[zone] * model.SSW_pumped[zone, month, time] + \
           A0_SSW[zone] * model.SSW_pumpOn[zone, month, time]


def DSW_gpm_to_pump_power(model, zone, month, time):
    return model.DSW_pumpPower[zone, month, time] == A2_DSW[zone] * model.DSW_pumped[zone, month, time] * \
           model.DSW_pumped[zone, month, time] \
           + A1_DSW[zone] * model.DSW_pumped[zone, month, time] + \
           A0_DSW[zone] * model.DSW_pumpOn[zone, month, time]

####uncertainity for wind####
def uncertainity_windSpeed(model, zone,month,time):
    return model.uncertainity_windSpeed[zone,month,time]== 1-math.exp(-(model.wind_speed[zone,month,time]/model.wind_del[zone,month,time])**model.wind_beta[zone,month,time])

######wind_energy_generation######3
def winddata(model, zone, month, time):
    return model.wind_pow[zone,month,time]== (((((model.wind_speed[zone,month, time]+ model.uncertainity_windSpeed[zone,month,time]) / 2.23693629) ** 3) * 0.5 * 3.14 * blade_length * blade_length * air_density * wind_tur_eff) / 1000)  * wind_increment

####uncertainity for solar####
def uncertainity_solargen(model, zone,month,time):
    return model.uncertainity_solar_gen[zone,month,time]== 1/2*(1+math.erf((model.solar_rad[zone,month,time]-model.solar_mean[zone,month,time])/(model.solar_std[zone,month,time]*sqrt(2))))

####solar radiation to solar energy
def solar_energy(model,zone,month,time):
    return model.solar[zone,month,time] == (solar_eff * (model.solar_rad[zone, month, time]+ model.unceratinity_solar_gen[zone,month,time]) * Solarpanel_area)


def power_balance(model, zone, month, time):
    return model.purchasedPower[zone, month, time] == model.base_electrical[zone, month, time] \
           + (solar_increment * model.solar[zone, month, time]) \
           + sum([model.SSW_pumpPower[zone, month, time]]) \
           + sum([model.DSW_pumpPower[zone, month, time]]) \
           + model.curtailedPower[zone, month, time] \
           - model.dischargePower[zone, month, time] \
           + model.chargePower[zone, month, time] \
           - model.wind_pow[zone, month, time]


def peak_power(model, zone, month, time):
    return model.peak_power[zone, month] >= model.purchasedPower[zone, month, time]


def limiting_power_curtail(model, zone, month, time):
    return model.curtailedPower[zone, month, time] <= solar_increment * -1 * model.solar[
        zone, month, time] + \
           model.wind_pow[zone, month, time]


def maximum_cap_of_a_SSWpump(model, zone, month, time):
    return model.SSW_pumped[zone, month, time] <= SSW_pump_max_gpm[zone]


def maximum_cap_of_a_DSWpump(model, zone, month, time):
    return model.DSW_pumped[zone, month, time] <= DSW_pump_max_gpm[zone]


def SSW_balance(model, zone, month, time):
    return sum([model.SSW_pumped[zone, month, time]]) == model.SSW_demand[zone, month, time] \
           + model.transferSSW[zone, month, time]


def DSW_balance(model, zone, month, time):
    return sum([model.DSW_pumped[zone, month, time]]) == model.DSW_demand[zone, month, time] \
           + model.transferDSW[zone, month, time]


def transfer_SSWdirection(model, month, time):
    return model.transferSSW[0, month, time] == -model.transferSSW[1, month, time]


def transfer_SSWoneWay(model, month, time):
    return model.transferSSW[0, month, time] <= 0


def transfer_DSWdirection(model, month, time):
    return model.transferDSW[0, month, time] == -model.transferDSW[1, month, time]


def transfer_DSWoneWay(model, month, time):
    return model.transferDSW[0, month, time] <= 0  # endregion


def stateOfCharge(model, zone, month, time):
    if month == initial_month:
        if time == 0:
            SOCpre = 0.5 * model.installed_capacity_kwh[zone]
        else:
            SOCpre = model.stateOfCharge[zone, month, time - 1]
    else:
        if time == 0:
            SOCpre = model.stateOfCharge[zone, month - 1, end_time]
        else:
            SOCpre = model.stateOfCharge[zone, month, time - 1]
    return model.stateOfCharge[zone, month, time] == SOCpre + (
                charge_eff * model.chargePower[zone, month, time]
                - model.dischargePower[
                    zone, month, time] / discharge_eff)


def final_stateOfCharge(model, zone):
    return model.stateOfCharge[zone, final_month, end_time] == 0.5 * \
           model.installed_capacity_kwh[zone]


def limits_stateOfCharge(model, zone, month, time):
    return model.stateOfCharge[zone, month, time] <= model.installed_capacity_kwh[zone]


def stateOfCharge_and_discharge(model, zone, month, time):
    return model.chargePower[zone, month, time] + model.dischargePower[zone, month, time] <= \
           model.installed_capacity_kw[zone]


def controlling_chargepower_shortmonthend(model, zone, month, time):
    if model.SSW_demand[zone, month, time] == 0:
        return model.chargePower[zone, month, time] == 0
    else:
        return model.chargePower[zone, month, time] <= ESmax


def controlling_dischargepower_shortmonthend(model, zone, month, time):
    if model.SSW_demand[zone, month, time] == 0:
        return model.dischargePower[zone, month, time] == 0
    else:
        return model.dischargePower[zone, month, time] <= ESmax


def control_charge_power(model, zone, month, time):
    return model.chargePower[zone, month, time] <= model.gamma[zone, month, time] * ESmax


def control_discharge_power(model, zone, month, time):
    return model.dischargePower[zone, month, time] <= (1 - model.gamma[zone, month, time]) * ESmax


#
##### BATTERY TEMPERATURE ####

def batterytemperature_gen(model, zone, month, time):
    return model.bat_temp_gen[zone, month, time] == (1 - charge_eff) * model.chargePower[zone, month, time] \
           + ((1 - discharge_eff) * model.dischargePower[zone, month, time])


def batterytemperature(model, zone, month, time):
    if time == 0:
        return model.battery_temperature[zone, month, time] == 299.15
    else:
        return model.battery_temperature[zone, month, time] == model.battery_temperature[zone, month, time - 1] + \
               (model.bat_temp_gen[zone, month, time] - ((convec_coeff * bat_area * (model.battery_temperature[zone, month, time - 1] - model.envTemp[zone, month, time])))) \
               * (900 / (battery_mass * specific_heat_cap))


def to_turn_on_SSW_pump(model, zone, month, time):
    return model.SSW_pumpOn[zone, month, time] >= model.SSW_pumped[zone, month, time] / \
           SSW_pump_max_gpm[zone]


def to_turn_on_DSW_pump(model, zone, month, time):
    return model.DSW_pumpOn[zone, month, time] >= model.DSW_pumped[zone, month, time] / \
           DSW_pump_max_gpm[zone]


def SSWpump_to_draw_its_MaxGpm(model, zone):
    return model.SSW_pumped[zone, month, time] == SSW_pump_max_gpm[zone]


def DSWpump_to_draw_its_MaxGpm(model, zone):
    return model.DSW_pump[zone, month, time] == DSW_pump_max_gpm[zone]


def time_of_use(model):
    return 7.75 * sum([model.purchasedPower[zone, month, time] * kWh_price[zone]
                       for zone in model.zone for month in model.month for time in model.time]) \
           + 7.75 * sum([(model.peak_power[zone, months] * kW_price[zone])
                         for zone in model.zone for months in model.month]) \
           + sum([Battery_cost_kw * model.installed_capacity_kw[zone]
                  for zone in model.zone]) \
           + sum([Battery_cost_kwh * model.installed_capacity_kwh[zone]
                  for zone in model.zone])


model.objective = Objective(rule=time_of_use, sense=minimize)

# model.constraint_power_balance = Constraint(model.zone, model.month, model.time,rule=power_balance)
model.constraint_stateOfCharge = Constraint(model.zone, model.month, model.time, rule=stateOfCharge)
model.constraint_SSW_balance = Constraint(model.zone, model.month, model.time, rule=SSW_balance)
model.constraint_DSW_balance = Constraint(model.zone, model.month, model.time, rule=DSW_balance)
model.constraint_SSW_gpm_to_pump_power = Constraint(model.zone, model.month, model.time,rule=SSW_gpm_to_pump_power)
model.constraint_DSW_gpm_to_pump_power = Constraint(model.zone, model.month, model.time,rule=DSW_gpm_to_pump_power)
# model.constraint_solar = Constraint(model.zone, model.month, model.time,rule=solar_energy)
model.constraint_wind_pow = Constraint(model.zone, model.month, model.time,rule=winddata)
model.constraint_stateOfCharge_and_discharge = Constraint(model.zone, model.month, model.time,rule=stateOfCharge_and_discharge)
model.constraint_limits_stateOfCharge = Constraint(model.zone, model.month, model.time,rule=limits_stateOfCharge)
model.constraint_controlling_chargepower_shortmonthend = Constraint(model.zone, model.month,model.time,rule=controlling_chargepower_shortmonthend)
model.constraint_controlling_dischargepower_shortmonthend = Constraint(model.zone, model.month,model.time,rule=controlling_dischargepower_shortmonthend)
model.constraint_control_charge_power = Constraint(model.zone, model.month, model.time,rule=control_charge_power)
model.constraint_control_discharge_power = Constraint(model.zone, model.month, model.time,rule=control_discharge_power)
model.constraint_bat_temp_gen = Constraint(model.zone, model.month, model.time,rule=batterytemperature_gen)
model.constraint_battery_temperature = Constraint(model.zone, model.month, model.time,rule=batterytemperature)
model.constraint_limiting_power_curtail = Constraint(model.zone, model.month, model.time,rule=limiting_power_curtail)
model.constraint_to_turn_on_SSW_pump = Constraint(model.zone, model.month, model.time,rule=to_turn_on_SSW_pump)
model.constraint_to_turn_on_DSW_pump = Constraint(model.zone, model.month, model.time,rule=to_turn_on_DSW_pump)
model.constraint_peak_power = Constraint(model.zone, model.month, model.time, rule=peak_power)
model.constraint_maximum_cap_of_a_SSWpump = Constraint(model.zone, model.month, model.time,rule=maximum_cap_of_a_SSWpump)
model.constraint_maximum_cap_of_a_DSWpump = Constraint(model.zone, model.month, model.time,rule=maximum_cap_of_a_DSWpump)
model.constraint_transfer_SSWdirection = Constraint(model.month, model.time,rule=transfer_SSWdirection)
model.constraint_transfer_DSWdirection = Constraint(model.month, model.time,rule=transfer_DSWdirection)
model.constraint_transfer_DSWoneway = Constraint(model.month, model.time,rule=transfer_DSWoneWay)
model.constraint_transfer_SSWoneway = Constraint(model.month, model.time,rule=transfer_SSWoneWay)
model.constraint_finalSOC = Constraint(model.zone, rule=final_stateOfCharge)

instance = model.create_instance(report_timing=True)

opt = SolverFactory('gurobi')
# opt.options['ResultFile'] = "test.mps"
opt.options["Threads"] = 24

opt.options["IntFeasTol"] = 1e-05
opt.options['NodefileStart'] = 0.90
opt.options["NodeMethod"] = 1
opt.options["MIPGapAbs"] = 0.07
opt.options["MIPGap"] = 0.07
opt.options["Method"] = 1
opt.options["TimeLimit"] = 6000
opt.options["MIPFocus"] = 1
opt.options["OutputFlag"] = 1
opt.options["DisplayInterval"] = 1
opt.options["NonConvex"] = 2
# model.write('myModel.mps')
results = opt.solve(instance, tee=True)
# results.write("test.mps")
# model.write('myModel.ilp')
# model = read('myModel.ilp')
# SolverFactory('gurobi').solve(model)
# model.computeIIS()
# model.write("model.ilp")
print(log_infeasible_constraints(model))

print('zone 1 Battery_kw = ', value(instance.installed_capacity_kw[0]))
print('zone 2 Battery_kw = ', value(instance.installed_capacity_kw[1]))
print('zone 1 Battery_kwh = ', value(instance.installed_capacity_kwh[0]))
print('zone 2 Battery_kwh = ', value(instance.installed_capacity_kwh[1]))
print('cost = ', value(instance.objective))

######  writing summary to excel file #######
summary = pd.DataFrame()
summary['time'] = pd.date_range("2019-01-01", periods=96, freq="1H")
summary['RC Demand'] = [instance.base_electrical[0, month, time]
                        for month in model.month
                        for time in model.time]

summary['RC Solar'] = [solar_increment * instance.solar[0, month, time]
                       for month in model.month
                       for time in model.time]

summary['RC wind'] = [instance.wind_pow[0, month, time]
                      for month in model.month
                      for time in model.time]

summary['power_curatiled'] = [instance.curtailedPower[0, month, time].value
                              for month in model.month
                              for time in model.time]

summary['RC Purchased'] = [instance.purchasedPower[0, month, time].value
                           for month in model.month
                           for time in model.time]

summary['RC SSW pumpPower'] = [instance.SSW_pumpPower[0, month, time].value
                               for month in model.month
                               for time in model.time]

summary['RC DSW pumpPower'] = [instance.DSW_pumpPower[0, month, time].value
                               for month in model.month
                               for time in model.time]

summary['RC Charge'] = [instance.chargePower[0, month, time].value
                        for month in model.month
                        for time in model.time]
summary['RC Discharge'] = [instance.dischargePower[0, month, time].value
                           for month in model.month
                           for time in model.time]
summary['RC SSW demand'] = [instance.SSW_demand[0, month, time]
                            for month in model.month
                            for time in model.time]
summary['RC DSW demand'] = [instance.DSW_demand[0, month, time]
                            for month in model.month
                            for time in model.time]

summary['RC SSW Pumped'] = [instance.SSW_pumped[0, month, time].value
                            for month in model.month
                            for time in model.time]

summary['RC DSW Pumped'] = [instance.DSW_pumped[0, month, time].value
                            for month in model.month
                            for time in model.time]

summary['RC transfer SSW'] = [instance.transferSSW[0, month, time].value
                              for month in model.month
                              for time in model.time]

summary['RC transfer DSW'] = [instance.transferDSW[0, month, time].value
                              for month in model.month
                              for time in model.time]
summary['battery_temperature'] = [instance.battery_temperature[0, month, time].value
                                  for month in model.month
                                  for time in model.time]

summary['RC SOC'] = [instance.stateOfCharge[0, month, time].value
                     for month in model.month
                     for time in model.time]
summary['RC peak power'] = np.nan
summary['RC peak power'].iloc[0:4] = [instance.peak_power[0, month].value
                                       for month in model.month]

summary2 = pd.DataFrame()
summary2['time'] = pd.date_range("2019-01-01", periods=96, freq="1H")
summary2['FF Demand'] = [instance.base_electrical[1, month, time]

                         for month in model.month
                         for time in model.time]
summary2['FF Solar'] = [instance.solar[1, month, time]

                        for month in model.month
                        for time in model.time]

summary2['FF wind'] = [instance.wind_pow[1, month, time]
                       for month in model.month
                       for time in model.time]

summary2['power_curatiled'] = [instance.curtailedPower[1, month, time].value
                               for month in model.month
                               for time in model.time]

summary2['FF Purchased'] = [instance.purchasedPower[1, month, time].value

                            for month in model.month
                            for time in model.time]

summary2['FF SSW pumpPower'] = [instance.SSW_pumpPower[1, month, time].value
                                for month in model.month
                                for time in model.time]

summary2['FF DSW pumpPower'] = [instance.DSW_pumpPower[1, month, time].value
                                for month in model.month
                                for time in model.time]

summary2['FF Charge'] = [instance.chargePower[1, month, time].value
                         for month in model.month
                         for time in model.time]
summary2['FF Discharge'] = [instance.dischargePower[1, month, time].value
                            for month in model.month
                            for time in model.time]
summary2['FF SSW demand'] = [instance.SSW_demand[1, month, time]
                             for month in model.month
                             for time in model.time]
summary2['FF DSW demand'] = [instance.DSW_demand[1, month, time]
                             for month in model.month
                             for time in model.time]

summary2['FF SSW Pumped'] = [instance.SSW_pumped[1, month, time].value
                             for month in model.month
                             for time in model.time]

summary2['FF DSW Pumped'] = [instance.DSW_pumped[1, month, time].value
                             for month in model.month
                             for time in model.time]

summary2['FF transfer SSW'] = [instance.transferSSW[1, month, time].value
                               for month in model.month
                               for time in model.time]

summary2['FF transfer DSW'] = [instance.transferDSW[1, month, time].value
                               for month in model.month
                               for time in model.time]

summary2['battery_temperature'] = [instance.battery_temperature[1, month, time].value
                                   for month in model.month
                                   for time in model.time]

summary2['FF SOC'] = [instance.stateOfCharge[1, month, time].value
                      for month in model.month
                      for time in model.time]
summary2['FF peak power'] = np.nan
summary2['FF peak power'].iloc[0:4] = [instance.peak_power[1, month].value
                                        for month in model.month]

summary3 = pd.DataFrame()
summary3['zone 1 Battery kw'] = [instance.installed_capacity_kw[0].value]
summary3['zone 2 Battery kw'] = value(instance.installed_capacity_kw[1])
summary3['zone 1 Battery kwh'] = value(instance.installed_capacity_kwh[0])
summary3['zone 2 Battery_kwh'] = value(instance.installed_capacity_kwh[1])
summary3['cost'] = value(instance.objective)


def generate_write_folder(solar_increment, transferMax, Battery_cost_kw, Battery_cost_kwh):
    Battery_cost_folder = '/ ${}_kW_${}_kWh'.format(Battery_cost_kw, Battery_cost_kwh)
    Solar_folder = '/ {}x_solar'.format(solar_increment)
    Bladelength = '/{}_meter'.format(blade_length)
    wind_incr = '/{}_incr'.format(wind_increment)
    windtureff = '/{}_eff'.format(wind_tur_eff)
    kWh_price_fol = '/{}_eff'.format(kWh_price)
    pmax = '/{}_limit'
    Bat_efficiency = '/{}'.format(charge_eff)

    # max_Transfer_limit_water_folder = '/ {}_max_transfer_of_water'.format(transferMax)
    variable_eff_folder = '/New_Sensitivity_study_only_ESS_solar'

    write_folder = os.getcwd() + variable_eff_folder + kWh_price_fol + Battery_cost_folder + Bat_efficiency + Solar_folder
    return write_folder


write_folder = generate_write_folder(solar_increment, transferMax, Battery_cost_kw,
                                     Battery_cost_kwh)
variable_eff_folder = '/New_Sensitivity_study_only_ESS_solar'

if not os.path.exists(write_folder):
    os.makedirs(write_folder)

excel_filename = variable_eff_folder + '_' + 's_' + str(solar_increment) + 'xincr' + '_' + str(
    kWh_price[0]) + '_' + str(Battery_cost_kw) + '_' + str(charge_eff)

filename = '{}.xlsx'.format(excel_filename)
writer = pd.ExcelWriter(write_folder + filename)
summary.to_excel(writer, sheet_name='Research Campus')
summary2.to_excel(writer, sheet_name='FF Station')
summary3.to_excel(writer, sheet_name='other_details')
writer.save()