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
    get_val_config,
    style_bars_in_datatable,
)

from backend.data import create_directory, collect_Y, get_Y_files, collect_XY, read_pickle, get_val_state
from backend.life_cycle_assessment import compute_deterministic_score
from backend.monte_carlo import run_simulations_from_X_all
from backend.sensitivity_analysis import (
    compute_model_linearity, compute_sensitivity_indices, collect_sensitivity_results, contribution_analysis
)
from backend.validation import run_validation, collect_validation_results
from make_figures import plot_mc_simulations, plot_model_linearity, create_table_gsa_ranking, plot_validation
from constants import ITERATIONS, INTERVAL_TIME, LINEARITY_THRESHOLD, GT_CUTOFF, GT_MAXCALC, PAGE_SIZE


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


@app.callback(
    Output("mc-graph", 'figure'),
    Output("mc-progress", "value"),
    Output("mc-progress", "label"),
    Output("mc-state", "data"),
    inputs=dict(
        n_intervals=Input("mc-interval", "n_intervals"),
        directory=Input("directory", "data"),
        score=Input("score", "children"),
    ),
    state=dict(
        unit=State("method-unit", "children"),
        mc_finished=State("mc-finished", "data"),
        mc_state=State("mc-state", "data"),
        mc_config=get_mc_config(State),
    ),
)
def plot_simulations(n_intervals, directory, score, unit, mc_finished, mc_state, mc_config):
    if score is None or directory is None:
        raise PreventUpdate
    if "score" == ctx.triggered_id or "directory" == ctx.triggered_id:
        fig = plot_mc_simulations(score, unit)
        return fig, 0, dash.no_update, 0
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
    iterations, iterations_chunk, seed = lca_mc_config.pop("iterations"), lca_mc_config.pop("iterations_chunk"), lca_mc_config.pop("seed")
    base_directory = create_directory(lca_mc_config)
    directory = base_directory / f"iterations{iterations}_chunk{iterations_chunk}_seed{seed}"
    directory.mkdir(parents=True, exist_ok=True)
    return str(directory)


@app.callback(
    Output("mc-finished", "data"),
    inputs=dict(
        directory=Input("directory", "data"),
        mc_config=get_mc_config(Input),
        n_clicks=State("btn-start-mc", "n_clicks"),
        lca_config=get_lca_config(State),
    )
)
def run_simulations_wrapper(directory, mc_config, n_clicks, lca_config):
    if directory is None:
        raise PreventUpdate
    if ctx.triggered_id in ["iterations", "iterations-chunk", "seed"]:
        return False
    lca_mc_config = {**lca_config, **mc_config}
    run_simulations_from_X_all(directory, lca_mc_config)
    return True


@app.callback(
    Output('mc-interval', 'max_intervals'),
    Input("btn-start-mc", "n_clicks"),
    Input("mc-finished", "data"),
)
def toggle_mc_interval(n_clicks, mc_finished):
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
    Output('sensitivity-indices', 'data'),
    inputs=dict(
        n_intervals=Input('mc-interval', 'n_intervals'),
        mc_finished=State("mc-finished", "data"),
        directory=State("directory", "data"),
        lca_config=get_lca_config(State),
        unit=State("method-unit", "children"),
    )
)
def plot_sensitivity_results(n_intervals, mc_finished, directory, lca_config, unit):
    if directory is not None:
        directory = Path(directory)
    if mc_finished:
        project, database, activity, amount, method = lca_config["project"], lca_config["database"], \
                                                      lca_config["activity"], lca_config["amount"], lca_config["method"]
        X, Y = collect_XY(directory)
        indices = read_pickle(directory / "indices.pickle")
        model_linearity = compute_model_linearity(X, Y)
        sensitivity_indices, sensitivity_method = compute_sensitivity_indices(X, Y, model_linearity, LINEARITY_THRESHOLD)
        contributions = contribution_analysis(directory, project, database, activity, amount, method, GT_CUTOFF, GT_MAXCALC)
        sensitivity_data = collect_sensitivity_results(
            project, sensitivity_indices, contributions, indices, sensitivity_method,
        )
        df = create_table_gsa_ranking(sensitivity_data, PAGE_SIZE)
        bar_styles_gsa = style_bars_in_datatable(df, 'GSA index', color_bars="#5757E5")
        bar_styles_ca = style_bars_in_datatable(df, "Contribution", color_bars="#9EC7E4")
        df_data = df.to_dict("records")
        contribution_column = f"Contribution \n {unit}"
        columns = [{"name": i if "Contribution" not in i else contribution_column, "id": i} for i in df.columns]
        fig_linearity = plot_model_linearity(model_linearity, LINEARITY_THRESHOLD, ITERATIONS)
        return fig_linearity, df_data, columns, bar_styles_gsa + bar_styles_ca, sensitivity_indices
    else:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output("val-graph", 'figure'),
    Output("val-state", "data"),
    inputs=dict(
        n_intervals=Input("val-interval", "n_intervals")
    ),
    state=dict(
        val_finished=State("val-finished", "data"),
        val_state=State("val-state", "data"),
        val_directory=State("val-directory", "data"),
        val_min=State('val-min', 'value'),
        val_max=State("val-max", "value")
    ),
)
def plot_validation_results(n_intervals, val_finished, val_state, val_directory, val_min, val_max):
    if "val-interval" == ctx.triggered_id:
        val_new_state = get_val_state(val_directory)
        if val_finished or (val_new_state > val_state):
            metric = collect_validation_results(val_directory)
            fig = plot_validation(min_influential=val_min, max_influential=val_max, metric=metric)
            return fig, val_new_state
    if val_finished:
        metric = collect_validation_results(val_directory)
        fig = plot_validation(min_influential=val_min, max_influential=val_max, metric=metric)
        return fig, dash.no_update
    else:
        return dash.no_update, dash.no_update


