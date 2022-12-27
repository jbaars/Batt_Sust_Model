from pathlib import Path
import pandas as pd
import re
import numpy as np
from tqdm import tqdm
import time

# Load default cost data
rel_path = "data/default_manufacturing_cost_parameters.xlsx"
parent = Path(__file__).parents[0]
workbook = pd.ExcelFile(parent / rel_path)
p_values_material = pd.read_excel(workbook, sheet_name="p_values_materials", index_col=0)["p_value"]
p_values_process = pd.read_excel(workbook, sheet_name="p_values_process", index_col=0).T
manuf_rate_base = pd.read_excel(workbook, sheet_name="default_manufacturing_rates", index_col=0).iloc[:, 0].to_dict()
base_factors = pd.read_excel(workbook, sheet_name="baseline_factors", index_col=0).T.drop("unit", axis=1)
volume_ratio_mapping = pd.read_excel(workbook, sheet_name="volume_ratio_mapping", index_col=0).iloc[:, 0].to_dict()
process_mapping = (
    pd.read_excel(workbook, sheet_name="process_mapping", index_col=0).loc[:, "foreground process"].to_dict()
)
cost_rates = pd.read_excel(workbook, sheet_name="cost_rates", index_col=0).loc[:, "value"].to_dict()
variable_overhead_labor = cost_rates["variable_overhead_labor"]
GSA_labour = cost_rates["GSA_labour"]
pack_profit = cost_rates["pack_profit"]
launch_cost_labor = cost_rates["launch_cost_labor"]
launch_cost_material = cost_rates["launch_cost_material"]
working_capital = cost_rates["working_capital"]
battery_warranty_costs = cost_rates["battery_warranty_costs"]
variable_overhead_depreciation = cost_rates["variable_overhead_depreciation"]
GSA_depreciation = cost_rates["GSA_depreciation"]
r_and_d = cost_rates["r_and_d"]
lifetime_capital_equipment = cost_rates["lifetime_capital_equipment"]


def calculate_depreciation(lifetime_capital_equipment):
    """Capital equipment and building equipment depreciation rates based lifetime of capital equipment as calculated in BatPaC

    Parameters
    ----------
    lifetime_capital_equipment : int
        lifetime in years

    Returns
    -------
    list
        depreciation rate (%) of the capital equipment and building investment
    """

    capital_equipment = lifetime_capital_equipment / 100
    building_investment = capital_equipment / 2
    return [capital_equipment, building_investment]


def parameter_to_brightway_name(parameter_name):
    """Convert parameter to name of parameters in Brightway"""
    new_name = re.sub("[^0-9a-zA-Z]+", "_", parameter_name)
    if new_name[-1] == "_":  # Remove underscore if last index
        new_name = new_name[0:-1]
    return new_name.lower()


def material_to_process_mapping(material, technology_matrix):
    """Returns battery production location of material input"""
    return_dict = {}
    for m in material:
        for process in technology_matrix.columns:
            if technology_matrix.loc[m, process] < 0:
                return_dict[m] = process
    return return_dict


