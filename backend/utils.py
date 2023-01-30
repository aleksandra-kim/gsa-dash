import json
import pickle


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
