import bw2data as bd
import bw2calc as bc


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
