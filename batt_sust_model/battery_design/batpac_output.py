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
        df_D.loc[303, column] + 2 * df_D.loc[80, column] + df_D.loc[74, column]
    ) * (df_D.loc[304, column] - 2 * df_D.loc[86, column]) + (
        df_D.loc[303, column] + df_D.loc[74, column]
    ) * (
        df_D.loc[304, column] - 2 * df_D.loc[86, column]
    )
    dict_cell_inventory = {
        "cell": df_D.loc[76, column],
        "separator": df_D.loc[64, column] * df_D.loc[64, "E"] * df_D.loc[64, "F"],
        "electrolyte": df_D.loc[65, "F"] * df_D.loc[65, column] * 1000,
        "cell_container": df_D.loc[75, column],
        "cell_neg_terminal": df_D.loc[68, column],
        "cell_pos_terminal": df_D.loc[67, column],
        "cathode_foil": df_D.loc[62, "E"] * df_D.loc[62, "F"] * df_D.loc[62, column],
        "cathode_coating": df_D.loc[47, column],
        "cathode_am": df_D.loc[43, column],
        "cathode_carbon": df_D.loc[44, column],
        "cathode_binder": df_D.loc[45, column],
        "anode_foil": df_D.loc[63, "E"] * df_D.loc[63, "F"] * df_D.loc[63, column],
        "anode_coating": df_D.loc[54, column],
        "anode_am": df_D.loc[50, column],
        "anode_carbon": df_D.loc[51, column],
        "anode_binder": df_D.loc[52, column],
        "cell_container_PET": cell_container_volume
        * df_D.loc[70, column]
        * df_L.loc["Density of PET", "Value"]
        / 1000000,
        "cell_container_PP": cell_container_volume
        * df_D.loc[71, column]
        * df_L.loc["Density of PP", "Value"]
        / 1000000,
        "cell_container_Al": cell_container_volume
        * df_D.loc[69, column]
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
        "cell_interconnect": df_D.loc[314, column] / 1000,
        "module_polymer_panels": df_D.loc[320, column] / 1000,
        "module_tabs": df_D.loc[324, column] / 1000,  # Cu
        "module_terminal": df_D.loc[328, column] / 1000,
        "module_conductors": df_D.loc[333, column] / 1000,
        "module_spacers": df_D.loc[341, column] / 1000,
        "module_enclosure": df_D.loc[340, column] / 1000,
        "module_soc_regulator": df_D.loc[336, column] / 1000,
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
        "coolant": df_D.loc[397, column],
        "pack_packaging_fe": df_D.loc[414, column],
        "pack_packaging_al": df_D.loc[415, column]
        + df_D.loc[422, column],  # includes base + top
        "pack_packaging_insulation": (
            df_D.loc[406, column] * df_D.loc[416, column] * 0.032
        )
        + (
            df_D.loc[423, column] * df_D.loc[406, column] * 0.032
        ),  # density insulation: 0.032
        "pack_packaging_total": df_D.loc[417, column] + df_D.loc[424, column],
        "module_row_rack": df_D.loc[382, column]
        * df_D.loc[26, column],  # all Fe, new in V5
        "module_interconnect_total": df_D.loc[430, column]
        * (df_D.loc[28, column] + 1)  # Cu
        / 1000,  # plus 1 module interconnect
        "module_bus_bar": df_D.loc[431, column] / 1000,
        "pack_terminals": df_D.loc[432, column] / 1000,  # 90% Cu, 10% seal material
        "pack_heaters": df_D.loc[434, column],
        "cooling_panels": df_D.loc[389, column],  # new in v5. Steel
        "cooling_mains_fe": df_D.loc[394, column] / 1000,  # new in v5. stainless steel
        "cooling_connectors": df_D.loc[395, column] / 1000,  # new in v5. steel
        "BMS": df_D.loc[436, column],
        "pack": df_D.loc[471, column],
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
        "cell_capacity_ah": df_D.loc[34, column],
        "module_capacity_ah": df_D.loc[35, column],
        # "module_bms_capacity_total": df_D.loc[81, column] * df_D.loc[74, column],
        "cell_container_al_layer": cell["cell_container_Al"],
        "cell_container_pet_layer": cell["cell_container_PET"],
        "cell_container_pp_layer": cell["cell_container_PP"],
        "pack_voltage": df_D.loc[356, column],
        "pack_capacity_ah": df_D.loc[352, column],
        "pack_power_kW": df_D.loc[357, column],
        "pack_energy_kWh": df_D.loc[353, column],
        "pack_usable_energy_kWh": df_D.loc[354, column],
        "power_to_energy_kw/kWh": df_D.loc[469, column],
        "specific_energy_cell_Wh/kg": df_D.loc[477, column],
        "energy_density_cell_Wh/L": df_D.loc[478, column],
        "specific_energy_pack_Wh/kg": df_D.loc[479, column],
        "energy_density_pack_Wh/L": df_D.loc[480, column],
        "battery_capacity": df_D.loc[353, column],
        "Vehicle_range_km": df_D.loc[451, column] * 1.609344,
        "cells_per_pack": df_D.loc[31, column],
        "cells_per_module": df_D.loc[24, column],
        "modules_per_pack": df_D.loc[28, column],
        "total_packs_vehicle": df_D.loc[12, column],
        "cell_volume": df_D.loc[305, column],
        "cell_group_interconnect": df_D.loc[314, column] * df_D.loc[28, column] / 1000,
        # "module_interconnect": df_D.loc[72, column]
        # + 1,  # see Manufacturing cost calculation row 99
        # "current_capacity_pack_terminal": round(
        #     df_D.loc[432, column], -2
        # ),  # Round, same as in BatPaC
        "cost_pack_heating_thermal": df_C.loc[163, column]  # baseline thermal system
        + df_C.loc[164, column],  # Heating system
        "battery_management_system_cost": df_C.loc[166, column],
        "total_bus_bars": total_busbars_packs(df_D, column),
        "cell_length": df_D.loc[304, column],
        "cell_width": df_D.loc[303, column],
        "cell_thickness": df_D.loc[80, column],
        "module_length": df_D.loc[345, column],
        "module_width": df_D.loc[346, column],
        "module_height": df_D.loc[347, column],
        "pack_length": df_D.loc[401, column],
        "pack_width": df_D.loc[402, column],
        "pack_height": df_D.loc[403, column],
        "system_volume": df_D.loc[438, column],
        "positive_electrode_thickness": df_D.loc[458, column],
        "battery_system_weight": df_D.loc[471, column],
        "fast_charge": parameter_dict['calculate_fast_charge']['value'],
        "charge_time": df_D.loc[248, column]
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
    if df_D.loc[431, column] > 0:
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
    cath_material = dict_df_batpac["df_design"].loc[62, "D"]
    cath_thickness = int(dict_df_batpac["df_design"].loc[62, "E"])
    ano_range = [
        int(x) for x in param_dict["negative_foil_thickness"]["range"].split(",")
    ]
    ano_material = dict_df_batpac["df_design"].loc[63, "D"]
    ano_thickness = int(dict_df_batpac["df_design"].loc[63, "E"])

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
        sep_film_thickness = int(dict_df_batpac["df_design"].loc[64, "E"])
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

 