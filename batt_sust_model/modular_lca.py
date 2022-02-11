import hashlib
import pandas as pd
import numpy as np
from pathlib import Path
import re



def project_parameters_brightway (path_parameter_file = None):
    """ Returns dictionary with amount and formula of the Brightway project parameter"""
    if path_parameter_file is None:
        rel_path = "data/bw_default_project_parameters.xlsx"
        parent= (Path(__file__)).parents[0]
        path = parent / rel_path
    else:
        path = path_parameter_file
    df =pd.read_excel(path, index_col=0).fillna(0)    
    
    project_param_dict =  df.T.to_dict()
    return project_param_dict


def update_project_parameter_amount (project_param_dict, design_dict):
    """ Update the 'amount' in the Brightway project parameter dictionary based on battery design"""
    for param in design_dict.keys():
        if param in project_param_dict.keys():
            project_param_dict[param]['amount'] = design_dict[param]
    return project_param_dict


def update_project_parameter_formulas (project_parameters_formulas):
    """ Calculates the project parameter formulas recursively.
    
    Args:
        project_parameters_dict (dict): dictionary with Brightway project parameters
        
    Return:
        dictionary with parameter name (key) and amount (value)
    """
    param_dict_2= {a:b['amount'] for a, b in project_parameters_formulas.items() if b['formula'] == 0}
    for param in project_parameters_formulas.keys():
        if project_parameters_formulas[param]['formula'] != 0:
            
            def calc_amount_formula(param,param_dict_2):
                """ Recursive function, calls itself if parameter name in project formula is based on a different formula"""
                try:
                    amount=eval(project_parameters_formulas[param]['formula'], param_dict_2)
                    return amount
                except NameError as Argument:
                    param_error = re.split("['']", str(Argument))[1]
                    amount = calc_amount_formula(param_error,param_dict_2 )
                    param_dict_2[param_error] = amount
                    amount = calc_amount_formula (param, param_dict_2)
                    return amount
            amount = calc_amount_formula(param,param_dict_2)    
            project_parameters_formulas[param]['amount'] = amount
            param_dict_2[param] = amount
    param_dict_amount = {a:b['amount'] for a, b in project_parameters_formulas.items()}
    return param_dict_amount


def get_project_parameters_dict (design_dict, project_param_dict = None):
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
        project_param_dict = project_parameters_brightway()#
    else:
        project_param_dict = project_param_dict
    #update 'amount' in project parameter based on design dictionary:
    project_param_dict_update = update_project_parameter_amount (
        project_param_dict, design_dict)        
    #Update project parameters with formulas:
    parameter_dictionary =  update_project_parameter_formulas(project_param_dict_update)  
    
    return parameter_dictionary


def update_module_formulas (design_dict, activity_functions ):
    """ Updates parameterised modules based on activity formulas and project parameters 
    
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
        
        if activity_functions[key]['material_group'] == 'reference product': 
            #Output/reference product is positive
            amount = eval(activity_functions[key]['formula'], design_dict)   
        else: 
            #Input is negative
            amount = -eval(activity_functions[key]['formula'], design_dict)
        output_dict[key] = amount 
    return output_dict



def calculate_modular_A (technology_matrix_default, battery_design_dictionary, process_formula=None, project_parameter_formula=None):
    """ Calculates the parameterised activities based on BW project parameters
    Parameters
    ----------
    technology_matrix_default : pd DataFrame
        Default A matrix 
    battery_design_dictionary : Dict
        All design parameters, match the Brightway ProjectParameters. Project formulas must be solved already!
    process_formulas : Dict
        Dictionary with process formulas, Default is None and local data file is obtained
        
    Returns
    -------
    Numpy array
        Square technology matrix of specific battery design 
    """             
    if process_formula is None:
        rel_path        = "data/process_formulas.xlsx"
        parent          = (Path(__file__).parents[0])
        process_formula = parent / rel_path
        process_formula =pd.read_excel(process_formula, sheet_name = 'activity_functions', index_col=[1,2]).T.to_dict()
      
    A_default   = technology_matrix_default
    updated_act = update_module_formulas (battery_design_dictionary,
                                          process_formula)
    A_new        = technology_matrix_default.values
    
    # Establish A frame for battery production. Production processes and process outputs (reference products)
    for product in A_default.index:
        idx_prod = A_default.index.get_loc(product)
        for process in A_default.columns:
            idx_proc = A_default.columns.get_loc(process)
            if (process, product) in updated_act.keys():
                A_new[idx_prod, idx_proc] = updated_act[(process, product)]
    return A_new


def get_emissions_modular_matrix (A_base, A_matrix_design, modular_emissions, return_vector=False ):
    """ Emissions of modular numpy matrix

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
    pack_idx = A_base.index.get_loc('battery pack')
    assembly_idx = A_base.columns.get_loc('module and pack assembly')
    
    pack_weight = A_matrix_design[pack_idx, assembly_idx]

    #Inverse the A' matrix:
    A_inv = np.linalg.pinv(A_matrix_design)

    #Establish final product demand vector for 1 battery based on pack weight
    y_prime = np.zeros(len(A_base.index))
    y_prime[pack_idx] = pack_weight

    #Calculate scaling vector:
    s_prime = A_inv.dot(y_prime)
    if return_vector is False:
        h = s_prime.dot(modular_emissions)
    else:
        h = s_prime*modular_emissions
    return h
    


def parameter_dictionary (material_content_battery, process_parameters, battery_parameters, project_formulas = None):
    """ Returns all system design parameters in non-alphanumric format
    
    return:
    
    Single dictionary with all battery  parameters
    """ 
    if project_formulas is None:
        rel_path = "data/bw_default_project_parameters.xlsx"
        parent= (Path(__file__)).parents[0]
        path = parent / rel_path
        df = pd.read_excel(path, index_col=0).fillna(0)  
        df.T.to_dict()
        project_formulas = project_formulas
    else:
        project_formulas = project_formulas
        
    return_dic = {}
    return_dic['design_parameters'] = {}
    return_dic['general_parameters'] = {}

    #Change battery design parameter name to Brightway ProjectParameter names (non-alpanumeric)
    for key in material_content_battery.keys():
        new_key = re.sub('[^0-9a-zA-Z]+', '_', key)
        if new_key[-1] == '_':  # Remove underscore if last index
            new_key = new_key[0:-1]
        return_dic['design_parameters'][new_key.lower()] = material_content_battery[key]
    #Append process and battery design parameters:
    return_dic['design_parameters'].update (process_parameters)
    return_dic['general_parameters'].update(battery_parameters)
    #Calculate project parameters:
    return_dic['project_param'] = get_project_parameters_dict(return_dic['design_parameters'], project_param_dict=project_formulas)
    
    return_dic_all = {**return_dic['design_parameters'], **return_dic['general_parameters'], **return_dic['project_param']}
    
    return return_dic_all
    
    
    
    
    return return_dic
