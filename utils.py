from pathlib import Path
import hashlib

# Local files
from brightway.lca_calculations import write_json, read_json


def get_base_directory(project, database, method, activity, amount):
    key = ";".join([project, database, str(len(method)), activity, str(amount)]).encode()
    hash_name = hashlib.blake2b(key=key, digest_size=8).hexdigest()
    base_directory = Path.home() / "gsa-dash-cache" / str(hash_name)
    return base_directory


def prepare_base_directory(project, database, method, activity, amount):
    base_directory = get_base_directory(project, database, method, activity, amount)
    base_directory.mkdir(parents=True, exist_ok=True)
    metadata = dict(
        project=project,
        method=method,
        database=database,
        activity=activity,
        amount=amount,
    )
    write_json(metadata, base_directory / "metadata.json")
    return base_directory


def get_mc_scores_files(directory):
    files = list(directory.iterdir())
    yfiles = sorted([f.name for f in files if "Y" in f.name])
    return yfiles


def collect_mc_scores(directory):
    yfiles = get_mc_scores_files(directory)
    yy = []
    for yf in yfiles:
        y = read_json(directory / yf)
        yy = yy + y
    return yy
