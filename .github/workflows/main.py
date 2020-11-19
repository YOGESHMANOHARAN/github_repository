from pyomo.environ import *
import pandas as pd
from pyomo.util.infeasible import log_infeasible_constraints
# data = pd.read_pickle('test_data_RC')['2019']

def run_main(data, SOCmax, ESmax=100):
    model = AbstractModel()
    end_time = len(data) - 1
    model.time = RangeSet(0, end_time)

    # region Define max power and flow from each section
    PmaxSSW = 100
    PmaxRC = 5000
    PmaxDSW = 200
    maxFlowSSW = 100
    maxFlowDSW = 100
    maxFlowRC = 1000
    solarMax = data.solar.max()
    # print(solarMax)

    # SOCmax = 1000  # Maximum state-of-charge in kWh
    charge_eff = 0.94
    discharge_eff = 0.94
    Pmax = 100
    dt = 1 # need to calculate this for different time steps
    # endregion

    # region Initialize input data
    def solar(model, time):
        return data.solar.values[time]
    model.solar = Param(model.time, initialize=solar)

    def base_demand(model, time):
        return data.kW.values[time]
    model.base_electrical = Param(model.time, initialize=base_demand)

    def SSW_demand(model, time):
        return data.SSW_demand[time]
    model.SSW_demand = Param(model.time, initialize=SSW_demand)

    def DSW_demand(model, time):
        return data.DSW_demand[time]
    model.DSW_demand = Param(model.time, initialize=DSW_demand)
    # endregion

    # region Declare Variable
    model.SSW_power = Var(model.time, domain=NonNegativeReals, bounds=(0, PmaxRC))
    model.DSW_power = Var(model.time, domain=NonNegativeReals, bounds=(0, PmaxRC))
    model.SSW_draw = Var(model.time, domain=NonNegativeReals, bounds=(0, maxFlowRC))
    model.DSW_draw = Var(model.time, domain=NonNegativeReals, bounds=(0, maxFlowRC))
    model.chargePower = Var(model.time, domain=NonNegativeReals, bounds=(0, ESmax))
    model.dischargePower = Var(model.time, domain=NonNegativeReals, bounds=(0, ESmax))
    model.purchasedPower = Var(model.time, domain=NonNegativeReals, bounds=(0, PmaxRC))
    model.stateOfCharge = Var(model.time, domain=NonNegativeReals, bounds=(0, SOCmax))
    model.curtailedPower = Var(model.time, domain=NonNegativeReals, bounds=(0, solarMax))
    # endregion

    # region Import breakpoints for Piecewise Linear Constraints
    SSW_points = pd.read_excel('sample_pump_eff.xlsx', sheet_name='SSW')
    P_SSW = SSW_points.kW
    m_SSW = SSW_points.gph

    DSW_points = pd.read_excel('sample_pump_eff.xlsx', sheet_name='DSW')
    P_DSW = DSW_points.kW
    m_DSW = DSW_points.gph

    number_of_points = len(P_DSW)
    model.breaks = RangeSet(0, number_of_points)
    model.alpha_SSW = Var(model.breaks, model.time, domain=Binary)
    model.beta_SSW = Var(model.breaks, model.time, domain=NonNegativeReals, bounds=(0, 1))

    model.alpha_DSW = Var(model.breaks, model.time, domain=Binary)
    model.beta_DSW = Var(model.breaks, model.time, domain=NonNegativeReals, bounds=(0, 1))
    def power_balance(model, time):
        return model.purchasedPower[time] == model.base_electrical[time] - model.solar[time] \
                                            - model.dischargePower[time] + model.chargePower[time] \
                                            + model.SSW_power[time] + model.DSW_power[time] \
                                            + model.curtailedPower[time]

    def SSW_balance(model, time):
        return model.SSW_draw[time] == model.SSW_demand[time]

    def DSW_balance(model, time):
        return model.DSW_draw[time] == model.DSW_demand[time]

    def stateOfCharge(model, time):
        if time == 0:
            SOCpre = 0.5 * SOCmax
        else:
            SOCpre = model.stateOfCharge[time-1]
        return model.stateOfCharge[time] == SOCpre + (charge_eff * model.chargePower[time]
                                                      - model.dischargePower[time]/discharge_eff) * dt

    def final_stateOfCharge(model):
        return model.stateOfCharge[end_time] == 0.5 * SOCmax

    # region Surface and Deep Sea water flow and power constraints
    def SSW_mass_flow(model, time):
        return model.SSW_draw[time] == sum(model.beta_SSW[b, time] * m_SSW[b] for b in range(0, number_of_points))

    def DSW_mass_flow(model, time):
        return model.DSW_draw[time] == sum(model.beta_DSW[b, time] * m_DSW[b] for b in range(0, number_of_points))

    def SSW_power_demand(model, time):
        return model.SSW_power[time] == sum(model.beta_SSW[b, time] * P_SSW[b] for b in range(0, number_of_points))

    def DSW_power_demand(model, time):
        return model.DSW_power[time] == sum(model.beta_DSW[b, time] * P_DSW[b] for b in range(0, number_of_points))
    # endregion

    # region SOS2 Constraints
    def beta_alpha_SSWconstraint(model, breaks, time):
        return model.beta_SSW[breaks, time] <= model.alpha_SSW[breaks, time]

    def alphaSSW_number_constraint(model, time):
        return sum(model.alpha_SSW[breaks, time] for breaks in range(0, number_of_points)) <= 2

    def consecutive_SSW_constraint1(model, time):
        return model.alpha_SSW[0, time] + model.alpha_SSW[3, time] <= 1

    def consecutive_SSW_constraint2(model, time):
        return model.alpha_SSW[0, time] + model.alpha_SSW[2, time] <= 1

    def consecutive_SSW_constraint3(model, time):
        return model.alpha_SSW[1, time] + model.alpha_SSW[3, time] <= 1

    def cumulative_SSW_beta(model, breaks, time):
        return sum(model.beta_SSW[breaks, time] for breaks in model.breaks) == 1

    def beta_alpha_DSWconstraint(model, breaks, time):
        return model.beta_DSW[breaks, time] <= model.alpha_DSW[breaks, time]

    def alphaDSW_number_constraint(model, time):
        return sum(model.alpha_DSW[breaks, time] for breaks in range(0, number_of_points)) <= 2

    def consecutive_DSW_constraint1(model, time):
        return model.alpha_DSW[0, time] + model.alpha_DSW[3, time] <= 1

    def consecutive_DSW_constraint2(model, time):
        return model.alpha_DSW[0, time] + model.alpha_DSW[2, time] <= 1

    def consecutive_DSW_constraint3(model, time):
        return model.alpha_DSW[1, time] + model.alpha_DSW[3, time] <= 1

    def cumulative_DSW_beta(model, breaks, time):
        return sum(model.beta_DSW[breaks, time] for breaks in model.breaks) == 1
    # endregion


    def time_of_use(model):
        return sum([model.purchasedPower[time] * data.price[time] for time in model.time])
    model.objective = Objective(rule=time_of_use, sense=minimize)

    model.constraint_power_balance = Constraint(model.time, rule=power_balance)
    model.constraint_stateOfCharge = Constraint(model.time, rule=stateOfCharge)
    model.constraint_SSW_balance = Constraint(model.time, rule=SSW_balance)
    model.constraint_DSW_balance = Constraint(model.time, rule=DSW_balance)
    model.constraint_SSW_mass_flow = Constraint(model.time, rule=SSW_mass_flow)
    model.constraint_DSW_mass_flow = Constraint(model.time, rule=DSW_mass_flow)
    model.constraint_SSW_power_demand = Constraint(model.time, rule=SSW_power_demand)
    model.constraint_DSW_power_demand = Constraint(model.time, rule=DSW_power_demand)

    model.constraint_beta_alpha_SSWconstraint = Constraint(model.breaks, model.time, rule=beta_alpha_SSWconstraint)
    model.constraint_alphaSSW_number_constraint = Constraint(model.time, rule=alphaSSW_number_constraint)
    model.constraint_consecutive_SSW_constraint1 = Constraint(model.time, rule=consecutive_SSW_constraint1)
    model.constraint_consecutive_SSW_constraint2 = Constraint(model.time, rule=consecutive_SSW_constraint2)
    model.constraint_consecutive_SSW_constraint3 = Constraint(model.time, rule=consecutive_SSW_constraint3)
    model.constraint_cumulative_SSW_beta = Constraint(model.breaks, model.time, rule=cumulative_SSW_beta)

    model.constraint_beta_alpha_DSWconstraint = Constraint(model.breaks, model.time, rule=beta_alpha_DSWconstraint)
    model.constraint_alphaDSW_number_constraint = Constraint(model.time, rule=alphaDSW_number_constraint)
    model.constraint_consecutive_DSW_constraint1 = Constraint(model.time, rule=consecutive_DSW_constraint1)
    model.constraint_consecutive_DSW_constraint2 = Constraint(model.time, rule=consecutive_DSW_constraint2)
    model.constraint_consecutive_DSW_constraint3 = Constraint(model.time, rule=consecutive_DSW_constraint3)
    model.constraint_cumulative_DSW_beta = Constraint(model.breaks, model.time, rule=cumulative_DSW_beta)
    model.constraint_finalSOC = Constraint(rule=final_stateOfCharge)

    instance = model.create_instance(report_timing=False)
    opt = SolverFactory('gurobi')
    results = opt.solve(instance, tee=False)
    # print(log_infeasible_constraints(model))

    summary = pd.DataFrame()
    summary['time'] = data.index
    summary['Demand'] = data.kW.values
    summary['Solar'] = data.solar.values
    summary['Charge'] = [instance.chargePower[t].value for t in range(0, len(data))]
    summary['Discharge'] = [instance.dischargePower[t].value for t in range(0, len(data))]
    summary['Purchased'] = [instance.purchasedPower[t].value for t in range(0, len(data))]
    return instance, results


