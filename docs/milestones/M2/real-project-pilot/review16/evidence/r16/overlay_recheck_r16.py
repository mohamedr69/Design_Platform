"""R16: the stored small-batch overlay checks with the r16 overlay module (unchanged from r15.1): each stored evaluator
result (evaluator .9, r14 rescore files, original and amended labels separately) annotated in its own declared
context with the r15.1 explicit-state labels. Evaluator authority: critical counts must equal the evaluator's."""
import collections
import importlib.util
import json
import pathlib

W = pathlib.Path("C:/t/iso/work/r2x")
H = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ov16", H / "overlay.py")
ov = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ov)
labels = json.loads((W / "labels/r15/SMALL-BATCH-LABELS.amended-r15.1.json").read_text(encoding="utf-8"))
out = {"overlay": ov.OVERLAY_VERSION, "runs": {}}
for track in ("det", "A", "B", "C"):
    rows = json.loads(pathlib.Path(f"C:/t/r2x/runs/r2x-small-{track}/out/rows.json").read_text(encoding="utf-8"))
    for version in ("original", "amended-r14.1"):
        res = json.loads((W / f"r14/rescore/small-{track}__{version}.json").read_text(encoding="utf-8"))
        o = ov.overlay(res, labels, rows)
        out["runs"][f"small-{track}__{version}"] = {"evaluator_critical": len(res["totals"]["evidence"]["critical"]), "overlay_critical": o["critical_after_overlay"],
                                                   "context": o["context"], "context_status": dict(collections.Counter(a["context_status"] for a in o["annotations"])),
                                                   "annotations": dict(collections.Counter(a["annotation"] for a in o["annotations"]))}
(H / "OVERLAY-RECHECK-r16.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
for k, v in out["runs"].items():
    print(k, v)