def material_cost_matrix(
    technology_matrix,
    price_material_mass,
    price_material_unit,
    system_design_parameters,
    run_multiple=False,
    process_columns=None,
    material_rows=None,
    disable_tqdm=False,
    unit_material_to_process_mapping=None,
    overhead_multiplier=None,
):
    """Calculates the unit and mass cost of externally sourced materials for battery production

    Parameters
    ----------
    technology_matrix : df
        Technology matrix
    price_material_mass : df
        Mass prices of materials/energy
    price_material_unit : dict
        Unit prices of materials
    system_design_parameters : dict
        Battery design parameters, including process design
    run_multiple : bool, optional
        To calculate several designs, by default False
    process_columns : _type_, optional
        Process column order , by default None
    material_rows : _type_, optional
        Material/energy index order, by default None
    disable_tqdm : bool, optional
        Hides tqdm, by default False
    unit_material_to_process_mapping : _type_, optional
        To increase speed up when calculating several design, by default None
    overhead_multiplier : float, optional
        Changes the material overhead multiplier, by default None

    Returns
    -------
    DataFrame/NP array
        process cost matrix of externally sourced materials

    Raises
    ------
    ValueError
        _description_
    """
    # import default parameters:
    if run_multiple == False:
        sd_param = {}
        sd_param[0] = system_design_parameters
        disable_tqdm = True
        unit_material_to_process_mapping = material_to_process_mapping(price_material_unit.keys(), technology_matrix)
    if run_multiple == True:
        if process_columns == None or material_rows == None:
            raise ValueError("The process_columns and material_rows parameters are not defined!")
        sd_param = system_design_parameters
        nested_C_matrix = np.zeros((len(sd_param.keys()), technology_matrix.shape[1], technology_matrix.shape[2]))
        if disable_tqdm != False:
            disable_tqdm = True
        # if unit_material_to_process_mapping == None:
        unit_material_to_process_mapping = material_to_process_mapping(
            price_material_unit.keys(), pd.DataFrame(technology_matrix[0], material_rows, process_columns)
        )
    if overhead_multiplier == None:
        overhead_multiplier = material_overhead_multiplier()
    internal_processes = list(set(process_mapping.values()))

    for idx, design in tqdm(enumerate(sd_param.values()), total=len(sd_param), disable=disable_tqdm):
        if run_multiple == True:
            technology_matrix_temp = pd.DataFrame(technology_matrix[idx], columns=process_columns, index=material_rows)
        if run_multiple == False:
            technology_matrix_temp = technology_matrix

        unit_cost_dict = battery_material_cost_unit(price_material_unit, design)
        monetary_matrix = battery_material_cost_mass(technology_matrix_temp, price_material_mass)

        # Set all internal process to zero

        monetary_matrix[internal_processes] = 0
        # set price of battery jacket production to zero :
        monetary_matrix.loc[:, "battery jacket production"] = 0
        # Material unit costs are attributed to the receiving battery production process:
        materials = unit_material_to_process_mapping.keys()
        processes = list(set(unit_material_to_process_mapping.values()))

        monetary_matrix.loc[materials, processes] = (
            (abs(technology_matrix_temp.loc[materials, processes])).T * (pd.Series(unit_cost_dict))
        ).T

        # Append unit cost with P values (for scale of unit cost) to monetary A matrix:
        process_rate = modelled_process_rates(design)

        cell_materials = [
            "cell terminal anode",
            "cell terminal cathode",
            "cell container",
        ]
        module_materials = [
            "cell group interconnect",
            "module polymer panels",
            "module terminal",
            "module container",
            "gas release",
        ]
        pack_materials = [
            "cooling connectors",
            "cooling mains Fe",
            "pack terminals",
        ]
        monetary_matrix.loc[cell_materials, internal_processes] *= (
            manuf_rate_base["baseline_total_cell"] / process_rate["total_cell"]
        ) ** (1 - p_values_material["material_exponent"])

        monetary_matrix.loc[module_materials, internal_processes] *= (
            manuf_rate_base["baseline_total_modules"] / process_rate["total_modules"]
        ) ** (1 - p_values_material["material_exponent"])

        monetary_matrix.loc[pack_materials, internal_processes] *= (
            manuf_rate_base["baseline_total_packs"] / process_rate["total_packs"]
        ) ** (1 - p_values_material["material_exponent"])

        monetary_matrix.loc[["battery jacket Al", "battery jacket Fe"], :] *= (
            manuf_rate_base["baseline_total_packs"] / process_rate["total_packs"]
        ) ** (1 - p_values_material["material_exponent"])

        monetary_matrix.loc["module thermal conductor", internal_processes] *= (
            manuf_rate_base["baseline_required_cell"] / process_rate["required_cell"]
        ) ** (1 - p_values_material["material_exponent"])

        monetary_matrix.loc["cell group interconnect", internal_processes] *= (
            manuf_rate_base["baseline_modules_cell_interconnects"] / process_rate["modules_cell_interconnects"]
        ) ** (1 - p_values_material["material_exponent"])

        monetary_matrix.loc["module interconnects", internal_processes] *= (
            manuf_rate_base["baseline_total_modules"] / process_rate["total_modules"]
        ) ** (1 - p_values_material["material_exponent"])

        monetary_matrix.loc["module row rack", internal_processes] *= (
            process_rate["total_row_racks"] / manuf_rate_base["baseline_row_racks"]
        ) ** (1 - p_values_material["material_exponent"]) * design["rows_of_modules"]

        monetary_matrix.loc["cooling panels", internal_processes] *= (
            process_rate["total_row_racks"] / manuf_rate_base["baseline_row_racks"]
        ) ** (1 - p_values_material["material_exponent"])

        #  Multiplier for basic cost to overhead:
        monetary_matrix *= overhead_multiplier

        if run_multiple == False:
            return monetary_matrix
        else:
            nested_C_matrix[idx] = monetary_matrix

    return nested_C_matrix


