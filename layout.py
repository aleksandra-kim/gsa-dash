import os
from dash import dcc, html, DiskcacheManager, CeleryManager, dash_table
import bw2data as bd
import dash_bootstrap_components as dbc
from make_figures import plot_mc_simulations, plot_model_linearity, create_table_gsa_ranking
from constants import ITERATIONS, SEED, INTERVAL_TIME, LINEARITY_THRESHOLD, PAGE_SIZE

color_even = "rgb(222, 221, 232, 0.5)"
color_odd = "#FBFAF1"
color_none = "rgba(0,0,0,0)"
color_light_purple = "rgb(175, 144, 193, 0.6)"
color_blue = "rgba(0, 0, 255, 0.5)"


def create_background_callback_manager():
    if 'REDIS_URL' in os.environ:
        # Use Redis & Celery if REDIS_URL set as an env variable
        from celery import Celery
        celery_app = Celery(__name__, broker=os.environ['REDIS_URL'], backend=os.environ['REDIS_URL'])
        background_callback_manager = CeleryManager(celery_app)
    else:
        # Diskcache for non-production apps when developing locally
        import diskcache
        cache = diskcache.Cache("./cache")
        background_callback_manager = DiskcacheManager(cache)
    return background_callback_manager


def create_layout():
    layout = html.Div([
        get_header(),
        get_top_controls(),
        get_tabs(),
    ])
    return layout


def get_header():
    header = html.Header([
        html.H1("Global Sensitivity Analysis Of Life Cycle Assessment"),
        html.H3("the complete story in one dashboard")
    ], className="d--header")
    return header


def get_top_controls():
    projects = [p.name for p in bd.projects]
    top_controls = html.Div([
        html.Div([
            html.Div([
                html.Label("Project", className="label"),
                dcc.Dropdown(projects, id="project"),
            ], className="control-project"),
            html.Div([
                html.Label("Database", className="label"),
                dcc.Dropdown([], id="database"),
            ], className="control-database"),
            html.Div([
                html.Label("Activity", className="label"),
                dcc.Dropdown([], id="activity"),
            ], className="control-activity"),
            html.Div([
                html.Label("Amount", className="label"),
                dbc.Input(id="amount", value=1, type="number", min=0)
            ], className="control-amount"),
            html.Div([
                html.Label("Method", className="label"),
                dcc.Dropdown([], id="method"),
            ], className="control-method"),
            html.Div([
                html.Label("LCIA score", className="label"),
                html.Div([
                    html.Span(id="score", className="score"),
                    html.Span(id="method-unit", className="method-unit")
                ], className="score-unit")
            ], className="output-lcia")
        ], className="top-controls-container"),
    ], className="top-controls")
    return top_controls


def get_tabs():
    tab1_content = get_tab_motivation()
    tab2_content = get_tab_uncertainty_propagation()
    tab3_content = get_tab_sensitivity_analysis()
    tab4_content = get_tab_gsa_validation()
    tab5_content = get_tab_summary()
    tabs = dbc.Tabs(
        active_tab="tab-propagation",
        children=[
            dbc.Tab(tab1_content, className="tab-content", label="Motivation"),
            dbc.Tab(tab2_content, className="tab-content", label="Uncertainty propagation", tab_id="tab-propagation"),
            dbc.Tab(tab3_content, className="tab-content", label="Global sensitivity analysis"),
            dbc.Tab(tab4_content, className="tab-content", label="GSA validation"),
            dbc.Tab(tab5_content, className="tab-content", label="Summary"),
        ],
        className="tabs-container"
    )
    return tabs


def get_tab_motivation():
    tab = html.Div([
        html.H2("So... what is life cycle assessment?"),
        html.P("Life cycle assessment or LCA (also known as life cycle analysis) is a methodology for assessing "
               "environmental impacts associated with all the stages of the life cycle of a commercial product, "
               "process, or service. For instance, in the case of a manufactured product, environmental impacts are "
               "assessed from raw material extraction and processing (cradle), through the product's manufacture, "
               "distribution and use, to the recycling or final disposal of the materials composing it (grave).", ),
        html.H2("Ok, how about global sensitivity analysis?"),
        html.P("Sensitivity analysis is the study of how the uncertainty in the output of a mathematical model or "
               "system (numerical or otherwise) can be divided and allocated to different sources of uncertainty in "
               "its inputs.[1][2] A related practice is uncertainty analysis, which has a greater focus on uncertainty "
               "quantification and propagation of uncertainty; ideally, uncertainty and sensitivity analysis should be "
               "run in tandem."),
        html.H2("But why do we need GSA of LCA?"),
        html.P("Because of important reasons!")
    ], className="tab-motivation")
    return tab


