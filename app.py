# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import os
import numpy as np
import bw2data as bd
import plotly.graph_objects as go
from pathlib import Path
import re

import dash
from dash import Dash, dcc, html, Input, Output, DiskcacheManager, CeleryManager, State
from dash.exceptions import PreventUpdate

# Local files
from brightway.lca_calculations import compute_lcia_score, create_lca
from make_figures import plot_mc_simulations
from constants import DEFAULT_MC_ITERATIONS, DEFAULT_RANDOM_SEED, CHUNK_SIZE
from utils import prepare_write_dirs, get_write_dir, write_json, read_json, collect_mc_scores, get_mc_scores_files

# dash_table.DataTable(id="my-table-promises", page_size=10),  # TODO include pagesize into tables


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

app = Dash(__name__, background_callback_manager=background_callback_manager, suppress_callback_exceptions=True)

# Brightway
bw_projects = [el.name for el in bd.projects]
default_bw_method = ('IPCC 2013', 'climate change', 'GWP 100a')

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
                                html.Span(dcc.Dropdown(bw_projects, id="bw-projects"), className="bw__field_menu"),
                            ],
                            className="bw__select_option"
                        ),
                        html.Div(
                            [
                                html.Span("Method", className="bw__field_name"),
                                html.Span(dcc.Dropdown([], id="bw-methods"), className="bw__field_menu"),
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
                                            html.Div(dcc.Dropdown([], id="bw-databases"), className="bw__field_menu"),
                                        ],
                                        className="bw__select_option"
                                    ),
                                    html.Div(
                                        [
                                            html.Div("Activity", className="bw__field_name"),
                                            html.Div(dcc.Dropdown([], id="bw-fu-activity"), className="bw__field_menu"),
                                        ],
                                        className="bw__select_option"
                                    ),
                                ],
                                className="bw__options_database_funame"
                            ),
                            html.Div([
                                html.Div(
                                    [
                                        html.Div("Amount", className="bw__field_name"),
                                        # html.Div(dcc.Input(1, id="bw-fu-amount", className="bw__input"), className="bw__field_menu"),
                                        html.Div(dcc.Input(1, id="bw-fu-amount"), className="bw__field_menu"),
                                    ],
                                    className="bw__select_option"
                                ),
                                html.Div(
                                    [
                                        html.Div("LCIA score", className="bw__field_name"),
                                        html.Div(id="lcia-score", className="bw__field_score"),
                                        html.Div(id="lcia-unit", className="bw__field_unit"),
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
                dcc.Store(id="project-dir"),
            ],
            className="bw__setups",
        ),
        # MC simulations
        html.Div(id="mc-simulations",),
    ],
)


@app.callback(
    Output('bw-methods', 'options'),
    Output('bw-databases', 'options'),
    Input('bw-projects', 'value'),
)
def update_project(project):
    if project is None:
        raise PreventUpdate
    bd.projects.set_current(project)
    # bw_methods = [str(m) for m in bd.methods if "superseded" not in str(m)]  # TODO uncomment in the end
    bw_methods = sorted([str(default_bw_method)])
    return bw_methods, sorted(list(bd.databases))


@app.callback(
    Output('bw-fu-activity', 'options'),
    Input('bw-projects', 'value'),
    Input('bw-databases', 'value'),
)
def update_functional_unit(project, db_name):
    if project is None:
        raise PreventUpdate
    bd.projects.set_current(project)
    db = bd.Database(db_name)
    db_activities = [f"{act['name']}, {act['location']}" for act in db]
    return sorted(db_activities)


@app.callback(
    Output("lcia-score", "children"),
    Output("lcia-unit", "children"),
    Input('bw-projects', 'value'),
    Input("bw-databases", "value"),
    Input("bw-methods", "value"),
    Input('bw-fu-activity', "value"),
    Input('bw-fu-amount', "value"),
)
def update_lcia_score(project, db_name, method, functional_unit, fu_amount):
    if (project is None) or (db_name is None) or (method is None) or (functional_unit is None):
        raise PreventUpdate
    lcia_score, unit = compute_lcia_score(project, db_name, method, functional_unit, fu_amount)
    return f"{lcia_score:7.3f}", unit


