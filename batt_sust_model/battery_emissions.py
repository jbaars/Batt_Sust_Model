import hashlib
import brightway2 as bw
import pandas as pd
import numpy as np
from bw2data.parameters import ActivityParameter, ProjectParameter, Group
from pathlib import Path
from bw2io.package import BW2Package
import bw2data
import re


# defined cut-off modules:
parent = Path(__file__).parents[0]
df_cut_off_modules = pd.read_csv(parent / "data/cut_off_modules.csv").set_index("process")

# Process formula:
process_formula = pd.read_csv(parent / "data/process_formulas.csv", index_col=[1, 2]).T.to_dict()


def import_db_brightway(data_path=None):
    """Imports required Brightway databases in BW2package format

    Parameters
    ----------
    data_path : str, optional
        Path to BW2Package battery db, by default None and takes relative path
    """

    if data_path is None:
        rel_path = "data/bw2package"
        parent = Path(__file__).parents[0]
        bw_db = parent / rel_path
    else:
        bw_db = data_path

    path_list = Path(bw_db).glob("**/*.bw2package")
    for path in path_list:
        db_name = BW2Package.load_file(path)[0]["name"]
        if db_name in bw.databases:
            print(db_name, " already present")
            continue
        else:
            print ('Importing ', db_name)
            BW2Package.import_file(path)


def export_brightway_data(project_name, path, ecoinvent_db_name):
    """Export all Brightway databases to BW2Package format

    Args:
        project_name (str): BW name for project
        path (str): local path where databases should be saved to
        ecoinvent_db_name (str): name of ecoinvent in the BW project (e.g. 'eidb 3.7.1')

    Returns:
        All databases in project except ecoinvent and biosphere

    """
    from bw2io.package import BW2Package

    project = bw.projects.set_current(project_name)
    for database in bw.databases:
        db_temp = bw.Database(database)
        if database == "biosphere3" or database == ecoinvent_db_name:
            continue
        BW2Package.export_obj(db_temp, database, folder=path)


def exchange_name(activity_input):
    """Get name of exchange product based on exchange input (e.g. 'exchange_1'['input'])"""
    db = bw.Database(activity_input[0])
    activity = db.get(activity_input[1])
    return activity["reference product"]


def output_excel_activity_browser(scenario_name, dict_output_bw_format, path=None):
    """Output of battery design in Activity Browser Excel format for parameter scenario input.

    Import the Excel file into Activity Browser -> Parameters -> Scenarios -> 'Import parameter-scenarios'

    Args:
        scenario_name (str): name of battery design scenario (header for Excel sheet)
        dict_output_bw_format (dict): dictionary of battery design model output in Brightway format
        path (str): Path to store the Excel file.

    Returns:
        Activity Browser Excel parameter file used for the scenario import function. Default name is 'battery_design_output'
    """
    bw.projects.set_current("parameterised_battery_lca")
    param_name = [x.name for x in ProjectParameter]
    default_value = [x.amount for x in ProjectParameter]
    df = pd.DataFrame(columns=["Name", "Group", "default"])
    df["Name"] = param_name
    df["Group"] = "project"
    df["default"] = default_value
    df[scenario_name] = 0
    df.set_index("Name", inplace=True)
    for param in dict_output_bw_format.keys():
        df.loc[param, scenario_name] = dict_output_bw_format[param]
    if path is None:
        df.to_excel("battery_design_output.xlsx")
    else:
        df.to_excel(rf"{path}\battery_design_output.xlsx")


def import_project_parameters(path_parameter_file=None):
    """Import all default Project parameters from Excel into Brightway and recalculate parameters

    Parameters
    ----------
    path_parameter_file : str, optional
        Path to Brightway project parameter file, by default None
    """
    if path_parameter_file is None:
        rel_path = "data/bw_default_project_parameters.xlsx"
        parent = (Path(__file__)).parents[0]
        bw_db = parent / rel_path
    else:
        bw_db = path_parameter_file
    df = pd.read_excel(bw_db).fillna(0)
    ProjectParameter.drop_table(safe=True, drop_sequences=True)  # delete all project parameters
    ProjectParameter.create_table()  # create a new empty table of project parameters
    output = []
    for ix in df.index:
        name = df.loc[ix, "name"]
        amount = df.loc[ix, "amount"]
        if df.loc[ix, "formula"] != 0:
            formula = df.loc[ix, "formula"]
            output.append({"name": name, "amount": amount, "formula": formula})
        else:
            output.append({"name": name, "amount": amount})
    bw2data.parameters.new_project_parameters(output)
    ProjectParameter.recalculate("project")


