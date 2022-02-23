import os

def generate_write_folder(solar_increment, transferMax, Battery_cost_kw, Battery_cost_kwh):
    Battery_cost_folder = '/ ${}_kW_${}_kWh'.format(Battery_cost_kw, Battery_cost_kwh)
    Solar_folder = '/ {}x_solar'.format(solar_increment)
    max_Transfer_limit_water_folder = '/ {}_max_transfer_of_water'.format(transferMax)
    variable_eff_folder = '/ variable_eff'

    write_folder = os.getcwd() + variable_eff_folder + Solar_folder + Battery_cost_folder + max_Transfer_limit_water_folder

    # if solar_increment == 1 and Battery_cost_kw != 0 and Battery_cost_kwh != 0 and transferMax == 100000:
    #
    #     write_folder = os.getcwd() + variable_eff_folder + Solar_folder + Battery_cost_folder
    #
    # elif solar_increment != 1 and Battery_cost_kw != 156 and Battery_cost_kwh != 408 or transferMax != 100000:
    #
    #     write_folder = os.getcwd() + variable_eff_folder + Solar_folder + Battery_cost_folder + max_Transfer_limit_water_folder
    # else:
    #
    #     write_folder = os.getcwd() + variable_eff_folder + Solar_folder + Battery_cost_folder + max_Transfer_limit_water_folder
    #

    return write_folder