def get_tab_uncertainty_propagation():
    fig = plot_mc_simulations()
    mc_controls = get_mc_controls()
    progress = get_progress()
    tab = html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.H2("Uncertainty propagation"),
                html.P("In statistics, propagation of uncertainty (or propagation of error) is the effect of "
                       "variables' uncertainties (or errors, more specifically random errors) on the uncertainty "
                       "of a function based on them. When the variables are the values of experimental "
                       "measurements they have uncertainties due to measurement limitations (e.g., instrument "
                       "precision) which propagate due to the combination of variables in the function."),
            ]), width=4, align="start"),
            dbc.Col(html.Div([
                html.H2("Monte Carlo simulations"),
                mc_controls,
                progress,
                dcc.Graph(id='mc-graph', figure=fig),
            ]), width=6, align="start"),
        ], justify="evenly"),
    ], className="tab-propagation")
    return tab


def get_mc_controls():
    mc_controls = html.Div([
        html.Div([
            html.Div([
                html.Label("Iterations", className="label"),
                dbc.Input(id="iterations", value=ITERATIONS, type="number")
            ], className="control-iterations"),
            html.Div([
                html.Label("Random seed", className="label"),
                dbc.Input(id="seed", value=SEED, type="number")
            ], className="control-random-seed"),
            dcc.Store(id="directory"),
            dcc.Store(id="mc-state", data=0),
            dcc.Store(id="mc-finished", data=False),
            dbc.Button("Start", id="btn-start-mc", n_clicks=0, outline=False, color="primary",
                       className="btn-start-mc"),
            dbc.Button("Cancel", id="btn-cancel-mc", n_clicks=0, outline=False, color="warning",
                       className="btn-cancel-mc"),
        ], className="mc-controls-container")
    ], className="mc-controls")
    return mc_controls


def get_progress():
    progress = html.Div([
        html.Label("Progress:"),
        dcc.Interval(id="mc-progress-interval", n_intervals=0, interval=INTERVAL_TIME * 1000),
        dbc.Progress(id="mc-progress", className="mc-progress", value=0, label="0%"),
    ], className="mc-progress-container")
    return progress


def get_tab_sensitivity_analysis():
    fig_model_linearity = plot_model_linearity(linearity_threshold=LINEARITY_THRESHOLD)
    df = create_table_gsa_ranking()
    df_data = df.to_dict("records")
    columns = [{"name": i, "id": i} for i in df.columns]
    tab = html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.H2("Global sensitivity analysis"),
                html.P("In statistics, propagation of uncertainty (or propagation of error) is the effect of "
                       "variables' uncertainties (or errors, more specifically random errors) on the uncertainty "
                       "of a function based on them. When the variables are the values of experimental "
                       "measurements they have uncertainties due to measurement limitations (e.g., instrument "
                       "precision) which propagate due to the combination of variables in the function."),
            ]), width=6, align="start"),
            dbc.Col(html.Div([
                html.H2("LCA model linearity"),
                dcc.Graph(id='linearity-graph', figure=fig_model_linearity, className="linearity-graph"),
            ]), width=5, align="start"),
        ], justify="evenly", className="row-gsa"),
        dbc.Col(html.H2("Influential model inputs, aka GSA results")),
        dbc.Row([
            dbc.Col(
                dash_table.DataTable(
                    data=df_data, columns=columns, id="ranking-table", page_size=PAGE_SIZE, sort_action='native',
                    style_table={"font-family": "sans-serif", "borderBottom": f'1px solid {color_light_purple}'},
                    style_header={'backgroundColor': f'{color_light_purple}', 'textAlign': 'center',
                                  "font-family": "sans-serif", "font-size": "16px", "font-weight": "bold"},
                    style_cell={"backgroundColor": color_none, 'textAlign': 'left', 'whiteSpace': 'pre-line',
                                'overflow': 'hidden', 'textOverflow': 'ellipsis'},
                    style_cell_conditional=[
                        {'if': {'column_id': 'Rank'}, 'width': '7%', 'textAlign': 'center'},
                        {'if': {'column_id': 'LCA model input'}, 'width': '45%'},
                        {'if': {'column_id': 'Amount'}, 'width': '15%'},
                        {'if': {'column_id': 'Type'}, 'width': '10%'},
                        {'if': {'column_id': 'GSA index'}, 'width': '15%'},
                        {'if': {'column_id': 'Contribution'}, 'width': '8%'},
                    ],
                    style_data={"border": '1px solid white', "font-family": "sans-serif",
                                'height': 'auto', 'lineHeight': '19px'},
                    style_data_conditional=get_style_data_conditional(color_even),
                ),
            )
        ], justify="evenly")
    ], className="tab-sensitivity")
    return tab


def get_style_data_conditional(bg_color):
    style_data_conditional = [
        {'if': {'row_index': "even"}, 'backgroundColor': f'{bg_color}'},
        {'if': {'column_id': 'Amount'}, 'textAlign': 'left'},
        {'if': {'column_id': 'GSA index'}, 'textAlign': 'right'},
        {'if': {'column_id': 'Contribution'}, 'textAlign': 'right'},
    ]
    return style_data_conditional


