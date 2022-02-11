from .batpac_solver import *


def get_inventory_cell(parameter_dict, dict_df_batpac):
    """Bills of material of a single cell in gram based on updated BatPaC value

    Returns:
        dictionary of cell components and values in gram
    """

    df_D = dict_df_batpac["df_design"]  # shortcut design sheet
    df_L = dict_df_batpac["df_list"]  # shortcut list sheet
    column = battery_design_column(parameter_dict["vehicle_type"]["value"])
    dict_cell_inventory = {
        "cell": df_D.loc[31, column],
        "separator": df_D.loc[23, column] * df_D.loc[23, "E"] * df_D.loc[23, "F"],
        "electrolyte": df_D.loc[24, "F"] * df_D.loc[24, column] * 1000,
        "cell_container": df_D.loc[30, column],
        "cathode": df_D.loc[13, column]
        + (df_D.loc[21, "E"] * df_D.loc[21, "F"] * df_D.loc[21, column]),
        "anode": df_D.loc[19, column]
        + (df_D.loc[22, "E"] * df_D.loc[22, "F"] * df_D.loc[22, column]),
        "cell_neg_terminal": df_D.loc[26, column],
        "cell_pos_terminal": df_D.loc[25, column],
        "cathode_foil": df_D.loc[21, "E"] * df_D.loc[21, "F"] * df_D.loc[21, column],
        "cathode_coating": df_D.loc[13, column],
        "cathode_am": df_D.loc[9, column],
        "cathode_carbon": df_D.loc[10, column],
        "cathode_binder": df_D.loc[11, column],
        "anode_foil": df_D.loc[22, "E"] * df_D.loc[22, "F"] * df_D.loc[22, column],
        "anode_coating": df_D.loc[19, column],
        "anode_am": df_D.loc[15, column],
        "anode_carbon": df_D.loc[16, column],
        "anode_binder": df_D.loc[17, column],
        "cell_container_PET": (df_D.loc[120, column] + 2 * df_D.loc[35, column] + 6)
        * (df_D.loc[121, column] - 6)
        * df_D.loc[28, column]
        * 2
        / 1000
        * 30
        * df_L.loc["Density of PET", "Value"]  # Thickness of PET in container is 30um
        / df_D.loc[28, column]
        / 1000,
        "cell_container_PP": (df_D.loc[120, column] + 2 * df_D.loc[35, column] + 6)
        * (df_D.loc[121, column] - 6)
        * df_D.loc[28, column]
        * 2
        / 1000
        * 20
        * df_L.loc["Density of PP", "Value"]
        / df_D.loc[28, column]  # Thickness of PP in container is 20um
        / 1000,
        "cell_container_Al": (df_D.loc[120, column] + 2 * df_D.loc[35, column] + 6)
        * (df_D.loc[121, column] - 6)
        * df_D.loc[28, column]
        * 2
        / 1000
        * df_D.loc[27, column]
        * df_L.loc["Density of Al", "Value"]
        / df_D.loc[28, column]
        / 1000,
    }
    return dict_cell_inventory


def get_inventory_module(parameter_dict, dict_df_batpac):
    """Inventory of a single module without cell components based on updated BatPaC value

    Returns:
        dictionary of module components and values in kilogram
    """
    df_D = dict_df_batpac["df_design"]
    column = battery_design_column(parameter_dict["vehicle_type"]["value"])
    dict_module_inventory = {
        "module": df_D.loc[144, column],
        "cell_interconnect": df_D.loc[125, column] * df_D.loc[68, column] / 1000,
        "module_soc_regulator": df_D.loc[126, column] / 1000,
        "module_terminal": df_D.loc[129, column] / 1000,
        "module_conductors": df_D.loc[136, column] / 1000,
        "module_spacers": df_D.loc[137, column] / 1000,
        "module_enclosure": df_D.loc[138, column] / 1000,
        "module_cells": df_D.loc[31, column] * df_D.loc[68, column] / 1000,
    }
    return dict_module_inventory


