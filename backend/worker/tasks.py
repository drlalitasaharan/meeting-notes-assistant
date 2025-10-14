import json
import math


def fsum_args(*args):
    # CLI passes strings; convert to float
    return math.fsum(float(a) for a in args)


def fsum_json(payload: str):
    # pass a JSON list as ONE string arg
    arr = json.loads(payload)
    return float(math.fsum(arr))
