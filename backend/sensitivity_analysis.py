import numpy as np
import bw2data as bd
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression


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
    return spearman


def compute_gradient_boosting_importances(X, Y):
    return np.zeros(X.shape[1])


def collect_sensitivity_results(project, S, indices, sensitivity_method="GSA index"):
    bd.projects.set_current(project)
    row_act_names, row_act_locations, row_act_categories = [], [], []
    col_act_names, col_act_locations, static_data = [], [], []
    types, amounts, units = [], [], []
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
    amounts_display = [f"{a[0]:4.2e} {a[1]} " for a in zip(amounts, units)]
    S_display = [float(f"{s: 6.3f}") for s in S]
    data = {
        "Input name": row_act_names,
        "Input location": row_act_locations,
        "Input categories": row_act_categories,
        "Output name": col_act_names,
        "Output location": col_act_locations,
        "Exchange type": types,
        "Exchange amount": amounts_display,
        "GSA index": S_display,
        "GSA method": sensitivity_method,
    }
    return data
#
#
# def create_gsa_results_dataframe(directory, project):
#     directory = Path(directory)
#     bd.projects.set_current(project)
#     spearman = compute_gsa_results(directory)
#     indices = read_pickle(directory / f"indices.pickle")
#     row_act_names, row_act_locations, row_act_categories = [], [], []
#     col_act_names, col_act_locations, static_data = [], [], []
#     for i in indices:
#         row_act = bd.get_activity(i['row'])
#         col_act = bd.get_activity(i['col'])
#         row_act_names.append(row_act['name'])
#         row_act_locations.append(row_act.get("location", "None"))
#         row_act_categories.append(row_act.get("category", "None"))
#         col_act_names.append(col_act['name'])
#         col_act_locations.append(col_act.get("location", "None"))
#         for exc in col_act.exchanges():
#             if row_act.id == exc.input.id:
#                 static_data.append(exc.amount)
#                 break
#     dict_ = {
#         "Input name": row_act_names,
#         "Input location": row_act_locations,
#         "categories": row_act_categories,
#         "Output name": col_act_names,
#         "Output location": col_act_locations,
#         "GSA index": spearman,
#     }
#     df = pd.DataFrame.from_dict(dict_)
#     df.sort_values(by="GSA index", axis=0, ascending=False, inplace=True)
#     df.reset_index(inplace=True, drop=True)
#     columns = df.columns.tolist()
#     df["GSA rank"] = np.arange(1, len(df)+1)
#     columns = ["GSA rank"] + columns
#     df = df[columns]
#     dfi.export(df, directory/"mytable.png")
#     return df
