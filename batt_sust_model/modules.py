import brightway2 as bw
import pandas as pd
import numpy as np
import re 
from bw2data.parameters import ActivityParameter, DatabaseParameter, ProjectParameter, Group, ParameterManager


def get_exc_name (key_tuple):
    db = list(key_tuple)[0]
    code = list(key_tuple)[1]
    return bw.Database(db).get(code)['name']

def get_exc_product (key_tuple):
    db = list(key_tuple)[0]
    code = list(key_tuple)[1]
    return bw.Database(db).get(code)['reference product']
      
    
def modules_with_cuts (cut_off_database):
    """ Returns dictionary of process name as key, values:'key' 'output', 'amount', 'cuts'
        
        cuts = [parent key, product name, exchange amount]
        if parent process is present in the cut-off database, the exchange is added to the 'cuts' list
        
        Inputs to modules are those products present in the 'cuts_database'. All other products in process are not included.

    'product', 'process', 'amount'
    Input is negative.. ; waste output is also negative

    """
    modules={}  
    cuts_db = bw.Database(cut_off_database)
    for act in cuts_db:

        act_key =(act['database'], act['code'])
        process = act['name']
        product = act['reference product']
        
        act_cuts = {}
        act_output = [exc['amount'] for exc in act.exchanges() if exc['type']=='production' ][0]
        for exc in act.exchanges():
            key = exc['input']
            parent_act = bw.get_activity(key)
            if key[0] == cut_off_database and act != parent_act: #if activity name of exchange is present in cut-off database and not the reference product:
                print (act, exc['amount'])
                if exc['amount']>0: #If exchange is not waste (negative in Brightway):
                    act_cuts[parent_act.key] = [parent_act['reference product'],-exc['amount']] #negative for input positive for output  
                elif exc['amount']<0:
                    act_cuts[parent_act.key] = [parent_act['reference product'],exc['amount']]
            else:
                pass
        modules[process] = {'key': act_key,
                            'output':product, 
                            'amount': act_output,
                            'cuts':act_cuts
        } 
    return modules

def get_lcia_score(key, amount, impact_category):
    activity = bw.get_activity(key)  #get activity by db and code name
    fu = {activity:amount}
    lca=bw.LCA(fu, impact_category)
    lca.lci()
    lca.lcia()
    return lca.score  

def modular_technology_matrix (modules_dict):
    """ Return modular technology matrix"""
    product_rows = [x['output'] for x in modules_dict.values()]
    process_cols = [x for x in modules_dict.keys()]
    df=pd.DataFrame(index=product_rows, columns=process_cols).fillna(0)
    
    for process in modules_dict.keys():
        df.loc[modules_dict[process]['output'], process] = modules_dict[process]['amount']
        for product in modules_dict[process]['cuts'].values():
            df.loc[product[0], process]   = product[1]
    return df

def inverse_technology_matrix (pd_matrix):
    df_inv = pd.DataFrame(np.linalg.pinv(pd_matrix.values), pd_matrix.columns, pd_matrix.index)
    return df_inv

def cut_modules_to_zero (modules_dict):
    """ Update the module input amounts based on cuts. All cut exchanges are set to zero, rest remains the same"""
    for module in modules_dict.keys():
        if modules_dict[module]['cuts']:
            act = bw.get_activity(modules_dict[module]['key'])
            cut_exchanges = [exc for exc in act.exchanges() if exc['input'] in modules_dict[module]['cuts'].keys()]
            for cut_exc in cut_exchanges:
                # print (f"Cut {bw.get_activity(cut_exc['input'])['reference product']} from {bw.get_activity(cut_exc['output'])['name']}, amount set to ZERO")
                cut_exc['amount']=0 #Amount to zero for cut-off modules
                cut_exc.save()