def get_inventory_pack(parameter_dict, dict_df_batpac):
    """Inventory of single pack excluding cell and module components based on updated BatPaC value

    Returns:
        dictionary of module components and values in kilogram
    """
    df_D = dict_df_batpac["df_design"]  # shortcut design sheet
    column = battery_design_column(parameter_dict["vehicle_type"]["value"])
    dict_pack_inventory = {
        "coolant": df_D.loc[174, column],
        "pack_packaging": df_D.loc[175, column] * df_D.loc[176, column] / 1000,
        "module_compression_plates": df_D.loc[167, column] / 1000,
        "module_interconnect_total": df_D.loc[166, column]
        * (df_D.loc[72, column] + 1)
        / 1000,  # plus 1 module interconnect
        "module_bus_bar": df_D.loc[168, column] / 1000,
        "pack_terminals": df_D.loc[171, column] / 1000,
        "pack_heaters": df_D.loc[173, column],
        "pack_ac_extension": df_D.loc[177, column],
        "BMS": df_D.loc[179, column],
        "pack": df_D.loc[180, column],
    }
    return dict_pack_inventory


def get_parameters_vehicle_model(dict_df_batpac):
    """Vehicle parameters calculated with the vehicle model"""
    if isinstance(dict_df_batpac["df_veh_model"], pd.DataFrame):
        df = dict_df_batpac["df_veh_model"]
        return_dict = {
            "glider_weight": df.loc[1, "Glider"],
            "transmission_weight": df.loc[1, "Transmission"],
            "battery_system_weight": df.loc[1, "Battery system"],
            "motor_controller_weight": df.loc[1, "Motor/Generator/Controller"],
            "vehicle_weight": df.loc[1, "Total weight"],
        }
        return return_dict
    else:
        return


def get_parameter_general(parameter_dict, dict_df_batpac):
    """General battery parameters used for cost calculation"""
    df_D = dict_df_batpac["df_design"]
    df_C = dict_df_batpac["df_manufacturing_cost"]

    cell = get_inventory_cell(parameter_dict, dict_df_batpac)
    column = battery_design_column(parameter_dict["vehicle_type"]["value"])

    dict_performance = {
        "electrode_pair": parameter_dict["electrode_pair"]["value"],
        "cell_capacity_ah": df_D.loc[82, column],
        "module_capacity_ah": df_D.loc[81, column],
        "module_bms_capacity_total": df_D.loc[81, column] * df_D.loc[74, column],
        "cell_container_al_layer": cell["cell_container_Al"],
        "cell_container_pet_layer": cell["cell_container_PET"],
        "cell_container_pp_layer": cell["cell_container_PP"],
        "pack_voltage": df_D.loc[60, column],
        "pack_capacity_ah": df_D.loc[196, column],
        "pack_power_kW": df_D.loc[208, column],
        "pack_energy_kWh": df_D.loc[209, column],
        "pack_usable_energy_kWh": df_D.loc[211, column],
        "power_to_energy_kw/kWh": df_D.loc[210, column],
        "specific_energy_cell_Wh/kg": df_D.loc[216, column],
        "energy_density_cell_Wh/L": df_D.loc[217, column],
        "specific_energy_pack_Wh/kg": df_D.loc[218, column],
        "energy_density_pack_Wh/L": df_D.loc[219, column],
        "battery_capacity": df_D.loc[209, column],
        "Vehicle_range_km": df_D.loc[193, column] * 1.609344,
        "cells_per_pack": df_D.loc[74, column],
        "cells_per_module": df_D.loc[68, column],
        "modules_per_pack": df_D.loc[72, column],
        "total_packs_vehicle": df_D.loc[56, column],
        "cell_area": df_D.loc[112, column],
        "positive_am_per_cell": df_D.loc[9, column],
        "negative_am_per_cell": df_D.loc[15, column],
        "cell_group_interconnect": df_D.loc[68, column] / df_D.loc[69, column] * 2,
        "module_interconnect": df_D.loc[72, column]
        + 1,  # see Manufacturing cost calculation row 99
        "current_capacity_pack_terminal": round(
            df_D.loc[165, column], -2
        ),  # Round, same as in BatPaC
        "cost_pack_heating_thermal": df_C.loc[105, column]  # baseline thermal system
        + df_C.loc[120, column]  # Additional cost to AC system
        + df_C.loc[106, column],  # Heating system
        "battery_management_system_cost": df_C.loc[113, column],
        "total_bus_bars": total_busbars_packs(df_D, column),
        "cell_length": df_D.loc[121, column],
        "cell_width": df_D.loc[120, column],
        "cell_thickness": df_D.loc[35, column],
        "module_length": df_D.loc[140, column],
        "module_width": df_D.loc[141, column],
        "module_height": df_D.loc[142, column],
        "pack_length": df_D.loc[157, column],
        "pack_width": df_D.loc[158, column],
        "pack_height": df_D.loc[159, column],
        "system_volume": df_D.loc[181, column],
        "positive_electrode_thickness": df_D.loc[199, column],
    }
    # Include BatPaC input parameters:
    input_param = {}
    for param in parameter_dict.keys():
        if parameter_dict[param]["value"] is not None:
            input_param[param] = parameter_dict[param]["value"]
    # Include vehicle model results, if included:
    veh_parameters = get_parameters_vehicle_model(dict_df_batpac)
    if veh_parameters != None:
        dict_performance.update(veh_parameters)

    return {**dict_performance, **input_param}


