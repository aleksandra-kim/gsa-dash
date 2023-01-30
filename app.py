# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import bw2data as bd

# Dash
from dash import Dash, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

# Local files
from layout import (
    create_background_callback_manager,
    create_layout,
    get_lca_config,
    get_mc_config,
    get_lca_mc_config,
)

from backend.life_cycle_assessment import (
    compute_deterministic_score
)
from make_figures import plot_mc_simulations
from backend.data import create_directory
# from constants import ITERATIONS_CHUNKSIZE

# TODO
# 1. add unit to activity amount
# 2. add default values for iterations, seed, amount, etc

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
        project, database, method, activity, amount, use_distributions=False, seed=None
    )
    return f"{score:.3e}", unit


@app.callback(
    Output("mc-graph", 'figure'),
    inputs=dict(
        score=Input("score", "children"),
        unit=State("method-unit", "children"),
        mc_config=get_mc_config(State),
    ),
)
def plot_simulations(score, unit, mc_config):
    iterations, seed = mc_config.get("Iterations"), mc_config.get("seed")
    fig = plot_mc_simulations(score, unit)
    return fig


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
    directory = create_directory(lca_mc_config)
    mc_directory = directory / f"iterations{iterations}_seed{seed}"
    mc_directory.mkdir(parents=True, exist_ok=True)
    return str(directory)


@app.callback(
    Output("mc-state", "data"),
    inputs=dict(
        n_clicks=Input("btn-start-mc", "n_clicks"),
        lca_mc_config=get_lca_mc_config(State),

    )
)
def run_simulations_wrapper(n_clicks, lca_mc_config):
    if n_clicks == 0:
        raise PreventUpdate
    iterations, seed = lca_mc_config.get("iterations"), lca_mc_config.get("seed")

    return True


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
#     project, database, method, activity, amount, iterations, seed = all_states["project"], all_states["database"], \
#         all_states["method"], all_states["activity"], all_states["amount"], all_states["iterations"], all_states["seed"]
#     run_mc_simulations_from_dp_X_all(
#         directory, project, database, method, activity, amount, iterations, seed, DEFAULT_CHUNKSIZE
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
