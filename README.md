[![DOI](https://zenodo.org/badge/540456211.svg)](https://zenodo.org/badge/latestdoi/540456211)


# Battery Sustainability Model
Integrated model to calculate the manufacturing costs, cradle-to-gate emissions, technical performance and material criticality of of electric vehicle batteries.


## Background
The integrated modelling framework for batteries aims to address two current gaps:
* Different sustainability aspects modelled by different studies and disciplines
 * Complexity of battery design and design choices not included in current studies

The model logic is as follow: 
* User defined battery parameters (e.g. active material, cell thickness, foil thickness, etc) and vehicle parameters (e.g. driving range, vehicle size) are send to an updated version of [BatPaC v5](https://www.anl.gov/cse/batpac-model-software). A vehicle model is added to your local BatPaC version automatically when vehicle parameters are defined. The BatPaC battery design model runs in the background by calculating the required battery capacity for the user specified design parameters and returns the battery bill of materials and design parameters. 

* Next, process parameters (e.g. manufacturing capacity, cell aging process yield) are defined and used to estalish the foreground system. The bill of materials and foreground system are used to calculate the impact layers, including: value added, emission and substance flows and thereby the impact indicators. 


<p align="center">
<img src="https://github.com/jbaars/Batt_Sust_Model/blob/main/docs/battery_model_overview.jpg" width="650">
</p>


## Usage

`Python code:` <br>

Use Python code to develop your own models. Each impact layer can be used in isolation (e.g. cost or emission layer) or in an integrated way. Several example notebooks are added to the repository:
* [Battery design example](https://github.com/jbaars/Batt_Sust_Model/blob/main/example%20notebooks/Example%20battery%20design.ipynb): several examples of automating BatPaC and adding a vehicle model
* [Battery LCA example](https://github.com/jbaars/Batt_Sust_Model/blob/main/example%20notebooks/Example%20battery%20LCA.ipynb): Examples of parameterised and modular LCA by linking BatPaC to a Brightway LCA model
* [Battery cost example](https://github.com/jbaars/Batt_Sust_Model/blob/main/example%20notebooks/Example%20battery%20cost.ipynb ): Examples of calculating battery costs based on a Python version of the BatPaC cost model
* [Integrated modelling example](https://github.com/jbaars/Batt_Sust_Model/tree/main/example%20notebooks/Example%20publication%20-%20integrated%20modelling): Case study example of integrating cost, carbon footprint, performance and criticality. Notebook based on publication: Baars, J., Cerdas, F., Heidrich, O. (UNDER REVIEW). "An integrated model to conduct multi-criteria technology assessments: the case of electric vehicle batteries". Submitted to Environmental Science and Technology

`Graphical user interface:`<br>

Second way of interacting with the model is by using the online graphical user interface (GUI):
* http://battery-sustainability-app.herokuapp.com/
Over 20,000 thousand battery designs have been precalculated in BatPaC. The GUI allows users to change battery design (e.g. cathode type, foil thickness), process design (e.g. production location or scale) and impact parameter (e.g. cathode material price or material carbon footprint). Inventories and results can be downloaded. 