def battery_material_cost_mass(technology_matrix, price_material_mass):
    """Monetary matrix based on material mass (technology matrix) and material price of externally procured materials

    Parameters
    ----------
    technology_matrix : df
        A matrix
    price_material_mass : df
        material prices mass

    Returns
    -------
    df
        monetary technology matrix
    """

    if price_material_mass.equals(technology_matrix.index) is False:
        price_material_mass = price_material_mass.reindex(technology_matrix.index).fillna(0)

    monetary_matrix_mass = (price_material_mass * technology_matrix.T).T

    return monetary_matrix_mass


def battery_material_cost_unit(price_material_unit, design_parameters):
    """Calculates the unit cost of battery materials per kg battery

    Parameters
    ----------
    price_material_unit : dict
        cost of materials per unit
    design_parameters : dict
        battery design parameters

    Returns
    -------
    dict
        unit cost per kg battery pack
    """
    unit_cost_dict = {}
    for material, v in price_material_unit.items():
        for parameter, value in v.items():
            material_bw_name = parameter_to_brightway_name(material)
            material_weight = design_parameters[material_bw_name]
            unit_price = value
            unit_value = design_parameters[parameter]
            if material_weight > 0:  #
                if material in unit_cost_dict.keys():
                    # Some material unit prices are based on several parameters (e.g. module electronics based on number of cells and bms capacity)
                    unit_cost_dict[material] += (unit_value * unit_price) / material_weight
                    if material == "module electronics":  # Multiply module electronics by total modules in pack
                        unit_cost_dict[material] *= design_parameters["modules_per_pack"]
                else:
                    unit_cost_dict[material] = (unit_value * unit_price) / material_weight

    return unit_cost_dict


def modelled_process_rates(design_param):
    """Annual modelled processing rate of battery production used to calculate the P values

    Args: parameter_dict (dict): battery and supply chain desing parameters

    Return: dictionary of the volume ratio per production process
    """
    pack_per_year = design_param["battery_manufacturing_capacity"] * design_param["total_packs_vehicle"]
    required_cells = pack_per_year * design_param["cells_per_pack"]
    total_cells = required_cells / design_param["py_cell_aging"]

    modelled_processing_rate_dict = {
        "energy": pack_per_year * design_param["pack_energy_kWh"],
        "required_cell": required_cells,
        "total_cell": total_cells,
        "positive_active_material": (design_param["positive_am_per_cell"] / 1000 * required_cells)
        / design_param["py_am_mixing_total"],
        "negative_active_material": design_param["negative_am_per_cell"]
        / 1000
        * required_cells
        / design_param["py_am_mixing_total"],
        "positive_electrode_area": total_cells * design_param["positive_electrode_area"] / 10000,
        "negative_electrode_area": total_cells * design_param["negative_electrode_area"] / 10000,
        "binder_solvent_recovery": pack_per_year
        * (
            design_param["binder_solvent_ratio"]
            * (design_param["cathode_binder_pvdf"] / design_param["py_am_mixing_total"])
        ),
        "total_cell": total_cells,
        "total_modules": (design_param["modules_per_pack"] * pack_per_year),
        "total_packs": pack_per_year,
        "total_row_racks": pack_per_year * design_param["rows_of_modules"],
        "modules_cell_interconnects": pack_per_year
        * design_param[
            "total_cell_interconnects"
        ],  # includes interconnects for tbs to terminals, this is not included in the BatPaC number of cell interconnect calculation
    }
    return modelled_processing_rate_dict


