import bw2data as bd
import bw2calc as bc
import bw_processing as bwp
import numpy as np
from pathlib import Path

# Local files
from .utils import write_json, write_pickle
from .life_cycle_assessment import prepare_lca, create_lca


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


def get_dps_without_background_uncertainty(method):
    me = bd.Method(method).datapackage()
    background = find_background_databases()
    dps = [me]
    for database in bd.databases:
        dp = bd.Database(database).datapackage()
        if database in background:
            dp = dp.exclude({"kind": "distributions"})
        dps.append(dp)
    return dps


def get_dps_without_foreground_background_uncertainty(method):
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
    dps_no_bg_unct = get_dps_without_background_uncertainty(method)
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
    dps_no_fg_bg_unct = get_dps_without_foreground_background_uncertainty(method)
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
