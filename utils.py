from pathlib import Path
import json
import hashlib


def read_json(fp):
    with open(fp, 'r') as f:
        data = json.load(f)
    return data


def write_json(data, fp):
    with open(fp, 'w') as f:
        json.dump(data, f)


def get_write_dir(project, db_name, method, functional_unit, fu_amount):
    key = ";".join([project, db_name, str(len(method)), functional_unit, str(fu_amount)]).encode()
    hash_name = hashlib.blake2b(key=key, digest_size=8).hexdigest()
    write_dir = Path.home() / "gsa-dash-cache" / str(hash_name)
    return write_dir


def prepare_write_dirs(project, db_name, method, functional_unit, fu_amount):
    write_dir = get_write_dir(project, db_name, method, functional_unit, fu_amount)
    write_dir.mkdir(parents=True, exist_ok=True)
    metadata = dict(
        bw_project=project,
        lcia_method=method,
        functional_unit_database=db_name,
        functional_unit_activity=functional_unit,
        functional_unit_amount=fu_amount,
    )
    write_json(metadata, write_dir / "metadata.json")
    return write_dir


def get_mc_scores_files(write_dir):
    files = list(write_dir.iterdir())
    yfiles = sorted([f.name for f in files if "Y" in f.name])
    return yfiles


def collect_mc_scores(write_dir):
    yfiles = get_mc_scores_files(write_dir)
    yy = []
    for yf in yfiles:
        y = read_json(write_dir / yf)
        yy = yy + y
        print(len(yy))
    return yy
