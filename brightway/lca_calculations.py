import bw2data as bd
import bw2calc as bc
import bw_processing as bwp
import numpy as np
import pandas as pd
from pathlib import Path
import json
import pickle
from sklearn.linear_model import LinearRegression
from scipy.stats import spearmanr
import dataframe_image as dfi


def write_json(data, fp):
    with open(fp, 'w') as h:
        json.dump(data, h)


def read_json(fp):
    with open(fp, 'r') as f:
        data = json.load(f)
    return data


def write_pickle(data, fp):
    with open(fp, 'wb') as h:
        pickle.dump(data, h, protocol=pickle.HIGHEST_PROTOCOL)


def read_pickle(fp):
    with open(fp, 'rb') as h:
        data = pickle.load(h)
    return data


def prepare_lca(project, database, method, activity):
    bd.projects.set_current(project)
    db = bd.Database(database)
    fu_location = activity.split(", ")[-1]
    fu_name = activity[:-len(fu_location)-2]
    fu = [act for act in db if fu_name == act['name'] and fu_location == act['location']]
    assert len(fu) == 1
    fu = fu[0]
    method = tuple(method.split(", "))
    return fu, method


def create_lca(project, database, method, activity, amount, use_distributions, seed):
    fu, method = prepare_lca(project, database, method, activity)
    lca = bc.LCA({fu: amount}, method, use_distributions=use_distributions, seed_override=seed)
    lca.lci()
    lca.lcia()
    return lca


def compute_deterministic_score(
        project, database, method, activity, amount, use_distributions, seed
):
    lca = create_lca(project, database, method, activity, amount, use_distributions, seed)
    method = lca.method
    unit = bd.Method(method).metadata.get("unit", "")
    return lca.score, unit


def create_dp_X(lca_obj, nsamples, matrix_type, name, seed):

    from matrix_utils.resource_group import FakeRNG

    dp = bwp.create_datapackage(
        name=name,
        seed=seed,
        sequential=True,
    )

    num_resources = 3
    if matrix_type == "technosphere":
        num_resources = 4

    obj = getattr(lca_obj, f"{matrix_type}_mm")

    indices_array = np.hstack([
        group.package.data[0] for group in obj.groups
        if (not isinstance(group.rng, FakeRNG)) and (not group.empty) and (len(group.package.data) == num_resources)
    ])

    mask = np.ones(len(indices_array), dtype=bool)

    data = []
    np.random.seed(seed)
    for _ in range(nsamples):
        next(obj)
        idata = []
        for group in obj.groups:
            if (not isinstance(group.rng, FakeRNG)) and (not group.empty):
                idata.append(group.rng.random_data)
        data.append(np.hstack(idata)[mask])
    data_array = np.vstack(data).T

    if matrix_type == "technosphere":
        flip_array = np.hstack([
            group.flip for group in obj.groups
            if (not isinstance(group.rng, FakeRNG)) and (not group.empty) and (len(group.package.data) == num_resources)
        ])
        dp.add_persistent_array(
            matrix=f"{matrix_type}_matrix",
            data_array=data_array,
            name=name,
            indices_array=indices_array[mask],
            flip_array=flip_array[mask],
        )
    else:
        dp.add_persistent_array(
            matrix=f"{matrix_type}_matrix",
            data_array=data_array,
            name=name,
            indices_array=indices_array[mask],
        )

    return dp


def find_background_databases():
    """TODO definitely need to find a better way of finding bg databases."""
    dbs = [name for name in bd.databases if "ecoinvent" in name]
    assert len(dbs) == 1
    return dbs


def get_dps_no_background_uncertainty(method):
    me = bd.Method(method).datapackage()
    background = find_background_databases()
    dps = [me]
    for database in bd.databases:
        dp = bd.Database(database).datapackage()
        if database in background:
            dp = dp.exclude({"kind": "distributions"})
        dps.append(dp)
    return dps


def get_dps_no_foreground_background_uncertainty(method):
    me = bd.Method(method).datapackage()
    bs = bd.Database("biosphere3").datapackage()
    dps = [me, bs]
    for database in bd.databases:
        if database != "biosphere3":
            dp = bd.Database(database).datapackage()
            dp = dp.exclude({"kind": "distributions"})
            dps.append(dp)
    return dps


def run_mc_simulations_from_dp_X_all(directory, project, database, method, activity, amount, iterations, seed, chunksize):
    directory = Path(directory)
    np.random.seed(seed)
    n_chunks = iterations//chunksize+1
    chunk_seeds = np.random.randint(1, np.iinfo(np.int32).max, n_chunks)
    fpI = directory / f"indices.pickle"
    for i in range(n_chunks):
        fpY = directory / f"Y{i}.json"
        fpX = directory / f"X{i}.json"
        if (not fpY.exists()) or (not fpX.exists()) or (not fpI.exists()):
            input_indices, input_data, mc_scores = run_mc_simulations_from_dp_X(
                project, database, method, activity, amount, chunksize, chunk_seeds[i]
            )
            write_json(mc_scores, fpY)
            write_json(input_data, fpX)
            write_pickle(input_indices, fpI)


