from pyomo.environ import *
import pandas as pd

data = pd.read_pickle('Sample_data')
model = AbstractModel()
model.time = RangeSet(0, len(data)-1)

# region Define max power and flow from each section
PmaxSSW = 100
PmaxRC = 100
PmaxDSW = 200
maxFlowSSW = 5
maxFlowDSW = 5
maxFlowRC = 5

SOCmax = 500  # Maximum state-of-charge in kWh
charge_eff = 0.94
discharge_eff = 0.94
Pmax = 100
dt = 2
# endregion

# region Initialize input data
def solar(model, time):
    return data.solar.values[time]
model.solar = Param(model.time, initialize=solar)

def base_demand(model, time):
    return data.kW.values[time]
model.base_electrical = Param(model.time, initialize=base_demand)

def SSW_demand(model, time):
    return data.SSW_h2O[time]
model.SSW_demand = Param(model.time, initialize=SSW_demand)

def DSW_demand(model, time):
    return data.DSW_h2O[time]
model.DSW_demand = Param(model.time, initialize=DSW_demand)
# endregion

# region Declare Variable
model.SSW_power = Var(domain=NonNegativeReals, bounds=(0, PmaxRC))
model.DSW_power = Var(domain=NonNegativeReals, bounds=(0, PmaxDSW))
model.SSW_draw = Var(domain=NonNegativeReals, bounds=(0, maxFlowRC))
model.DSW_draw = Var(domain=NonNegativeReals, bounds=(0, maxFlowDSW))
model.chargePower = Var(model.time, domain=NonNegativeReals, bounds=(0, Pmax))
model.dischargePower = Var(model.time, domain=NonNegativeReals, bounds=(0, Pmax))
model.purchasedPower = Var(model.time, domain=NonNegativeReals, bounds=(0, 450))
model.stateOfCharge = Var(model.time, domain=NonNegativeReals, bounds=(0, SOCmax))
# endregion

# region Import breakpoints for Piecewise Linear Constraints
SSW_points = pd.read_excel('sample_pump_eff.xlsx', sheet_name='SSW')
P_SSW = SSW_points.P
m_SSW = SSW_points.m

DSW_points = pd.read_excel('sample_pump_eff.xlsx', sheet_name='DSW')
P_DSW = DSW_points.P
m_DSW = DSW_points.m

number_of_points = len(P_DSW)
model.breaks = RangeSet(0, number_of_points-1)
alpha_SSW = Var(model.breaks, domain=NonNegativeReals, bounds=(0, 1))
beta_SSW = Var(model.breaks, domain=Binary)

alpha_DSW = Var(model.breaks, domain=NonNegativeReals, bounds=(0, 1))
beta_DSW = Var(model.breaks, domain=Binary)
def power_balance(model, time):
    return model.purchasedPower[time] == model.base_electrical[time] - model.solar[time] \
                                        - model.dischargePower[time] + model.chargePower[time] \
                                        + model.SSW_power[time] + model.DSW_power[time]

def SSW_balance(model, time):
    return model.SSW_demand[time] == model.SSW_draw[time]

def DSW_balance(model, time):
    return model.DSW_demand[time] == model.DSW_draw[time]

def stateOfCharge(model, time):
    if time == 0:
        SOCpre = 0.5 * SOCmax
    else:
        SOCpre = model.stateOfCharge[time-1]
    return model.stateOfCharge[time] == SOCpre + (charge_eff * model.chargePower[time]
                                                  - model.dischargePower[time]/discharge_eff) * dt

# region Surface and Deep Sea water flow and power constraints
def SSW_mass_flow(model, time):
    return model.SSW_draw[time] == sum(beta_SSW[b, time] * m_SSW[b, time] for b in range(0, number_of_points-1))

def DSW_mass_flow(model, time):
    return model.DSW_draw[time] == sum(beta_DSW[b] * m_DSW[b] for b in range(0, number_of_points-1))

def SSW_power_demand(model, time):
    return model.SSW_power[time] == sum(beta_SSW[b, time] * P_SSW[b, time] for b in range(0, number_of_points-1))

def DSW_power_demand(model, time):
    return model.DSW_power[time] == sum(beta_DSW[b, time] * P_DSW[b, time] for b in range(0, number_of_points-1))
# endregion

# region SOS2 Constraints
def beta_alpha_SSWconstraint(model, breaks, time):
    return model.beta_SSW[breaks, time] <= model.alpha_SSW[breaks, time]

def alphaSSW_number_constraint(model, time):
    return sum(model.alpha_SSW[breaks, time] for breaks in range(number_of_points-1)) <= 2

def consecutive_SSW_constraint1(model, time):
    return model.alpha_SSW[0, time] + model.alpha_SSW[3, time] <= 1

def consecutive_SSW_constraint2(model, time):
    return model.alpha_SSW[0, time] + model.alpha_SSW[2, time] <= 1

def consecutive_SSW_constraint3(model, time):
    return model.alpha_SSW[1, time] + model.alpha_SSW[3, time] <= 1

def beta_alpha_DSWconstraint(model, breaks, time):
    return model.beta_DSW[breaks, time] <= model.alpha_DSW[breaks, time]

def alphaDSW_number_constraint(model, time):
    return sum(model.alpha_DSW[breaks, time] for breaks in range(number_of_points-1)) <= 2

def consecutive_DSW_constraint1(model, time):
    return model.alpha_DSW[0, time] + model.alpha_DSW[3, time] <= 1

def consecutive_DSW_constraint2(model, time):
    return model.alpha_DSW[0, time] + model.alpha_DSW[2, time] <= 1

def consecutive_DSW_constraint3(model, time):
    return model.alpha_DSW[1, time] + model.alpha_DSW[3, time] <= 1
# endregion
print('done')