def import_activity_functions(df_bw_param_functions):
    """Update Brightway activity formulas with formulas from DataFrame

    Follows same logic as Activity Browser: if activity is parameterised, generates activity parameter (if not present).
    Code from Activity Browser is adopted to assure comptability between Brightway and Activity Browser parameters.

    Parameters
    ----------
    df_bw_param_functions : Dataframe
        Dataframe with activity, product name and the formula
    """

    di = df_bw_param_functions.T.to_dict()
    for x in di.keys():
        db = bw.Database(di[x]["database"])
        act = [act for act in db if act["name"] == di[x]["activity"]][0]
        for exc in act.exchanges():
            if exc["type"] == "biosphere":
                continue
            elif exchange_name(exc["input"]) == di[x]["exchange"]:
                exc.update({"amount": 0})
                exc.update({"formula": di[x]["formula"]})
                exc.save()
            else:
                pass
        parameterise_exchanges(act.key)
    ProjectParameter.recalculate("project")


def add_activity_parameters(database_name):
    """Reset all activities in database modules based on the formula

    Parameters
    ----------
    database_name : str
        Brightway database name
    """
    db = bw.Database(database_name)
    for act in db:
        exc_list = [exc for exc in act.exchanges() if "formula" in list(exc)]  # Check if one of the exchanges has formula
        if exc_list:
            parameterise_exchanges(act.key)
        continue


def parameterise_exchanges(key):
    """Used whenever a formula is set on an exchange in an activity.

    If no `ActivityParameter` exists for the key, generate one immediately.
    Function modified from Activity Browser.

    Args:
        key (tuple): activity key
    """
    group = build_activity_group_name(key)

    if not (ActivityParameter.select().where(ActivityParameter.group == group).count()):
        auto_add_parameter(key)

    act = bw.get_activity(key)

    with bw.parameters.db.atomic():
        bw.parameters.remove_exchanges_from_group(group, act)
        bw.parameters.add_exchanges_to_group(group, act)
        ActivityParameter.recalculate_exchanges(group)


def build_activity_group_name(key, name=None):
    """Constructs a group name unique to a given bw activity.

    If given a `name`, use that instead of looking up the activity name. Function from Activity Browser.

    Args:
        key (tuple): activity key
        name (str): activity group name

    """
    simple_hash = hashlib.md5(":".join(key).encode()).hexdigest()
    if name:
        return "{}_{}".format(name, simple_hash)
    act = bw.get_activity(key)
    clean = clean_activity_name(act.get("name"))
    return "{}_{}".format(clean, simple_hash)


def clean_activity_name(activity_name):
    """Takes a given activity name and remove or replace all characters not allowed to be in there.

    Use this when creating parameters, as there are specific characters not allowed to be in parameter names.
    These are ' -,.%[]/+' Integers are also removed aggressively, there are allowed, but not at the start of a
    parameter name. Function from Activity Browser.

    Args:
        activity_name (str): activity name
    """
    remove = ",.%[]()0123456789/+"
    replace = " -"
    # Remove invalid characters
    for char in remove:
        if char in activity_name:
            activity_name = activity_name.replace(char, "")
    # Replace spacing and dashes with underscores
    for char in replace:
        if char in activity_name:
            activity_name = activity_name.replace(char, "_")
    # strip underscores from start of string
    activity_name = activity_name.lstrip("_")
    return activity_name


def auto_add_parameter(key):
    """Given the activity key, generate a new row with data from the activity and immediately call
    `new_activity_parameters`.

    Function from Activity Browser.

    Args:
       key (tuple): activity key
    """
    act = bw.get_activity(key)
    prep_name = clean_activity_name(act.get("name"))
    group = build_activity_group_name(key, prep_name)
    count = ActivityParameter.select().where(ActivityParameter.group == group).count()
    row = {
        "name": "{}_{}".format(prep_name, count + 1),
        "amount": act.get("amount", 1.0),
        "formula": act.get("formula", ""),
        "database": key[0],
        "code": key[1],
    }
    # Save the new parameter immediately.
    bw.parameters.new_activity_parameters([row], group)


