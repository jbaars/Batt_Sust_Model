import xlwings as xw
import pandas as pd
from . import vehicle_model


def parameter_to_batpac(batpac_path, parameter_dict, visible=False, wb=None):
    """Update BatPaC parameters in Excel based on user defined parameters.

    Several default battery designs are present in the 'Battery Design' sheet. Based on the approach in GREET, for
    BEV, Battery 5 is chosen as default and for PHEV and HEV battery Battery 1.

    Args:
        batpac_path (str):

    Returns:
        dictionary with DataFrames of BatPaC sheets and updated values based on user defined parameters
    """
    param_dict = parameter_dict
    if wb is None:
        wb_batpac = xw.App(visible=visible, add_book=False).books.open(
            batpac_path
        )  # xlwings opens BatPaC workbook
    else:
        wb_batpac = wb
    wb_batpac.app.calculation = "manual"  # Suppress calculation after each value input
    sheets = [sheet.name for sheet in wb_batpac.sheets]

    if (
        parameter_dict["A_coefficient"]["value"] != None
        and parameter_dict["B_coefficient"]["value"] != None
        and parameter_dict["C_coefficient"]["value"] != None
        and parameter_dict["motor_power"]["value"] != None
        and parameter_dict["vehicle_range_miles"]["value"] != None
    ):
        vehicle_model.append_sheet_vehicle_model(
            parameter_dict, wb_batpac, design_column="H"
        )

    try:
        pack_demand_parameter(
            wb_batpac, param_dict
        )  # Check if only one of the demand value is assigned
        for (
            param_name
        ) in (
            param_dict.keys()
        ):  # Add the user defined parameters to BatPaC using xlwings
            param = param_dict[param_name]
            if (
                param["sheet"] == "None"
            ):  # Skip parameters that are not in BatPaC (e.g. 'anode binder cmc')
                continue
            elif (
                param["sheet"] == "Vehicle model" and "Vehicle model" not in sheets
            ):  # Skip parameters for vehicle model if vehicle parameters not assigned
                continue
            elif param["value"] is not None:

                param_sheet = param["sheet"]
                param_column = parameter_column(param, parameter_dict)
                param_index = param_column + str(int(param["row"]))
                param_value = param["value"]
                try:
                    wb_batpac.sheets[param_sheet].range(param_index).value = param_value
                except:
                    wb_batpac.app.kill()
                    raise ValueError(
                        f"Could not assign parameter {param_name} with value {param_value} to batpac "
                        f"excel location {param_sheet, param_index}"
                    )
            pass

        # Change value for silicon additive and separator coating thickness:
        # if param_dict['silicon_anode']['value'] > 0:
        neg_electrode_capacity(
            workbook_batpac=wb_batpac, silicon_pct=param_dict["silicon_anode"]["value"]
        )

        if param_dict["sep_coat_thickness"]["value"] is not None:
            if param_dict["sep_coat_thickness"]["value"] > 0:
                update_separator_density(wb_batpac, param_dict)
                update_separator_thickness(wb_batpac, param_dict)

        update_anode_binder(wb_batpac, param_dict)

        reset = wb_batpac.macro("Reset")  # Recalculate BatPaC, use BatPaC macro
        reset()
        dict_df_batpac = df_batpac_results(wb_batpac)
        if wb is None and visible is False:
            wb_batpac.app.kill()
        return dict_df_batpac
    except ValueError:
        wb_batpac.app.kill()
        raise ValueError("Something went wrong, BatPaC is closed")
    except NameError:
        wb_batpac.app.kill()
        raise NameError("Something went wrong, BatPaC is closed")
    except TypeError:
        wb_batpac.app.kill()
        raise TypeError("Something went wrong, BatPaC is closed")


def add_default_param(wb_batpac, vehicle_type):
    """Adds the default values based on vehicle type to the cell parameter box.

    Default value is box 1 in the 'List' sheet

    Args:
        wb_batpac (wb): open xlwings workbooks
        vehicle_type (str): electric vehicle type
    """
    range_vehicle = vehicle_type["column"] + str(vehicle_type["row"])
    wb_batpac.sheets["Dashboard"].range(range_vehicle).value = vehicle_type["value"]
    # Set all 'current iteration' to default value of 1:
    wb_batpac.sheets["Default Vehicle Configurations"].range("G16").value = 0
    # Call macro to append default values:

    add_default_macro = wb_batpac.macro("copytorange")
    add_default_macro()


