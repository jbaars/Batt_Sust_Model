import dash
from dash import dcc
from dash import html
from dash import dash_table as dt
from textwrap import dedent
import dash_bootstrap_components as dbc

import pandas as pd
import battery_model as bat

from maindash import app
from callbacks_pack import *
from callbacks_process import *
from callback_process_cost import *
from callback_criticality import *

from datatable import *

import config


server = app.server
layout = {
    "cell_margin_bottom": "10px",
    "cell_margin_top": "5px",
    "bg_color": "#F2F2F2",
    "box_color": "#f9f9f9",
    "font_type": "Arial"
    # 'text': '#7FDBFF'
}

columns_data_table = [
    "Parameter",
    "Unit",
    "Pack 1"

]


electricity = {


    "Active material mixing": "electricity_consumption_mixing",
    "Electrode coating and drying": "electricity_consumption_coating_drying",
    "Electode calendering": "electricity_consumption_calendering",
    "Electrode slitting": "electricity_consumption_slitting",
    "Final drying": "electricity_consumption_final_drying",
    "Stacking": "electricity_consumption_stacking",
    "Material handling/operation others": "electricity_consumption_material_handling",
    "Dryroom operation": "electricity_consumption_dryroom",
    "Cell formation": "electricity_consumption_formation",

    "Cell assembly": "electricity_consumption_cell_assembly",

    "Module and pack assembly": "electricity_consumption_assembly",


}
heat = {'Coating and drying': "heat_consumption_coating_drying",
        "Final drying": "heat_consumption_final_drying",
        "Formation": "heat_consumption_formation",
        "Dry room": "heat_consumption_dryroom",
        }


process_yields = {
    "Active material, mixing": "py_am_mixing",
    "Cell, formation and aging": "py_cell_aging",
    "Electrode, stacking": "py_electrode_stacking",
    "Electrolyte, electrolyte filling": "py_electrolyte_filling",
    "Foil, electrode coating": "py_foil_coating",
    "Foil, electrode slitting": "py_foil_slitting",
    "NMP, NMP recovery": "py_nmp_recovery",
    "Separator, cell stacking": "py_separator_stacking",
    "Slurry, electrode coating": "py_slurry_coating",
    "Coating, electrode slitting": "py_slurry_slitting"

}


def energy_slider(id, heat=None):
    if heat == None:
        input_values = {"min": 100, "max": 2000, "multiplier": 1000}
    else:
        input_values = {"min": 100, "max": 2000, "multiplier": 277.78}

    div = html.Div(
        [
            html.P(id=f"{id}_output", className="control_label"),
            dcc.Slider(
                id=f"{id}_slider",
                min=input_values["min"],
                max=input_values["max"],
                value=config.dict_project_parameters[id]["amount"]
                * input_values["multiplier"],
            ),
        ],
        className="control_label_process_param",
        id=f"{id}_container",
        style={"display": "none"},
    )
    return div


def py_slider(id):
    default_value = config.dict_py_default[id]
    div = html.Div(
        [
            html.P(id=f"{id}_output", className="control_label"),
            dcc.Slider(
                id=f"{id}_slider",
                value=int(default_value * 100),
                min=90,
                max=100,
                step=1,
                marks={
                    90: "90%",
                    100: "100%",
                },),
        ],
        className="control_label_process_param",
        id=f"{id}_container",
        style={"display": "none"},
    )
    return div


def price_slider(id_param):
    default_value = float(config.df_mineral_prices.loc[id_param, 'used'])
    low = round(config.df_mineral_prices.loc[id_param, 'low'], 2)
    high = round(config.df_mineral_prices.loc[id_param, 'high'], 2)
    div = html.Div(

        [html.P(id=f"{id_param}_output", className="control_label"),
         dcc.Slider(
            id=f"{id_param}_slider",
            value=default_value,
            min=low,
            max=high,
            # step=5,
            marks={
                low*0.75: str(round(low*0.75, 0)),  # prices 25% lower and higher than historic
                high*1.25: str(round(high*1.25, 0)),
            },),
         ],
        className="control_label_process_param",
        id=f"{id_param}_price_container",
        style={"display": "none"},
    )
    return div


