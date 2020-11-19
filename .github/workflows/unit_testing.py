'''
This isn't exactly a true full unit test, but I'll put a bunch of the major code
checks here to be sure that everything is working smoothly
'''
from main import *
import pandas as pd
import numpy as np

# region Check SOS2 power and gph outputs
empty_file = 'empty_index'
break_file = 'sample_pump_eff.xlsx'

SSW_points = pd.read_excel(break_file, sheet_name='SSW')
P_SSW = SSW_points.kW
m_SSW = SSW_points.gph

DSW_points = pd.read_excel(break_file, sheet_name='DSW')
P_DSW = DSW_points.kW
m_DSW = DSW_points.gph

# region Test Definitions
def test_SSW_SOS2_at_BPs():
    break_file, empty_file = define_empty_file()
    P_SSW, m_SSW = read_breakpoints(break_file, 'SSW')
    data = pd.read_pickle(empty_file)[0:23]

    for i in range(0, len(m_SSW)):
        data.SSW_demand = 0
        gph = m_SSW[i]
        breakpoint_power = P_SSW[i]
        data.SSW_demand.iloc[0] = gph
        data.price = 1
        instance, results = run_main(data, 0)
        print('Breakpoint {}'.format(i))
        print(SSW_power_isclose_match(instance, breakpoint_power))
        print(purchased_power_isclose(instance, breakpoint_power))
        print(objective_is_right(breakpoint_power, data, instance))

def test_DSW_SOS2_at_BPs():
    break_file, empty_file = define_empty_file()
    P_SSW, m_SSW = read_breakpoints(break_file, 'DSW')
    data = pd.read_pickle(empty_file)[0:23]

    for i in range(0, len(m_SSW)):
        data.DSW_demand = 0
        gph = m_DSW[i]
        breakpoint_power = P_DSW[i]
        data.DSW_demand.iloc[0] = gph
        data.price = 1
        instance, results = run_main(data, 0)
        print('Breakpoint {}'.format(i))
        print(purchased_power_isclose(instance, breakpoint_power))
        print(DSW_power_isclose_match(instance, breakpoint_power))
        print(objective_is_right(breakpoint_power, data, instance))

def test_SSW_SOS2_between_BPs():
    break_file, empty_file = define_empty_file()
    P_SSW, m_SSW = read_breakpoints(break_file, 'SSW')
    data = pd.read_pickle(empty_file)[0:23]

    for i in range(0, len(m_SSW)-1):
        data.SSW_demand = 0
        ratio = np.random.uniform(0.1, 0.9)
        gph = ratio * m_SSW[i] + (1-ratio) * m_SSW[i+1]
        breakpoint_power = ratio * P_SSW[i] + (1-ratio) * P_SSW[i+1]
        data.SSW_demand.iloc[0] = gph
        data.price = 1
        instance, results = run_main(data, 0)
        print('Breakpoint {}-{}'.format(i, i+1))
        print(SSW_draw_matches(gph, instance))
        print(SSW_power_isclose_match(instance, breakpoint_power))
        print(purchased_power_isclose(instance, breakpoint_power))
        print(objective_is_right(breakpoint_power, data, instance))

def test_DSW_SOS2_between_BPs():
    break_file, empty_file = define_empty_file()
    powers, flow_rates = read_breakpoints(break_file, 'DSW')
    data = pd.read_pickle(empty_file)[0:23]

    for i in range(0, len(flow_rates)-1):
        data.DSW_demand = 0
        ratio = np.random.uniform(0.1, 0.9)
        gph = ratio * flow_rates[i] + (1-ratio) * flow_rates[i+1]
        breakpoint_power = ratio * powers[i] + (1-ratio) * powers[i+1]
        data.DSW_demand.iloc[0] = gph
        data.price = 1
        instance, results = run_main(data, 0)
        print('Breakpoint {}-{}'.format(i, i+1))
        print(DSW_draw_isclosematch(gph, instance))
        print(DSW_power_isclose_match(instance, breakpoint_power))
        print(purchased_power_isclose(instance, breakpoint_power))
        print(objective_is_right(breakpoint_power, data, instance))

def test_energy_utilized_SSW():
    break_file, empty_file = define_empty_file()
    powers, flow_rates = read_breakpoints(break_file, 'SSW')
    data = pd.read_pickle(empty_file)[0:23]
    gph = flow_rates[2]
    data.SSW_demand.iloc[0] = gph
    data.price = 1
    maxkW = 100
    maxkWh = 2.5 * maxkW
    instance, results = run_main(data, maxkWh, maxkW)
    print(SSW_draw_isclosematch(instance, gph))
    target = powers[2] - maxkW
    print(SSW_power_isclose_match(instance, powers[2]))
    print(purchased_power_isclose(instance, target))
    print(objective_is_right(target, data, instance))

