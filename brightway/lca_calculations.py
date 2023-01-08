import bw2data as bd
import bw2calc as bc


def compute_lcia_score(project, db_name, method, functional_unit, fu_amount):
    bd.projects.set_current(project)
    db = bd.Database(db_name)
    fu_location = functional_unit.split(",")[-1][1:]
    fu_name = functional_unit[:-len(fu_location)-2]
    fu = [act for act in db if fu_name == act['name'] and fu_location == act['location']]
    assert len(fu) == 1
    fu = fu[0]
    method = tuple(method.split("'")[1::2])
    unit = bd.Method(method).metadata.get("unit", "")
    lca = bc.LCA({fu: fu_amount}, method)
    lca.lci()
    lca.lcia()
    return lca.score, unit
