from pathlib import Path
import pandas as pd
import re


def parameter_to_brightway_name(parameter_name):
    """Convert parameter to name of parameters in Brightway"""
    new_name = re.sub("[^0-9a-zA-Z]+", "_", parameter_name)
    if new_name[-1] == "_":  # Remove underscore if last index
        new_name = new_name[0:-1]
    return new_name


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
    material_category,
    manuf_rate_base,
    p_values,
    parameter_dict,
    internal_processes,
    unit_material_to_process_mapping=None,
    overhead_multiplier=1.0516,  # Based on BatPaC but adjusted for energy consumption. Recalculated from BatPaC
    # baseplant and basepack design, assuming average energy consumption by Degen and Schutte 2021 on a per kg cell level (and Wh level for cell formation)
    # and average natural gas and electricity costs in the US for 2018.
):
    """Calculates the unit and mass cost of externally sourced materials for
    battery production

    Returns: df: process cost matrix of externally sourced materials
    """

    unit_cost_dict = battery_material_cost_unit(price_material_unit, parameter_dict)
    monetary_matrix = battery_material_cost_mass(technology_matrix, price_material_mass)
    # Set all internal process to zero
    monetary_matrix[internal_processes] = 0

    # Append unit cost to mass cost:
    if unit_material_to_process_mapping is None:
        unit_material_to_process_mapping = material_to_process_mapping(
            unit_cost_dict.keys(), technology_matrix
        )
    # Material unit costs are attributed to the receiving battery production process:
    for material, process in unit_material_to_process_mapping.items():
        # First check if material from material-process mapping in unit_cost dict:
        if material not in unit_cost_dict.keys():
            continue
        else:
            monetary_matrix.loc[material, process] += unit_cost_dict[material] * abs(
                technology_matrix.loc[material, process]
            )

    # Append unit cost with P values (for scale) to monetary A matrix:
    if p_values == None:
        process_rate = modelled_process_rates(parameter_dict)
        cathode_am = list(
            material_category.set_index("material category").loc[
                "cathode active material", "material choices"
            ]
        )
        anode_am = list(
            material_category.set_index("material category").loc[
                "anode active material", "material choices"
            ]
        )

        monetary_matrix.loc["cell terminal anode", :] *= (
            manuf_rate_base["baseline_total_cell"] / process_rate["total_cell"]
        ) ** (1 - p_values["cell terminal anode"])

        monetary_matrix.loc["cell terminal cathode", :] *= (
            manuf_rate_base["baseline_total_cell"] / process_rate["total_cell"]
        ) ** (1 - p_values["cell terminal cathode"])

        monetary_matrix.loc[cathode_am, :] *= (
            manuf_rate_base["baseline_positive_active_material"]
            / process_rate["positive_active_material"]
        ) ** (1 - p_values["positive active material"])

        monetary_matrix.loc[anode_am, :] *= (
            manuf_rate_base["baseline_negative_active_material"]
            / process_rate["negative_active_material"]
        ) ** (1 - p_values["negative active material"])

        monetary_matrix.loc["cell container", :] *= (
            manuf_rate_base["baseline_total_cell"] / process_rate["total_cell"]
        ) ** (1 - p_values["cell container"])

        monetary_matrix.loc["module thermal conductor", :] * (
            manuf_rate_base["baseline_required_cell"] / process_rate["required_cell"]
        ) ** (1 - p_values["module thermal conductor"])
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

    return monetary_matrix


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
        price_material_mass = price_material_mass.reindex(technology_matrix.index)

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
            material_adjust = [
                "cell container",
                "cell terminal cathode",
                "cell terminal anode",
            ]  # Need to be adjusted for process yield cell aging
            if material_weight > 0:  #
                if material in material_adjust:
                    unit_cost_dict[material] = (
                        (unit_value / design_parameters["py_cell_aging"]) * unit_price
                    ) / (material_weight * design_parameters["py_cell_aging"])
                elif material in unit_cost_dict.keys():
                    # Some material unit prices are based on several parameters (e.g. module electronics based on number of cells and bms capacity)
                    unit_cost_dict[material] += (
                        unit_value * unit_price
                    ) / material_weight
                else:
                    unit_cost_dict[material] = (
                        unit_value * unit_price
                    ) / material_weight
    return unit_cost_dict