def update_param_battery_bw(parameter_dict):
    """Update and recalculate all Brightway activity and project formulas based on design dictionary.

    Parameters
    ----------
    parameter_dict : dict
        Battery design dictionary.
    """
    bw_project_param = [x.name for x in ProjectParameter.select()]
    for param in parameter_dict.keys():
        if param in bw_project_param:
            select = [x for x in ProjectParameter.select() if x.name == param][0]
            select.amount = parameter_dict[param]
            select.save()
        else:
            continue
    ProjectParameter.recalculate()
    for a in Group.select():
        try:
            ActivityParameter.recalculate(a.name)
        except:
            pass


def output_as_bw_param(parameter_dict):
    """Output battery design to Brightway parameter names.

    Parameters
    ----------
    parameter_dict : dict
        Dictionary of battery design parameters, output of BatPaC

    Returns
    -------
    dict
        Dictionary of BW battery design parameters with non-alphanumeric keys. Keys match Brightway project parameters.
    """

    material_content_dict = parameter_dict["material_content_pack"]
    general_parameters = parameter_dict["general_battery_parameters"]
    return_dic = {}
    for key in material_content_dict.keys():
        new_key = re.sub("[^0-9a-zA-Z]+", "_", key)
        if new_key[-1] == "_":  # Remove underscore if last index
            new_key = new_key[0:-1]
        return_dic[new_key.lower()] = material_content_dict[key]
    return_dic["battery_capacity"] = general_parameters["pack_energy_kWh"]
    return return_dic


def update_formulas(project_parameters):
    """Recalculates the project parameter and activity formulas

    Parameters
    ----------
    project_parameters : dict
        Brightway project parameter values

    Returns
    -------
    dict
        Dictionary with updated activity amounts
    """
    output_dict = {}
    project_param_dict = {}
    for param in ProjectParameter:
        project_param_dict[param.name] = {
            "amount": param.amount,
            "formula": param.formula,
        }
    design_dict = project_parameters

    # update the amount in the project parameter dictionary based on battery design:
    for param in design_dict["design_parameters"].keys():
        project_param_dict[param]["amount"] = design_dict["design_parameters"][param]
    # Update project parameters with formulas:
    parameter_dictionary = calc_project_formulas(project_param_dict)

    # Update all activity formulas based on project parameters:

    for key in func_dict.keys():
        if func_dict[key]["material_group"] == "reference product":
            # Output/reference product is positive
            amount = eval(func_dict[key]["formula"], parameter_dictionary)
        else:
            # Input is negative
            amount = -eval(func_dict[key]["formula"], parameter_dictionary)
        output_dict[key] = amount
    return output_dict


def emissions_per_module(technology_matrix_default, pre_calculated_modules, battery_design_dictionary):
    updated_act = update_formulas(battery_design_dictionary)
    battery_weight = battery_design_dictionary["design_parameters"]["battery_pack"]
    A_matrix = technology_matrix_default.copy(deep=True)  # To make sure the default A dataframe is not modified
    h = pre_calculated_modules
    bat_product_act = [act["name"] for act in bw.Database("battery_production")]

    for idx in A_matrix.index:
        for col in A_matrix.columns:
            if (col, idx) in updated_act.keys() and col in bat_product_act:
                A_matrix.loc[idx, col] = updated_act[(col, idx)] / battery_weight
            elif (col, idx) in updated_act.keys():
                A_matrix.loc[idx, col] = updated_act[(col, idx)]
    A_inv = ev_lca.inverse_technology_matrix(A_matrix.fillna(0))
    y = pd.Series(data=0, index=A_matrix.index)
    y.loc["battery pack"] = battery_weight
    s = A_inv.dot(y)
    q = h[:, 2] * s
    return q


def get_exc_name(key_tuple):
    db = list(key_tuple)[0]
    code = list(key_tuple)[1]
    return bw.Database(db).get(code)["name"]


def get_exc_product(key_tuple):
    db = list(key_tuple)[0]
    code = list(key_tuple)[1]
    return bw.Database(db).get(code)["reference product"]


