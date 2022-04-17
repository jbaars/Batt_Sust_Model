from .batpac_solver import *


def get_inventory_cell(parameter_dict, dict_df_batpac):
    """Bills of material of a single cell in gram based on updated BatPaC value

    Returns:
        dictionary of cell components and values in gram
    """

    df_D = dict_df_batpac["df_design"]  # shortcut design sheet
    df_L = dict_df_batpac["df_list"]  # shortcut list sheet
    column = battery_design_column(parameter_dict["vehicle_type"]["value"])
    cell_container_volume = (
        df_D.loc[306, column] + 2 * df_D.loc[81, column] + df_D.loc[75, column]
    ) * (df_D.loc[307, column] - 2 * df_D.loc[87, column]) + (
        df_D.loc[306, column] + df_D.loc[75, column]
    ) * (
        df_D.loc[307, column] - 2 * df_D.loc[87, column]
    )
    dict_cell_inventory = {
        "cell": df_D.loc[77, column],
        "separator": df_D.loc[65, column] * df_D.loc[65, "E"] * df_D.loc[65, "F"],
        "electrolyte": df_D.loc[66, "F"] * df_D.loc[66, column] * 1000,
        "cell_container": df_D.loc[76, column],
        "cell_neg_terminal": df_D.loc[69, column],
        "cell_pos_terminal": df_D.loc[68, column],
        "cathode_foil": df_D.loc[63, "E"] * df_D.loc[63, "F"] * df_D.loc[63, column],
        "cathode_coating": df_D.loc[48, column],
        "cathode_am": df_D.loc[44, column],
        "cathode_carbon": df_D.loc[45, column],
        "cathode_binder": df_D.loc[46, column],
        "anode_foil": df_D.loc[64, "E"] * df_D.loc[64, "F"] * df_D.loc[64, column],
        "anode_coating": df_D.loc[55, column],
        "anode_am": df_D.loc[51, column],
        "anode_carbon": df_D.loc[52, column],
        "anode_binder": df_D.loc[53, column],
        "cell_container_PET": cell_container_volume
        * df_D.loc[71, column]
        * df_L.loc["Density of PET", "Value"]
        / 1000000,
        "cell_container_PP": cell_container_volume
        * df_D.loc[72, column]
        * df_L.loc["Density of PP", "Value"]
        / 1000000,
        "cell_container_Al": cell_container_volume
        * df_D.loc[70, column]
        * df_L.loc["Density of Al", "Value"]
        / 1000000,
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
        "cell_interconnect": df_D.loc[317, column] / 1000,
        "module_polymer_panels": df_D.loc[323, column] / 1000,
        "module_tabs": df_D.loc[327, column] / 1000,  # Cu
        "module_terminal": df_D.loc[331, column] / 1000,
        "module_conductors": df_D.loc[336, column] / 1000,
        "module_spacers": df_D.loc[344, column] / 1000,
        "module_enclosure": df_D.loc[343, column] / 1000,
        "module_soc_regulator": df_D.loc[339, column] / 1000,
        "module_total": df_D.loc[352, column]
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
        "coolant": df_D.loc[401, column],
        "pack_packaging_fe": df_D.loc[418, column],
        "pack_packaging_al": df_D.loc[419, column]
        + df_D.loc[426, column],  # includes base + top
        "pack_packaging_insulation": (
            df_D.loc[410, column] * df_D.loc[420, column] * 0.032
        )
        + (
            df_D.loc[427, column] * df_D.loc[410, column] * 0.032
        ),  # density insulation: 0.032
        
        "pack_packaging_total": df_D.loc[421, column] + df_D.loc[428, column],
        "module_row_rack": df_D.loc[386, column]
        * df_D.loc[28, column],  # all steel, new in V5
        "module_interconnect_total": df_D.loc[434, column]
        * (df_D.loc[29, column] + 1)  # Cu
        / 1000,  # plus 1 module interconnect
        "module_bus_bar": df_D.loc[435, column] / 1000,
        "pack_terminals": df_D.loc[436, column] / 1000,  # 90% Cu, 10% seal material
        "pack_heaters": df_D.loc[438, column],
        "cooling_panels": df_D.loc[393, column],  # new in v5. Steel
        "cooling_mains_fe": df_D.loc[398, column] / 1000,  # new in v5. stainless steel
        "cooling_connectors": df_D.loc[399, column] / 1000,  # new in v5. steel
        "BMS": df_D.loc[440, column],
        "pack": df_D.loc[475, column],
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
        "cell_capacity_ah": df_D.loc[35, column],
        "cell_nominal_voltage":(df_D.loc[359, column]/(df_D.loc[29, column]/df_D.loc[30, column]))/(df_D.loc[25, column]/df_D.loc[26, column]),
        "module_capacity_ah": df_D.loc[36, column],
        "module_nominal_voltage":df_D.loc[359, column]/(df_D.loc[29, column]/df_D.loc[30, column]),
        "pack_capacity_ah": df_D.loc[355, column],
        "pack_nominal_voltage": df_D.loc[359, column],
        "pack_power_kW": df_D.loc[361, column],
        "pack_energy_kWh": df_D.loc[356, column],
        "pack_usable_energy_kWh": df_D.loc[357, column],
        "power_to_energy_kw/kWh": df_D.loc[473, column],
        "specific_energy_cell_Wh/kg": df_D.loc[481, column],
        "energy_density_cell_Wh/L": df_D.loc[482, column],
        "specific_energy_pack_Wh/kg": df_D.loc[483, column],
        "energy_density_pack_Wh/L": df_D.loc[484, column],
        "Vehicle_range_km": df_D.loc[455, column] * 1.609344,
        "cells_per_pack": df_D.loc[31, column],
        "cells_per_module": df_D.loc[25, column],
        "modules_per_pack": df_D.loc[29, column],
        "total_packs_vehicle": df_D.loc[12, column],
        "cell_volume": df_D.loc[308, column],
        "cell_group_interconnect": df_D.loc[317, column] * df_D.loc[29, column] / 1000,
        # "module_interconnect": df_D.loc[72, column]
        # + 1,  # see Manufacturing cost calculation row 99
        # "current_capacity_pack_terminal": round(
        #     df_D.loc[432, column], -2
        # ),  # Round, same as in BatPaC
        "cost_pack_heating_thermal": df_C.loc[164, column]  # baseline thermal system
        + df_C.loc[165, column],  # Heating system
        "battery_management_system_cost": df_C.loc[167, column],
        "total_bus_bars": total_busbars_packs(df_D, column),
        "cell_length": df_D.loc[307, column],
        "cell_width": df_D.loc[306, column],
        "cell_thickness": df_D.loc[81, column],
        "module_length": df_D.loc[348, column],
        "module_width": df_D.loc[349, column],
        "module_height": df_D.loc[350, column],
        "pack_length": df_D.loc[405, column],
        "pack_width": df_D.loc[406, column],
        "pack_height": df_D.loc[407, column],
        "system_volume": df_D.loc[442, column],
        "positive_electrode_thickness": df_D.loc[462, column],
        "battery_system_weight": df_D.loc[475, column],
        "charge_time": df_D.loc[249, column],
        "cell_container_al_layer": cell["cell_container_Al"],
        "cell_container_pet_layer": cell["cell_container_PET"],
        "cell_container_pp_layer": cell["cell_container_PP"],
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
    if df_D.loc[435, column] > 0:
        return 1
    else:
        return 0


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
        "cell": cell["cell"],
        "modules":module['module_total'],
        "cathode binder (PVDF)": cell["cathode_binder"],
        "cathode carbon black": cell["cathode_carbon"],
        "anode binder additive (SBR)": cell["anode_binder"]
        * cmc_quantity(param_dict)["sbr"],
        "anode binder (CMC)": cell["anode_binder"] * cmc_quantity(param_dict)["cmc"],
        "anode carbon black": cell["anode_carbon"],
        "cell terminal anode": cell["cell_neg_terminal"],
        "cell terminal cathode": cell["cell_pos_terminal"],
        "cell container": cell["cell_container"],
        "cell container Al layer": cell["cell_container_Al"],
        "cell container PET layer": cell["cell_container_PET"],
        "cell container PP layer": cell["cell_container_PP"],
        "module container": module["module_enclosure"],
        "module electronics": module["module_soc_regulator"],
        "module terminal": module["module_terminal"],
        "module thermal conductor": module["module_conductors"],
        "gas release": module["module_spacers"],
        "cell group interconnect": module["cell_interconnect"],
        "module polymer panels": module["module_polymer_panels"],
        "module tabs": module["module_tabs"],
        "battery jacket": pack["pack_packaging_total"],
        "battery jacket Al": pack["pack_packaging_al"],
        "battery jacket Fe": pack["pack_packaging_fe"],
        "battery jacket insulation": pack["pack_packaging_insulation"],
        "module row rack": pack["module_row_rack"],
        "module interconnects": pack["module_interconnect_total"],
        "pack terminals": pack["pack_terminals"],
        "pack heater": pack["pack_heaters"],
        "busbar": pack["module_bus_bar"],
        "coolant": pack["coolant"],
        "cooling panels": pack["cooling_panels"],
        "cooling mains Fe": pack["cooling_mains_fe"],
        "cooling connectors": pack["cooling_connectors"],
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
        **separator_name(param_dict, dict_df_batpac,value=cell["separator"]),
        **electrolyte_name(parameter_dict, value=cell["electrolyte"]),
    }

    return dict(sorted(dict_material_content_pack.items()))


