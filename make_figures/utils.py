import json


def read_json(fp):
    with open(fp, 'r') as f:
        data = json.load(f)
    return data