def df_batpac_results(wb_batpac):
    """Import user defined parameters into BatPaC.

    Args:
        wb_batpac (wb): open xlwings BatPaC workbook

    Return:
        dict: dictionary with pd DataFrames of updated BatPaC sheets
    """
    design_sheet = (
        wb_batpac.sheets["Battery Design"]
        .range("A1:M480")
        .options(pd.DataFrame, header=False, index=False)
        .value
    )
    design_sheet.columns = [
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
        "K",
        "L",
        "M",
    ]
    design_sheet.index = list(range(1, 481))
    cost_sheet = (
        wb_batpac.sheets["Cost Breakdown"]
        .range("A1:M113")
        .options(pd.DataFrame, header=False, index=False)
        .value
    )
    cost_sheet.columns = [
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
        "K",
        "L",
        "M",
    ]
    cost_sheet.index = list(range(1, 114))

    manufacturing_cost_calculation = (
        wb_batpac.sheets["Manufacturing Costs"]
        .range("A1:M510")
        .options(pd.DataFrame, header=False, index=False)
        .value
    )
    manufacturing_cost_calculation.columns = [
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
        "K",
        "L",
        "M",
    ]
    manufacturing_cost_calculation.index = list(range(1, 511))

    sheets = [sheet.name for sheet in wb_batpac.sheets]
    if "Vehicle model" in sheets:
        vehicle_model = (
            wb_batpac.sheets["Vehicle model"]
            .range("A7:F9")
            .options(pd.DataFrame, header=True, index=False)
            .value
        )
    else:
        vehicle_model = []

    dict_df_batpac = {
        "df_design": design_sheet,
        "df_chem": wb_batpac.sheets["Chem"]
        .range("B1:C106")
        .options(pd.DataFrame, header=True, index=True)
        .value,
        "df_list": wb_batpac.sheets["Lists"]
        .range("F17:I32")
        .options(pd.DataFrame, header=True, index=True)
        .value,
        "df_dashboard": wb_batpac.sheets["Dashboard"]
        .range("A1:G225")
        .options(pd.DataFrame, header=False, index=False)
        .value,
        "df_manufacturing_cost": manufacturing_cost_calculation,
        "df_veh_model": vehicle_model,
    }
    return dict_df_batpac


def battery_design_column(vehicle_type):
    """Returns the column of the BatPaC Designsheet based on vehicle type. EV = battery 5, rest is battery 1"""  ##INCORRECT.. REMOVE THIS !!!!!!!!!!!!!!!!!!!!!!
    column = (
        "K" if vehicle_type == "EV" else "G"
    )  # Battery design column based on vehicle type
    return column


def dashboard_design_column(vehicle_type):
    """Returns the column of the BatPaC dashboard based on vehicle type. EV = battery 5, rest is battery 1"""  ##INCORRECT.. REMOVE THIS !!!!!!!!!!!!!!!!!!!!!!
    column = (
        "H" if vehicle_type == "EV" else "D"
    )  # Battery design column based on vehicle type
    return column


def parameter_column(parameter, parameter_dict):
    """Return BatPaC parameter column based on vehicle type"""
    param_sheet = parameter["sheet"]
    if param_sheet == "Battery Design":
        param_column = battery_design_column(parameter_dict["vehicle_type"]["value"])
    elif param_sheet == "Dashboard" and parameter["column"] == "None":
        param_column = dashboard_design_column(parameter_dict["vehicle_type"]["value"])
    else:
        param_column = parameter["column"]
    return param_column


def pack_demand_parameter(batpac_workbook, parameter_dict):
    """Changes only one pack demand parameter (capacity, energy of vehicle range) and removes the others
    Args:
        parameter_dict (dict): Dictionary with all parameters
        batpac_workbook: Open BatPaC workbook
    Returns:
        Changes pack demand parameter in BatPaC. Returns ValueError if more than one pack demand parameter defined
    """
    vehicle_type = parameter_dict["vehicle_type"]["value"]
    column = dashboard_design_column(vehicle_type)
    param_value = {}
    demand_parameter = [
        param
        for param in parameter_dict.keys()
        if parameter_dict[param]["parameter family"] == "pack_demand_parameters"
    ]
    for param in demand_parameter:
        if parameter_dict[param]["value"] is not None:
            if parameter_dict[param]["value"] != 0:
                param_value[param] = parameter_dict[param]["value"]
        else:
            param_value[param] = ""

    param_count_value = 0

    for x in param_value.values():  # Check if only one demand parameter
        if isinstance(x, int) or isinstance(x, float) is True:
            param_count_value += 1
    if param_count_value > 1:
        raise ValueError(
            "Only one demand parameter can be assigned, remove one of the following:",
            param_value,
        )
    batpac_workbook.sheets["Dashboard"].range(column + "42").value = param_value[
        "pack_capacity"
    ]
    batpac_workbook.sheets["Dashboard"].range(column + "43").value = param_value[
        "pack_energy"
    ]


