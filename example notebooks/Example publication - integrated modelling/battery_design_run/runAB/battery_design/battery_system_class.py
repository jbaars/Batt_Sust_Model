import pandas as pd
from pathlib import Path
import os


class Battery_system:
    """ " A class to establish a electric vehicle battery system based on BatPaC version 4.
    ...
    Args:
            parameter_file (str): path to parameter file, if None is relative to battery_design module
            vehicle_type (str): type of vehicle ('EV', 'PHEV', 'HEV-HP', 'microHEV')
            electrode_pair (str): anode and cathode active material type
            silicon_anode (int): add silicon to graphite anode (1-20%)
            graphite_type (str): synthetic or natural graphite. Default is synthetic
            unique_name (str) : optional name for system
            **kwargs: additional parameters as defined in the parameter_linkage document

    """

    def __init__(
        self,
        vehicle_type,
        electrode_pair,
        silicon_anode=None,
        graphite_type="synthetic",
        calculate_fast_charge="No",
        parameter_file=None,
        **kwargs,
    ):
        self.parameter_file = parameter_file
        self.vehicle_type = vehicle_type
        self.electrode_pair = electrode_pair
        self.calculate_fast_charge = calculate_fast_charge  # No fast charge by default
        self.silicon_anode = silicon_anode  # None by default
        self.graphite_type = graphite_type  # default is synthetic
        self.dict_df_batpac = (
            None  # dictionary of pd DataFrames containing updated BatPaC sheets
        )
        self.__dict__.update(kwargs)

    def parameter_dictionary(self):
        """Obtain the parameter index locations in BatPaC and adds class value to dictionary

        Returns:
            Dictionary of parameter location in BatPaC. Keys is parameter name, values is BatPaC location.
            ValueError if class attribute value is not within range according to parameter excel file
        """
        parameter_dict = {}
        if self.parameter_file is None:

            rel_path = "data/battery_design_parameters.xlsx"
            parent = Path(__file__).parents[1]
            parameter_file = (parent / rel_path).resolve()
        else:
            parameter_file = self.parameter_file

        if "df_parameters" not in globals():
            global df_parameters
            df_parameters = pd.concat(
                pd.read_excel(parameter_file, sheet_name=None), ignore_index=True
            )

        self.check_param_name(
            df_parameters
        )  # check if class parameters are present in Excel parameter file
        for parameter in df_parameters.index:
            parameter_name = df_parameters.loc[parameter, "Parameter name"]
            parameter_family = df_parameters.loc[parameter, "Parameter family"]
            sheet_name = df_parameters.loc[parameter, "BatPaC sheet"]
            description = df_parameters.loc[parameter, "Parameter description"]
            unit = df_parameters.loc[parameter, "Unit"]
            if "Default" in df_parameters.columns:
                default = df_parameters.loc[parameter, "Default"]
            else:
                default = 0

            value_range = df_parameters.loc[parameter, "Range"]
            row = df_parameters.loc[parameter, "Row"]
            column = df_parameters.loc[parameter, "Column"]
            value = self.get_param_value(parameter_name, value_range)
            parameter_dict[parameter_name] = {
                "parameter family": parameter_family,
                "description": description,
                "unit": unit,
                "range": value_range,
                "sheet": sheet_name,
                "column": column,
                "row": row,
                "value": value,
                "default": default,
            }
        return parameter_dict

    def get_param_value(self, parameter_name, value_range):
        """Check if parameter value is in value range and return value

        Class instance value should be in value range as defined in the Parameter_Linkage Excel sheet.

        Args:
            parameter_name (str): Name of the parameter as defined in the Parameter Linkage file
            value_range (str): Range of values for parameters as defined in the Parameter Linkage file

        Returns:
            Parameter value
        """
        if parameter_name in self.__dict__.keys():
            value = getattr(self, parameter_name)
            if value_range == "None":
                return value
            value_range = value_range.strip("'").split(",")
            if value_range[
                0
            ].isdigit():  # Convert ranges to integer, float or string list
                value_range = list(map(int, value_range))
            else:
                try:
                    value_range = list(map(float, value_range))
                except ValueError:
                    value_range = list(map(str, value_range))
            if value not in value_range:
                raise ValueError(
                    f"{parameter_name} with value: {value} is not within parameter range: {value_range}."
                    "Change the instance value or the value range in the parameter spreadsheet"
                )
            return value
        else:
            value = None
            return value

    def check_param_name(self, df_parameters):
        """Checks if the class argument names match the parameters in the Parameter Linkage file.

        Class instance variables not present in BatPaC (e.g. 'parameter_file') are excluded.
        Args:
            df_parameters (df): dataframe of parameters
        Returns:
            value error if class argument name does not match the ones defined in the Parameter Linkage file
        """
        non_batpac_arguments = [
            "parameter_file",
            "batpac",
            "visible",
            "add_silicon_content",
            "dict_df_batpac",
        ]
        for param in self.__dict__.keys():
            if (
                param not in list(df_parameters.loc[:, "Parameter name"])
                and param not in non_batpac_arguments
            ):
                raise ValueError(
                    f"Class attribute {param} not found in the parameter excel linkage"
                )
            pass


def print_battery_parameters(parameter_file_path=None):
    """Print the available battery design parameter and range as dataframe"""
    if parameter_file_path is None:
        rel_path = "data/battery_design_parameters.xlsx"
        parent = Path(__file__).parents[1]
        parameter_file_path = parent / rel_path

    df_parameters = pd.concat(
        pd.read_excel(parameter_file_path, sheet_name=None), ignore_index=True
    )

    xl = pd.ExcelFile(parameter_file_path)

    df_parameters = pd.concat(
        pd.read_excel(
            parameter_file_path,
            sheet_name=[sheet for sheet in xl.sheet_names if sheet != "Info"],
        ),
        ignore_index=True,
    )
    df_parameters = df_parameters.drop(
        ["BatPaC sheet", "Column", "Row", "Unit", "Note"], axis=1
    )

    return df_parameters.set_index("Parameter family")
