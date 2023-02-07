# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import bw2data as bd
from pathlib import Path

# Dash
import dash
from dash import Dash, Input, Output, State, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import time

# Local files
from layout import (
    create_background_callback_manager,
    create_layout,
    get_lca_config,
    get_mc_config,
    get_lca_mc_config,
    style_bars_in_datatable,
)

from backend.data import create_directory, collect_Y, get_Y_files, collect_XY, read_pickle
from backend.life_cycle_assessment import compute_deterministic_score
from backend.monte_carlo import run_simulations_from_X_all
from backend.sensitivity_analysis import compute_model_linearity, compute_sensitivity_indices, collect_sensitivity_results
from make_figures import plot_mc_simulations, plot_model_linearity, create_table_gsa_ranking

from constants import ITERATIONS_CHUNKSIZE, INTERVAL_TIME, LINEARITY_THRESHOLD

# TODO
# 1. add unit to activity amount

app = Dash(
    __name__,
    background_callback_manager=create_background_callback_manager(),
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.PULSE]
)
app.layout = create_layout()


@app.callback(
    Output('method', 'options'),
    Output('database', 'options'),
    Input('project', 'value'),
)
def get_methods_databases(project):
    if project is None:
        raise PreventUpdate
    bd.projects.set_current(project)
    # methods = [", ".join(m) for m in bd.methods if "superseded" not in str(m)]  # TODO uncomment in the end
    methods = [", ".join(('IPCC 2013', 'climate change', 'GWP 100a'))]
    return sorted(methods), sorted(list(bd.databases))


@app.callback(
    Output('activity', 'options'),
    Input('project', 'value'),
    Input('database', 'value'),
)
def get_activities(project, database):
    if project is None:
        raise PreventUpdate
    bd.projects.set_current(project)
    db = bd.Database(database)
    activities = [f"{act['name']}, {act['location']}" for act in db]
    return sorted(activities)


@app.callback(
    Output("score", "children"),
    Output("method-unit", "children"),
    inputs=dict(lca_config=get_lca_config(Input)),
)
def compute_deterministic_score_wrapper(lca_config):
    project, database, activity, amount, method = lca_config.get("project"), lca_config.get("database"), \
                                                  lca_config.get("activity"), lca_config.get("amount"), \
                                                  lca_config.get("method")
    if (project is None) or (database is None) or (activity is None) or (method is None):
        raise PreventUpdate
    score, unit = compute_deterministic_score(
        project, database, activity, amount, method, use_distributions=False, seed=None
    )
    return f"{score:.3e}", unit


# @app.callback(
#     Output("mc-state", "data"),
#     Input("mc-progress-interval", "n_intervals"),
#     State("directory", "data"),
#     State("mc-state", "data"),
# )
# def check_mc_state(n_intervals, directory, mc_state):
#     if directory is None:
#         raise PreventUpdate
#     files = get_scores_files(directory)
#     updated_mc_state = len(files)
#     print(mc_state, updated_mc_state)
#     if mc_state != updated_mc_state:
#         return updated_mc_state
#     else:
#         return dash.no_update


@app.callback(
    Output("mc-graph", 'figure'),
    Output("mc-progress", "value"),
    Output("mc-progress", "label"),
    Output("mc-state", "data"),
    inputs=dict(
        n_intervals=Input("mc-progress-interval", "n_intervals"),
        score=Input("score", "children"),
    ),
    state=dict(
        unit=State("method-unit", "children"),
        mc_finished=State("mc-finished", "data"),
        mc_state=State("mc-state", "data"),
        directory=State("directory", "data"),
        mc_config=get_mc_config(State),
    ),
)
def plot_simulations(n_intervals, score, unit, mc_finished, mc_state, directory, mc_config):
    if score is None:
        raise PreventUpdate
    if "score" == ctx.triggered_id:
        fig = plot_mc_simulations(score, unit)
        return fig, dash.no_update, dash.no_update, dash.no_update
    Y_files = get_Y_files(directory)
    if mc_finished or (len(Y_files) > mc_state):
        Y_data = collect_Y(Y_files)
        fig = plot_mc_simulations(score, unit, Y_data, mc_config["iterations"])
        progress = len(Y_data) / mc_config['iterations'] * 100
        return fig, progress, f"{progress:2.0f}%", len(Y_files)
    else:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output("directory", "data"),
    inputs=dict(
        n_clicks=Input("btn-start-mc", "n_clicks"),
        lca_mc_config=get_lca_mc_config(State),
    )
)
def create_directory_wrapper(n_clicks, lca_mc_config):
    if n_clicks == 0:
        raise PreventUpdate
    iterations, seed = lca_mc_config.pop("iterations"), lca_mc_config.pop("seed")
    base_directory = create_directory(lca_mc_config)
    directory = base_directory / f"iterations{iterations}_seed{seed}"
    directory.mkdir(parents=True, exist_ok=True)
    return str(directory)