def modules_with_cuts(cut_off_database):
    """Returns dictionary of process name as key, values:'key' 'output', 'amount', 'cuts'

        cuts = [parent key, product name, exchange amount]
        if parent process is present in the cut-off database, the exchange is added to the 'cuts' list

        Inputs to modules are those products present in the 'cuts_database'. All other products in process are not included.

    'product', 'process', 'amount'
    Input is negative.. ; waste output is positive

    """
    modules = {}
    cuts_db = bw.Database(cut_off_database)
    for act in cuts_db:
        act_key = (act["database"], act["code"])
        process = act["name"]
        product = act["reference product"]
        act_cuts = {}
        act_output = [exc["amount"] for exc in act.exchanges() if exc["type"] == "production"][0]
        for exc in act.exchanges():
            key = exc["input"]
            parent_act = bw.get_activity(key)
            if key[0] == cut_off_database and act != parent_act:  # if input is present in cut-off database and not the reference product:
                if exc["amount"] > 0:  # If exchange is not waste (negative in Brightway):
                    act_cuts[parent_act.key] = [
                        parent_act["reference product"],
                        -exc["amount"],
                    ]  # negative for input positive for output
                elif exc["amount"] < 0:
                    act_cuts[parent_act.key] = [
                        parent_act["reference product"],
                        -exc["amount"],
                    ]  # positive for outputs (negative in BW)
            else:
                pass
        modules[process] = {
            "key": act_key,
            "output": product,
            "amount": act_output,
            "cuts": act_cuts,
        }
    return modules


def get_lcia_score(key, amount, impact_category):
    activity = bw.get_activity(key)  # get activity by db and code name
    fu = {activity: amount}
    lca = bw.LCA(fu, impact_category)
    lca.lci()
    lca.lcia()
    return lca.score


def modular_technology_matrix(modules_dict):
    """Return modular technology matrix"""
    product_rows = [x["output"] for x in modules_dict.values()]
    process_cols = [x for x in modules_dict.keys()]
    df = pd.DataFrame(index=product_rows, columns=process_cols).fillna(0)

    for process in modules_dict.keys():
        df.loc[modules_dict[process]["output"], process] = modules_dict[process]["amount"]
        for product in modules_dict[process]["cuts"].values():
            df.loc[product[0], process] = product[1]
    return df


def inverse_technology_matrix(pd_matrix):
    df_inv = pd.DataFrame(np.linalg.pinv(pd_matrix.values), pd_matrix.columns, pd_matrix.index)
    return df_inv


def cut_modules_to_zero(modules_dict):
    """Cuts parameterised modules to zero..

    Update the module input amounts based on cuts. All cut exchanges are set to zero, rest remains the same"""
    for module in modules_dict.keys():
        if modules_dict[module]["cuts"]:
            act = bw.get_activity(modules_dict[module]["key"])
            cut_exchanges = [exc for exc in act.exchanges() if exc["input"] in modules_dict[module]["cuts"].keys()]
            for cut_exc in cut_exchanges:
                try:  # Exchanges with formulas
                    if cut_exc["formula"] is not None:
                        cut_exc["amount"] = 0  # Amount to zero for cut-off modules
                        cut_exc.save()
                except KeyError:  # If exchange has no formula, set formula to amount
                    # make new activity parameter:
                    cut_exc["formula"] = cut_exc["amount"]
                    cut_exc.save()
                    bw.parameters.add_exchanges_to_group("my group", act)
                    cut_exc["amount"] = 0
                    cut_exc.save()


def lcia_modules(modules_dict, impact_category):
    """Calculate the module LCIA score.

    Args:
        modules_dict (dict): dictionary of cut modules
        impact_category (str or list): Impact category can be single or several impact categories

    Returns:
        numpy array
    """
    if not isinstance(impact_category, list):
        impact_category = [impact_category]
    list_fu = [{bw.get_activity(modules_dict[act]["key"]): modules_dict[act]["amount"]} for act in modules_dict.keys()]
    bw.calculation_setups["multi_lca"] = {"inv": list_fu, "ia": impact_category}
    MultiLCA = bw.MultiLCA("multi_lca")
    return MultiLCA.results


def calc_project_formulas(param_dict):
    """Calculates the project parameter formulas recursively.

    Args:
        param_dict (dict): parameter dictionary

    Return:
        dictionary with parameter name (key) and amount (value)
    """
    param_dict_2 = {a: b["amount"] for a, b in param_dict.items() if b["formula"] == 0}

    for param in param_dict.keys():
        if param_dict[param]["formula"] != 0:

            def calc_amount_formula(param, param_dict_2):
                """Calls itself if parameter name in formula is also based on formula"""
                try:
                    amount = eval(param_dict[param]["formula"], param_dict_2)
                    return amount
                except NameError as Argument:
                    param_error = re.split("['']", str(Argument))[1]
                    amount = calc_amount_formula(param_error, param_dict_2)
                    param_dict_2[param_error] = amount
                    amount = calc_amount_formula(param, param_dict_2)
                    return amount

            amount = calc_amount_formula(param, param_dict_2)
            param_dict[param]["amount"] = amount
            param_dict_2[param] = amount
    param_dict_amount = {a: b["amount"] for a, b in param_dict.items()}
    return param_dict_amount