def total_busbars_packs(design_sheet, column):
    """Returns total busbars required for module and pack interconnects"""
    df_D = design_sheet
    busbar = 0
    if (
        df_D.loc[71, column] == 1 and df_D.loc[70, column] > 0
    ):  # packs with one row of modules
        busbar += 1
    if df_D.loc[73, column] > 1:  # packs with parallel modules
        busbar += df_D.loc[73, column]
    if df_D.loc[56, column] > 1:  # interconnected battery packs
        busbar += df_D.loc[56, column]
    return busbar


def components_content_pack(parameter_dict, dict_df_batpac):
    """Components in battery pack based on updated BatPaC parameters.

    This function is used to create the material content file: 3_MC_product_components.

    Returns:
          Dictionary of the material content of total pack in kg. Dict keys match classification file
    """
    param_dict = parameter_dict
    technical_info = get_parameter_general(parameter_dict, dict_df_batpac)
    cell = get_inventory_cell(parameter_dict, dict_df_batpac)
    pack = get_inventory_pack(parameter_dict, dict_df_batpac)
    module = get_inventory_module(parameter_dict, dict_df_batpac)

    total_cell = technical_info["cells_per_pack"]
    total_modules = technical_info["modules_per_pack"]

    cell.update(
        (key, value * total_cell / 1000) for key, value in cell.items()
    )  # weight of all cells components in battery pack (kg)
    module.update((key, value * total_modules) for key, value in module.items())

    silicon_anode = param_dict["silicon_anode"]["value"] / 100
    dict_material_content_pack = {
        "battery pack": pack["pack"],
        "cathode binder (PVDF)": cell["cathode_binder"],
        "cathode carbon black": cell["cathode_carbon"],
        "anode binder additive (SBR)": cell["anode_binder"]
        * cmc_quantity(param_dict)["sbr"],
        "anode binder (CMC)": cell["anode_binder"] * cmc_quantity(param_dict)["cmc"],
        "anode carbon black": cell["anode_carbon"],
        "cell": cell["cell"],
        "cell terminal anode": cell["cell_neg_terminal"],
        "cell terminal cathode": cell["cell_pos_terminal"],
        "cell container": cell["cell_container"],
        "cell container Al layer": cell["cell_container_Al"],
        "cell container PET layer": cell["cell_container_PET"],
        "cell container PP layer": cell["cell_container_PP"],
        "module container": module["module_enclosure"],
        "module terminal": module["module_terminal"],
        "module thermal conductor": module["module_conductors"],
        "gas release": module["module_spacers"],
        "module electronics": module["module_soc_regulator"],
        "cell group interconnect": module["cell_interconnect"],
        "battery jacket": pack["pack_packaging"],
        "module compression plates": pack["module_compression_plates"],
        "module interconnects": pack["module_interconnect_total"],
        "pack terminals": pack["pack_terminals"],
        "pack heater": pack["pack_heaters"],
        "busbar": pack["module_bus_bar"],
        "coolant": pack["coolant"],
        "battery management system": pack["BMS"],
        "anode active material (synthetic graphite)": 1
        * cell["anode_am"]
        * (1 - silicon_anode)
        if param_dict["graphite_type"]["value"] == "synthetic"
        else 0,
        "anode active material (natural graphite)": 1
        * cell["anode_am"]
        * (1 - silicon_anode)
        if param_dict["graphite_type"]["value"] == "natural"
        else 0,
        "anode active material (SiO)": cell["anode_am"] * silicon_anode,
        **current_collector_name(parameter_dict, dict_df_batpac, values=cell),
        **cathode_active_material(parameter_dict, value=cell["cathode_am"]),
        **separator_name(param_dict, value=cell["separator"]),
        **electrolyte_name(dict_df_batpac, value=cell["electrolyte"]),
    }

    return dict(sorted(dict_material_content_pack.items()))