def test_energy_SOC_tracks():
    break_file, empty_file = define_empty_file()
    powers, flow_rates = read_breakpoints(break_file, 'SSW')
    data = pd.read_pickle(empty_file)[0:23]
    gph = flow_rates[2]
    data.SSW_demand.iloc[0] = gph
    data.price = 1
    maxkW = 100
    maxkWh = 2.5 * maxkW
    initial = 0.5 * maxkWh
    final = initial - maxkW / 0.94
    instance, results = run_main(data, maxkWh, maxkW)
    print(SSW_draw_isclosematch(instance, gph))
    target = powers[2] - maxkW
    print(SSW_power_isclose_match(instance, powers[2]))
    print(purchased_power_isclose(instance, target))
    print(objective_is_right(target, data, instance))
    print(np.isclose(final, instance.stateOfCharge[1].value))

def test_solar_utilized_over_battery():
    break_file, empty_file = define_empty_file()
    powers, flow_rates = read_breakpoints(break_file, 'SSW')
    data = pd.read_pickle(empty_file)[0:23]
    gph = flow_rates[2]
    data.SSW_demand.iloc[0] = gph
    data.solar[0] = powers[2]
    data.price = 1
    maxkW = 100
    maxkWh = 2.5 * maxkW
    initial = 0.5 * maxkWh
    final = initial
    instance, results = run_main(data, maxkWh, maxkW)
    print(SSW_draw_isclosematch(instance, gph))
    print(np.isclose(instance.curtailedPower[0].value, 0, rtol=1e-2), instance.curtailedPower[0].value)
    print(np.isclose(instance.chargePower[0].value, 0))
    print(np.isclose(instance.dischargePower[0].value, 0), instance.dischargePower[0].value)
    print(instance.beta_SSW[2, 0].value, instance.beta_SSW[3, 0].value)
    print(SSW_power_isclose_match(instance, powers[2]))
    print(purchased_power_isclose(instance, 0))
    print(objective_is_right(0, data, instance))
    print(final_SOC_isclose(final, instance))

def test_excess_solar_curtailed():
    break_file, empty_file = define_empty_file()
    powers, flow_rates = read_breakpoints(break_file, 'SSW')
    data = pd.read_pickle(empty_file)[0:23]
    gph = flow_rates[2]
    data.SSW_demand.iloc[0] = gph
    data.solar[0] = powers[2] * 2
    data.price = 1
    maxkW = 100
    maxkWh = 2.5 * maxkW
    initial = 0.5 * maxkWh
    final = initial
    instance, results = run_main(data, maxkWh, maxkW)
    print(SSW_draw_isclosematch(instance, gph))
    target = powers[2] - maxkW
    print(SSW_power_isclose_match(instance, powers[2]))
    print(purchased_power_isclose(instance, 0))
    print(objective_is_right(0, data, instance))
    print(final_SOC_isclose(final, instance))

def test_charge_before_curtailing():
    pass

# endregion

# region Additional Methods
def read_breakpoints(break_file, sheet_name):
    SSW_points = pd.read_excel(break_file, sheet_name=sheet_name)
    P_SSW = SSW_points.kW
    m_SSW = SSW_points.gph
    return P_SSW, m_SSW

def final_SOC_isclose(final, instance):
    value = instance.stateOfCharge[1].value
    print(value)
    return np.isclose(final, value)

def define_empty_file():
    empty_file = 'empty_index'
    break_file = 'sample_pump_eff.xlsx'
    return break_file, empty_file


def objective_is_right(breakpoint_SSW_power, data, instance):
    objective = value(instance.objective)
    target = breakpoint_SSW_power * data.price[0]
    return np.isclose(objective, target)


def purchased_power_isclose(instance, target):
    value = instance.purchasedPower[0].value
    return np.isclose(value, target)


def SSW_power_isclose_match(instance, target):
    value = instance.SSW_power[0].value
    print(value, target)
    return np.isclose(value, target)

def SSW_draw_isclosematch(instance, target):
    value = instance.SSW_draw[0].value
    return np.isclose(value, target)

def DSW_power_isclose_match(instance, target):
    value = instance.DSW_power[0].value
    # print(value)
    return np.isclose(value, target)

def DSW_draw_isclosematch(target, instance):
    value = instance.DSW_draw[0].value
    # print(value)
    return np.isclose(value, target)

def SSW_draw_matches(target, instance):
    return instance.SSW_draw[0].value == target
# endregion

if __name__ == "__main__":
    # test_SSW_SOS2_at_BPs()
    # test_DSW_SOS2_at_BPs()
    # test_SSW_SOS2_between_BPs()
    # test_DSW_SOS2_between_BPs()
    # test_energy_utilized_SSW()
    # test_energy_SOC_tracks()
    # test_solar_utilized_over_battery()
    test_excess_solar_curtailed()