def modelled_process_rates(design_param):
    """Annual modelled processing rate of battery production used to calculate
    the P values

    Args: parameter_dict (dict): battery and supply chain desing parameters

    Return: dictionary of the volume ratio per production process
    """
    pack_per_year = (
        design_param["battery_manufacturing_capacity"]
        * design_param["total_packs_vehicle"]
    )
    required_cells = pack_per_year * design_param["cells_per_pack"]
    total_cells = required_cells / design_param["py_cell_aging"]

    modelled_processing_rate_dict = {
        "packs": pack_per_year,
        "energy": pack_per_year * design_param["pack_energy_kWh"],
        "required_cell": required_cells,
        "total_cell": total_cells,
        "electrode_area": total_cells * design_param["cell_area"] / 10000,
        "positive_active_material": (
            design_param["positive_am_per_cell"] / 1000 * required_cells
        )
        / design_param["py_am_mixing_total"],
        "negative_active_material": design_param["negative_am_per_cell"]
        / 1000
        * required_cells
        / design_param["py_am_mixing_total"],
        "binder_solvent_recovery": pack_per_year
        * design_param["binder_solvent_ratio"]
        * (design_param["cathode_binder_pvdf"] / design_param["py_am_mixing_total"]),
        "dry_room_area": 0,
    }
    return modelled_processing_rate_dict


def factor_overhead_multiplier(
    production_capacity,
    land_overhead=1.5325,
    labour_overhead=1.8665,
    capital_overhead=3.8764,
):
    """Returns the factor cost overhead multiplier. Capital is converted from
    millions"""
    baseline_production_capacity = 100000
    multiplier_dict = {}
    multiplier_dict["land"] = land_overhead * baseline_production_capacity / 1000000
    multiplier_dict["labour"] = labour_overhead
    multiplier_dict["capital"] = capital_overhead * baseline_production_capacity
    return multiplier_dict