def current_collector_name(param_dict, dict_df_batpac, values):
    """Returns a dictionary of the current collector name based on material and thickness and their quantities"""
    cath_range = [
        int(x) for x in param_dict["positive_foil_thickness"]["range"].split(",")
    ]
    cath_material = dict_df_batpac["df_design"].loc[21, "D"]
    cath_thickness = int(dict_df_batpac["df_design"].loc[21, "E"])
    ano_range = [
        int(x) for x in param_dict["negative_foil_thickness"]["range"].split(",")
    ]
    ano_material = dict_df_batpac["df_design"].loc[22, "D"]
    ano_thickness = int(dict_df_batpac["df_design"].loc[22, "E"])

    def get_values(foil_range, material, thickness, electrode_type, value):
        temp_return_dict = {}
        for foil in foil_range:
            name = f"{electrode_type} current collector {material} ({foil}um)"
            if foil == thickness:
                temp_return_dict[name] = value
            else:
                temp_return_dict[name] = 0
        return temp_return_dict

    return_dict = {
        **get_values(
            cath_range, cath_material, cath_thickness, "cathode", values["cathode_foil"]
        ),
        **get_values(
            ano_range, ano_material, ano_thickness, "anode", values["anode_foil"]
        ),
    }
    return return_dict


def cathode_active_material(param_dict, value):
    """Returns the name and value of all cathode active material choices"""

    range_am = param_dict["electrode_pair"]["range"].split(",")
    return_dict = {}
    for am in range_am:
        if param_dict["electrode_pair"]["value"] == am:
            name = am.strip("-G")
            return_dict[f"cathode active material ({name})"] = value
        else:
            name = am.strip("-G")
            return_dict[f"cathode active material ({name})"] = 0
    return return_dict


