import json
from deepdiff import DeepDiff

def load_snapshot(file_path):
    with open(file_path) as f:
        return json.load(f)

def compare_snapshots(file1, file2):
    data1 = load_snapshot(file1)
    data2 = load_snapshot(file2)
    diff = DeepDiff(data1, data2, ignore_order=True)
    return diff