def factors_battery_production(
    design_param,
    run_multiple=None,
    return_aggregated=True,
):

    """Calculates the total production factor requirement (matrix F)
    for all production processes as in BatPaC adjusted for the manufacturing
    capacity.

    Manufacturing capacity must be within 20 to 500% of the BatPaC baseline
    rate, which is 100,000 packs per year. All calculations are based on BatPaC.
    Factors in physical terms including including labor (hr/yr), capital
    (US$/yr) and land (m2/yr). Default baseline parameters based on BatPaC.

    Param: parameter_dict (dict): battery and supply chain design parameters
        default_cost_data (string): path to cost parameters, if None path is
        relative
        return_aggregated (bool): If false, process aggregation based
        on BatPaC; if True process aggregation same as LCA.

    Return: dataframe: matrix with factor (row) requirement per process (column)
    """
    if run_multiple is None:
        rel_path = "data/default_manufacturing_cost_parameters.xlsx"
        parent = Path(__file__).parents[0]
        default_cost_data = parent / rel_path
        xlsx_baseline = pd.ExcelFile(default_cost_data)
        p_values = pd.read_excel(
            xlsx_baseline, sheet_name="p_values_process", index_col=0
        ).drop("unit", axis=1)
        base_factors = pd.read_excel(
            xlsx_baseline, sheet_name="baseline_factors", index_col=0
        ).drop("unit", axis=1)
        base_process_rates = (
            pd.read_excel(
                xlsx_baseline, sheet_name="default_manufacturing_rates", index_col=0
            )
            .iloc[:, 0]
            .to_dict()
        )
        volume_ratio_mapping = (
            pd.read_excel(xlsx_baseline, sheet_name="volume_ratio_mapping", index_col=0)
            .iloc[:, 0]
            .to_dict()
        )
        process_mapping = (
            pd.read_excel(xlsx_baseline, sheet_name="process_mapping", index_col=0)
            .iloc[:, 0]
            .to_dict()
        )
    else:
        p_values = run_multiple[0]
        base_factors = run_multiple[1]
        base_process_rates = run_multiple[2]
        volume_ratio_mapping = run_multiple[3]
        process_mapping = run_multiple[4]

    if "battery_manufacturing_capacity" not in design_param.keys():
        raise ValueError("battery_manufacturing_capacity not in parameter dictionary")

    if design_param["battery_manufacturing_capacity"] < 20000:
        raise ValueError(
            f"battery_manufacturing_capacity of {design_param['battery_manufacturing_capacity']} is to flow to provide a reasonable estimate. The minimum production capacity is 20,000. See also BatPaC Version 3 manual page 82"
        )

    elif design_param["battery_manufacturing_capacity"] > 500000:
        raise ValueError(
            f"battery_manufacturing_capacity of {design_param['battery_manufacturing_capacity']} is to high to provide a reasonable estimate. The maximum production capacity is 500,000. See also BatPaC Version 3 manual page 82"
        )

    packs_per_year = (
        design_param["battery_manufacturing_capacity"]
        * design_param["total_packs_vehicle"]
    )

    design_process_rates = modelled_process_rates(design_param)
    process_rates = {**base_process_rates, **design_process_rates}
    volume_ratios = production_volume_ratio(
        volume_ratio_mapping, process_rates, design_param
    )

    # Factor requirement is based on baseline production factors, modelled volume
    # ratio and the p values
    factor_requirement_df = base_factors * volume_ratios ** p_values

    # EXCEPTIONS: Capital equipment requirement electrode coating and drying
    # dependent on solvent evaporated:
    cathode_solvent_evaporated_m2 = (
        packs_per_year
        * design_param["binder_solvent_ratio"]
        * (design_param["cathode_binder_pvdf"] / design_param["py_am_mixing_total"])
        / design_process_rates["electrode_area"]
    )

    anode_solvent_evaporated_m2 = (
        packs_per_year
        * design_param["binder_solvent_ratio"]
        * (
            (
                design_param["anode_binder_additive_sbr"]
                + design_param["anode_binder_cmc"]
            )
            / design_param["py_am_mixing_total"]
        )
        / design_process_rates["electrode_area"]
    )
    base_cath_solvent_evaporated = (
        base_process_rates["baseline_positive_binder_evaporate_kg"]
        / base_process_rates["baseline_electrode_area"]
    )
    base_ano_solvent_evaporated = (
        base_process_rates["baseline_negative_binder_evaporate_kg"]
        / base_process_rates["baseline_electrode_area"]
    )

    factor_requirement_df.loc["capital", "cathode coating and drying"] *= (
        cathode_solvent_evaporated_m2 / base_cath_solvent_evaporated
    ) ** 0.2
    factor_requirement_df.loc["capital", "anode coating and drying"] *= (
        anode_solvent_evaporated_m2 / base_ano_solvent_evaporated
    ) ** 0.2
    # Dry room operating area based on area requiremented of dry room processes:
    dry_room_processing_rate = (
        factor_requirement_df.loc[
            "land",
            [
                "electrolyte filling and sealing",
                "cell stacking",
                "terminal welding",
                "jelly roll enclosing",
            ],
        ].sum()
        + factor_requirement_df.loc["land", "material handling"] / 3
    )
    dry_room_volume_ratio = (
        dry_room_processing_rate / base_process_rates["baseline_dry_room_area"]
    )

    factor_requirement_df.loc[:, "dry room management"] = (
        base_factors.loc[:, "dry room management"]
        * dry_room_volume_ratio ** p_values["dry room management"]
    )

    # Capital requirement pack assembly based on modules per pack:
    factor_requirement_df.loc["capital", "pack assembly"] = (
        factor_requirement_df.loc["capital", "pack assembly"]
        * (design_param["modules_per_pack"] / 20) ** 0.3
    )
    # default modules per pack is 20, and p_value is 0.3
    # Capital requirement for stacking, rack loading and formation cycling based
    # on cell capacity (Ah) if > 80Ah multiply by 1.1:
    if design_param["cell_capacity_ah"] > 80:
        factor_requirement_df.loc[
            "capital", ["cell stacking", "formation cycling", "rack loading"]
        ] = (
            factor_requirement_df.loc[
                "capital", ["cell stacking", "formation cycling", "rack loading"]
            ]
            * 1.1
        )

    if return_aggregated is True:
        factor_requirement_df.rename(columns=process_mapping, inplace=True)
        factor_requirement_df = factor_requirement_df.groupby(
            factor_requirement_df.columns, axis=1
        ).sum()
        return factor_requirement_df

    return factor_requirement_df


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
