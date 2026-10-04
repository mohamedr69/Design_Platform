"""R15 saved-output checks (no new calls):
  1. BOQ: every stored row's truth ordinal / join state / outcome under the r15.1 contract (with and without the
     verified H-06 geometry) versus the r14 replay, per (run, label version) -- any difference listed with its row;
  2. documents: the stored small-batch evaluator results (evaluator .9, unchanged, r14 rescore files, original and
     amended labels separately) annotated by overlay r15.1 in each run's own declared context, beside overlay r14.1.
Writes R15-SAVED-OUTPUT-CHECK.json."""
import collections
import importlib.util
import json
import pathlib

W = pathlib.Path("C:/t/iso/work/r2x")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ov15 = load(W / "r15/overlay.py", "ov15")
ov14 = load(W / "r14/overlay.py", "ov14")
r14 = json.loads((W / "r14/REPLAY-BOQ.json").read_text(encoding="utf-8"))
out = {"boq": {}, "documents": {}}
for name in ("REPLAY-BOQ-r15.json", "REPLAY-BOQ-r15-geometry.json"):
    r15 = json.loads((W / "r15" / name).read_text(encoding="utf-8"))
    for key, run in r15["runs"].items():
        a = {x["request_order"]: x for x in r14["runs"][key]["rows"]}
        diffs = []
        for x in run["rows"]:
            y = a[x["request_order"]]
            if (x["after"]["truth_ordinal"], x["after"]["outcome"], x["after"]["blind_right"]) != (y["after"]["truth_ordinal"], y["after"]["outcome"], y["after"]["blind_right"]):
                diffs.append({"request_order": x["request_order"], "emitted_id": x["emitted_id"], "r14": y["after"], "r15": x["after"]})
        out["boq"][f"{name}|{key}"] = {"rows": len(run["rows"]), "rows_different_from_r14": diffs,
                                        "join_states": dict(collections.Counter(x["after"]["join"] for x in run["rows"]))}
labels15 = json.loads((W / "labels/r15/SMALL-BATCH-LABELS.amended-r15.1.json").read_text(encoding="utf-8"))
labels14 = json.loads((W / "labels/r14/SMALL-BATCH-LABELS.amended-r14.1.json").read_text(encoding="utf-8"))
for track in ("det", "A", "B", "C"):
    rows = json.loads(pathlib.Path(f"C:/t/r2x/runs/r2x-small-{track}/out/rows.json").read_text(encoding="utf-8"))
    for version in ("original", "amended-r14.1"):
        res = json.loads((W / f"r14/rescore/small-{track}__{version}.json").read_text(encoding="utf-8"))
        n_eval = len(res["totals"]["evidence"]["critical"])
        o15 = ov15.overlay(res, labels15, rows)
        entry = {"evaluator_critical": n_eval, "overlay_r15_critical": o15["critical_after_overlay"], "overlay_r15_context": o15["context"],
                 "overlay_r15_annotations": dict(collections.Counter(a["annotation"] for a in o15["annotations"])),
                 "overlay_r15_context_status": dict(collections.Counter(a["context_status"] for a in o15["annotations"])),
                 "labels_for_annotation": "r15.1 (explicit states)"}
        if version != "original":
            o14 = ov14.overlay(res, labels14, rows)
            entry["overlay_r14_critical"] = o14["critical_after_overlay"]
        out["documents"][f"small-{track}__{version}"] = entry
(W / "r15/R15-SAVED-OUTPUT-CHECK.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
for k, v in out["boq"].items():
    print(k, "rows", v["rows"], "diffs", len(v["rows_different_from_r14"]), v["join_states"])
for k, v in out["documents"].items():
    print(k, {kk: vv for kk, vv in v.items() if kk != "labels_for_annotation"})