# Calculate and append parameters to dictionary (project parameters in Brightway):


def project_parameters_brightway(path_parameter_file=None):
    """Returns dictionary with amount and formula of the Brightway project parameter"""
    if path_parameter_file is None:
        rel_path = "data/bw_default_project_parameters.xlsx"
        parent = (Path(__file__)).parents[0]
        path = parent / rel_path
    else:
        path = path_parameter_file
    df = pd.read_excel(path, index_col=0).fillna(0)

    project_param_dict = df.T.to_dict()
    return project_param_dict


def update_project_parameter_amount(project_param_dict, design_dict):
    """Update the 'amount' in the Brightway project parameter dictionary based on battery design"""
    for param in design_dict.keys():
        if param in project_param_dict.keys():
            project_param_dict[param]["amount"] = design_dict[param]
    return project_param_dict


def update_project_parameter_formulas(project_parameters_formulas):
    """Calculates the project parameter formulas recursively.

    Args:
        project_parameters_dict (dict): dictionary with Brightway project parameters

    Return:
        dictionary with parameter name (key) and amount (value)
    """
    param_dict_2 = {a: b["amount"] for a, b in project_parameters_formulas.items() if b["formula"] == 0}
    for param in project_parameters_formulas.keys():
        if project_parameters_formulas[param]["formula"] != 0:

            def calc_amount_formula(param, param_dict_2):
                """Recursive function, calls itself if parameter name in project formula is based on a different formula"""
                try:
                    amount = eval(project_parameters_formulas[param]["formula"], param_dict_2)
                    return amount
                except NameError as Argument:
                    param_error = re.split("['']", str(Argument))[1]
                    amount = calc_amount_formula(param_error, param_dict_2)
                    param_dict_2[param_error] = amount
                    amount = calc_amount_formula(param, param_dict_2)
                    return amount

            amount = calc_amount_formula(param, param_dict_2)
            project_parameters_formulas[param]["amount"] = amount
            param_dict_2[param] = amount
    param_dict_amount = {a: b["amount"] for a, b in project_parameters_formulas.items()}
    return param_dict_amount


def get_project_parameters_dict(design_dict, project_param_dict=None):
    """Returns a dictionary of the Brightway project parameters based on design parameter amounts and calculated project formulas

    Parameters
    ----------
    design_dict : dict
        battery design parameters in Brightway format.
    project_parameters_dictionary : dict
        Default project parameter dictionary with amounts and formulas. Use this for iteration.

    Returns
    -------
    dict
        parameter name and amount
    """

    if project_param_dict is None:
        project_param_dict = project_parameters_brightway()
    # update 'amount' in project parameter based on design dictionary:
    project_param_dict_update = update_project_parameter_amount(project_param_dict, design_dict)
    # Update project parameters with formulas:
    parameter_dictionary = update_project_parameter_formulas(project_param_dict_update)
    return parameter_dictionary


def update_module_formulas(design_dict, activity_functions):
    """Updates parameterised modules based on activity formulas and project parameters

    Args:
        project_parameters (dict): Brightway project parameter values. Formulas are already solved.
        activity_functions (dict): Brightway activity functions

        project_parameter_formula : Dict
        Dictionary with ProjectParameter formulas, Default is None and local data file is obtained
    Returns:
        Dictionary with updated activity amounts
    """
    output_dict = {}

    # Update all activity formulas based on project parameters:
    for key in activity_functions.keys():
        if activity_functions[key]["material_group"] == "reference product":
            # Output/reference product is positive
            amount = eval(activity_functions[key]["formula"], design_dict)
        else:
            # Input is negative
            amount = -eval(activity_functions[key]["formula"], design_dict)
        output_dict[key] = amount
    return output_dict


