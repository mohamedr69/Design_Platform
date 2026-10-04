"""Review 31 dry run: score one lane's rows offline with evaluator .10 (scripts.m2_eval6 in C:/t/iso/cand-r29, AI disabled)
and the frozen harness v4.3 coverage contract, against the frozen r26.2 labels, and write the NORMALISED lane of
score_bcr.py. No model request. Usage: score_lane.py <lane> <rows.json abs> <policy|none> <out.json abs>"""
import json
import os
import pathlib
import sys

lane, rows_path, policy, out_path = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3], pathlib.Path(sys.argv[4])
assert rows_path.is_absolute() and out_path.is_absolute()
DECL = json.loads(pathlib.Path("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json").read_text(encoding="utf-8"))
sys.path.insert(0, "C:/t/iso/work/r2x/review25/harness-v4.3")
import coverage_v4 as cv  # noqa: E402

TREE = "C:/t/iso/cand-r29/backend"
os.environ["AI_ENABLED"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///C:/t/iso/tmp/r31-score-no-db.db"
for k in [k for k in os.environ if k.startswith("AI_EVIDENCE_")]:
    os.environ.pop(k)
sys.path.insert(0, TREE)
os.chdir(TREE)
from scripts import m2_eval6 as EV  # noqa: E402

assert pathlib.Path(EV.__file__).resolve().is_relative_to(pathlib.Path(TREE).resolve())
L = pathlib.Path(DECL["harness_dir"]) / DECL["labels"]["dir"]
REG = json.loads((L / DECL["labels"]["register"]).read_text(encoding="utf-8"))
PAGE = json.loads((L / DECL["labels"]["page"]).read_text(encoding="utf-8"))
planned = DECL["sources"]["sample"]["documents_planned"]
rows = json.loads(rows_path.read_text(encoding="utf-8"))
ctx = {"variant": "EV1", "profile": "default", "policy": policy}
ok_rows, elig, _ = cv.eligible_rows(rows, planned, ctx) if policy != "none" else (rows, {}, [])
res = EV.evaluate(REG, PAGE, ok_rows, PAGE.get("page1_corrections"), ai_context={"variant": "EV1", "profile": "default", "policies": [policy]})
by_doc = {d["doc"]: d for d in res["documents"]}
WRONG = ("wrong", "wrong_unassociated", "fp", "accepted_on_conflict")
docs = {}
for p in planned:
    att, reason = cv.select_attempt(rows.get(p["doc"]), p, ctx) if policy != "none" else (None, "evidence reader off")
    cov = cv.document_coverage(p, att, max_pages=4, reason=reason)
    ev = (by_doc.get(p["doc"]) or {}).get("layers", {}).get("evidence", {})
    acc = {}
    for f in ("identity", "revision", "decision"):
        c = (ev.get("precision_by_state") or {}).get(f"{f}:accepted") or {}
        acc[f] = {"correct": c.get("correct", 0), "wrong": sum(c.get(k, 0) for k in WRONG)}
    docs[p["doc"]] = {"attempted": bool(cov.get("attempted")) or policy == "none", "unsupported": cov["state"] == "unsupported_input",
                      "recovery": ev.get("recovery") or {}, "accepted": acc,
                      "critical": [{"page": r.get("page"), "field": r.get("field"), "outcome": r.get("outcome"), "value": r.get("value"), "truth": r.get("truth")}
                                   for r in ev.get("critical") or []],
                      "association": ev.get("association") or {},
                      "coverage": {pg: {k.split(":", 1)[1]: v for k, v in cls.items() if k.startswith("own:")} for pg, cls in (cov.get("pages") or {}).items()}}
out = {"lane": lane, "rows": str(rows_path), "policy": policy, "evaluator": EV.EVALUATOR_VERSION, "documents": docs,
       "eligibility": {k: v["state"] for k, v in elig.items()},
       "totals_evidence": {f: {k: v[k] for k in ("asserted_distinct", "accepted_precision", "recovery", "clean_recovery", "readable")}
                           for f, v in res["totals"]["evidence"]["fields"].items()},
       "critical_total": len(res["totals"]["evidence"]["critical"])}
out_path.write_text(json.dumps(out, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"lane": lane, "evaluator": EV.EVALUATOR_VERSION, "totals": out["totals_evidence"], "critical": out["critical_total"]}))