def separator_name(param_dict, value):
    """Returns a dictionary of all separator types and values (zero for none)"""
    sep_foil_thickness = param_dict["sep_foil_thickness"]["value"]
    sep_foil_range = [
        int(x) for x in param_dict["sep_foil_thickness"]["range"].split(",")
    ]
    sep_coat_thickness = param_dict["sep_coat_thickness"]["value"]
    sep_coat_range = [
        int(x) for x in param_dict["sep_coat_thickness"]["range"].split(",")
    ][1:]
    return_dict = {}
    # Separator types with coating:
    for foil in sep_foil_range:
        for coat in sep_coat_range:
            if coat == 3 and foil != 9:  # 3 um coating only for foil with 9um
                continue
            elif coat == 2 and foil == 9:  # 2 um coating not for 9 um foil
                continue
            elif sep_coat_thickness is not None and sep_coat_thickness != 0:
                if coat == sep_coat_thickness and foil == sep_foil_thickness:
                    return_dict[f"coated separator ({foil}um+{coat}um)"] = value
                else:
                    return_dict[f"coated separator ({foil}um+{coat}um)"] = 0
            else:
                return_dict[f"coated separator ({foil}um+{coat}um)"] = 0
    # Separator types without coating:
    for foil in sep_foil_range:
        if sep_coat_thickness is None or sep_coat_thickness == 0:
            if foil == sep_foil_thickness:
                return_dict[f"separator ({foil}um)"] = value  #
            else:
                return_dict[f"separator ({foil}um)"] = 0
        else:
            return_dict[f"separator ({foil}um)"] = 0

    return return_dict


def electrolyte_name(dict_df_batpac, value):
    """Returns a dict of the electrolyte type (NMC & NCA, LFP or LMO) and the parameter values
    based on the name of the cathode active material.
    """
    cath_am = dict_df_batpac["df_chem"].iloc[4, 0]
    return_dict = {}

    if "NMC" in cath_am or "NCA" in cath_am:
        return_dict["electrolyte (NMC/NCA)"] = value
        return_dict["electrolyte (LFP)"] = 0
        return_dict["electrolyte (LMO)"] = 0
        return return_dict
    elif "LMO" in cath_am and not "NMC" in cath_am:
        return_dict["electrolyte (NMC/NCA)"] = 0
        return_dict["electrolyte (LFP)"] = 0
        return_dict["electrolyte (LMO)"] = value
        return return_dict
    elif "LFP" in cath_am:
        return_dict["electrolyte (NMC/NCA)"] = 0
        return_dict["electrolyte (LFP)"] = value
        return_dict["electrolyte (LMO)"] = 0
        return return_dict
    else:
        raise ValueError(
            f"{cath_am} does not match NCA, NMC, LFP or LMO chemistry. Check name again or add new electrolyte type"
        )

        #
        # def mc_to_excel(mc_dictionary, datapath=None, overwrite_all=False, overwrite_design=False):
        # """ Returns Batpac generated values into ODYM material content (3_MC) excel sheet.
        # If overwrite is True deletes all previous values"""
        # if datapath is None:
        #     path = r'\3_MC_component_product.xlsx'
        # else:
        #     path = datapath + '\3_MC_component_product.xlsx'
        # name = list(mc_dictionary.keys())[0]
        #
        # try:
        #     wb = openpyxl.load_workbook(path)
        # except FileNotFoundError:  # make new xlsx file
        #     wb = openpyxl.Workbook()
        #     wb.save(path)
        # if overwrite_all is True:
        #     try:
        #         sheet = wb['Data']
        #         wb.remove(sheet)
        #         wb.save(path)
        #     except ValueError:
        #         pass
        # if 'Data' in wb.sheetnames:
        #     df = pd.read_excel(path, sheet_name='Data', index_col=0)
        #     if name in df.columns and overwrite_design is False:
        #         raise ValueError(
        #             f'{name} already present in 3_MC_component_product.xlsx, change design name or use overwrite_design=True to overwrite existing values')
        #     for key in mc_dictionary[name].keys():
        #         df.loc[key, name] = mc_dictionary[name][key]
        # else:
        #     df = pd.DataFrame.from_dict(mc_dictionary, orient='index')
        #
        # with pd.ExcelWriter(path, engine='openpyxl', mode='a') as writer:
        #     df.to_excel(writer, sheet_name='Data')
