# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import bw2data as bd

# Local files
from make_figures import plot_unct_distributions, get_prioritized_list, generate_table


app = Dash(__name__)
app_color = {"graph_bg": "#132b57", "graph_line": "#ff4595"}

# Brightway
bw_methods = ["('IPCC 2013', 'climate change', 'GWP 100a')", ]
bw_projects = [el.name for el in bd.projects]
bw_databases = list(bd.databases)


fig = plot_unct_distributions()
df = get_prioritized_list()


app.layout = html.Div(
    [
        # Header
        html.Div(html.H1("Dashboard: Global sensitivity analysis of life cycle assessment"), className="header",),
        # BW setups
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span("Project", className="bw__field_name"),
                                html.Span(dcc.Dropdown(bw_projects), className="bw__field_menu"),
                            ],
                            className="bw__select_option"
                        ),
                        html.Div(
                            [
                                html.Span("Method", className="bw__field_name"),
                                html.Span(dcc.Dropdown(bw_methods), className="bw__field_menu"),
                            ],
                            className="bw__select_option"
                        ),
                    ],
                    className="bw__options_project_method"
                ),
                html.Div(
                    html.Div(
                        [
                            html.Div(
                                "Functional Unit (FU)",
                                className="bw__options_func_unit_title"
                            ),
                            html.Div([
                                    html.Div(
                                        [
                                            html.Div("Database", className="bw__field_name"),
                                            html.Div(dcc.Dropdown(bw_databases),
                                                     className="bw__field_menu"),
                                        ],
                                        className="bw__select_option"
                                    ),
                                    html.Div(
                                        [
                                            html.Div("Name", className="bw__field_name"),
                                            html.Div(dcc.Input(className="bw__input"), className="bw__field_menu"),
                                        ],
                                        className="bw__select_option"
                                    ),
                                ],
                                className="bw__options_database_funame"
                            ),
                            html.Div([
                                html.Div(
                                    [
                                        html.Div("Location", className="bw__field_name"),
                                        html.Div(dcc.Dropdown(bw_databases), className="bw__field_menu"),
                                    ],
                                    className="bw__select_option"
                                ),
                                html.Div(
                                    [
                                        html.Div("Amount", className="bw__field_name"),
                                        html.Div(dcc.Input(1, className="bw__input"), className="bw__field_menu"),
                                    ],
                                    className="bw__select_option"
                                ),
                            ],
                                className="bw__options_location_amount"
                            ),
                        ],
                        className="bw__func_unit_flex",
                    ),
                    className="bw__func_unit"),
            ],
            className="bw__setups",
        ),
    ],
)

# app.layout = html.Div(
#     [
#         html.Div(
#             [
#                 html.Div([html.H1("Dashboard: Global sensitivity analysis of life cycle assessment")]),
#             ],
#             className="header",
#         ),
#         # Setups
#         html.Div(
#             [
#                 # Project and method
#                 html.Div(
#                     [
#                         html.Div(
#                             [
#                                 html.H3("Project"),
#                                 html.Div(
#                                     [
#                                         dcc.Dropdown(
#                                             options=sorted([p.name for p in bd.projects]),
#                                             value="default",
#                                             id="bw-project",
#                                         )
#                                     ],
#                                     className="setups__bw__one_component"
#                                 )
#                             ],
#                             className="setups__bw__components"
#                         ),
#                         html.Div(
#                             [
#                                 html.H3("LCIA method"),
#                                 html.Div(
#                                     [
#                                         dcc.Dropdown(
#                                             options=bw_methods,
#                                             value=bw_methods[0],
#                                             id="lcia-method",
#                                         )
#                                     ],
#                                     className="setups__bw__one_component"
#                                 )
#                             ],
#                             className="setups__bw__components"
#                         )
#                     ],
#                     className="setups__bw",
#                 ),
#                 # Functional unit
#                 html.Div(
#                     [
#                         html.Div(
#                             [
#                                 html.H3("FU database"),
#                                 html.Div(
#                                     [
#                                         dcc.Dropdown(
#                                             options=sorted([d for d in bd.databases]),
#                                             value="default",
#                                             id="fu-database",
#                                         )
#                                     ],
#                                     className="setups__bw__one_component"
#                                 )
#                             ],
#                             className="setups__bw__components"
#                         ),
#                         html.Div(
#                             [
#                                 html.H3("FU name"),
#                                 html.Div(
#                                     [
#                                         dcc.Input(
#                                             id="fu-name",
#                                         )
#                                     ],
#                                     className="setups__bw__one_component"
#                                 )
#                             ],
#                             className="setups__bw__components"
#                         )
#                     ],
#                     className="setups__bw",
#                 ),
#                 # Functional unit
#                 html.Div(
#                     [
#                         html.H2("Selected FU: "),
#                         html.Div(id="selected-fu"),
#                     ],
#                 ),
#             ],
#             className="setups__bw__components",
#         ),
#         html.Div(
#             [
#                 html.Div([
#                     html.Div(
#                         [
#                             html.H2("Monte Carlo simulations"),
#                             dcc.Graph(
#                                 id='monte-carlo',
#                                 figure=fig
#                             ),
#                         ],
#                         className="container",
#                     ),
#                     html.Div(
#                         [
#                             html.H2("Contribution analysis"),
#                             dcc.Graph(
#                                 id='life-exp-vs-gdp2',
#                                 figure=fig
#                             )
#                         ],
#                         className="container",
#                     )
#                 ]),
#                 html.Div([
#                     html.Div(
#                         [
#                             html.H2("GSA validation"),
#                             dcc.Graph(
#                                 id='hist',
#                                 figure=fig,
#                             )
#                         ],
#                         className="container",
#                     ),
#                     html.Div(
#                         [
#                             html.H2("GSA convergence"),
#                             dcc.Graph(
#                                 id='hist2',
#                                 figure=fig,
#                             )
#                         ],
#                         className="container",
#                     )
#                 ]),
#                 html.Div(
#                     [
#                         html.H2("GSA results"),
#                         generate_table(df, max_rows=20),
#                     ],
#                     className="container",
#                 ),
#             ],
#             className="app__subheader",
#         )
#     ]
# )
#
#
# @app.callback(
#     Output('selected-fu', 'children'),
#     Input('bw-project', 'value'),
#     Input('lcia-method', 'value'),
# )
# def update_selected_fu(project, method):
#     bd.projects.set_current(project)
#     return project


if __name__ == '__main__':
    app.run_server(debug=True)
