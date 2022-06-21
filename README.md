# Battery Sustainability Model
> **ADD PUBLICATION**


Integrated modelling framework for lithium-ion batteries to calculate costs, emissions and material demands.

## Background

Model logic:
* User defined battery parameters (e.g. cathode active material, cell thickness) and vehicle parameters (e.g. driving range, size) are send to an updated version of [BatPaC v5](https://www.anl.gov/cse/batpac-model-software), returning the bill of materials
* User defined process parameters (e.g. manufacturing capacity, cell aging process yield) are used to estalish foreground system
* The bill of materials and foreground system are used to calculate the impact layers, including: value added, emission and substance flows


<p align="center">
<img src="https://github.com/jbaars2/Batt_Sust_Model/blob/main/docs/battery_model_overview.jpg" width="650">
</p>


## Usage

