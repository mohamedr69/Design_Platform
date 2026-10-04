"""Score the model-disabled candidate (det), AI-EV0, AI-EV1 and AI-EV2 on the same eligible projects with the frozen
evaluator .4, labels restricted to those projects (so other projects are not counted as not run).
Usage: compare_variants.py <out.json> <eps> name=rows.json ..."""
import collections, json, sys

sys.path.insert(0, r"C:\t\iso\ep-platform\backend")
from scripts import m2_eval4 as ev  # noqa: E402

P = r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot"
out_path, eps = sys.argv[1], sys.argv[2].split(",")
runs = dict(a.split("=", 1) for a in sys.argv[3:])
labels = json.load(open(P + r"\GOLDEN-LABELS.json", encoding="utf-8"))
pages = json.load(open(P + r"\review05\labels\GOLDEN-LABELS-v2-PAGES.json", encoding="utf-8"))
labels = {**labels, "documents": [d for d in labels["documents"] if d["ep"] in eps]}
pages = {**pages, "documents": {k: v for k, v in pages["documents"].items() if any(k.startswith(f"EP-{ep}/") for ep in eps)}}
result = {"evaluator": ev.EVALUATOR_VERSION, "eps": eps, "documents_labelled": len(labels["documents"]), "runs": {}}


def cell(t, layer, f):
    x = t[layer].get(f) or {}
    return {k: x.get(k, 0) for k in ("tp", "accepted", "readable", "wrong", "fp", "tn", "held", "missed", "unscorable")} | {
        "precision_of_accepted": x.get("precision_of_accepted"), "recovery_of_readable": x.get("recovery_of_readable")}


for name, path in runs.items():
    rows = json.load(open(path, encoding="utf-8"))
    rows = {k: v for k, v in rows.items() if any(k.startswith(f"EP-{ep}/") for ep in eps)}
    r = ev.evaluate(labels, pages, rows)
    t = r["totals"]
    result["runs"][name] = {"rows": len(rows), "critical": [c["kind"] for c in t["critical"]], "critical_detail": t["critical"],
                            "execution": t["execution"],
                            "register": {f: cell(t, "register", f) for f in ("reference", "revision", "decision")},
                            "raw": {f: cell(t, "raw", f) for f in ("identity", "revision", "decision")},
                            "evidence": {f: cell(t, "evidence", f) for f in ("identity", "revision", "decision")},
                            "evidence_introduced_errors": t["evidence_introduced_errors"], "ai": t["ai"],
                            "mirror": {k: (v.get("mirror") or {}) for k, v in rows.items()}}
    json.dump(r, open(out_path.replace(".json", f"-{name}.json"), "w", encoding="utf-8"), indent=1, default=str)
# the register mirror must be identical between EV0 and EV1 / EV2 (the evidence stage never changes a record)
names = list(runs)
if "ev0" in runs:
    base = result["runs"]["ev0"]["mirror"]
    for n in names:
        if n.startswith("ev") and n != "ev0":
            m = result["runs"][n]["mirror"]
            result["runs"][n]["mirror_identical_to_ev0"] = all(m.get(k) == v for k, v in base.items()) and set(m) == set(base)
for n in names:
    result["runs"][n].pop("mirror")
json.dump(result, open(out_path, "w", encoding="utf-8"), indent=1, default=str)


def fmt(c):
    return f"{c['tp']}/{c['accepted']}/{c['readable']} (w{c['wrong']} fp{c['fp']} held{c['held']})"


print("| run | critical | register reference | register revision | register decision | raw identity | raw revision | raw decision | evidence identity | evidence revision | evidence decision | AI |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
for n, x in result["runs"].items():
    print(f"| {n} | {len(x['critical'])} {dict(collections.Counter(x['critical']))} | {fmt(x['register']['reference'])} | {fmt(x['register']['revision'])} | {fmt(x['register']['decision'])} | "
          f"{fmt(x['raw']['identity'])} | {fmt(x['raw']['revision'])} | {fmt(x['raw']['decision'])} | {fmt(x['evidence']['identity'])} | {fmt(x['evidence']['revision'])} | "
          f"{fmt(x['evidence']['decision'])} | {x['ai']} |")
for n, x in result["runs"].items():
    if "mirror_identical_to_ev0" in x:
        print(n, "register mirror identical to EV0:", x["mirror_identical_to_ev0"])
    if x["evidence_introduced_errors"]:
        print(n, "evidence introduced errors:", x["evidence_introduced_errors"])