@app.callback(
    Output("mc-finished", "data"),
    inputs=dict(
        directory=Input("directory", "data"),
        n_clicks=State("btn-start-mc", "n_clicks"),
        lca_mc_config=get_lca_mc_config(State),
    )
)
def run_simulations_wrapper(directory, n_clicks, lca_mc_config):
    if directory is None:
        raise PreventUpdate
    run_simulations_from_X_all(directory, lca_mc_config, ITERATIONS_CHUNKSIZE)
    return True


@app.callback(
    Output('mc-progress-interval', 'max_intervals'),
    Input("btn-start-mc", "n_clicks"),
    Input("mc-finished", "data"),
)
def disable_mc_interval(n_clicks, mc_finished):
    if mc_finished:
        time.sleep(INTERVAL_TIME)
        return None
    if n_clicks > 0:
        return 1e5


@app.callback(
    Output('linearity-graph', 'figure'),
    Output('ranking-table', 'data'),
    Output('ranking-table', 'columns'),
    Output('ranking-table', 'style_data_conditional'),
    Input('mc-progress-interval', 'n_intervals'),
    State("mc-finished", "data"),
    State("directory", "data"),
    State("project", "value")
)
def plot_sensitivity_results(n, mc_finished, directory, project):
    if directory is not None:
        directory = Path(directory)
    if mc_finished:
        X, Y = collect_XY(directory)
        indices = read_pickle(directory / "indices.pickle")
        model_linearity = compute_model_linearity(X, Y)
        sensitivity_indices, sensitivity_method = compute_sensitivity_indices(X, Y, model_linearity, LINEARITY_THRESHOLD)
        sensitivity_data = collect_sensitivity_results(project, sensitivity_indices, indices, sensitivity_method)
        df = create_table_gsa_ranking(sensitivity_data)
        styles = style_bars_in_datatable(df, 'GSA index')
        df_data = df.to_dict("records")
        columns = [{"name": i, "id": i} for i in df.columns]
        fig_linearity = plot_model_linearity(model_linearity, LINEARITY_THRESHOLD)
        return fig_linearity, df_data, columns, styles
    else:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update


# @app.callback(
#     Output("sensitivity-analysis", 'children'),
#     Output("mc-completed", 'value'),
#     inputs=dict(
#         directory=Input("directory", "value"),
#         all_states=get_lca_mc_config(State),
#     ),
# )
# def run_mc_simulations_wrapper(directory, all_states):
#     if directory is None:
#         raise PreventUpdate
#     project, database, activity, amount, method, iterations, seed = all_states["project"], all_states["database"], \
#         all_states["method"], all_states["activity"], all_states["amount"], all_states["iterations"], all_states["seed"]
#     run_mc_simulations_from_dp_X_all(
#         directory, project, database, activity, amount, method, iterations, seed, DEFAULT_CHUNKSIZE
#     )
#     df = create_gsa_results_dataframe(directory, project)
#     gsa_section = create_gsa_section(df)
#     return gsa_section, True
#
#
# # @app.callback(
# #     Output('mc-interval', 'disabled'),
# #     Input("mc-completed", "value"),
# # )
# # def disable_mc_interval(mc_completed):
# #     if mc_completed is not None and mc_completed:
# #         return True
#
#
# @app.callback(
#     Output("mc-state", "value"),
#     Output("mc-graph", "figure"),
#     Input('mc-interval', 'n_intervals'),
#     Input("mc-button", "n_clicks"),
#     Input("mc-completed", "value"),
#     State("directory", "value"),
#     State("mc-state", "value"),
#     State("score", "children"),
#     State("method-unit", "children"),
# )
# def update_mc_state(n_intervals, n_clicks, mc_completed, directory, mc_state, score, method_unit):
#     if mc_completed is not None and mc_completed:
#         directory = Path(directory)
#         mc_scores = collect_mc_scores(directory)
#         figure = plot_mc_simulations(score, method_unit, mc_scores)
#         import plotly.graph_objects as go
#         f = go.Figure(figure)
#         f.write_image(directory / "mc.webp")
#         return dash.no_update, figure
#     if directory is None or n_clicks == 0:
#         return dash.no_update, dash.no_update
#     directory = Path(directory)
#     yfiles = get_mc_scores_files(directory)
#     if mc_state is None:
#         return len(yfiles), dash.no_update
#     if mc_state == len(yfiles):
#         return dash.no_update, dash.no_update
#     if mc_state + 1 == len(yfiles):
#         mc_scores = collect_mc_scores(directory)
#         if len(mc_scores) > 0:
#             figure = plot_mc_simulations(score, method_unit, mc_scores)
#             return mc_state + 1, figure


if __name__ == '__main__':
    app.run_server(port=8050, debug=True, processes=4, threaded=False)