@app.callback(
    Output("val-directory", "data"),
    inputs=dict(
        n_clicks=Input("btn-start-val", "n_clicks"),
        directory=State('directory', 'data'),
        val_iterations=State('val-iterations', 'value'),
    ),
)
def create_validation_directory(n_clicks, directory, val_iterations):
    if directory is None:
        raise PreventUpdate
    val_directory = Path(directory) / f"validation_iterations{val_iterations}"
    val_directory.mkdir(exist_ok=True, parents=True)
    return str(val_directory)


@app.callback(
    Output("val-finished", "data"),
    inputs=dict(
        val_directory=Input("val-directory", "data"),
        n_clicks=State("btn-start-val", "n_clicks"),
        sensitivity_indices=State('sensitivity-indices', 'data'),
        val_config=get_val_config(State),
        lca_config=get_lca_config(State),
    ),
)
def run_validation_wrapper(val_directory, n_clicks, sensitivity_indices, val_config, lca_config):
    if val_directory is None:
        raise PreventUpdate
    run_validation(val_directory, sensitivity_indices, val_config, lca_config)
    return True


@app.callback(
    Output('val-interval', 'max_intervals'),
    Input("btn-start-val", "n_clicks"),
    Input("val-finished", "data"),
)
def toggle_val_interval(n_clicks, val_finished):
    if val_finished:
        time.sleep(INTERVAL_TIME)
        return None
    if n_clicks > 0:
        return 1e5


# @app.callback(
#     Output("loading", "children"),
#     Input("btn-start-mc", "n_clicks"),
#     Input("mc-finished", "data"),
# )
# def show_spinner(n_clicks, mc_finished):
#     if n_clicks > 0 and not mc_finished:
#         return dbc.Spinner
#     else:
#         return ""


if __name__ == '__main__':
    app.run_server(port=8050, debug=True, processes=4, threaded=False)
    # S = [4.603434194207573e-07, 2.2249683869030188e-05, 3.9360692583675376e-05, 6.829567686821097e-06, 0.00015842636669209997, 3.551273901176164e-05, 0.000184551181813614, 7.054943648507228e-05, 0.00018215709387586402, 7.867614387276886e-05, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.00033280917001736877, 2.584947636800068e-05, 0.10972620439924098, 0.2724981409967113, 0.00018457405848154113, 0.0012288022072621477, 2.1383620949436447e-05, 0.0001348117550599159, 7.552255360738365e-05, 0.0009538848457231237, 0.007721988479436372, 0.013300715865253408, 0.0008915836482620274, 0.000185372391008026, 1.4224811226337263e-05, 0.0001195778767520251, 9.187438700718488e-05, 0.0014423581429162105, 0.00015401592493782812, 0, 0.0009701767380501706, 6.890766349306294e-05, 0.00038529065074951216, 0.0004131647479950618, 0, 0.022048581800915297, 0, 0.11700268404946852, 0, 0.1463808191369305, 0, 0.027037078020182233, 0, 0.03119299658358151, 0, 0.03255405434807512, 0, 0.024937797544296134, 0, 0.03472719724355662, 0, 0.08358332603421352, 0, 0.031620923017200125, 0, 0.036831060395590504, 0, 6.302513115373807e-05, 3.839752982900482e-05, 6.5355717002662834e-06, 3.4695276843202386e-06, 2.394251970391751e-07, 6.3514838825418516e-09, 5.456150321608011e-05, 2.727171983956564e-07, 7.237749383616146e-09, 1.829328180860258e-05, 0.00016449301164658158, 1.279803864025152e-05, 1.3748388637538642e-06]
    # directory = Path("/home/aleksandrakim/gsa-dash-cache/8a7c0f6422780773/iterations8000_seed1234567/validation")
    # val_config = dict(
    #     max_influential=80,
    #     step_influential=40,
    #     iterations=10,
    # )
    # lca_config = dict(
    #     project="Uncertainties Chaerhan",
    #     database="Chaerhan_38",
    #     activity="Rotary dryer, CN",
    #     amount=1,
    #     method="IPCC 2013, climate change, GWP 100a",
    # )
    # run_validation(directory, S, val_config, lca_config)
