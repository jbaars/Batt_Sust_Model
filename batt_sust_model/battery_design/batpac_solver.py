import xlwings as xw
import pandas as pd


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

    add_default_param(
        wb_batpac, param_dict["vehicle_type"]["value"]
    )  # Add the default vehicle parameters

    if (
        parameter_dict["A_coefficient"]["value"] != None
        and parameter_dict["B_coefficient"]["value"] != None
        and parameter_dict["C_coefficient"]["value"] != None
        and parameter_dict["motor_power"]["value"] != None
        and parameter_dict["vehicle_range"]["value"] != None
    ):
        append_sheet_vehicle_model(parameter_dict, wb_batpac, design_column="H")

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
        # else:
        #     wb_batpac.sheets['Chem'].range('D28').value = 'No'
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
    wb_batpac.sheets["Dashboard"].range("E28").value = vehicle_type
    # Set all 'current value' to 'number of values' to assure the first table is chosen (see LIST sheet):
    wb_batpac.sheets["Lists"].range("S57").value = (
        wb_batpac.sheets["Lists"].range("T57").value
    )
    wb_batpac.sheets["Lists"].range("AB57").value = (
        wb_batpac.sheets["Lists"].range("AC57").value
    )
    wb_batpac.sheets["Lists"].range("AK57").value = (
        wb_batpac.sheets["Lists"].range("AL57").value
    )
    wb_batpac.sheets["Lists"].range("AT57").value = (
        wb_batpac.sheets["Lists"].range("AU57").value
    )
    add_default_macro = wb_batpac.macro("Add_Default_Parameters")
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
        .range("A1:M225")
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
    design_sheet.index = list(range(1, 226))
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
        wb_batpac.sheets["Manufacturing Cost Calculations"]
        .range("A1:M275")
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
    manufacturing_cost_calculation.index = list(range(1, 276))

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
    if (
        param_value["vehicle_range"] is not None
        and vehicle_type == "HEV-HP"
        or vehicle_type == "microHEV"
    ):
        raise ValueError(
            f"Vehicle range is not a valid parameter for {vehicle_type}, please change to the demand"
            f"parameter to either pack capacity or energy"
        )
    batpac_workbook.sheets["Dashboard"].range(column + "42").value = param_value[
        "pack_capacity"
    ]
    batpac_workbook.sheets["Dashboard"].range(column + "43").value = param_value[
        "pack_energy"
    ]
    batpac_workbook.sheets["Dashboard"].range(column + "44").value = param_value[
        "vehicle_range"
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
    # workbook_batpac.sheets['Chem'].range('D28').value = 'Yes'
    workbook_batpac.sheets["Chem"].range("E31").value = graphite_capacity * (
        1 - silicon_pct
    ) + (silicon_capacity * silicon_pct)
    graphite_density = workbook_batpac.sheets["Chem"].range("D39").value
    workbook_batpac.sheets["Chem"].range("E39").value = (
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
        void_fraction = chem_sheet.range("C50").value / 100
    sep_density = (
        (th_foil * rho_foil + th_coating * rho_coating) / (th_coating + th_foil)
    ) * void_fraction
    chem_sheet.range("E51").value = sep_density


def update_separator_thickness(workbook_batpac, param_dic):
    """Changes the separator thickness in BatPaC based on the separator foil and coating thickness

    workbook_batpac (workbook): open XLwings batpac workbook
    """
    dashboard_sheet = workbook_batpac.sheets["Dashboard"]
    separator_thickness = (
        param_dic["sep_foil_thickness"]["value"]
        + param_dic["sep_coat_thickness"]["value"]
    )
    dashboard_sheet.range("E22").value = separator_thickness


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
    chem_sheet.range("E41").value = density


def append_sheet_vehicle_model(
    parameter_dictionary, batpac_workbook, design_column="H"
):
    wb = batpac_workbook
    sheets = [sheet.name for sheet in wb.sheets]
    parameters = parameter_dictionary

    if "Vehicle model" in sheets:
        # Change target battery pack power parameter:
        wb.sheets["Dashboard"].range(
            design_column + "33"
        ).value = "='Vehicle model'!B12"
        wb.sheets["Dashboard"].range(
            design_column + "40"
        ).value = "=IF(D56=0, 250,'Vehicle model'!B24)"
        # Do nothing
        return
    # Add sheet and full model
    sh = wb.sheets.add("Vehicle model")

    sh.range("A1").value = "Vehicle fuel consumption parameters"
    sh.range("A1").font.bold = True

    # Add parameters:
    vehicle_model_parameters = [
        param
        for param in parameters.keys()
        if parameters[param]["sheet"] == "Vehicle model"
    ]
    for k in vehicle_model_parameters:
        column = parameters[k]["column"]
        row = parameters[k]["row"]
        sh.range("A" + str(row)).value = k
        if parameters[k]["value"]:
            sh.range(column + str(row)).value = parameters[k]["value"]
        else:
            sh.range(column + str(row)).value = parameters[k]["default"]

    # Add formulas:
    vehicle_weight = {
        "B": ["Glider", 1295, "=1295+B16*(C9+D9+E9-C8-D8-E8)"],
        "C": ["Transmission", 86, "=B14*B12"],
        "D": ["Battery system", 448, "=B26"],
        "E": ["Motor/Generator/Controller", 147, "=B15*B12"],
        "F": ["Total weight", "=SUM(B8:E8)", "=SUM(B9:E9)"],
    }
    row = 7
    sh.range("A" + str(row + 1)).value = "BEV-baseline"
    sh.range("A" + str(row + 2)).value = "BEV"
    for k, v in vehicle_weight.items():
        sh.range(k + str(row)).value = v[0]
        sh.range(k + str(row + 1)).value = v[1]
        sh.range(k + str(row + 2)).value = v[2]

    sh.range("A12").value = "Battery at rated power, kW"
    sh.range("B12").value = "=B11*(1+(1-B39))*(1+(1-B30))"

    sh.range("A13").value = "Battery system energy intensity, kWh/kg"
    sh.range("B13").value = "='Battery Design'!K218/1000"

    sh.range("A21").value = "Plug consumption rate, MJ/km"
    sh.range("B21").value = "=B22/B38"

    sh.range("A22").value = "Fuel consumption rate combined, MJ/km"
    sh.range("B22").value = "=B41*B49+C41*C49"

    sh.range("A23").value = "Average driving speed, combined, m/s"
    sh.range("B23").value = "=1/(B49/(B45/B48)+C49/(C45/C48))"

    sh.range("A24").value = "Fuel consumption rate Wh/miles"
    sh.range("B24").value = "=B22*1000/3.6/0.6213"

    sh.range("A26").value = "Battery system mass, kg"
    sh.range("B26").value = "=B27/B13"

    sh.range("A27").value = "Battery capacity (kWh)"
    sh.range("B27").value = "=IF(Dashboard!D56=0, 1,B28*B22/B37/3.6)"

    sh.range("A28").value = "Range (km)"
    sh.range("B28").value = "=Dashboard!H44*1.609344"

    sh.range("A29").value = "Vehicle mass (kg)"
    sh.range("B29").value = "=F9"

    sh.range("A35").value = "regen_breaking_efficiency*charging_Efficiency"
    sh.range("B35").value = "=B34*B25"

    sh.range("A37").value = "Capacity accessible ratio"
    sh.range("B37").value = "=Dashboard!H28/100"

    sh.range("B40").value = "UDDS"
    sh.range("C40").value = "HWFET"

    sh.range("A44").value = "integral avdt"
    sh.range("A45").value = "integral_vdt"
    sh.range("A46").value = "integral_v3dt"
    sh.range("A47").value = "integral_v2dt"
    sh.range("A48").value = "integral_dt"

    sh.range("A41").value = "Fuel consumption rate, MJ/km"
    sh.range("B41").value = "=(B42+B43)/B45*1000"
    sh.range("C41").value = "=(C42+C43)/C45*1000"

    sh.range("A42").value = "Weight-induced fuel consumption (MJ)"
    sh.range(
        "B42"
    ).value = "=(B2*B45+B3*B47+(1-B34*B50*B35)*B29*B44)/1000000/(B30*B31*B32)/B33"
    sh.range(
        "C42"
    ).value = "=(B2*C45+B3*C47+(1-B34*C50*B35)*B29*C44)/1000000/(B30*B31*B32)/B33"

    sh.range("A43").value = "Weight-independent fuel consumption (MJ)"
    sh.range("B43").value = "=(B4/B33*B46)/1000000/(B30*B31*B32)+B36*B48/1000000"
    sh.range("C43").value = "=(B4/B33*C46)/1000000/(B30*B31*B32)+B36*C48/1000000"

    if parameters["city_driving_ratio"]["value"]:
        city_drive_ratio = parameters["city_driving_ratio"]["value"]
    else:
        city_drive_ratio = parameters["city_driving_ratio"]["default"]

    sh.range("B49").value = city_drive_ratio
    sh.range("C49").value = 1 - city_drive_ratio

    # Change target battery pack power parameter:
    wb.sheets["Dashboard"].range(design_column + "33").value = "='Vehicle model'!B12"
    wb.sheets["Dashboard"].range(
        design_column + "40"
    ).value = "=IF(D56=0, 250,'Vehicle model'!B24)"