def current_collector_name(param_dict, dict_df_batpac, values):
    """Returns a dictionary of the current collector name based on material and thickness and their quantities"""
    cath_range = [
        int(x) for x in param_dict["positive_foil_thickness"]["range"].split(",")
    ]
    cath_material = dict_df_batpac["df_design"].loc[63, "D"]
    cath_thickness = int(dict_df_batpac["df_design"].loc[63, "E"])
    ano_range = [
        int(x) for x in param_dict["negative_foil_thickness"]["range"].split(",")
    ]
    ano_material = dict_df_batpac["df_design"].loc[64, "D"]
    ano_thickness = int(dict_df_batpac["df_design"].loc[64, "E"])

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
        if "Power" in am:
            am = am.strip(" (Power)")
            selected_am = param_dict["electrode_pair"]["value"].strip(" (Power)")
        elif "Energy" in am:
            am = am.strip(" (Energy)")
            selected_am = param_dict["electrode_pair"]["value"].strip(" (Energy)")
        if selected_am == am:
            name = am.strip("-G")
            return_dict[f"cathode active material ({name})"] = value
        else:

            name = am.strip("-G")
            return_dict[f"cathode active material ({name})"] = 0
    return return_dict


def separator_name(param_dict, dict_df_batpac, value):
    """Returns a dictionary of all separator types and values (zero for none)"""
    sep_film_thickness = param_dict["sep_film_thickness"]["value"]
    sep_film_range = [
        int(x) for x in param_dict["sep_film_thickness"]["range"].split(",")
    ]
    sep_coat_thickness = param_dict["sep_coat_thickness"]["value"]
    sep_coat_range = [
        int(x) for x in param_dict["sep_coat_thickness"]["range"].split(",")
    ][1:]
    return_dict = {}
    if sep_film_thickness == None: #if separator thickness not defined as input parameter
        sep_film_thickness = int(dict_df_batpac["df_design"].loc[65, "E"])
    # Separator types with coating:
    for foil in sep_film_range:
        for coat in sep_coat_range:
            if coat == 3 and foil != 9:  # 3 um coating only for foil with 9um
                continue
            elif coat == 2 and foil == 9:  # 2 um coating not for 9 um foil
                continue
            elif sep_coat_thickness is not None and sep_coat_thickness != 0:
                if coat == sep_coat_thickness and foil == sep_film_thickness:
                    return_dict[f"coated separator ({foil}um+{coat}um)"] = value
                else:
                    return_dict[f"coated separator ({foil}um+{coat}um)"] = 0
            else:
                return_dict[f"coated separator ({foil}um+{coat}um)"] = 0
    # Separator types without coating:
    for foil in sep_film_range:
        if sep_coat_thickness is None or sep_coat_thickness == 0:
            if foil == sep_film_thickness:
                return_dict[f"separator ({foil}um)"] = value  #
            else:
                return_dict[f"separator ({foil}um)"] = 0
        else:
            return_dict[f"separator ({foil}um)"] = 0

    return return_dict


def electrolyte_name(parameter_dict, value):
    """Returns a dict of the electrolyte type (NMC & NCA, LFP or LMO) and the parameter values
    based on the name of the cathode active material.
    """
    cath_am = parameter_dict["electrode_pair"]["value"]
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

 