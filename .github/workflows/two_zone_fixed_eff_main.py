from pyomo.environ import *
import pandas as pd
from pyomo.util.infeasible import log_infeasible_constraints
# data = pd.read_pickle('test_data_RC')['2019']

def run_main(data_RC, data_FF, SOCmax=100, ESmax=100):
    points_per_hour = pd.to_timedelta('1h') / (data_FF.index[1] - data_FF.index[0])

    # kWh/kgal ratios for SSW pumps at RC and FF
    powerSSW = [0.42, 0.368]
    powerDSW = [0.3725, 0.4292]
    flowToPower = {}
    flowToPower[0] = powerSSW
    flowToPower[1] = powerDSW
    kgal_to_gpm = 60/1000
    model = AbstractModel()
    end_time = len(data_RC) - 1
    model.time = RangeSet(0, end_time)
    model.zone = RangeSet(0, 1)

    # region Define max power and flow from each section
    PmaxSSW = 100
    PmaxRC = 500000000
    PmaxDSW = 200
    maxFlowSSW = 300000000
    maxFlowDSW = 30000000
    transferMax = 0
    solarMax = data_RC.solar.max()
    demand_charge = [13, 25]
    # print(solarMax)

    # SOCmax = 1000  # Maximum state-of-charge in kWh
    charge_eff = 0.94
    discharge_eff = 0.94
    Pmax = 100
    dt = 1 / points_per_hour  # need to calculate this for different time steps
    # endregion

    # region Initialize input data
    def solar(model, zone, time):
        if zone == 0:
            solar = data_RC.solar.values[time]
        else:
            solar = data_FF.solar.values[time]
        return solar
    model.solar = Param(model.zone, model.time, initialize=solar)

    def base_demand(model, zone, time):
        if zone == 0:
            base_power = data_RC.kW.values[time]
        else:
            base_power = data_FF.kW.values[time]
        return base_power
    model.base_electrical = Param(model.zone, model.time, initialize=base_demand)

    def SSW_demand(model, zone, time):
        if zone == 0:
            SSW_draw = data_RC.SSW_demand.values[time]
        else:
            SSW_draw = data_FF.SSW_demand.values[time]
        return SSW_draw
    model.SSW_demand = Param(model.zone, model.time, initialize=SSW_demand)

    def DSW_demand(model, zone, time):
        if zone == 0:
            DSW_draw = data_RC.DSW_demand.values[time]
        else:
            DSW_draw = data_FF.DSW_demand.values[time]
        return DSW_draw
    model.DSW_demand = Param(model.zone, model.time, initialize=DSW_demand)
    # endregion

    # region Declare Variable
    model.SSW_power = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, PmaxRC))
    model.DSW_power = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, PmaxRC))
    model.peak_power = Var(model.zone, domain=NonNegativeReals, bounds=(0, PmaxRC))
    model.chargePower = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, ESmax))
    model.SSW_pumped = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, maxFlowSSW))
    model.DSW_pumped = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, maxFlowDSW))

    model.transferSSW = Var(model.zone, model.time, domain=Reals, bounds=(-transferMax, transferMax))
    model.transferDSW = Var(model.zone, model.time, domain=Reals, bounds=(-transferMax, transferMax))
    model.dischargePower = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, ESmax))
    model.purchasedPower = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, PmaxRC))
    model.stateOfCharge = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, SOCmax))
    model.curtailedPower = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, solarMax))
    # endregion

    # region Import breakpoints for Piecewise Linear Constraints
    def power_balance(model, zone, time):
        return model.base_electrical[zone, time] - model.solar[zone, time] - model.dischargePower[zone, time] \
               + model.chargePower[zone, time] + model.SSW_power[zone, time] + model.DSW_power[zone, time] \
               + model.curtailedPower[zone, time] == model.purchasedPower[zone, time]

    def peak_power(model, zone, time):
        return model.peak_power[zone] >= model.purchasedPower[zone, time]

    def SSW_balance(model, zone, time):
        return model.SSW_demand[zone, time] + model.transferSSW[zone, time] == model.SSW_pumped[zone, time]

    def transfer_SSWdirection(model, time):
        return model.transferSSW[0, time] == -model.transferSSW[1, time]

    def transfer_SSWoneWay(model, time):
        return model.transferSSW[0, time] <= 0

    def DSW_balance(model, zone, time):
        return model.DSW_demand[zone, time] + model.transferDSW[zone, time] - model.DSW_pumped[zone, time] == 0

    def transfer_DSWdirection(model, time):
        return model.transferDSW[0, time] == -model.transferDSW[1, time]

    def transfer_DSWoneWay(model, time):
        return model.transferDSW[0, time] <= 0

    def stateOfCharge(model, zone, time):
        if time == 0:
            SOCpre = 0.5 * SOCmax
        else:
            SOCpre = model.stateOfCharge[zone, time-1]
        return model.stateOfCharge[zone, time] == SOCpre + (charge_eff * model.chargePower[zone, time]
                                                            - model.dischargePower[zone, time]/discharge_eff) * dt

    def final_stateOfCharge(model, zone):
        return model.stateOfCharge[zone, end_time] == 0.5 * SOCmax

    # region Surface and Deep Sea water flow and power constraints
    def SSW_flow_to_power(model, zone, time):
        return model.SSW_power[zone, time] == model.SSW_pumped[zone, time] * flowToPower[0][zone] * kgal_to_gpm

    def DSW_flow_to_power(model, zone, time):
        return model.DSW_power[zone, time] == model.DSW_pumped[zone, time] * flowToPower[1][zone] * kgal_to_gpm

    # endregion

    def time_of_use(model):
        return sum([model.purchasedPower[zone, time] * data_RC.price[time]
                    for time in model.time for zone in model.zone])

    def time_of_use_peak_power(model):
        return sum([model.purchasedPower[zone, time] * data_RC.price[time] / points_per_hour
                    for time in model.time for zone in model.zone]) \
               + sum([model.peak_power[zone] * demand_charge[zone] for zone in model.zone])
    model.objective = Objective(rule=time_of_use_peak_power, sense=minimize)

    model.constraint_power_balance = Constraint(model.zone, model.time, rule=power_balance)
    model.constraint_peak_power = Constraint(model.zone, model.time, rule=peak_power)
    model.constraint_stateOfCharge = Constraint(model.zone, model.time, rule=stateOfCharge)
    model.constraint_SSW_balance = Constraint(model.zone, model.time, rule=SSW_balance)
    model.constraint_DSW_balance = Constraint(model.zone, model.time, rule=DSW_balance)
    model.constraint_SSW_power_demand = Constraint(model.zone, model.time, rule=SSW_flow_to_power)
    model.constraint_DSW_power_demand = Constraint(model.zone, model.time, rule=DSW_flow_to_power)
    model.constraint_SSWtransferDirection = Constraint(model.time, rule=transfer_SSWdirection)
    model.constraint_DSWtransferDirection = Constraint(model.time, rule=transfer_DSWdirection)
    model.constraint_oneWayTransferSSW = Constraint(model.time, rule=transfer_SSWoneWay)
    model.constraint_oneWayTransferDSW = Constraint(model.time, rule=transfer_DSWoneWay)
    model.constraint_finalSOC = Constraint(model.zone, rule=final_stateOfCharge)

    instance = model.create_instance(report_timing=True)
    opt = SolverFactory('gurobi')
    results = opt.solve(instance, tee=True)
    # print(log_infeasible_constraints(model))

    return instance, results


