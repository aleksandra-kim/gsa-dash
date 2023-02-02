import numpy as np
import pandas as pd
import bw2data as bd
from pathlib import Path
from scipy.stats import spearmanr
import dataframe_image as dfi
from sklearn.linear_model import LinearRegression

# Local files
from .data import read_json, read_pickle


def compute_model_linearity():
    return


# def compute_degree_of_linearity(X, Y, train_test_ratio=0.8):
#     X, Y = np.array(X), np.array(Y)
#     iterations = len(Y)
#     split = int(train_test_ratio*iterations)
#     Xtrain, Ytrain = X[:split, :], Y[:split]
#     Xtest, Ytest = X[split:, :], Y[split:]
#     reg = LinearRegression().fit(Xtrain, Ytrain)
#     # High reg.score in linear regression means that the model performs well on the train and test data.
#     print(reg.score(Xtrain, Ytrain), reg.score(Xtest, Ytest))
#     stdX = np.std(X, axis=0)
#     stdY = np.std(Y)
#     src_coefficients = reg.coef_ * stdX / stdY
#     src_sum = sum(src_coefficients**2)
#     return src_sum
#
#
# def collect_X_Y(directory):
#     files = list(directory.iterdir())
#     yfiles = sorted([f.name for f in files if "Y" in f.name])
#     xfiles = sorted([f.name for f in files if "X" in f.name])
#     assert (n := len(yfiles)) == len(xfiles)
#     X, Y = [], []
#     for i in range(n):
#         y = read_json(directory / f"Y{i}.json")
#         x = read_json(directory / f"X{i}.json")
#         Y += y
#         X += x
#     return X, Y
#
#
# def compute_gsa_results(directory):
#     X, Y = collect_X_Y(directory)
#     X, Y = np.array(X), np.array(Y).flatten()
#     spearman = []
#     for x in X.T:
#         if len(set(x)) != 1:
#             spearman.append(spearmanr(x, Y)[0])
#         else:
#             spearman.append(0)
#     spearman = np.array(spearman)
#     return spearman
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
