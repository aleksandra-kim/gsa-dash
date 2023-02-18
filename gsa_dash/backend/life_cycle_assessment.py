import bw2data as bd
import bw2calc as bc


def get_bw_activity_and_method(project, database, activity, method):
    bd.projects.set_current(project)
    db = bd.Database(database)
    fu_location = activity.split(", ")[-1]
    fu_name = activity[:-len(fu_location)-2]
    fu = [act for act in db if fu_name == act['name'] and fu_location == act['location']]
    assert len(fu) == 1
    fu = fu[0]
    method = tuple(method.split(", "))
    return fu, method


def create_lca(project, database, activity, amount, method, use_distributions=False, seed=None):
    bw_activity, bw_method = get_bw_activity_and_method(project, database, activity, method)
    lca = bc.LCA({bw_activity: amount}, bw_method, use_distributions=use_distributions, seed_override=seed)
    lca.lci()
    lca.lcia()
    return lca


def compute_deterministic_score(
        project, database, activity, amount, method, use_distributions, seed
):
    lca = create_lca(project, database, activity, amount, method, use_distributions, seed)
    bw_method = lca.method
    unit = bd.Method(bw_method).metadata.get("unit", "")
    return lca.score, unit
