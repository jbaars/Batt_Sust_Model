# Battery Sustainability Model
> **ADD PUBLICATION**


Integrated modelling framework for lithium-ion batteries to calculate costs, emissions and material demands.

## Background

Model logic:
* Step 1. Define battery parameters (e.g. cathode active material, cell thickness) and vehicle parameters (e.g. driving range, size)


Model utilises the [BatPaC version 5](https://www.anl.gov/cse/batpac-model-software) battery design model to automate the extraction of bill of materials (BOM) and performance parameters of user specific battery design parameters. The BOM is used as input to the battery cost (Python version of BatPaC cost model), LCA (Brightway2 model) and material criticality models. <br>


<p align="center">
<img src="https://github.com/jbaars2/Batt_Sust_Model/blob/main/docs/battery_model_overview.jpg" width="750">
</p>


## Usage