def labour_overhead_multiplier():
    """The factor cost overhead multiplier for direct labour. Function and parameters are based on BatPaC V5."""
    a = (
        1
        + variable_overhead_labor
        + GSA_labour * (1 + variable_overhead_labor)
        + pack_profit
        * (launch_cost_labor * (1 + variable_overhead_labor) + working_capital * (1 + variable_overhead_labor))
    )
    return a * (1 + battery_warranty_costs)


def capital_overhead_multiplier():
    """The factor cost overhead multiplier for capital equipment. Function and parameters are based on BatPaC V5."""
    depreciation_capital_equipment = calculate_depreciation(cost_rates["lifetime_capital_equipment"])[0]

    a = variable_overhead_depreciation + GSA_depreciation + GSA_labour * variable_overhead_depreciation + r_and_d + 1
    b = 1 + variable_overhead_depreciation * (launch_cost_labor + working_capital) * depreciation_capital_equipment
    return (a * depreciation_capital_equipment + b * pack_profit) * (1 + battery_warranty_costs)


def land_overhead_multiplier():
    """The factor cost overhead multiplier for capital equipment. Function and parameters are based on BatPaC V5."""
    deprecation_building_investment = calculate_depreciation(cost_rates["lifetime_capital_equipment"])[1]
    a = variable_overhead_depreciation + GSA_depreciation + GSA_labour * variable_overhead_depreciation + r_and_d + 1
    b = 1 + variable_overhead_depreciation * (launch_cost_labor + working_capital) * deprecation_building_investment
    return (a * deprecation_building_investment + b * pack_profit) * (1 + battery_warranty_costs)


def factor_overhead_multiplier(return_index=["labour", "capital", "land"]):
    """Returns the factor cost overhead multiplier"""
    land_overhead = land_overhead_multiplier()
    labour_overhead = labour_overhead_multiplier()
    capital_overhead = capital_overhead_multiplier()
    multiplier_dict = {}
    multiplier_dict["labour"] = labour_overhead
    multiplier_dict["capital"] = capital_overhead
    multiplier_dict["land"] = land_overhead
    return_dictionary = {k: multiplier_dict[k] for k in return_index}
    return return_dictionary


def material_overhead_multiplier():
    """The factor cost overhead multiplier for capital equipment. Function and parameters are based on BatPaC V5."""
    a = launch_cost_material + working_capital
    b = 1 + battery_warranty_costs
    return (1 + pack_profit * a) * b