def build_modal_info_overlay(id, side, content, title=None):
    """
    Build div representing the info overlay for a plot panel FROM:
    https://dash.gallery/dash-world-cell-towers/

    """
    if title is None:
        title = "Description"

    div = html.Div(
        [  # modal div
            html.Div(
                [  # content div
                    html.Div(
                        [
                            html.H4(
                                [
                                    title,
                                    html.Img(
                                        id=f"close-{id}-modal",
                                        src="assets/times-circle-solid.svg",
                                        n_clicks=0,
                                        className="info-icon-close",
                                        style={"margin": 0},
                                    ),
                                ],
                                className="container_title",
                                style={"color": "black"},
                            ),
                            dcc.Markdown(content),
                        ]
                    )
                ],
                className=f"modal-content {side}",
            ),
            html.Div(className="modal"),
        ],
        id=f"{id}-modal",
        style={"display": "none"},
    )

    return div


app.layout = html.Div(
    style={
        "backgroundColor": layout["bg_color"],
        "padding": "5px",
        "font-family": layout["font_type"],
    },
    children=[
        html.Div([
            html.Img(
                src='assets\logo.png',
                style={'height': '20%', 'width': '20%', 'display': 'inline-block'}),

            # html.H1('Under development!'),
            build_modal_info_overlay('model-info', 'top', dedent(
                """
                # **Under development**
                Calculate the cost, carbon footprint, performance and material criticality of different lithium-ion battery designs. <br>


                The underlying Python code and a further descriptions can be found here: https://github.com/jbaars2/Batt_Sust_Model.

                """
            ), title='Information'),
            html.Img(
                id="show-model-info-modal",
                src="assets/info_icon.svg",
                n_clicks=0,
                className="info-icon-open",
                style={'height': '2.5%', 'width': '2.5%', "float": "right"},
            ),


        ],
            style={'display': 'inline-block'},
            id="model-info-div",
        ),
        html.Div(
            # style={
            #     "backgroundColor": layout["box_color"],
            #     "box-shadow": "2px 2px 2px lightgrey",
            #     "padding": "5px",
            #     "border-radius": "5px",
            # },
            children=[

                dbc.Row(
                    [
                        # FIRST ROW

                        html.Div(
                            children=[
                                dcc.Store(id="A_matrix_design"),
                                # html.H1('Parameters', className='container_title_overview'),
                                # BATTERY DESIGN PARAMETER
                                html.Div(
                                    children=[
                                        # FIRST ROW

                                        build_modal_info_overlay(
                                            "product-parameters",
                                            "bottom",
                                            dedent(
                                                """ The *battery design* parameters ...""",
                                            ),
                                        ),
                                        # html.H1('Under development!'),
                                        html.H2(
                                            [
                                                "Battery design",
                                                html.Img(
                                                    id="show-product-parameters-modal",
                                                    src="assets/question-circle-solid.svg",
                                                    n_clicks=0,
                                                    className="info-icon-open",
                                                ),
                                            ],
                                            className="container_title",
                                        ),
                                        dcc.Dropdown(
                                            id="product_param_selection",
                                            options=[
                                                {"label": k, "value": k}
                                                for k in [
                                                    "Vehicle, pack and module level",
                                                    "Cathode design",
                                                    "Anode design",
                                                    "Cell design other",
                                                ]
                                            ],
                                            value="Vehicle, pack and module level",
                                            className="control_label"
                                        ),
                                        # Cell other
                                        html.Div(
                                            [
                                                # html.H3("Cell other"),
                                                html.P(
                                                    html.Strong(
                                                        "Cell format"
                                                    ),
                                                    className="control_label",
                                                ),
                                                dcc.RadioItems(
                                                    id="cell_format_type",
                                                    options=[
                                                        {
                                                            "label": i,
                                                            "value": i,
                                                        }
                                                        for i in [
                                                            "cylindrical"
                                                        ]
                                                    ],
                                                    value="cylindrical",
                                                    labelStyle={
                                                        "display": "inline-block",
                                                        "margin-left": "0.37em",
                                                    },
                                                    style={
                                                        "margin-bottom": layout[
                                                            "cell_margin_bottom"
                                                        ],
                                                        'font-size': '0.825em'
                                                    },
                                                ),
                                                html.P(
                                                    html.Strong(
                                                        "Separator thickness"
                                                    ),
                                                    className="control_label",
                                                ),
                                                dcc.RadioItems(
                                                    id="sep_thickness_type",
                                                    options=[
                                                        {
                                                            "label": str(
                                                                i
                                                            )
                                                            + " μm",
                                                            "value": i,
                                                        }
                                                        for i in config.df_parameters[
                                                            "sep_foil_thickness"
                                                        ].unique()
                                                    ],
                                                    value=7,
                                                    labelStyle={
                                                        "display": "inline-block",
                                                        "margin-left": "0.37em",
                                                    },
                                                    style={
                                                        "margin-bottom": layout[
                                                            "cell_margin_bottom"
                                                        ],
                                                        'font-size': '0.825em'
                                                    },
                                                ),
                                                html.P(
                                                    html.Strong(
                                                        "Ceramic coating separator"
                                                    ),
                                                    className="control_label",
                                                ),
                                                dcc.RadioItems(
                                                    id="sep_coat_thickness_type",
                                                    options=[
                                                        {
                                                            "label": str(
                                                                i
                                                            )
                                                            + " μm",
                                                            "value": i,
                                                        }
                                                        for i in config.df_parameters[
                                                            "sep_coat_thickness"
                                                        ].unique()
                                                    ],
                                                    value=0,
                                                    labelStyle={
                                                        "display": "inline-block",
                                                        "margin-left": "0.37em",
                                                    },
                                                    style={
                                                        "margin-bottom": layout[
                                                            "cell_margin_bottom"
                                                        ],
                                                        'font-size': '0.825em'
                                                    },

                                                ),
                                                html.P(
                                                    html.Strong(
                                                        "Cell thickness"
                                                    ),
                                                    className="control_label",
                                                ),
                                                dcc.RadioItems(
                                                    id="cell_thickness",
                                                    options=[
                                                        {
                                                            "label": str(
                                                                i
                                                            )
                                                            + " mm",
                                                            "value": i,
                                                        }
                                                        for i in sorted(
                                                            config.df_parameters[
                                                                "cell_thickness"
                                                            ].unique()
                                                        )
                                                    ],
                                                    value=20,
                                                    labelStyle={
                                                        "display": "inline-block",
                                                        "margin-left": "0.37em",
                                                    },
                                                    style={
                                                        "margin-bottom": layout[
                                                            "cell_margin_bottom"
                                                        ],
                                                        'font-size': '0.825em'
                                                    },
                                                ),
                                            ],
                                            className="parameter_process_container",
                                            id="cell_other_container",
                                            style={"display": "none"},
                                        ),
                                        # Vehicle
                                        html.Div(
                                            [
                                                html.P(
                                                    html.Strong(
                                                        "Vehicle type"
                                                    ),
                                                    className="control_label",
                                                ),
                                                dcc.RadioItems(
                                                    id="vehicle_type",
                                                    options=[
                                                        {
                                                            "label": i,
                                                            "value": i,
                                                        }
                                                        for i in config.df_parameters[
                                                            "vehicle_type"
                                                        ].unique()
                                                    ],
                                                    value="EV",
                                                    labelStyle={
                                                        "display": "inline-block",
                                                        "margin-left": "0.37em",
                                                    },
                                                    style={
                                                        "margin-bottom": layout[
                                                            "cell_margin_bottom"
                                                        ],
                                                        'font-size': '0.825em'
                                                    },
                                                ),
                                                html.P(
                                                    html.Strong(
                                                        "Vehicle size"
                                                    ),
                                                    className="control_label",
                                                ),
                                                dcc.RadioItems(
                                                    inline=True,
                                                    id="vehicle_size",
                                                    options=[
                                                        {
                                                            "label": "Compact",
                                                            "value": 101.8642746,
                                                        },
                                                        {
                                                            "label": "Small",
                                                            "value": 110.5783408,
                                                        },
                                                        {
                                                            "label": "Medium",
                                                            "value": 135.9999272,
                                                        },
                                                        {
                                                            "label": "Large",
                                                            "value": 208.0433242,
                                                        },
                                                    ],
                                                    value=135.9999272,

                                                    labelStyle={
                                                        "display": "inline-block",
                                                        "margin-left": "0.37em",
                                                    },
                                                    style={
                                                        "margin-bottom": layout[
                                                            "cell_margin_bottom"
                                                        ],
                                                        'font-size': '0.825em'
                                                    },
                                                ),
                                            ],
                                            className="parameter_process_container",
                                            id="vehicle_container",
                                            style={"display": "none"},
                                        ),
                                        # Cathode
                                        html.Div(
                                            [
                                                # html.H3("Cathode"),
                                                html.P(
                                                    html.Strong(
                                                        "Electrode pair"
                                                    ),
                                                    className="control_label",
                                                ),
                                                dcc.Dropdown(
                                                    id="cathode_type",
                                                    options=[
                                                        {
                                                            "label": i,
                                                            "value": i,
                                                        }
                                                        for i in config.df_parameters[
                                                            "electrode_pair"
                                                        ].unique()
                                                    ],
                                                    value="NMC333-G",
                                                    className="control_label"

                                                ),
                                                html.P(
                                                    html.Strong(
                                                        "Cathode foil type"
                                                    ),
                                                    className="control_label",
                                                ),
                                                dcc.RadioItems(
                                                    id="cathode_foil_type",
                                                    options=[
                                                        {
                                                            "label": i,
                                                            "value": i,
                                                        }
                                                        for i in [
                                                            "aluminium"
                                                        ]
                                                    ],
                                                    value="aluminium",
                                                    labelStyle={
                                                        "display": "inline-block",
                                                        "margin-left": "0.37em",
                                                    },
                                                    style={
                                                        "margin-bottom": layout[
                                                            "cell_margin_bottom"
                                                        ],
                                                        'font-size': '0.825em'
                                                    },
                                                ),
                                                html.P(
                                                    html.Strong(
                                                        "Cathode foil thickness"
                                                    ),
                                                    className="control_label",
                                                ),
                                                dcc.RadioItems(
                                                    id="cathode_foil_thickness_type",
                                                    options=[
                                                        {
                                                            "label": str(
                                                                i
                                                            )
                                                            + " μm",
                                                            "value": i,
                                                        }
                                                        for i in sorted(
                                                            config.df_parameters[
                                                                "positive_foil_thickness"
                                                            ].unique()
                                                        )
                                                    ],
                                                    value=14,
                                                    labelStyle={
                                                        "display": "inline-block",
                                                        "margin-left": "0.37em",
                                                    },
                                                    style={
                                                        "margin-bottom": layout[
                                                            "cell_margin_bottom"
                                                        ],
                                                        'font-size': '0.825em'
                                                    },
                                                ),
                                            ],
                                            className="parameter_process_container",
                                            id="cathode_container",
                                            style={"display": "none"},
                                        ),
                                        # Anode
                                        html.Div(
                                            [
                                                # html.H3("Anode"),
                                                html.P(
                                                    html.Strong(
                                                        "Graphite type"
                                                    ),
                                                    className="control_label",
                                                ),
                                                dcc.RadioItems(
                                                    id="graphite_type",
                                                    options=[
                                                        {
                                                            "label": i,
                                                            "value": i,
                                                        }
                                                        for i in config.df_parameters[
                                                            "graphite_type"
                                                        ].unique()
                                                    ],
                                                    value="natural",
                                                    labelStyle={
                                                        "display": "inline-block",
                                                        "margin-left": "0.37em",
                                                    },
                                                    style={
                                                        "margin-bottom": layout[
                                                            "cell_margin_bottom"
                                                        ],
                                                        'font-size': '0.825em'
                                                    },
                                                ),
                                                html.P(
                                                    html.Strong(
                                                        "Anode foil type"
                                                    ),
                                                    className="control_label",
                                                ),
                                                dcc.RadioItems(
                                                    id="anode_foil_type",
                                                    options=[
                                                        {
                                                            "label": i,
                                                            "value": i,
                                                        }
                                                        for i in [
                                                            "copper"
                                                        ]
                                                    ],
                                                    value="copper",

                                                    labelStyle={
                                                        "display": "inline-block",
                                                        "margin-left": "0.37em",
                                                    },
                                                    style={
                                                        "margin-bottom": layout[
                                                            "cell_margin_bottom"
                                                        ],
                                                        'font-size': '0.825em'
                                                    },
                                                ),
                                                html.P(
                                                    html.Strong(
                                                        "Anode foil thickness type"
                                                    ),
                                                    className="control_label",
                                                ),
                                                dcc.RadioItems(
                                                    id="anode_foil_thickness_type",
                                                    options=[
                                                        {
                                                            "label": str(
                                                                i
                                                            )
                                                            + " μm",
                                                            "value": i,
                                                        }
                                                        for i in sorted(
                                                            config.df_parameters[
                                                                "negative_foil_thickness"
                                                            ].unique()
                                                        )
                                                    ],
                                                    value=10,
                                                    labelStyle={
                                                        "display": "inline-block",
                                                        "margin-left": "0.37em",
                                                    },
                                                    style={
                                                        "margin-bottom": layout[
                                                            "cell_margin_bottom"
                                                        ],
                                                        'font-size': '0.825em'
                                                    },
                                                ),
                                                html.P(
                                                    html.Strong(
                                                        "Silicon additive (wt%)"
                                                    ),
                                                    className="control_label",
                                                ),
                                                dcc.RadioItems(
                                                    id="silicon_additive_type",
                                                    options=[
                                                        {
                                                            "label": str(
                                                                i
                                                            ),
                                                            "value": float(
                                                                i
                                                            ),
                                                        }
                                                        for i in sorted(
                                                            config.df_parameters[
                                                                "silicon_anode"
                                                            ].unique()
                                                        )
                                                    ],
                                                    value=0.0,
                                                    labelStyle={
                                                        "display": "inline-block",
                                                        "margin-left": "0.37em",
                                                    },
                                                    style={
                                                        "margin-bottom": layout[
                                                            "cell_margin_bottom"
                                                        ],
                                                        'font-size': '0.825em'
                                                    },
                                                ),
                                            ],
                                            className="parameter_process_container",
                                            id="anode_container",
                                            style={"display": "none"},
                                        ),

                                    ],
                                    className="parameter_container", id="product-parameters-div",
                                ),
                                # PROCESS DESIGN PARAMETER
                                html.Div(
                                    children=[
                                        build_modal_info_overlay(
                                            "process-parameters",
                                            "bottom",
                                            dedent(
                                                """ The **process design** parameters refer to the changeable battery manufacturing processes parameters. Parameters included are:
                            * **Production scale and location - ** Refers to the location of the battery factory and the production scale. The battery production location impacts both the cost (labour, building and energy cost) and
                            the carbon footprint (carbon intensity of the electricity grid). Currently only the top seven European countries with the largest production announcements are included, as wel as an average of these seven countries.

                            Production scale refers to the annual battery packs produced in the respective factory and only impacts the production costs. Calculations are based on BatPaC version 4.
                            * **Electricity consumption** Electricity consumption of different battery production proceses, including: mixing, coating, calendering, slitting, drying, stacking,
                            dryroom operation, cell formation and aging, cell assembly, module and pack assembly and other activities such as material handling.
                            The calculations and data are based on Degen and Schütte (2022), DOI:10.1016/j.jclepro.2021.129798. Electricity consumption impacts both the carbon footprint and cost.
                            * **Heat consumption** Heat consumption (natural gas) of different battery production proceses, including: Coating, final drying, formation and dry room operation. The calculations and data are based on Degen and Schütte (2022), DOI:10.1016/j.jclepro.2021.129798. Heat consumption impacts both the carbon footprint and cost.

                            * **Process yields**



                                                * **Electricity consumption**


                                                """
                                            ),
                                        ),
                                        # Title
                                        html.H2(
                                            [
                                                "Process design",
                                                html.Img(
                                                    id="show-process-parameters-modal",
                                                    src="assets/question-circle-solid.svg",
                                                    n_clicks=0,
                                                    className="info-icon-open",
                                                ),
                                            ],
                                            className="container_title",
                                        ),
                                        # Dropdown
                                        dcc.Dropdown(
                                            id="process_param_selection",
                                            options=[
                                                {"label": k, "value": k}
                                                for k in [
                                                    "Production scale and location",
                                                    "Electricity consumption",
                                                    "Heat consumption",
                                                    "Process yields",
                                                ]
                                            ],
                                            value="Production scale and location",
                                            className="control_label"

                                        ),
                                        # Production
                                        html.Div(
                                            children=[
                                                html.P(html.Strong(
                                                    "Battery production location"),
                                                    className="control_label",
                                                ),
                                                dcc.Dropdown(
                                                    id="manufacturing_location_type",
                                                    options=[
                                                        {
                                                            "label": i,
                                                            "value": i,
                                                        }
                                                        for i in config.IndexTable.loc[
                                                            "Regions",
                                                            "Classification",
                                                        ].Items
                                                    ],
                                                    value="European average",
                                                    className="control_label"
                                                ),
                                                html.P(html.Strong(
                                                    "Production scale (thousand packs/yr)"),
                                                    className="control_label",
                                                ),
                                                dcc.Slider(
                                                    id="production_capacity_slider",
                                                    min=20000,
                                                    max=500000,
                                                    step=None,
                                                    value=100000,
                                                    marks={
                                                        50000: "50",
                                                        100000: "100",
                                                        200000: "200",
                                                        300000: "300",
                                                        400000: "400",
                                                        500000: "500",
                                                    },
                                                ),
                                            ],
                                            className="parameter_process_container",
                                            style={"display": "none"},
                                            id="manufacturing_container",
                                        ),
                                        # Electricity
                                        html.Div(
                                            children=[html.P(html.Strong(
                                                "Select electricity consumption parameter"),
                                                className="control_label",
                                            ),
                                                dcc.Dropdown(
                                                id="electricity_process_selection",
                                                options=[
                                                    {
                                                        "label": v,
                                                        "value": k,
                                                    }
                                                    for v, k in electricity.items()
                                                ],
                                                value="electricity_consumption_mixing",
                                                className="control_label"
                                            ),
                                                html.Div(
                                                [
                                                    energy_slider(
                                                        parameter
                                                    )
                                                    for parameter in electricity.values()
                                                ]
                                            ),
                                            ],
                                            className="parameter_process_container",
                                            id="electricity_consumption_container",
                                            style={"display": "none"},
                                        ),
                                        # Heat
                                        html.Div(
                                            children=[
                                                html.P(html.Strong(
                                                    "Select heat consumption parameter"),
                                                    className="control_label",
                                                ),
                                                dcc.Dropdown(
                                                    id="heat_process_selection",
                                                    options=[
                                                        {
                                                            "label": v,
                                                            "value": k,
                                                        }
                                                        for v, k in heat.items()
                                                    ],
                                                    value="heat_consumption_dryroom",
                                                    className="control_label"
                                                ),
                                                html.Div(
                                                    [
                                                        energy_slider(
                                                            parameter,
                                                            heat=True,
                                                        )
                                                        for parameter in heat.values()
                                                    ]
                                                ),
                                            ],
                                            className="parameter_process_container",
                                            id="heat_consumption_container",
                                            style={"display": "none"},
                                        ),
                                        # Process yield
                                        html.Div(
                                            children=[

                                                html.P(html.Strong(
                                                    "Select process yield parameter"),
                                                    className="control_label",
                                                ),


                                                dcc.Dropdown(id="yield_process_selection",
                                                             options=[{
                                                                 "label": v,
                                                                 "value": k,
                                                             } for v, k in process_yields.items()

                                                             ],
                                                             value="py_am_mixing",
                                                             className="control_label"
                                                             ),

                                                html.Div(
                                                    [
                                                        py_slider(
                                                            parameter,
                                                        )
                                                        for parameter in process_yields.values()
                                                    ]
                                                ),
                                            ],
                                            className="parameter_process_container",
                                            id="process_yield_container",
                                            style={"display": "none"},
                                        ),

                                        #     material prices slider
                                        html.Div(
                                            children=[
                                                html.P(
                                                    id="cobalt_output",
                                                    className="control_label",
                                                ),
                                                dcc.Slider(
                                                    id=f"cobalt_slider",
                                                    value=10,
                                                    min=90,
                                                    max=100,
                                                    step=1,
                                                    #     marks={
                                                    #         90: "90%",
                                                    #         100: "100%",
                                                    #     },
                                                )
                                                # html.Button(
                                                #     "Reset default values",
                                                #     id="btn_reset_py_sliders",
                                                #     n_clicks=0,
                                                #     className="button",
                                                #     style={
                                                #         "horizontalAlign": "center",
                                                #         "display": "inline",
                                                #     },
                                                # ),
                                            ],
                                            style={"display": "none"},
                                            className="parameter_process_container",
                                            id="material_price_container",
                                        ),
                                    ],
                                    className="parameter_container",
                                    id="process-parameters-div",
                                ),
                                # IMPACT PARAMETERS
                                html.Div(
                                    children=[
                                        build_modal_info_overlay(
                                            "impact-parameters",
                                            "bottom",
                                            dedent(
                                                """ The impact.... """
                                            ),
                                        ),
                                        # Title
                                        html.H2(
                                            [
                                                "Impact parameters",
                                                html.Img(
                                                    id="show-impact-parameters-modal",
                                                    src="assets/question-circle-solid.svg",
                                                    n_clicks=0,
                                                    className="info-icon-open",
                                                ),
                                            ],
                                            className="container_title",
                                        ),
                                        # Dropdown
                                        dcc.Dropdown(
                                            id="impact_param_selection",
                                            options=[
                                                {"label": k, "value": k}
                                                for k in [
                                                    "Metal prices",
                                                    "Material carbon footprints",
                                                ]
                                            ],
                                            value="Metal prices",
                                            className="control_label"
                                        ),


                                        # MATERIAL PRICE
                                        html.Div(
                                            children=[
                                                html.P(html.Strong(
                                                    "Select metal"),
                                                    className="control_label",
                                                ),
                                                dcc.Dropdown(
                                                    id="metal_price_selection",
                                                    options=[
                                                        {
                                                            "label": i,
                                                            "value": i,
                                                        }
                                                        for i in config.df_mineral_prices.index if i not in ['C', 'Fe', 'Si', 'P']

                                                    ],
                                                    value="Co",
                                                    className="control_label"
                                                ),
                                                html.P(html.Strong(
                                                    "Metal price"),
                                                    className="control_label",
                                                ),
                                                html.Div(
                                                    [
                                                        price_slider(
                                                            parameter,
                                                        )
                                                        for parameter in config.df_mineral_prices.index
                                                    ]
                                                ),
                                            ],
                                            className="parameter_process_container",
                                            style={"display": "none"},
                                            id="price_container",
                                        ),

                                        # Material carbon footprint
                                        html.Div(
                                            children=[
                                                html.P(html.Strong(
                                                    "Select material"),
                                                    className="control_label",
                                                ),
                                                dcc.Dropdown(
                                                    id="material_carbon_footprint",
                                                    options=[
                                                        {
                                                            "label": i,
                                                            "value": i,
                                                        }
                                                        for i in ['Natural graphite', 'Synthetic graphite', 'Nickel sulphate', 'Cobalt sulphate', 'Lithium hydroxide', 'Lithium carbonate', 'Silicon']
                                                    ],
                                                    value="Natural graphite",
                                                    className="control_label"
                                                ),
                                                html.P(html.Strong(
                                                    "Carbon footprint"),
                                                    className="control_label",
                                                ),
                                                # html.Div(
                                                #     [
                                                #         price_slider(
                                                #             parameter,
                                                #         )
                                                #         for parameter in  ['Natural graphite', 'Synthetic graphite', 'Nickel sulphate', 'Cobalt sulphate', 'Lithium hydroxide', 'Lithium carbonate', 'Silicon']
                                                #     ]
                                                # ),


                                            ],
                                            className="parameter_process_container",
                                            style={"display": "none"},
                                            id="carbonfootprint_container",
                                        ),

                                    ],
                                    className="parameter_container",
                                    id="impact-parameters-div",
                                ),

                                html.Div([
                                    html.H2(
                                        "Impact overview:",
                                        className="container_title_impact",
                                    ),
                                    dcc.Graph(
                                        id="impact_parameter_graph",
                                        style={"width": "100%",
                                               "display": "inline-block",
                                               "height": "100%"
                                               }
                                    ),
                                ],
                                    className="impact_figure",
                                ),
                                html.Div([
                                    dcc.Dropdown(
                                        id="datatable_select",
                                        options=[
                                            {
                                                "label": "Vehicle design parameters",
                                                "value": "vehicle_table",
                                            },
                                            {
                                                "label": "Battery design parameters",
                                                "value": "battery_table",
                                            },
                                            {
                                                "label": "Material prices input",
                                                "value": "Prices",
                                            },
                                            {
                                                "label": "Carbon footprint input parameters",
                                                "value": "carbon_table",
                                            },
                                            {
                                                "label": "Process input parameters",
                                                "value": "process_table",
                                            },
                                            {
                                                "label": "Annual mineral demand factory",
                                                "value": "metal_table",
                                            },

                                        ],

                                        value="process_table",
                                        className="control_label",
                                    ),
                                    
                                    
                                    html.Div(children=[

                                        html.Div(dt.DataTable(
                                            id=f"data_table_{table}",
                                            columns=[],
                                            style_table={
                                                'height': '19rem',
                                                'width': '31.25rem',
                                                'overflowY': 'auto'
                                            },
                                            style_header={
                                                'backgroundColor': 'lightgrey',
                                                'color': 'black',
                                                'fontWeight': 'bold',
                                                'font-family': 'Arial',
                                            },
                                            style_data={
                                                'backgroundColor': 'white',
                                                'color': 'black',
                                                'fontSize': "0.75rem",
                                                'font-family': 'Arial',
                                            },    style_as_list_view=True),
                                            style={"display": "none"},
                                            id=f"{table}_table_container",) for table in ["metal", "process", "carbon", "battery", "vehicle","process", "carbon", "battery", "vehicle"]]
                                    ),

                                    html.Button(
                                        children=["Download all data"],
                                        id="btn_download_tables",
                                        n_clicks=0,
                                        className="button2",
                                    ),
                                    dcc.Download(id="download_tables"), ],


                                    className="datatable_container",


                                )


                            ],
                            className="parameter_border",
                        ),
                    ]
                ),
                # SECOND ROW

                html.Div(children=[
                    # html.H2(
                    #      "Results", className="container_title_overview"),
                    html.Div(
                        dcc.Graph(id="emission_figure"),
                        className="result_figures"

                    ),    html.Div(
                        dcc.Graph(id="cost_figure"),
                        className="result_figures"

                    ),
                    html.Div(

                        dcc.Graph(
                            id="bom_graph"
                        ),

                        className="result_figures"
                    ),
                    html.Div(
                        dcc.Graph(id="criticality_figure"),
                        style={
                            "width": "25%",
                            "display": "inline-block",
                            "justifyContent": "center",
                            "padding-left": "30px"
                        },
                    ),
                    
                    #   html.Div(
                    #     dcc.Graph(id="comparison_figure"),
                    #     style={
                    #         "width": "20%",
                    #         "display": "inline-block",
                    #         "justifyContent": "center",
                    #         "padding-left": "10px"
                    #     },
                    # ),


                ],
                ),


            ],
            # className="parameter_border"
        ),


        # Fourth block:
        # FIRST ROW:
        html.Div(
            [
                html.Div(
                    children=[
                        # Storage of all design parameters:
                        dcc.Store(id="pack_ID"),
                        dcc.Store(
                            id="electricity_consumption_output"),
                        dcc.Store(id="gas_consumption_output"),
                        dcc.Store(id='metal_demand_output'),
                        dcc.Store(id='pack_cost_total'),
                        dcc.Store(id='pack_emission_total'),
                        dcc.Store(id='material_prices'),
                        # dcc.Store(id='data_table_battery'),
                        # SECOND ROW:

                    ],
                    className="parameter_container",
                ),
                   



            ],
        ),
    ],
)


if __name__ == "__main__":
    app.title = 'Battery Sustainability Calculator'
    app.run_server(debug=True)
