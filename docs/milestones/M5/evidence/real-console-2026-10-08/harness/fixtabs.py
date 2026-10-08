import json
import sys

p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))


def fix(o):
    if isinstance(o, dict):
        return {k: fix(v) for k, v in o.items()}
    if isinstance(o, list):
        return [fix(v) for v in o]
    if isinstance(o, str):
        return o.replace("\t", "\\t")
    return o


open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(fix(d), indent=1))
