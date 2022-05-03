from pathlib import Path
import pandas as pd
import re
import numpy as np
from tqdm import tqdm
import time


rel_path = "data/default_manufacturing_cost_parameters.xlsx"
parent = Path(__file__).parents[0]
default_cost_data = parent / rel_path
xlsx_baseline = pd.ExcelFile(default_cost_data)
p_values = pd.read_excel(xlsx_baseline, sheet_name="p_values_materials", index_col=0)["p_value"]
manuf_rate_base = (
    pd.read_excel(xlsx_baseline, sheet_name="default_manufacturing_rates", index_col=0).iloc[:, 0].to_dict()
)
internal_processes = (
    pd.read_excel(xlsx_baseline, sheet_name="process_mapping", index_col=0).loc[:, "foreground process"].unique()
)


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
    overhead_multiplier=1.0516,  # Based on BatPaC but adjusted for energy consumption. Recalculated from BatPaC
    # baseplant and basepack design, assuming average energy consumption by Degen and Schutte 2021 on a per kg cell level (and Wh level for cell formation)
    # and average natural gas and electricity costs in the US for 2018.
):
    """Calculates the unit and mass cost of externally sourced materials for
    battery production

    Returns: df: process cost matrix of externally sourced materials
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

    for idx, design in tqdm(enumerate(sd_param.values()), total=len(sd_param), disable=disable_tqdm):
        t0 = time.time()

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
        # return monetary_matrix.loc[materials, processes], ((abs(technology_matrix_temp.loc[materials, processes])).T * (
        #     pd.Series(unit_cost_dict)
        # )).T

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
        ) ** (1 - p_values["material_exponent"])

        monetary_matrix.loc[module_materials, internal_processes] *= (
            manuf_rate_base["baseline_total_modules"] / process_rate["total_modules"]
        ) ** (1 - p_values["material_exponent"])

        monetary_matrix.loc[pack_materials, internal_processes] *= (
            manuf_rate_base["baseline_total_packs"] / process_rate["total_packs"]
        ) ** (1 - p_values["material_exponent"])

        monetary_matrix.loc[["battery jacket Al", "battery jacket Fe"], :] *= (
            manuf_rate_base["baseline_total_packs"] / process_rate["total_packs"]
        ) ** (1 - p_values["material_exponent"])

        monetary_matrix.loc["module thermal conductor", internal_processes] *= (
            manuf_rate_base["baseline_required_cell"] / process_rate["required_cell"]
        ) ** (1 - p_values["material_exponent"])

        monetary_matrix.loc["cell group interconnect", internal_processes] *= (
            manuf_rate_base["baseline_modules_cell_interconnects"] / process_rate["modules_cell_interconnects"]
        ) ** (1 - p_values["material_exponent"])

        monetary_matrix.loc["module interconnects", internal_processes] *= (
            manuf_rate_base["baseline_total_modules"] / process_rate["total_modules"]
        ) ** (1 - p_values["material_exponent"])

        monetary_matrix.loc["module row rack", internal_processes] *= (
            process_rate["total_row_racks"] / manuf_rate_base["baseline_row_racks"]
        ) ** (1 - p_values["material_exponent"]) * design["rows_of_modules"]

        monetary_matrix.loc["cooling panels", internal_processes] *= (
            process_rate["total_row_racks"] / manuf_rate_base["baseline_row_racks"]
        ) ** (1 - p_values["material_exponent"])

        #  Multiplier for basic cost to overhead (only for materials, excluding energy):
        if overhead_multiplier != None:
            monetary_matrix[
                ~monetary_matrix.index.isin(
                    [
                        "heat, district or industrial, natural gas for battery production",
                        "electricity for battery production, medium voltage",
                    ]
                )
            ] *= overhead_multiplier

        if run_multiple == False:
            return monetary_matrix
        else:
            nested_C_matrix[idx] = monetary_matrix

    return nested_C_matrix


def battery_material_cost_mass(technology_matrix, price_material_mass):
    """Monetary matrix based on material mass (technology matrix) and material
    price of externally procured materials

    Args: technology_matrix (df): input (negative) and output (positive)
        technology matrix (material is index, columns is processes)
        price_material_mass (pd series): price of all battery materials (index
        in technology matrix)

    Return: df: ..
    """
    if price_material_mass.equals(technology_matrix.index) is False:
        price_material_mass = price_material_mass.reindex(technology_matrix.index).fillna(0)

    monetary_matrix_mass = (price_material_mass * technology_matrix.T).T

    return monetary_matrix_mass


def battery_material_cost_unit(price_material_unit, design_parameters):
    """Calculates the unit cost of battery materials

    Args: price_material_unit (dataframe): cost of materials per unit
        parameter_dict (dict): battery design parameters

    Return: dict: unit cost (values) per material (keys) on a pack level
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
    """Annual modelled processing rate of battery production used to calculate
    the P values

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


def labour_overhead_multiplier(
    variable_overhead_labor=0.4,
    GSA=0.25,
    pack_profit=0.05,
    investment_cost=0.10,
    working_capital=0.15,
    battery_warranty_costs=0.056,
):
    """The factor cost overhead multiplier for direct labour. Function and parameters are based on BatPaC V5."""
    a = (
        1
        + variable_overhead_labor
        + GSA * (1 + variable_overhead_labor)
        + pack_profit
        * (investment_cost * (1 + variable_overhead_labor) + working_capital * (1 + variable_overhead_labor))
    )
    return a * (1 + battery_warranty_costs)


def capital_overhead_multiplier(
    variable_overhead_deprecation=0.2,  # f94
    GSA_deprecation=0.25,  # 99
    GSA_labour=0.25,  # 98
    r_and_d=0.4,  # 100
    deprecation_capital_equipment=0.1,  # 103
    launch_cost_labor=0.10,  # 86
    working_capital=0.15,  # 87
    pack_profit=0.05,  # f109
    battery_warranty_costs=0.056,  # f110
):
    """The factor cost overhead multiplier for capital equipment. Function and parameters are based on BatPaC V5."""
    a = variable_overhead_deprecation + GSA_deprecation + GSA_labour * variable_overhead_deprecation + r_and_d + 1
    b = 1 + variable_overhead_deprecation * (launch_cost_labor + working_capital) * deprecation_capital_equipment
    return (a * deprecation_capital_equipment + b * pack_profit) * (1 + battery_warranty_costs)


def land_overhead_multiplier(
    variable_overhead_deprecation=0.2,  # f94
    GSA_deprecation=0.25,  # 99
    GSA_labour=0.25,  # 98
    r_and_d=0.4,  # 100
    deprecation_building_investment=0.05,  # 104
    launch_cost_labor=0.10,  # 86
    working_capital=0.15,  # 87
    pack_profit=0.05,  # f109
    battery_warranty_costs=0.056,  # f110
):
    """The factor cost overhead multiplier for capital equipment. Function and parameters are based on BatPaC V5."""
    a = variable_overhead_deprecation + GSA_deprecation + GSA_labour * variable_overhead_deprecation + r_and_d + 1
    b = 1 + variable_overhead_deprecation * (launch_cost_labor + working_capital) * deprecation_building_investment
    return (a * deprecation_building_investment + b * pack_profit) * (1 + battery_warranty_costs)


def factor_overhead_multiplier():
    """Returns the factor cost overhead multiplier"""
    land_overhead = land_overhead_multiplier()
    labour_overhead = labour_overhead_multiplier()
    capital_overhead = capital_overhead_multiplier()
    multiplier_dict = {}
    multiplier_dict["labour"] = labour_overhead
    multiplier_dict["capital"] = capital_overhead
    multiplier_dict["land"] = land_overhead

    return multiplier_dict


def factors_battery_production(
    system_design_parameters,
    run_multiple=False,
    return_aggregated=True,
):
    """Calculates the total production factor requirement (matrix F) for all production processes as in BatPaC adjusted
    for the manufacturing capacity.

    Manufacturing capacity must be within 20 to 500% of the BatPaC baseline rate, which is 100,000 packs per year.
    All calculations are based on BatPaC. Factors in physical terms including including labour (hr/yr), capital
    (US$/yr) and land (m2/yr). Default baseline parameters all based on BatPaC version 5.

    Param:
        system_design_parameters (dict): battery and supply chain design parameters
        run_multiple (bool): to return a nested F matrix of multiple pack designs
        return_aggregated (bool): If false, process aggregation based on BatPaC; if True process aggregation same as LCA.

    Return: DataFrame or nested NP array. Factors order: labour, capital, land
    """

    # if run_multiple is None:
    rel_path = "data/default_manufacturing_cost_parameters.xlsx"
    parent = Path(__file__).parents[0]
    default_cost_data = parent / rel_path
    xlsx_baseline = pd.ExcelFile(default_cost_data)
    p_values = pd.read_excel(xlsx_baseline, sheet_name="p_values_process", index_col=0).T
    base_factors = pd.read_excel(xlsx_baseline, sheet_name="baseline_factors", index_col=0).T.drop("unit", axis=1)
    base_process_rates = (
        pd.read_excel(xlsx_baseline, sheet_name="default_manufacturing_rates", index_col=0).iloc[:, 0].to_dict()
    )
    volume_ratio_mapping = (
        pd.read_excel(xlsx_baseline, sheet_name="volume_ratio_mapping", index_col=0).iloc[:, 0].to_dict()
    )
    process_mapping = pd.read_excel(xlsx_baseline, sheet_name="process_mapping", index_col=0).iloc[:, 0].to_dict()

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
        nested_F_matrix = np.zeros((len(sd_param.keys()), len(p_values.index), len(p)))
        disable_tqdm = False

    for idx, design in tqdm(enumerate(sd_param.values()), total=len(sd_param), disable=disable_tqdm):
        if "battery_manufacturing_capacity" not in design.keys():
            raise ValueError("battery_manufacturing_capacity not in parameter dictionary")
        packs_per_year = design["battery_manufacturing_capacity"] * design["total_packs_vehicle"]
        design_process_rates = modelled_process_rates(design)
        process_rates = {**base_process_rates, **design_process_rates}

        # return base_factors, p_values
        volume_ratios = production_volume_ratio(volume_ratio_mapping, process_rates, design)

        # Factor requirement is based on baseline production factors, modelled volume ratio and the p values
        factor_requirement_df = base_factors * volume_ratios**p_values

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
            cathode_solvent_evaporated_m2 / base_process_rates["baseline_pos_solvent_evaporated_m2"]
        ) ** 0.2
        factor_requirement_df.loc["capital", "anode coating and drying"] *= (
            anode_solvent_evaporated_m2 / base_process_rates["baseline_neg_solvent_evaporated_m2"]
        ) ** 0.2

        # Cell stacking based on cell capacity (baseline 68Ah, p value of 0.95)
        factor_requirement_df.loc[:, "cell stacking"] = (
            base_factors["cell stacking"]
            * (design["cell_capacity_ah"] / 68) ** 0.95
            * volume_ratios["cell stacking"] ** p_values["cell stacking"]
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
        if run_multiple == False:
            return factor_requirement_df
        else:
            nested_F_matrix[idx] = factor_requirement_df

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


def mineral_cost(molar_mass_df, metal_prices):
    """Process cost and profit margin estimation cathode active material
    cathode active material price calculation - data: 22-10-2021"""

    cathode_list = [
        "cathode active material (LFP)",
        "cathode active material (LMO)",
        "cathode active material (NMC333)",
        "cathode active material (NMC532)",
        "cathode active material (NMC622)",
        "cathode active material (NMC811)",
        "cathode active material (NCA)",
        "cathode active material (50%/50% NMC532/LMO - )",
    ]
    cost_element = {}
    for cathode in cathode_list:
        cost_element[cathode] = {}
        for element in molar_mass_df.columns:
            if element == "all":
                continue
            cost_element[cathode][element] = molar_mass_df.loc[cathode, element] * metal_prices[element]

    return cost_element


def total_metal_cost(cost_element):
    total_dict = {}
    for k, v in cost_element.items():
        total_dict[k] = sum(v.values())
    return total_dict


def process_cost_profit_margin_cam(molar_mass_df, cam_prices, metal_prices, return_pcpm=False):
    cost_elements = mineral_cost(molar_mass_df, metal_prices)
    metal_cost = total_metal_cost(cost_elements)
    df = pd.DataFrame(index=metal_cost.keys(), columns=["Unit", "Li", "Co", "Mn", "Ni", "Fe", "P", "Al"])
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
    molar_mass,
    pcpm_cam={
        "cathode active material (LFP)": 5.30,
        "cathode active material (LMO)": 3.11,
        "cathode active material (NMC333)": 5.08,
        "cathode active material (NMC532)": 5.08,
        "cathode active material (NMC622)": 7.19,
        "cathode active material (NMC811)": 11.46,
        "cathode active material (NCA)": 7.19,
        "cathode active material (50%/50% NMC532/LMO - )": 4.10,
    },
):
    """Calculates the cathode active material price based on metal cost and process cost and profit margin

    Parameters
    ----------
    metal_price : [type]
        Metal price based on elemental value
    pcpm_cam : [type]
        process cost and profit margin for cathode active material. Calculated.
    molar_mass :
        Molar mass of elements in cathode active material
    """

    cost_elements = mineral_cost(molar_mass, metal_cost)
    metal_cost = total_metal_cost(cost_elements)
    cam_price_dict = {}
    for k in pcpm_cam.keys():
        cam_price_dict[k] = metal_cost[k] + pcpm_cam[k]
    return cam_price_dict
