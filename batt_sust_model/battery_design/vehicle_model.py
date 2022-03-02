def battery_design_column(vehicle_type):
    """Returns the column of the BatPaC Designsheet based on vehicle type. EV = battery 5, rest is battery 1"""  ##INCORRECT.. REMOVE THIS !!!!!!!!!!!!!!!!!!!!!!
    column = (
        "K" if vehicle_type == "EV" else "G"
    )  # Battery design column based on vehicle type
    return column


def append_sheet_vehicle_model(
    parameter_dictionary, batpac_workbook, design_column="H"
):
    wb = batpac_workbook
    sheets = [sheet.name for sheet in wb.sheets]
    parameters = parameter_dictionary

    if "Vehicle model" in sheets:
        # Change target battery pack power parameter:
        wb.sheets["Dashboard"].range(
            design_column + "38"
        ).value = "='Vehicle model'!B12"
        wb.sheets["Vehicle Considerations"].range(
            "B37"
        ).value = "=IF(Restart__0_1=0, 250,'Vehicle model'!B24)"
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

    sh.range("A5").value = "Vehicle range (miles)"
    sh.range("B5").value = parameters["vehicle_range_miles"]["value"]

    # Change range from miles to km to match vehicle model:
    sh.range("A28").value = "Range (km)"
    sh.range("B28").value = sh.range("B5").value * 1.609344
    # Remove storage requirement from Dashboard:
    wb.sheets["Dashboard"].range(design_column + "51").value = ""
    wb.sheets["Dashboard"].range(design_column + "52").value = ""

    # Range not present anymore in V5. Include range calculation to capacity estimating and Capacity columns:
    for c in ["G", "H", "I", "J", "K", "L", "M"]:
        old_454 = wb.sheets["Battery Design"].range(c + "454").formula
        new_454 = old_454.strip("))") + (
            f",'Vehicle model'!B28/1.609344*{c}449/{c}450*100/{c}30*{c}25*{c}29/{c}146))"
        )
        wb.sheets["Battery Design"].range(c + "454").value = new_454
        old_455 = wb.sheets["Battery Design"].range(c + "455").formula
        new_455 = old_455.strip("0)))") + (
            f"IF({c}451='Vehicle model'!B28/1.609344,{c}456,{c}456-{c}455*({c}451-\
                'Vehicle model'!B28/1.609344)/'Vehicle model'!B28/1.609344))))"
        )  # km to miles
        wb.sheets["Battery Design"].range(c + "455").value = new_455

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
    sh.range(
        "B13"
    ).value = f"='Battery Design'!{battery_design_column(parameter_dictionary['vehicle_type']['value'])}479/1000"

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
    sh.range("B27").value = "=IF(Dashboard!D6=0, 1,B28*B22/B37/3.6)"

    sh.range("A29").value = "Vehicle mass (kg)"
    sh.range("B29").value = "=F9"

    sh.range("A35").value = "regen_breaking_efficiency*charging_Efficiency"
    sh.range("B35").value = "=B34*B25"

    sh.range("A37").value = "Capacity accessible ratio"
    sh.range("B37").value = "=Dashboard!I34/100"

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
    wb.sheets["Dashboard"].range(design_column + "38").value = "='Vehicle model'!B12"
    wb.sheets["Battery Design"].range(
        battery_design_column(parameter_dictionary["vehicle_type"]["value"]) + "448"
    ).value = "=IF(Restart__0_1=0, 250,'Vehicle model'!B24)"
