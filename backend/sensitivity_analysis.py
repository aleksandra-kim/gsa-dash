import numpy as np
import bw2data as bd
import bw2calc as bc
from pathlib import Path
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression

# Local files
from .data import read_json, write_json
from .life_cycle_assessment import create_lca


def compute_model_linearity(X, Y):
    iterations_all = len(Y)
    n_chunks = 10
    chunk_size = iterations_all//n_chunks
    iterations_spaced = np.arange(chunk_size, iterations_all, chunk_size)
    model_linearity = dict()
    for iterations in iterations_spaced:
        Xi, Yi = X[:iterations, :], Y[:iterations]
        src = compute_src(Xi, Yi)
        model_linearity[iterations] = src
    return model_linearity


def compute_src(X, Y):
    """Standardized regression coefficients."""
    X, Y = np.array(X), np.array(Y)
    reg = LinearRegression().fit(X, Y)
    # High reg.score in linear regression means that the model performs well on the train and test data.
    stdX = np.std(X, axis=0)
    stdY = np.std(Y)
    src_coefficients = reg.coef_ * stdX / stdY
    src_sum = sum(src_coefficients**2)
    return src_sum


def compute_sensitivity_indices(X, Y, linearity, linearity_threshold):
    src = list(linearity.values())[-1]
    if src > linearity_threshold:
        S = compute_spearman_coefficients(X, Y)
        sensitivity_method = "Spearman correlations"
    else:
        S = compute_gradient_boosting_importances(X, Y)
        sensitivity_method = "Gradient boosting"
    return S, sensitivity_method


def compute_spearman_coefficients(X, Y):
    spearman = []
    for x in X.T:
        if len(set(x)) != 1:
            spearman.append(spearmanr(x, Y)[0])
        else:
            spearman.append(0)
    spearman = np.array(spearman)
    ctv = spearman**2 / sum(spearman**2)
    return ctv


def compute_gradient_boosting_importances(X, Y):
    return np.zeros(X.shape[1])


def contribution_analysis(directory, project, database, activity, amount, method, cutoff=0.005, max_calc=1e5):
    lca = create_lca(project, database, activity, amount, method)
    contributions_tech = contribution_analysis_technosphere(directory, lca, cutoff, max_calc)
    contributions = {**contributions_tech}
    return contributions


def contribution_analysis_technosphere(directory, lca, cutoff=0.005, max_calc=1e5):
    directory = Path(directory)
    contribution_file = directory.parent / f"graph_traversal_cutoff{cutoff:4.3e}_maxcalc{max_calc:4.3e}.json"
    if contribution_file.exists():
        res = read_json(contribution_file)
    else:
        gt = bc.graph_traversal.AssumedDiagonalGraphTraversal()
        res = gt.calculate(lca, cutoff=cutoff, max_calc=max_calc)
        write_json(res, contribution_file)
    contributions = dict()
    for edge in res["edges"]:
        if edge["to"] != -1:
            row, col = edge['from'], edge['to']
            i, j = lca.dicts.activity.reversed[row], lca.dicts.activity.reversed[col]
            contributions[(i, j)] = edge['impact']
    return contributions


def collect_sensitivity_results(project, S, C, indices, sensitivity_method="GSA index"):
    bd.projects.set_current(project)
    row_act_names, row_act_locations, row_act_categories = [], [], []
    col_act_names, col_act_locations, static_data = [], [], []
    types, amounts, units = [], [], []
    contributions = []
    for i in indices:
        row_act = bd.get_activity(i['row'])
        col_act = bd.get_activity(i['col'])
        row_act_names.append(row_act['name'])
        row_act_locations.append(row_act.get("location"))
        row_act_categories.append(row_act.get("category"))
        col_act_names.append(col_act['name'])
        col_act_locations.append(col_act.get("location"))
        for exc in col_act.exchanges():
            if row_act.id == exc.input.id:
                amounts.append(exc.amount)
                units.append(exc.input["unit"])
                types.append(exc.get("type"))
        contribution = C.get((row_act.id, col_act.id), 0)
        contributions.append(contribution)
    amounts_display = [f"{a[0]:4.2e} {a[1]} " for a in zip(amounts, units)]
    S_display = [float(f"{s: 6.4f}") for s in S]
    C_display = [float(f"{c: 6.4f}") for c in contributions]
    data = {
        "Input name": row_act_names,
        "Input location": row_act_locations,
        "Input categories": row_act_categories,
        "Output name": col_act_names,
        "Output location": col_act_locations,
        "Exchange type": types,
        "Exchange amount": amounts_display,
        "GSA index": S_display,
        "Contribution": C_display,
        "GSA method": sensitivity_method,
        "indices": indices,
    }
    return data
