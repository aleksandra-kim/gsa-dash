import numpy as np
import json
import pickle
from pathlib import Path
import hashlib


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


def get_directory_hash(project, database, activity, amount, method):
    key = ";".join([project, database, activity, str(amount), str(len(method))]).encode()
    hash_name = hashlib.blake2b(key=key, digest_size=8).hexdigest()
    directory = Path.home() / "gsa-dash-cache" / str(hash_name)
    return directory


def create_directory(metadata):
    project, database, activity, amount, method = metadata["project"], metadata["database"], metadata["activity"], \
                                                  metadata["amount"], metadata["method"]
    directory = get_directory_hash(project, database, activity, amount, method)
    directory.mkdir(parents=True, exist_ok=True)
    write_json(metadata, directory / "metadata.json")
    return directory


def get_Y_files(directory):
    directory = Path(directory)
    files = list(directory.iterdir())
    Y_files = sorted([f for f in files if "Y" in f.name])
    return Y_files


def collect_Y(Y_files):
    if len(Y_files) == 0:
        return []
    else:
        directory = Path(Y_files[0]).parent
        Y = []
        for Y_file in Y_files:
            Y_data = read_json(directory / Y_file)
            Y += Y_data
        return Y


def collect_XY(directory):
    directory = Path(directory)
    files = list(directory.iterdir())
    Y_files = sorted([f for f in files if "Y" in f.name and "inf" not in f.name])
    Y, X = [], []
    for Y_file in Y_files:
        X_file = directory / Y_file.name.replace("Y", "X")
        assert X_file in files
        Y_data = read_json(directory / Y_file)
        X_data = read_json(directory / X_file)
        Y = Y + Y_data
        X = X + X_data
    return np.array(X), np.array(Y)


def get_val_state(val_directory):
    val_directory = Path(val_directory)
    files = list(val_directory.iterdir())
    val_files = sorted([f for f in files if "Yinf" in f.name])
    return len(val_files)


def collect_Y_validation(val_directory):
    val_directory = Path(val_directory)
    files = list(val_directory.iterdir())
    Y_files = sorted([f for f in files if "Yinf" in f.name])
    Y = dict()
    for Y_file in Y_files:
        Yinf = read_json(val_directory / Y_file)
        current_inf = int(Y_file.stem.split("Yinf")[1])
        Y[current_inf] = np.array(Yinf)
        iterations = len(Yinf)  # TODO needs to be implemented better, possibly with a class
    _, Yall = collect_XY(val_directory.parent)
    Y["all"] = Yall[:iterations]
    return Y