@app.callback(
    Output("mc-simulations", 'children'),
    Input("lcia-score", "children"),
    State("lcia-unit", "children"),
)
def display_mc_simulations(score, unit):
    print("This should only be called once")
    fig = plot_mc_simulations(score, unit)
    mc_section = html.Div(
        [
            html.Div(
                [
                    html.Div("Number of MC simulations", className="bw__field_name"),
                    dcc.Input(DEFAULT_MC_ITERATIONS, id='mc-iterations'),
                    html.Div("Random seed", className="bw__field_name"),
                    dcc.Input(DEFAULT_RANDOM_SEED, id='mc-seed'),
                    html.Button(id='button-mc-simulations', n_clicks=0, children='Run MC', className="button"),
                    # html.Button(id="button-cancel-mc-simulations", children="Cancel MC", className="button"),
                    dcc.Store(id="mc-directory"),
                    dcc.Store(id="mc-state"),
                    dcc.Interval(id="mc-interval", interval=2*1000, n_intervals=0),  # in milliseconds
                    html.Div("", id="mc-finished", className="bw__field_name"),
                ],
                className="bw__mc_simulations",
            ),
            html.Div(
                [
                    html.P(id='err', style={'color': 'red'}),
                    dcc.Graph(id='graph-mc-simulations', figure=fig)
                ],
                id="graph-mc-simulations-container",
                className="bw__mc_simulations",
            ),
        ],
    )
    return mc_section


@app.callback(
    Output("mc-directory", "children"),
    Input("button-mc-simulations", "n_clicks"),
    State("mc-iterations", "value"),
    State("mc-seed", "value"),
    State('bw-projects', 'value'),
    State("bw-databases", "value"),
    State("bw-methods", "value"),
    State('bw-fu-activity', "value"),
    State('bw-fu-amount', "value"),
    # running=[
    #     (Output("button-mc-simulations", "disabled"), True, False),
    #     (Output("button-cancel-mc-simulations", "disabled"), False, True),
    # ],
    # cancel=Input("button-cancel-mc-simulations", "n_clicks"),
    # background=True,
)
def create_mc_directory(n_clicks, iterations, seed, project, db_name, method, functional_unit, fu_amount):
    if n_clicks == 0:
        raise PreventUpdate
    write_dir = prepare_write_dirs(project, db_name, method, functional_unit, fu_amount)
    write_dir_mc = write_dir / f"iterations{iterations}_seed{seed}"
    write_dir_mc.mkdir(parents=True, exist_ok=True)
    return str(write_dir_mc)


@app.callback(
    Output("mc-finished", "value"),
    Input("mc-directory", "children"),
    State("mc-iterations", "value"),
    State("mc-seed", "value"),
    State('bw-projects', 'value'),
    State("bw-databases", "value"),
    State("bw-methods", "value"),
    State('bw-fu-activity', "value"),
    State('bw-fu-amount', "value"),
    # background=True,
)
def run_mc_simulations(write_dir_mc, iterations, seed, project, db_name, method, functional_unit, fu_amount):
    if write_dir_mc is None:
        raise PreventUpdate
    write_dir_mc = Path(write_dir_mc)
    bd.projects.set_current(project)
    lca = create_lca(project, db_name, method, functional_unit, fu_amount, seed)
    lca.keep_first_iteration()
    for ichunk in range(iterations//CHUNK_SIZE+1):
        mc_scores = []
        for _ in range(CHUNK_SIZE):
            next(lca)
            mc_scores.append(lca.score)
        write_json(mc_scores, write_dir_mc / f"Y{ichunk}.json")
    return "MC finished!"


@app.callback(
    Output("mc-state", "value"),
    Output("graph-mc-simulations", "figure"),
    Input('mc-interval', 'n_intervals'),
    Input("button-mc-simulations", "n_clicks"),
    State("mc-directory", "children"),
    State("mc-state", "value"),
    State("lcia-score", "children"),
    State("lcia-unit", "children"),
)
def update_mc_state(n_intervals, n_clicks, write_dir_mc, state, lcia_score, unit):
    if write_dir_mc is None or n_clicks == 0:
        return dash.no_update, dash.no_update
    write_dir_mc = Path(write_dir_mc)
    yfiles = get_mc_scores_files(write_dir_mc)
    print(state)
    if state is None:
        print(state, "position 1", len(yfiles))
        return len(yfiles), dash.no_update
    if state == len(yfiles):
        return dash.no_update, dash.no_update
    if state + 1 == len(yfiles):
        mc_scores = collect_mc_scores(write_dir_mc)
        if len(mc_scores) > 0:
            figure = plot_mc_simulations(lcia_score, unit, mc_scores)
        print(state, "position 2", state + 1)
        return state + 1, figure


if __name__ == '__main__':
    app.run_server(port=8050, debug=True, processes=4, threaded=False)