def style_bars_in_datatable(df, column, bar_percentage_in_cell=70):
    styles = get_style_data_conditional(color_even)
    values = df[column].values
    max_value = values.max()
    for i, val in enumerate(values):
        color_row = color_even if i % 2 == 0 else color_odd
        max_bound_percentage = int(val/max_value * bar_percentage_in_cell)
        style_element = {
            'if': {
                'filter_query': '{{column}} = {{val}} && {{Rank}}={i}'.format(column=column, val=val, i=i+1),
                'column_id': column,
            },
            'background': (
                f"""
                    linear-gradient(90deg,
                    {color_blue} 0%,
                    {color_blue} {max_bound_percentage}%,
                    {color_row} {max_bound_percentage}%,
                    {color_row} 100%)
                """
            ),
            'paddingBottom': 2, 'paddingTop': 2
        }
        styles.append(style_element)
    return styles


def get_tab_gsa_validation():
    tab = dbc.Card(
        dbc.CardBody(
            [
                html.H2("Sensitivity results validation"),
                dbc.Button("Don't click here", color="danger"),
            ]
        ),
    )
    return tab


def get_tab_summary():
    tab = dbc.Card(
        dbc.CardBody(
            [
                html.H2("Summary"),
                dbc.Button("Don't click here", color="danger"),
            ]
        ),
    )
    return tab


def get_lca_config(state_or_input):
    lca_config = dict(
        project=state_or_input('project', 'value'),
        database=state_or_input("database", "value"),
        activity=state_or_input('activity', "value"),
        amount=state_or_input('amount', "value"),
        method=state_or_input("method", "value"),
    )
    return lca_config


def get_mc_config(state_or_input):
    mc_config = dict(
        iterations=state_or_input('iterations', 'value'),
        seed=state_or_input("seed", "value"),
    )
    return mc_config


def get_lca_mc_config(state_or_input):
    lca_config = get_lca_config(state_or_input)
    mc_config = get_mc_config(state_or_input)
    lca_mc_config = {**lca_config, **mc_config}
    return lca_mc_config
#
#
# def create_mc_section(fig):
#     mc_section = html.Div([
#         # html.Div([
#         #     html.Div("Number of MC simulations", className="bw__field_name"),
#         #     dcc.Input(DEFAULT_ITERATIONS, id='iterations'),
#         #     html.Div("Random seed", className="bw__field_name"),
#         #     dcc.Input(DEFAULT_SEED, id='seed'),
#         #     html.Button(id='mc-button', n_clicks=0, children='Run MC', className="button"),
#         #     # html.Button(id="button-cancel-mc-simulations", children="Cancel MC", className="button"),
#         #     dcc.Interval(id="mc-interval", interval=2*1000, n_intervals=0),  # in milliseconds
#         #     dcc.Store(id="directory"),
#         #     dcc.Store(id="mc-state"),
#         #     dcc.Store(id="mc-completed"),
#         # ], className="bw__mc_simulations",),
#         # html.Div([
#         #     # html.P(id='err', style={'color': 'red'}),
#         #     dcc.Graph(id='mc-graph', figure=fig)
#         # ], className="bw__mc_simulations",),
#     ])
#     return mc_section
#
#
# def create_gsa_section(df):
#     gsa_section = html.Div([
#         html.Div([
#             html.Button(id='button-mc-simulations', n_clicks=0, children='Run GSA', className="button"),
#             # html.Button(id="button-cancel-gsa", children="Cancel MC", className="button"),
#             html.Div("", id="gsa-finished", className="bw__field_name"),
#         ], className="bw__sensitivity_analysis",),
#         html.Div([
#             dash_table.DataTable(
#                 df.to_dict('records'), [{"name": i, "id": i} for i in df.columns], page_size=40,
#                 style_data={'color': 'white', 'backgroundColor': '#1a4c73', "maxWidth": "300px"},
#                 style_header={'color': 'white', 'backgroundColor': '#1a4c73'},
#                 style_table={'maxWidth': '300px'},
#                 style_cell_conditional=[{'if': {'column_id': 'GSA rank'}, 'width': '50px'},
#                                         {'if': {'column_id': 'Input name'}, 'maxWidth': '130px', 'minWidth': '130px'},
#                                         {'if': {'column_id': 'location'}, 'maxWidth': '50px', 'minWidth': '50px'},
#                                         {'if': {'column_id': 'categories'}, 'maxWidth': '50px', 'minWidth': '50px'},
#                                         {'if': {'column_id': 'Output name'}, 'maxWidth': '130px', 'minWidth': '130px'},
#                                         {'if': {'column_id': 'location'}, 'maxWidth': '50px', 'minWidth': '50px'},
#                                         {'if': {'column_id': 'GSA index'}, 'maxWidth': '50px', 'minWidth': '50px'}],
#             )
#         ],),
#     ], className="bw__table_gsa_container")
#     return gsa_section
