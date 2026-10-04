"""Missed discovery on the exposed pilot (r7-det9 default, evaluator .9 + reader .7): where it happens -- by labelled
component kind, document stratum, project and page -- to target reading changes at evidence, not at guesses."""
import collections
import json
import pathlib

r = json.loads(pathlib.Path("C:/t/iso/work/r12/eval9-reader7/r7-det9-pilot-default.json").read_text(encoding="utf-8"))
out = collections.defaultdict(collections.Counter)
examples = collections.defaultdict(list)
for d in r["documents"]:
    ev = d["layers"]["evidence"]
    for idx, c in enumerate(ev["components"]):
        for f in ("identity", "revision", "decision"):
            if c["fields"].get(f) != "missed":
                continue
            on_page = [j for j in ev["judged"] if j["field"] == f and j.get("page") == c["page"]]
            if on_page or d.get("execution") not in ("complete", None):
                continue
            kind = (c["expected"] or {}).get("component")
            out[f]["kind:" + str(kind)] += 1
            out[f]["stratum:" + str(d.get("stratum"))] += 1
            out[f]["ep:" + str(d.get("ep"))] += 1
            out[f]["page1" if c["page"] == 1 else "page>1"] += 1
            out[f]["scan_like" if d.get("scan_like") else "text_layer"] += 1
            if len(examples[f]) < 12:
                examples[f].append({"doc": d["doc"], "page": c["page"], "kind": kind, "truth": (c["expected"] or {}).get(
                    {"identity": "reference", "revision": "printed_revision", "decision": "decision"}[f]), "scan_like": d.get("scan_like")})
res = {f: dict(sorted(v.items(), key=lambda kv: -kv[1])) for f, v in out.items()}
json.dump({"breakdown": res, "examples": examples}, open("C:/t/iso/work/r2x/failure-inventory/MISSED-DISCOVERY-BREAKDOWN.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for f, v in res.items():
    print(f, {k: n for k, n in v.items() if not k.startswith("ep:")})
    print("   by project", {k: n for k, n in v.items() if k.startswith("ep:")})
