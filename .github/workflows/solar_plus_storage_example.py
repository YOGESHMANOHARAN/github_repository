import pandas as pd
from pyomo.environ import *

full_data = pd.read_pickle('sample_solar_demand')
data = full_data['1/2019']

model = AbstractModel()
model.time = RangeSet(0, len(data)-1)
Pmax = 100      # Max battery power in kW
SOCmax = 100    # Max battery SOC in kWh
charge_eff = 0.90
discharge_eff = 0.90
dt = 1

def demand(model, time):
    return data.Demand.values[time]
model.demand = Param(model.time, initialize=demand)

def solar(model, time):
    return data.solar_kW.values[time]
model.solar = Param(model.time, initialize=solar)

model.chargePower = Var(model.time, domain=NonNegativeReals, bounds=(0, Pmax))
model.dischargePower = Var(model.time, domain=NonNegativeReals, bounds=(0, Pmax))
model.stateOfCharge = Var(model.time, domain=NonNegativeReals, bounds=(0, SOCmax))
model.purchasedPower = Var(model.time, domain=Reals, bounds=(-450, 450))

def power_balance(model, time):
    return model.purchasedPower[time] == model.demand[time] - model.solar[time] \
                                        - model.dischargePower[time] + model.chargePower[time]
def stateOfCharge(model, time):
    if time == 0:
        SOCpre = 0.5 * SOCmax
    else:
        SOCpre = model.stateOfCharge[time-1]
    return model.stateOfCharge[time] == SOCpre + (charge_eff * model.chargePower[time]
                                                  - model.dischargePower[time]/discharge_eff) * dt

def objective_time_of_use(model):
    return sum([model.purchasedPower[time] * data.energy_charge[time] for time in model.time])
model.objective = Objective(rule=objective_time_of_use, sense=minimize)

model.constraint1 = Constraint(model.time, rule=power_balance)
model.constraint2 = Constraint(model.time, rule=stateOfCharge)

instance = model.create_instance()
opt = SolverFactory('gurobi')
opt.solve(instance)

summary = pd.DataFrame()
summary['time'] = data.index
summary['Demand'] = data.Demand
summary['Solar'] = data.solar_kW
summary['Charge'] = [instance.chargePower[t].value for t in range(0, len(data))]
summary['Discharge'] = [instance.dischargePower[t].value for t in range(0, len(data))]
summary['Purchased'] = [instance.purchasedPower[t].value for t in range(0, len(data))]
