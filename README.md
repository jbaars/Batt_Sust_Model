# Battery Sustainability Model
> **ADD PUBLICATION**


Integrated modelling framework for lithium-ion batteries to calculate manufacturing costs, cradle-to-gate emissions and manufacturing substance flows.

## Background
The integrated modelling framework for batteries aims to address two current gaps:
* Different sustainability aspects modelled by different studies and disciplines
 * Complexity of battery design and design choices not included in current studies

The model logic is as follow. User defined battery parameters (e.g. cathode active material, cell thickness) and vehicle parameters (e.g. driving range, size) are send to an updated version of [BatPaC v5](https://www.anl.gov/cse/batpac-model-software). A vehicle model is added to your local BatPaC version automatically when vehicle parameters are defined. The BatPaC battery design model runs in the background by calculating the required battery capacity for the user specified design parameters and returns the battery bill of materials and design parameters. 

Next, process parameters (e.g. manufacturing capacity, cell aging process yield) are defined and used to estalish the foreground system. The bill of materials and foreground system are used to calculate the impact layers, including: value added, emission and substance flows and thereby the impact indicators. 


<p align="center">
<img src="https://github.com/jbaars2/Batt_Sust_Model/blob/main/docs/battery_model_overview.jpg" width="650">
</p>


## Usage

There are two ways to use the model. First, using Python code to develop your own models. Each satellite layer can be used in isolation (e.g. cost or emission layer) or in an integrated way. Several example notebooks are added to the repository:
* [Battery design notebook](https://github.com/jbaars2/Batt_Sust_Model/blob/main/example%20notebooks/Battery%20design/Example%20notebook%20battery%20design.ipynb): severak example of automating BatPaC and adding a vehicle model