def lcia_modules (modules_dict, impact_category):
    """ Calculate the module LCIA score. 
     
    Args:
        modules_dict (dict): dictionary of cut modules
        impact_category (str or list): Impact category can be single or several impact categories
        
    Returns:
        numpy array 
    """
    score_dict = {}
    if not isinstance(impact_category, list):
        impact_category = [impact_category]
    list_fu = [{bw.get_activity(modules_dict[act]['key']): modules_dict[act]['amount']} for act in modules_dict.keys()]
    bw.calculation_setups['multi_lca'] = {'inv': list_fu, 'ia': impact_category}
    MultiLCA = bw.MultiLCA('multi_lca')
    return MultiLCA.results


def lcia_modules_dataframe (lcia_score):
    """ Return dataframe with lcia score of modules"""
    score_rows ={method[2] for method, name in lcia_score.keys()}
    process_cols = {name for method, name in impact_all.keys()}
    df=pd.DataFrame(index=score_rows, columns=process_cols).fillna(0)
    
    for process in process_cols:
        for method in lcia_score.keys():
            df.loc[method[0][2], process]   = lcia_score[method[0], process]
    return df        

    


def update_formulas(battery_design_dictionary):
    """ Calculates the project parameter and activity formulas
    
    Args:
        battery_design_dictionary (dict): dictionary with battery design
        
    Returns:
        Dictionary with updated activity amounts
    """
    output_dict = {}
    design_dict = battery_design_dictionary
    #update the amount in the project parameter dictionary based on battery design:
    for param in design_dict['design_parameters'].keys():
        project_param_dict[param]['amount'] = design_dict['P'][param]
    #Update project parameters with formulas:
    parameter_dictionary =  calc_project_formulas(project_param_dict)  
    # Upate all activity formulas based on project parameters:
    for key in func_dict.keys():
        if func_dict[key]['material_group'] == 'reference product': 
            #Output/reference product is positive
            amount = eval(func_dict[key]['formula'], parameter_dictionary)   
        else: 
            #Input is negative
            amount = -eval(func_dict[key]['formula'], parameter_dictionary)
        output_dict[key] = amount 
    return output_dict

def calc_project_formulas(param_dict):
    """ Calculates the project parameter formulas recursively.
    
    Args:
        param_dict (dict): parameter dictionary
        
    Return:
        dictionary with parameter name (key) and amount (value)
    """
    param_dict_2= {a:b['amount'] for a, b in param_dict.items() if b['formula'] == 0}

    for param in param_dict.keys():
        if param_dict[param]['formula'] != 0:
            def calc_amount_formula(param,param_dict_2):
                """ Calls itself if parameter name in formula is also based on formula"""
                try:
                    amount=eval(param_dict[param]['formula'], param_dict_2)
                    return amount
                except NameError as Argument:
                    param_error = re.split("['']", str(Argument))[1]
                    amount = calc_amount_formula(param_error,param_dict_2 )
                    param_dict_2[param_error] = amount
                    amount = calc_amount_formula (param, param_dict_2)
                    return amount
            amount = calc_amount_formula(param,param_dict_2)    
            param_dict[param]['amount'] = amount
            param_dict_2[param] = amount
    param_dict_amount = {a:b['amount'] for a, b in param_dict.items()}
    return param_dict_amount


def calculate_lcia_module (technology_matrix_default, pre_calculated_modules, battery_design_dictionary):
    updated_act = update_formulas(battery_design_dictionary)
    battery_weight = battery_design_dictionary['design_parameters']['battery_pack']
    A_matrix = technology_matrix_default.copy(deep=True) # To make sure the default A dataframe is not modified
    h = pre_calculated_modules
    bat_product_act = [act['name'] for act in bw.Database('battery_production')]

    for idx in A_matrix.index:
        for col in A_matrix.columns:
            if (col, idx) in updated_act.keys() and col in bat_product_act:
                A_matrix.loc[idx, col] = updated_act[(col, idx)]/battery_weight
            elif  (col, idx) in updated_act.keys():
                A_matrix.loc[idx, col] = updated_act[(col, idx)]         
    A_inv=inverse_technology_matrix(A_matrix.fillna(0))
    y = pd.Series(data = 0, index=A_matrix.index)
    y.loc['battery pack']= battery_weight
    s = A_inv.dot(y)
    q=impact_all[:,2]*s

    return q
            