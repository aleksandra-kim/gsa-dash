from copy import deepcopy
import numpy as np
import bw_processing as bwp
import bw2data as bd
import bw2calc as bc
from pathlib import Path
from scipy.stats import spearmanr

# Local files
from .data import collect_XY, write_json, collect_Y_validation, read_pickle
from .life_cycle_assessment import get_bw_activity_and_method

BIOSPHERE_TYPES = ['economic', 'emission', 'inventory indicator', 'natural resource', 'social']


def run_validation(val_directory, S, val_config, lca_config):
    val_directory = Path(val_directory)
    S = np.array(S)
    descending_argsort = np.argsort(S)[-1::-1]

    max_inf, step_inf, iterations = val_config["max_influential"], val_config["step_influential"], val_config["iterations"]

    project, database, activity, amount, method = lca_config["project"], lca_config["database"], \
                                                  lca_config["activity"], lca_config["amount"], lca_config["method"]
    bw_activity, method = get_bw_activity_and_method(project, database, activity, method)
    bd.projects.set_current(project)

    for current_inf in range(step_inf, max_inf+step_inf, step_inf):
        fp_inf = val_directory / f"Yinf{current_inf:04d}.json"
        if not fp_inf.exists():
            mask_inf = descending_argsort[:current_inf]
            Yinf = run_validation_step(val_directory, mask_inf, iterations, bw_activity, amount, method)
            write_json(Yinf, fp_inf)
    return


def collect_validation_results(directory):
    directory = Path(directory)
    Y = collect_Y_validation(directory)
    print(Y)
    Yall = Y.pop("all")
    metric = dict()
    for current_inf, Yinf in Y.items():
        r = spearmanr(Yall, Yinf)
        metric[current_inf] = r.correlation
    return metric


def run_validation_step(val_directory, mask_inf, iterations, bw_activity, amount, method):
    directory = val_directory.parent
    me = bd.Method(method).datapackage()  # TODO Method can also have uncertainty!
    dps_no_unct = [me]
    for database in bd.databases:
        dp = bd.Database(database).datapackage()
        dp = dp.exclude({"kind": "distributions"})
        dps_no_unct.append(dp)

    influential = len(mask_inf)
    name = f"validation_inf{influential}"
    dps_inf = bwp.create_datapackage(
        name=name,
        sequential=True,
    )
    Xall, _ = collect_XY(directory)
    Xinf = Xall[:iterations, :][:, mask_inf]
    indices = read_pickle(directory / "indices.pickle")
    indices_inf = indices[mask_inf]
    mask_bio = np.zeros(len(indices_inf), dtype=bool)
    for i, index in enumerate(indices_inf):
        if bd.get_activity(index[0]).get("type") in BIOSPHERE_TYPES:
            mask_bio[i] = 1
    dps_inf.add_persistent_array(
        matrix=f"technosphere_matrix",
        data_array=Xinf[:, ~mask_bio].T,
        name=f"{name}_tech",
        indices_array=indices_inf[~mask_bio],
        flip_array=np.ones(len(indices_inf[~mask_bio]), dtype=bool),  # TODO this is definitely bad, needs to be figured out
    )
    dps_inf.add_persistent_array(
        matrix=f"biosphere_matrix",
        data_array=Xinf[:, mask_bio].T,
        name=f"{name}_bio",
        indices_array=indices_inf[mask_bio],
    )

    lca = bc.LCA(
        {bw_activity.id: amount},
        data_objs=dps_no_unct + [dps_inf],
        use_distributions=False,
        use_arrays=True,
    )
    lca.lci()
    lca.lcia()
    lca.keep_first_iteration()
    scores_inf = []
    for i in range(iterations):
        next(lca)
        scores_inf.append(lca.score)
    return scores_inf
