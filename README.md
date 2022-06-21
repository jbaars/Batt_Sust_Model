# Battery Sustainability Model
> **ADD PUBLICATION**


Integrated modelling framework for lithium-ion batteries to calculate costs, emissions and material demands.

## Background

Model logic:
* User defined battery parameters (e.g. cathode active material, cell thickness) and vehicle parameters (e.g. driving range, size) are send to an updated version of [BatPaC v5](https://www.anl.gov/cse/batpac-model-software) and returns the bill of materials (BOM) and performance parameters
* User defined process parameters (e.g. manufacturing capacity, cell aging process yield) are used to estalish the material and energy flow system
*  
*    of user specific battery design parameters. The BOM is used as input to the battery cost (Python version of BatPaC cost model), LCA (Brightway2 model) and material criticality models. <br>


<p align="center">
<img src="https://github.com/jbaars2/Batt_Sust_Model/blob/main/docs/battery_model_overview.jpg" width="750">
</p>


## Usage

