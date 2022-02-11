
def internal_material_cost (internal_materials, materials, technology_matrix, external_cost_matrix):

    A = technology_matrix
    C = external_cost_matrix
    internal_unit_price={}
    for material in internal_materials:
        #EXCLUDE ENERGY!!!!!!!!!!!!!!!!!!!!!!
        process = [process for process in A.loc[material, :].index if A.loc[material, process]>0][0]  #name of the material process
        input_materials  = [material for material in materials if A.loc[material, process] < 0]       # all input materials of process

        if any(e in input_materials for e in internal_materials):                                      # if any of the input materials are internal materials:
            internal_input_materials = [e for e in input_materials if e in internal_materials]           #Filter the input material that is internal      

            def calculate_internal_price (int_material, internal_input_material, process):
                """ Changes the price of all internal materials in the C matrix based on the interal material input price and quantity required.
                    Internal material input price is the sum of material cost of activity inputs and system costs, divided by total physical quanity of material input. (MFCA ISO standard)

                """                                                                                    # If none of the internal materials is present in the internal_unit_price dicationary, 
                for m in internal_input_material:      
                    if m in internal_unit_price.keys():  
                        print ('here',m, internal_input_material)

                        amount                      = float(abs(C.loc[input_materials, process].sum() / A.loc[input_materials, process].sum()))
                        C.loc[material, :]         =  amount*A.loc[material, :]

                        return amount


                    else:
                        print (m)
                        #filter out which material in the internal input material is not present in the internal_unit_price dictionary/ which has not been calculated yet...
                        process = [process for process in A.loc[m, :].index if A.loc[m, process]>0][0] #get process of internal material without unit price calculation yet
                        input_materials_2  = [material for material in materials if A.loc[m, process] < 0] 
                        internal_input_material_2 = [e for e in input_materials_2 if e in internal_materials]  

                        amount = calculate_internal_price(m, internal_input_material_2, process)
    #                     print (amount, m)
                        return amount



    #         print (process)

            internal_unit_price [material] = calculate_internal_price(material, internal_input_materials, process)  # The internal material price is based on recursive function
    #         print (internal_unit_price)

        else:                                                                                          # None of the process inputs are internal materials              
            internal_unit_price [material] = float(abs(C.loc[input_materials, process].sum() / A.loc[input_materials, process].sum()))
            C.loc[material, :]             = float(internal_unit_price[material])*A.loc[material, :]
        

import numpy as np
import pandas as pd

test = np.array([[1, -5, -10], [0, 1, -6],[0,0,1]])
alpha = np.array([10, 0, 0])
test_df = pd.DataFrame(test)
internal_materials = [1,2]
A = pd.DataFrame(alpha)
C = test_alpha.values *test_df


internal_material_cost (internal_materials, A.index, A, C)








def output_materials_to_esankey (flow_matrix, waste_materials, waste_processes):
    """ """
    
    df = pd.DataFrame (columns = ['material','P_Start', 'P_End', 'layer', 'values'])

    count = 0
    for material in flow_matrix.index:
        p_start = [process for process in flow_matrix.columns if flow_matrix.loc[material, process] > 0]
        if material in waste_materials:
            p_start = [process for process in flow_matrix.columns if flow_matrix.loc[material, process] < 0 and 
                       process in waste_processes] #Waste always flows from process
        if not p_start: #skip materials
            continue
        else:
            for process in flow_matrix.columns:#
                value = flow_matrix.loc[material, process]
                if value < 0 and material not in waste_materials:
                    p_end = process
                    df.loc[count, 'material'] = material
                    df.loc[count, 'P_Start'] = p_start[0]
                    df.loc[count, 'P_End'] = p_end
                    df.loc[count, 'values'] = abs(value)
                elif value > 0 and material in waste_materials: 
                    print (material, p_start, value)

                    df.loc[count, 'material'] = material
                    df.loc[count, 'P_Start'] = process
                    df.loc[count, 'P_End'] = p_start[0] #waste flows from process to waste handling process
                    df.loc[count, 'values'] = abs(value)
                else:
                    continue
                count += 1        
    return df






def internal_material_cost (internal_materials, materials, technology_matrix, external_cost_matrix):

    A = technology_matrix
    A_m = external_cost_matrix
    internal_unit_price={}
    for material in internal_materials:
        process = [process for process in A.loc[material, :].index if A.loc[material, process]>0][0]  
        #name of the material process         #EXCLUDE ENERGY!!!!!!!!!!!!!!!!!!!!!!
        input_materials  = [material for material in materials if A.loc[material, process] < 0]       # all input materials of process

        if any(e in input_materials for e in internal_materials):
            # if any of the input materials are internal materials:
            internal_input_materials = [e for e in input_materials if e in internal_materials]          
            #Filter the input material that is internal      

            def calculate_internal_price (internal_input_material, input_materials, process):
                """ Changes the price of all internal materials in the C matrix based on the interal material 
                input price and quantity required.
                
                Internal material input price is the sum of material cost of activity inputs and system costs, divided by total physical quanity of material input. (MFCA ISO standard)

                """                                                                                    
                # If none of the internal materials is present in the internal_unit_price dicationary, 
                if not internal_input_material: #Empty list, intermediate materials are not internal materials
                    
                    unit_process_amount = float(abs((A_m.loc[input_materials, process].sum())) / abs(A.loc[input_materials, process].sum()))
                    
                    A_m .loc[material, :] = unit_process_amount*A.loc[material, :]
                    return unit_process_amount
                
                for m in internal_input_material:  
                    if m in internal_unit_price.keys():  
                        unit_process_amount = float(abs((A_m.loc[input_materials, process].sum()) / A.loc[input_materials, process].sum()))
                        
                        A_m.loc[material, :] =  unit_process_amount*A.loc[material, :]
                        return unit_process_amount

                    else:
                        #filter out which material in the internal input material is not present in the internal_unit_price dictionary/ which has not been calculated yet...
                        process = [process for process in A.loc[m, :].index if A.loc[m, process]>0][0] #get process of internal material without unit price calculation yet
                        input_materials_2  = [material for material in materials if A.loc[material, process] < 0] 
                        internal_input_material_2 = [e for e in input_materials_2 if e in internal_materials]  
                        print (m)
                        return calculate_internal_price(internal_input_material_2, input_materials_2,process)

            internal_unit_price [material] = calculate_internal_price(internal_input_materials, input_materials, process)
            A_m.loc[material, :] = float(internal_unit_price[material])*A.loc[material, :]


        else: # None of the process inputs are internal materials              
            internal_unit_price [material] = float(abs((A_m.loc[input_materials, process].sum())) 
                                                   / abs(A.loc[input_materials, process].sum()))
            
            A_m.loc[material, :]           = float(internal_unit_price[material])*A.loc[material, :]          
            
    return internal_unit_price

materials = IndexTable.loc['Goods', 'Classification'].Items
internal_materials =IndexTable.loc['Internal_goods','Classification'].Items

C_all = internal_material_cost(internal_materials, materials, A_matrix, C_matrix, b)