def neg_electrode_capacity(
    workbook_batpac,
    silicon_pct,
    graphite_capacity=360,
    silicon_capacity=2000,
    silicon_density=2.13,
):
    """calculate negative electrode capacity based on silicon content.

    Function recalculates the negative active material capacity based on the practical discharge capacity of
    silicon, the percentage of silicon added to the anode and the default active material capacity for graphite
    (360 mAh/g)

    Args:
        workbook_batpac (workbook): Open XLwings BatPaC workbook
        silicon_pct (int): Silicon additive in percentage (e.g. 5% is 5)
        graphite_capacity (int): practical discharge capacity of graphite in mAH/g, 360 as default based on BatPac
        silicon_capacity (int): Practical discharge capacity of silicon in mAh/g, 2000 as default based on BatPac
        silicon_density (int): density of silicon oxide based on Greenwood et al 2021.

    Returns:
        Updates negative active material capacity (Chem, E31) and material density (Chem, E39) in BatPaC
    """
    silicon_pct = silicon_pct / 100
    workbook_batpac.sheets["Chem"].range("E37").value = graphite_capacity * (
        1 - silicon_pct
    ) + (silicon_capacity * silicon_pct)
    graphite_density = workbook_batpac.sheets["Chem"].range("D46").value
    workbook_batpac.sheets["Chem"].range("E46").value = (
        graphite_density * (1 - silicon_pct) + silicon_density * silicon_pct
    )


def update_separator_density(
    workbook_batpac, param_dic, rho_foil=0.9, rho_coating=1.996, void_fraction=None
):
    """Changes the separator density in BatPaC based on coating type and density

    The separator density is based on the thickness of the PE foil, the density of PE, the thickness of the coating layer and the density of the coating divided by the total thickness of the separator times the void or porosity of the separator.

    Args:
        workbook_batpac (wb): open XLwings batpac workbook
        rho_foil (int): density of the separator foil, 0.9 g/cm3 as default value for polypropylene
        rho_coating (int): density of separator coating, 1.996 g/cm3 as default value for silica coating based
                            on the values of Notter et al., 2010.
        void_fraction (float): porosity of separator. Default 0.5 from BatPaC
    """
    chem_sheet = workbook_batpac.sheets["Chem"]
    th_coating = param_dic["sep_coat_thickness"]["value"]
    th_foil = param_dic["sep_foil_thickness"]["value"]
    if void_fraction is None:
        void_fraction = chem_sheet.range("C62").value / 100
    sep_density = (
        (th_foil * rho_foil + th_coating * rho_coating) / (th_coating + th_foil)
    ) * void_fraction
    chem_sheet.range("E63").value = sep_density


def update_separator_thickness(workbook_batpac, param_dic):
    """Changes the separator thickness in BatPaC based on the separator foil and coating thickness

    workbook_batpac (workbook): open XLwings batpac workbook
    """
    dashboard_sheet = workbook_batpac.sheets["Dashboard"]
    separator_thickness = (
        param_dic["sep_foil_thickness"]["value"]
        + param_dic["sep_coat_thickness"]["value"]
    )
    dashboard_sheet.range("E26").value = separator_thickness


def cmc_quantity(param_dict):
    """Returns a dictionary of the value of cmc and sbr in the binder of the anode

    Default value for cmc is 0.6 (60:40 solution) but can be changed with the perc_cmc_anode_binder parameter
    """
    if param_dict["perc_cmc_anode_binder"]["value"] is not None:
        if param_dict["perc_cmc_anode_binder"]["value"] > 0:
            perc_cmc = param_dict["perc_cmc_anode_binder"]["value"] / 100
    else:
        perc_cmc = 0.6
    value = {"cmc": perc_cmc, "sbr": 1 - perc_cmc}
    return value


def update_anode_binder(workbook_batpac, param_dict, rho_cmc=1.6, rho_sbr=0.94):
    """Updates the anode binder density based on a defined mixture of CMC:SBR

    Default value for cmc is 0.6 (60:40 solution) but can be changed with the perc_cmc_anode_binder parameter

    Args:
        param_dict: dictionary of battery system parameters
        workbook_batpac (workbook): Open XLwings BatPaC workbook
        rho_cmc (float): density of carboxymethyl cellulose (CMC)
        rho_sbr (float): density of Styrene butadiene rubber

    """
    perc_dict = cmc_quantity(param_dict)
    chem_sheet = workbook_batpac.sheets["Chem"]
    density = (perc_dict["cmc"] * rho_cmc) + ((1 - perc_dict["sbr"]) * rho_sbr)
    chem_sheet.range("E48").value = density
