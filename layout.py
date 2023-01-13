import os
from dash import dcc, html, DiskcacheManager, CeleryManager, dash_table
from constants import DEFAULT_ITERATIONS, DEFAULT_SEED
import bw2data as bd


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


def get_lca_config(state_or_input):
    lca_config = dict(
        project=state_or_input('project', 'value'),
        database=state_or_input("database", "value"),
        method=state_or_input("method", "value"),
        activity=state_or_input('activity', "value"),
        amount=state_or_input('amount', "value"),
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


def create_main_layout():
    bw_projects = [el.name for el in bd.projects]
    layout = html.Div([
        # Header
        html.Div(html.H1("Dashboard: Global sensitivity analysis of life cycle assessment"), className="header",),
        # BW setups
        html.Div([
            html.Div([
                html.Div([
                    html.Span("Project", className="bw__field_name"),
                    html.Span(dcc.Dropdown(bw_projects, id="project"), className="bw__field_menu"),
                ], className="bw__select_option"),
                html.Div([
                    html.Span("Method", className="bw__field_name"),
                    html.Span(dcc.Dropdown([], id="method"), className="bw__field_menu"),
                ], className="bw__select_option"),
            ], className="bw__options_project_method"),
            html.Div([
                html.Div([
                    html.Div("Functional Unit (FU)", className="bw__options_func_unit_title"),
                    html.Div([
                        html.Div([
                            html.Div("Database", className="bw__field_name"),
                            html.Div(dcc.Dropdown([], id="database"), className="bw__field_menu"),
                        ], className="bw__select_option"),
                        html.Div([
                            html.Div("Activity", className="bw__field_name"),
                            html.Div(dcc.Dropdown([], id="activity"), className="bw__field_menu"),
                        ], className="bw__select_option"),
                    ], className="bw__options_database_funame"),
                    html.Div([
                        html.Div([
                            html.Div("Amount", className="bw__field_name"),
                            html.Div(dcc.Input(1, id="amount"), className="bw__field_menu"),
                        ], className="bw__select_option"),
                        html.Div([
                            html.Div("LCIA score", className="bw__field_name"),
                            html.Div(id="score", className="bw__field_score"),
                            html.Div(id="method-unit", className="bw__field_unit"),
                        ], className="bw__select_option"),
                    ], className="bw__options_location_amount"),
                ], className="bw__func_unit_flex",),
            ], className="bw__func_unit"),
        ], className="bw__setups",),
        # MC simulations
        html.Div(id="monte-carlo",),
        html.Div(id="sensitivity-analysis",),
    ])
    return layout


def create_mc_section(fig):
    mc_section = html.Div([
        html.Div([
            html.Div("Number of MC simulations", className="bw__field_name"),
            dcc.Input(DEFAULT_ITERATIONS, id='iterations'),
            html.Div("Random seed", className="bw__field_name"),
            dcc.Input(DEFAULT_SEED, id='seed'),
            html.Button(id='mc-button', n_clicks=0, children='Run MC', className="button"),
            # html.Button(id="button-cancel-mc-simulations", children="Cancel MC", className="button"),
            dcc.Interval(id="mc-interval", interval=2*1000, n_intervals=0),  # in milliseconds
            dcc.Store(id="directory"),
            dcc.Store(id="mc-state"),
            dcc.Store(id="mc-completed"),
        ], className="bw__mc_simulations",),
        html.Div([
            # html.P(id='err', style={'color': 'red'}),
            dcc.Graph(id='mc-graph', figure=fig)
        ], className="bw__mc_simulations",),
    ])
    return mc_section


def create_gsa_section(df):
    gsa_section = html.Div([
        html.Div([
            html.Button(id='button-mc-simulations', n_clicks=0, children='Run GSA', className="button"),
            # html.Button(id="button-cancel-gsa", children="Cancel MC", className="button"),
            html.Div("", id="gsa-finished", className="bw__field_name"),
        ], className="bw__sensitivity_analysis",),
        html.Div([
            dash_table.DataTable(
                df.to_dict('records'), [{"name": i, "id": i} for i in df.columns], page_size=40,
                style_data={'color': 'white', 'backgroundColor': '#1a4c73', "maxWidth": "300px"},
                style_header={'color': 'white', 'backgroundColor': '#1a4c73'},
                style_table={'maxWidth': '300px'},
                style_cell_conditional=[{'if': {'column_id': 'GSA rank'}, 'width': '50px'},
                                        {'if': {'column_id': 'Input name'}, 'maxWidth': '130px', 'minWidth': '130px'},
                                        {'if': {'column_id': 'location'}, 'maxWidth': '50px', 'minWidth': '50px'},
                                        {'if': {'column_id': 'categories'}, 'maxWidth': '50px', 'minWidth': '50px'},
                                        {'if': {'column_id': 'Output name'}, 'maxWidth': '130px', 'minWidth': '130px'},
                                        {'if': {'column_id': 'location'}, 'maxWidth': '50px', 'minWidth': '50px'},
                                        {'if': {'column_id': 'GSA index'}, 'maxWidth': '50px', 'minWidth': '50px'}],
            )
        ],),
    ], className="bw__table_gsa_container")
    return gsa_section
