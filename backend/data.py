from pathlib import Path
import hashlib

# Local files
from backend.monte_carlo import write_json


def get_directory_hash(project, database, method, activity, amount):
    key = ";".join([project, database, str(len(method)), activity, str(amount)]).encode()
    hash_name = hashlib.blake2b(key=key, digest_size=8).hexdigest()
    directory = Path.home() / "gsa-dash-cache" / str(hash_name)
    return directory


def create_directory(metadata):
    project, database, method, activity, amount = metadata["project"], metadata["database"], metadata["method"], \
                                                  metadata["activity"], metadata["amount"]
    directory = get_directory_hash(project, database, method, activity, amount)
    directory.mkdir(parents=True, exist_ok=True)
    write_json(metadata, directory / "metadata.json")
    return directory


# def get_mc_scores_files(directory):
#     files = list(directory.iterdir())
#     yfiles = sorted([f.name for f in files if "Y" in f.name])
#     return yfiles
#
#
# def collect_mc_scores(directory):
#     yfiles = get_mc_scores_files(directory)
#     yy = []
#     for yf in yfiles:
#         y = read_json(directory / yf)
#         yy = yy + y
#     return yy