def run_mc_simulations_from_dp_X(project, database, method, activity, amount, iterations, seed):
    # Prepare input data
    fu, method = prepare_lca(project, database, method, activity)
    dps_no_bg_unct = get_dps_no_background_uncertainty(method)
    lca_temp = bc.LCA(
        {fu.id: amount},
        data_objs=dps_no_bg_unct,
        use_distributions=True,
        seed_override=seed,
    )
    lca_temp.lci()
    lca_temp.lcia()
    dp_name = "no_background_uncertainty"
    dp_tech = create_dp_X(lca_temp, iterations, "technosphere", dp_name, seed)
    dp_bio = create_dp_X(lca_temp, iterations, "biosphere", dp_name, seed)
    input_data = np.vstack([dp_tech.data[1], dp_bio.data[1]]).T.tolist()
    input_indices = np.hstack([dp_tech.data[0], dp_bio.data[0]])
    # Run Monte Carlo simulations
    dps_no_fg_bg_unct = get_dps_no_foreground_background_uncertainty(method)
    dps_gsa = dps_no_fg_bg_unct + [dp_tech, dp_bio]
    lca_gsa = bc.LCA(
        {fu.id: amount},
        data_objs=dps_gsa,
        use_distributions=False,
        use_arrays=True,
    )
    lca_gsa.lci()
    lca_gsa.lcia()
    lca_gsa.keep_first_iteration()
    mc_scores = []
    for i in range(iterations):
        next(lca_gsa)
        mc_scores.append(lca_gsa.score)
    return input_indices, input_data, mc_scores


def run_mc_simulations(directory, project, database, method, activity, amount, iterations, seed, chunksize):
    directory = Path(directory)
    bd.projects.set_current(project)
    lca = create_lca(project, database, method, activity, amount, use_distributions=True, seed=seed)
    lca.keep_first_iteration()
    for i in range(iterations//chunksize+1):
        mc_scores = []
        for _ in range(chunksize):
            next(lca)
            mc_scores.append(lca.score)
        write_json(mc_scores, directory / f"Y{i}.json")


def compute_degree_of_linearity(X, Y, train_test_ratio=0.8):
    X, Y = np.array(X), np.array(Y)
    iterations = len(Y)
    split = int(train_test_ratio*iterations)
    Xtrain, Ytrain = X[:split, :], Y[:split]
    Xtest, Ytest = X[split:, :], Y[split:]
    reg = LinearRegression().fit(Xtrain, Ytrain)
    # High reg.score in linear regression means that the model performs well on the train and test data.
    print(reg.score(Xtrain, Ytrain), reg.score(Xtest, Ytest))
    stdX = np.std(X, axis=0)
    stdY = np.std(Y)
    src_coefficients = reg.coef_ * stdX / stdY
    src_sum = sum(src_coefficients**2)
    return src_sum


def collect_X_Y(directory):
    files = list(directory.iterdir())
    yfiles = sorted([f.name for f in files if "Y" in f.name])
    xfiles = sorted([f.name for f in files if "X" in f.name])
    assert (n := len(yfiles)) == len(xfiles)
    X, Y = [], []
    for i in range(n):
        y = read_json(directory / f"Y{i}.json")
        x = read_json(directory / f"X{i}.json")
        Y += y
        X += x
    return X, Y


def compute_gsa_results(directory):
    X, Y = collect_X_Y(directory)
    X, Y = np.array(X), np.array(Y).flatten()
    spearman = []
    for x in X.T:
        if len(set(x)) != 1:
            spearman.append(spearmanr(x, Y)[0])
        else:
            spearman.append(0)
    spearman = np.array(spearman)
    return spearman


def create_gsa_results_dataframe(directory, project):
    directory = Path(directory)
    bd.projects.set_current(project)
    spearman = compute_gsa_results(directory)
    indices = read_pickle(directory / f"indices.pickle")
    row_act_names, row_act_locations, row_act_categories = [], [], []
    col_act_names, col_act_locations, static_data = [], [], []
    for i in indices:
        row_act = bd.get_activity(i['row'])
        col_act = bd.get_activity(i['col'])
        row_act_names.append(row_act['name'])
        row_act_locations.append(row_act.get("location", "None"))
        row_act_categories.append(row_act.get("category", "None"))
        col_act_names.append(col_act['name'])
        col_act_locations.append(col_act.get("location", "None"))
        for exc in col_act.exchanges():
            if row_act.id == exc.input.id:
                static_data.append(exc.amount)
                break
    dict_ = {
        "Input name": row_act_names,
        "location": row_act_locations,
        "categories": row_act_categories,
        "Output name": col_act_names,
        "location": col_act_locations,
        "GSA index": spearman,
    }
    df = pd.DataFrame.from_dict(dict_)
    df.sort_values(by="GSA index", axis=0, ascending=False, inplace=True)
    df.reset_index(inplace=True, drop=True)
    columns = df.columns.tolist()
    df["GSA rank"] = np.arange(1, len(df)+1)
    columns = ["GSA rank"] + columns
    df = df[columns]
    dfi.export(df, directory/"mytable.png")
    return df