def factors_battery_production(
    system_design_parameters,
    run_multiple=False,
    return_aggregated=True,
    return_index=["labour", "capital", "land"],
    return_columns=None,
):
    """Calculates the total production factor requirement (matrix F) for all production processes as in BatPaC adjusted
    for the manufacturing capacity.

    All calculations are based on BatPaC. Factors in physical terms including including labour (hr/yr), capital
    (US$/yr) and land (m2/yr). Default baseline parameters all based on BatPaC version 5.

    Parameters
    ----------
    system_design_parameters : Dict
        battery and supply chain design parameters
    run_multiple : bool, optional
        to return a nested F matrix of multiple pack designs, by default False
    return_aggregated : bool, optional
        If false, process aggregation based on BatPaC; if True process aggregation same as LCA, by default True

    Returns
    -------
    DataFrame if run_multiple = False, nested Numpy array if run_multiple = True.
        Factor requirements.

    Raises
    ------
    ValueError
        Error if battery manufacturing capacity is not defined
    """
    global process_mapping
    if run_multiple == False:
        sd_param = {}
        sd_param[0] = system_design_parameters
        disable_tqdm = True
    if run_multiple == True:
        sd_param = system_design_parameters
        if return_aggregated == False:
            p = process_mapping.keys()
        else:
            p = set(process_mapping.values())
        nested_F_matrix = np.zeros((len(sd_param.keys()), len(p_values_process.index), len(p)))
        disable_tqdm = False
    if return_columns != None:
        if all(process in return_columns for process in process_mapping.values()) == False:
            false_list = []
            for process in process_mapping.values():
                if process not in return_columns:
                    false_list.append(process)
            raise ValueError("The following processes are not defined: ", false_list)
        process_maping_new = {}
        for process in return_columns:
            if process not in process_mapping.values():
                continue
            else:
                new_mapping = {k: v for k, v in process_mapping.items() if v == process}
                process_maping_new.update(new_mapping)
        process_mapping = process_maping_new
    for idx, design in tqdm(enumerate(sd_param.values()), total=len(sd_param), disable=disable_tqdm):
        if "battery_manufacturing_capacity" not in design.keys():
            raise ValueError("battery_manufacturing_capacity not in parameter dictionary")
        packs_per_year = design["battery_manufacturing_capacity"] * design["total_packs_vehicle"]
        design_process_rates = modelled_process_rates(design)
        process_rates = {**manuf_rate_base, **design_process_rates}

        # return base_factors, p_values
        volume_ratios = production_volume_ratio(volume_ratio_mapping, process_rates, design)

        # Factor requirement is based on baseline production factors, modelled volume ratio and the p values
        factor_requirement_df = base_factors * volume_ratios**p_values_process

        # EXCEPTIONS:
        # Capital equipment requirement electrode coating and drying dependent on solvent evaporated:
        cathode_solvent_evaporated_m2 = (
            packs_per_year
            * design["binder_solvent_ratio"]
            * (design["cathode_binder_pvdf"] / design["py_am_mixing_total"])
            / design_process_rates["positive_electrode_area"]
        )

        anode_solvent_evaporated_m2 = (
            packs_per_year
            * design["binder_solvent_ratio"]
            * ((design["anode_binder_additive_sbr"] + design["anode_binder_cmc"]) / design["py_am_mixing_total"])
            / design_process_rates["negative_electrode_area"]
        )

        factor_requirement_df.loc["capital", "cathode coating and drying"] *= (
            cathode_solvent_evaporated_m2 / manuf_rate_base["baseline_pos_solvent_evaporated_m2"]
        ) ** 0.2
        factor_requirement_df.loc["capital", "anode coating and drying"] *= (
            anode_solvent_evaporated_m2 / manuf_rate_base["baseline_neg_solvent_evaporated_m2"]
        ) ** 0.2

        # Cell stacking based on cell capacity (baseline 68Ah, p value of 0.95)
        factor_requirement_df.loc[:, "cell stacking"] = (
            base_factors["cell stacking"]
            * (design["cell_capacity_ah"] / 68) ** 0.95
            * volume_ratios["cell stacking"] ** p_values_process["cell stacking"]
        )

        # Capital requirement for formation is based on cell capacity (baseline 68 Ah, p value 0.3)
        factor_requirement_df.loc[:, "cell formation"] *= (design["cell_capacity_ah"] / 68) ** 0.3

        # if cell > 80Ah, capital is multiplied by 1.1:
        if design["cell_capacity_ah"] > 80:
            factor_requirement_df.loc["capital", "cell formation"] *= 1.1

        # Labour and capital requirement pack assembly based on modules per pack, default modules per pack is 20, and p_value is 0.3:
        factor_requirement_df.loc[["capital", "labour"], "pack assembly"] = (
            factor_requirement_df.loc[["capital", "labour"], "pack assembly"] * (design["modules_per_pack"] / 20) ** 0.3
        )
        if return_aggregated is True:
            factor_requirement_df.rename(columns=process_mapping, inplace=True)
            factor_requirement_df = factor_requirement_df.groupby(factor_requirement_df.columns, axis=1).sum()
            if return_columns != None:
                column_index = list(set(process_mapping.values()))
                factor_requirement_df = factor_requirement_df[column_index]
        if run_multiple == False:
            return factor_requirement_df.loc[return_index]
        else:

            nested_F_matrix[idx] = factor_requirement_df.loc[return_index]

    return nested_F_matrix


