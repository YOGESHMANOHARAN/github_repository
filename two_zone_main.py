from pyomo.environ import *
import pandas as pd
from pyomo.util.infeasible import log_infeasible_constraints
# data = pd.read_pickle('test_data_RC')['2019']

def run_main(data_RC, data_FF, SOCmax=100, ESmax=100):

    model = AbstractModel()
    end_time = len(data_RC) - 1
    model.time = RangeSet(0, end_time)
    model.zone = RangeSet(0, 1)

    # region Define max power and flow from each section
    PmaxSSW = 100
    PmaxRC = 5000
    PmaxDSW = 200
    maxFlowSSW = 30000
    maxFlowDSW = 30000
    transferMax = 30000
    solarMax = data_RC.solar.max()
    demand_charge = [13, 25]
    # print(solarMax)

    # SOCmax = 1000  # Maximum state-of-charge in kWh
    charge_eff = 0.94
    discharge_eff = 0.94
    Pmax = 100
    dt = 1 # need to calculate this for different time steps
    # endregion

    # region Initialize input data
    def solar(model, zone, time):
        if zone == 0:
            solar = data_RC.solar.values[time]
        else:
            solar = data_FF.solar.values[time]
        return solar
    model.solar = Param(model.zone, model.time, initialize=solar, within=Any)

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

    def DSW_demand(model,zone, time):
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
    model.SSW_draw = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, maxFlowSSW))
    model.DSW_draw = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, maxFlowDSW))

    model.transfer_SSW = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, transferMax))
    model.transfer_DSW = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, transferMax))
    model.dischargePower = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, ESmax))
    model.purchasedPower = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, PmaxRC))
    model.stateOfCharge = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, SOCmax))
    model.curtailedPower = Var(model.zone, model.time, domain=NonNegativeReals, bounds=(0, solarMax))
    # endregion

    # region Import breakpoints for Piecewise Linear Constraints
    SSW_points = pd.read_excel('sample_pump_eff.xlsx', sheet_name='SSW')
    P_SSW = SSW_points.kW
    m_SSW = SSW_points.gph

    DSW_points = pd.read_excel('sample_pump_eff.xlsx', sheet_name='DSW')
    P_DSW = DSW_points.kW
    m_DSW = DSW_points.gph

    number_of_points = len(P_DSW)
    model.breaks = RangeSet(0, number_of_points-1)
    model.alpha_SSW = Var(model.breaks, model.zone, model.time, domain=Binary)
    model.beta_SSW = Var(model.breaks, model.zone, model.time, domain=NonNegativeReals, bounds=(0, 1))

    model.alpha_DSW = Var(model.breaks, model.zone, model.time, domain=Binary)
    model.beta_DSW = Var(model.breaks, model.zone, model.time, domain=NonNegativeReals, bounds=(0, 1))

    def power_balance(model, zone, time):
        return model.purchasedPower[zone, time] == model.base_electrical[zone, time] - model.solar[zone, time] \
                                            - model.dischargePower[zone, time] + model.chargePower[zone, time] \
                                            + model.SSW_power[zone, time] + model.DSW_power[zone, time] \
                                            + model.curtailedPower[zone, time]

    def peak_power(model, zone, time):
        return model.peak_power[zone] >= model.purchasedPower[zone, time]

    def SSW_balance(model, zone, time):
        return model.SSW_demand[zone, time] + model.trasnferSSW[zone, time] == model.SSW_draw[zone, time]

    def transfer_SSWoneWay(model, time):
        return model.transfer_SSW[0, time] == 0


    def DSW_balance(model, zone, time):
        return model.DSW_demand[zone, time] + model.trasnferDSW[zone, time] == model.DSW_draw[zone, time]

    def transfer_DSWoneWay(model, time):
        return model.transfer_DSW[0, time] == 0

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
    def SSW_mass_flow(model, zone, time):
        return model.SSW_draw[zone, time] == sum(model.beta_SSW[b, zone, time] * m_SSW[b]
                                                 for b in range(0, number_of_points))

    def DSW_mass_flow(model, zone, time):
        return model.DSW_draw[zone, time] == sum(model.beta_DSW[b, zone, time] * m_DSW[b]
                                                 for b in model.breaks)

    def SSW_power_demand(model, zone, time):
        return model.SSW_power[zone, time] == sum(model.beta_SSW[b, zone, time] * P_SSW[b]
                                                  for b in range(0, number_of_points))

    def DSW_power_demand(model, zone, time):
        return model.DSW_power[zone, time] == sum(model.beta_DSW[b, zone, time] * P_DSW[b]
                                                  for b in range(0, number_of_points))
    # endregion

    # region SOS2 Constraints
    def beta_alpha_SSWconstraint(model, breaks, zone, time):
        return model.beta_SSW[breaks, zone, time] <= model.alpha_SSW[breaks, zone, time]

    def alphaSSW_number_constraint(model, zone, time):
        return sum(model.alpha_SSW[breaks, zone, time] for breaks in range(0, number_of_points)) <= 2

    def consecutive_SSW_constraint1(model, zone, time):
        return model.alpha_SSW[0, zone, time] + model.alpha_SSW[3, zone, time] <= 1

    def consecutive_SSW_constraint2(model, zone, time):
        return model.alpha_SSW[0, zone, time] + model.alpha_SSW[2, zone, time] <= 1

    def consecutive_SSW_constraint3(model, zone, time):
        return model.alpha_SSW[1, zone, time] + model.alpha_SSW[3, zone, time] <= 1

    def cumulative_SSW_beta(model, zone, time):
        return sum(model.beta_SSW[breaks, zone, time] for breaks in model.breaks) == 1

    def beta_alpha_DSWconstraint(model, breaks, zone, time):
        return model.beta_DSW[breaks, zone, time] <= model.alpha_DSW[breaks, zone, time]

    def alphaDSW_number_constraint(model, zone, time):
        return sum(model.alpha_DSW[breaks, zone, time] for breaks in range(0, number_of_points)) <= 2

    def consecutive_DSW_constraint1(model, zone, time):
        return model.alpha_DSW[0, zone, time] + model.alpha_DSW[3, zone, time] <= 1

    def consecutive_DSW_constraint2(model, zone, time):
        return model.alpha_DSW[0, zone, time] + model.alpha_DSW[2, zone, time] <= 1

    def consecutive_DSW_constraint3(model, zone, time):
        return model.alpha_DSW[1, zone, time] + model.alpha_DSW[3, zone, time] <= 1

    def cumulative_DSW_beta(model, zone, time):
        return sum(model.beta_DSW[breaks, zone, time] for breaks in model.breaks) == 1
    # endregion


    def time_of_use(model):
        return sum([model.purchasedPower[zone, time] * data_RC.price[time] for time in model.time for zone in model.zone])

    def time_of_use_peak_power(model):
        return sum([model.purchasedPower[zone, time] * data_RC.price[time]
                    for time in model.time for zone in model.zone]) + sum([model.peak_power[zone] * demand_charge[zone] for zone in model.zone])
    model.objective = Objective(rule=time_of_use, sense=minimize)

    model.constraint_power_balance = Constraint(model.zone, model.time, rule=power_balance)
    model.constraint_peak_power = Constraint(model.zone, model.time, rule=peak_power)
    model.constraint_stateOfCharge = Constraint(model.zone, model.time, rule=stateOfCharge)
    model.constraint_SSW_balance = Constraint(model.zone, model.time, rule=SSW_balance)
    model.constraint_DSW_balance = Constraint(model.zone, model.time, rule=DSW_balance)
    model.constraint_SSW_mass_flow = Constraint(model.zone, model.time, rule=SSW_mass_flow)
    model.constraint_DSW_mass_flow = Constraint(model.zone, model.time, rule=DSW_mass_flow)
    model.constraint_oneWayTransferSSW = Constraint(model.zone, model.time, rule=transfer_SSWoneWay)
    model.constraint_oneWayTransferDSW = Constraint(model.zone, model.time, rule=transfer_DSWoneWay)
    model.constraint_SSW_power_demand = Constraint(model.zone, model.time, rule=SSW_power_demand)
    model.constraint_DSW_power_demand = Constraint(model.zone, model.time, rule=DSW_power_demand)

    model.constraint_beta_alpha_SSWconstraint = Constraint(model.breaks, model.zone, model.time, rule=beta_alpha_SSWconstraint)
    model.constraint_alphaSSW_number_constraint = Constraint(model.zone, model.time, rule=alphaSSW_number_constraint)
    model.constraint_consecutive_SSW_constraint1 = Constraint(model.zone, model.time, rule=consecutive_SSW_constraint1)
    model.constraint_consecutive_SSW_constraint2 = Constraint(model.zone, model.time, rule=consecutive_SSW_constraint2)
    model.constraint_consecutive_SSW_constraint3 = Constraint(model.zone, model.time, rule=consecutive_SSW_constraint3)
    model.constraint_cumulative_SSW_beta = Constraint(model.zone, model.time, rule=cumulative_SSW_beta)

    model.constraint_beta_alpha_DSWconstraint = Constraint(model.breaks, model.zone, model.time, rule=beta_alpha_DSWconstraint)
    model.constraint_alphaDSW_number_constraint = Constraint(model.zone, model.time, rule=alphaDSW_number_constraint)
    model.constraint_consecutive_DSW_constraint1 = Constraint(model.zone, model.time, rule=consecutive_DSW_constraint1)
    model.constraint_consecutive_DSW_constraint2 = Constraint(model.zone, model.time, rule=consecutive_DSW_constraint2)
    model.constraint_consecutive_DSW_constraint3 = Constraint(model.zone, model.time, rule=consecutive_DSW_constraint3)
    model.constraint_cumulative_DSW_beta = Constraint(model.zone, model.time, rule=cumulative_DSW_beta)
    model.constraint_finalSOC = Constraint(model.zone, rule=final_stateOfCharge)

    instance = model.create_instance(report_timing=False)
    opt = SolverFactory('gurobi')
    results = opt.solve(instance, tee=False)
    # print(log_infeasible_constraints(model))

    return instance, results