def update_parameterised_modules(technology_matrix_base, battery_design_dict, activity_functions_dict):
    """Updates modules based on functions with design specific parameters

    Args:
        technology_matrix_base (df): base product-module matrix (A_prime)
        battery_design_dict (dict): dictionary of activity project parameters
        activity_functions (dict): dictionary of parameterised modules (based on functions) including

    Return:
        df: updated square product-module matrix
    """
    updated_act = update_module_formulas(battery_design_dict, activity_functions_dict)
    battery_weight = battery_design_dict["battery_pack"]
    A_matrix = technology_matrix_base.copy(deep=True)  # To make sure the default A dataframe is not modified
    bat_product_act = [act["name"] for act in bw.Database("battery_production")]

    for idx in A_matrix.index:
        for col in A_matrix.columns:
            if (col, idx) in updated_act.keys() and col in bat_product_act:
                A_matrix.loc[idx, col] = updated_act[(col, idx)] / battery_weight
            elif (col, idx) in updated_act.keys():
                A_matrix.loc[idx, col] = updated_act[(col, idx)]

    return A_matrix


def calculate_modular_A(
    technology_matrix_default,
    battery_design_dictionary,
):
    """Calculates the parameterised activities based on BW project parameters
    Parameters
    ----------
    technology_matrix_default : pd DataFrame
        Default A matrix
    battery_design_dictionary : Dict
        All design parameters, match the Brightway ProjectParameters. Project formulas must be solved already!

    Returns
    -------
    Numpy array
        Technology matrix of specific battery design
    """

    A_default = technology_matrix_default
    updated_act = update_module_formulas(battery_design_dictionary, process_formula)
    A_new = technology_matrix_default.values
    # Establish A frame for battery production. Production processes and process outputs (reference products)
    for k, v in updated_act.items():
        if k[0] in A_default.columns:
            process_index = A_default.columns.get_loc(k[0])
        if k[1] in A_default.index:
            product_index = A_default.index.get_loc(k[1])
        A_new[product_index, process_index] = v
    return A_new


def get_emissions_modular_matrix(A_base, A_matrix_design, modular_emissions, return_vector=False):
    """Emissions of modular numpy matrix

    Parameters
    ----------
    A_default : Dataframe
        Default technology matrix
    A_matrix_design : Numpy array
        Technology matrix of specific battery design (product*module)
    modular_emissions : Numpy array
        Vector of module emissions (impact category*module)
    return_vector : bool, optional
        Returns emissions in matrix format (product*module), by default False

    Returns
    -------
    float
        Emission of system
    """
    pack_idx = A_base.index.get_loc("battery pack")
    assembly_idx = A_base.columns.get_loc("module and pack assembly")
    pack_weight = A_matrix_design[pack_idx, assembly_idx]
    # Inverse the A' matrix:
    A_inv = np.linalg.pinv(A_matrix_design)

    # Establish final product demand vector for 1 battery based on pack weight
    y_prime = np.zeros(len(A_base.index))
    y_prime[pack_idx] = pack_weight

    # Calculate scaling vector:
    s_prime = A_inv.dot(y_prime)

    if return_vector is False:
        h = s_prime.dot(modular_emissions)
    else:
        h = s_prime * modular_emissions
    return h


def parameter_dictionary(
    material_content_battery,
    process_parameters,
    battery_parameters,
    project_formulas=None,
):
    """Returns all system design parameters of specific battery design.
    Brightway Project parameters in non-alphanumeric parameters

    return:

    Single dictionary with all battery  parameters
    """
    if project_formulas is None:
        rel_path = "data/bw_default_project_parameters.xlsx"
        parent = (Path(__file__)).parents[0]
        path = parent / rel_path
        df = pd.read_excel(path, index_col=0).fillna(0)
        df.T.to_dict()
        project_formulas = project_formulas
    else:
        project_formulas = project_formulas

    return_dic = {}
    return_dic["design_parameters"] = {}

    # Change battery design parameter name to Brightway ProjectParameter names (non-alpanumeric)
    for key in material_content_battery.keys():
        new_key = re.sub("[^0-9a-zA-Z]+", "_", key)
        if new_key[-1] == "_":  # Remove underscore if last index
            new_key = new_key[0:-1]
        return_dic["design_parameters"][new_key.lower()] = material_content_battery[key]
    # Append process and battery design parameters:
    return_dic["design_parameters"].update(process_parameters)
    return_dic["design_parameters"].update(battery_parameters)
    # Calculate project parameters:
    return_dic["project_param"] = get_project_parameters_dict(return_dic["design_parameters"], project_param_dict=project_formulas)

    return_dic_all = {
        **return_dic["design_parameters"],
        **return_dic["project_param"],
    }

    return return_dic_all


# end