def production_volume_ratio(volume_ratio_mapping, process_rates, parameter_dict):
    """Calculate the volume ratio of specific battery design as in BatPaC;
    volume/baseline number

    Args: volume_ratio_mapping (dict): process_rates (dict)
        baseline_manuf_rates(dict):

    Returns: dict: p values per process
    """
    process_rates["py_cell_aging"] = parameter_dict["py_cell_aging"]
    return_dict = {}
    for x in volume_ratio_mapping.keys():
        return_dict[x] = eval(volume_ratio_mapping[x], process_rates)
    return return_dict


def mineral_cost(elemental_content_df, metal_prices, cathode_list):
    """Calculates mineral cost for cathode active material based on elemental content and mineral prices

    Parameters
    ----------
    elemental_content_df : DataFrame
        elemental content of 1kg cathode active material
    metal_prices : dict
        prices of metals
    cathode_list : lst
        list of cathode active material

    Returns
    -------
    Dict
        mineral cost of cathode active material
    """
    cost_element = {}
    for cathode in cathode_list:
        cost_element[cathode] = {}
        for element in elemental_content_df.columns:
            if element == "all":
                continue
            cost_element[cathode][element] = elemental_content_df.loc[cathode, element] * metal_prices[element]

    return cost_element


def total_metal_cost(cost_element):
    """Total metal cost

    Parameters
    ----------
    cost_element : dict
        mineral cost of cathode active material

    Returns
    -------
    dict
        total mineral cost
    """
    total_dict = {}
    for k, v in cost_element.items():
        total_dict[k] = sum(v.values())
    return total_dict


def process_cost_profit_margin_cam(molar_mass_df, cam_prices, metal_prices, return_pcpm=False):
    cost_elements = mineral_cost(molar_mass_df, metal_prices, cam_prices.keys())
    metal_cost = total_metal_cost(cost_elements)
    df = pd.DataFrame(index=metal_cost.keys(), columns=["Unit", "Li", "Co", "Mn", "Ni", "Fe", "P"])
    df["Unit"] = "$/kg"

    for k in metal_cost.keys():
        df.loc[k, "Metal cost"] = metal_cost[k]
        for element, value in cost_elements[k].items():
            df.loc[k, element] = value
        if k not in cam_prices.keys():
            continue
        df.loc[k, "CAM price"] = cam_prices[k]
        df.loc[k, "PCPM"] = cam_prices[k] - metal_cost[k]

    if return_pcpm is True:
        return df["PCPM"].to_dict()
    return df.fillna(0)


def cam_price(
    metal_cost,
    elemental_content_df,
    pcpm_cam={
        "cathode active material (LFP)": 5.30,
        "cathode active material (LMO)": 3.11,
        "cathode active material (NMC333)": 6.72,
        "cathode active material (NMC532)": 6.72,
        "cathode active material (NMC622)": 7.19,
        "cathode active material (NMC811)": 15.05,
        "cathode active material (NCA)": 15.05,
        "cathode active material (50%/50% NMC532/LMO - )": 4.92,
    },
):
    """Calculates the cathode active material price based on metal cost and process cost and profit margin

    Parameters
    ----------
    metal_price : dict
        Metal price based on elemental value
    pcpm_cam : dict
        process cost and profit margin for cathode active material. Default values are calculated, data: 01-05-2022.
    elemental_content_df : DataFrame
        elemental content of 1 kg cathode active material

    Returns
    -------
    Dictionary
        cathode active material prices
    """

    cost_elements = mineral_cost(elemental_content_df, metal_cost, cathode_list=pcpm_cam.keys())
    metal_cost = total_metal_cost(cost_elements)
    cam_price_dict = {}
    for k in pcpm_cam.keys():
        cam_price_dict[k] = metal_cost[k] + pcpm_cam[k]
    return cam_price_dict
