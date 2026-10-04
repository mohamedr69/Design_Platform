"""Score one set of rows (frozen stored rows or a replay) offline, AI disabled, with a chosen evaluator in its own tree:
  .9  = scripts.m2_eval5 in C:/t/iso/frozen-r12 (the frozen experiment's evaluator and reader association code)
  .10 = scripts.m2_eval6 in C:/t/iso/cand-r29   (Review 29 C4)
Eligibility and coverage use the frozen harness v4.3 contract (coverage_v4), with the attempt policy of THIS run (from the
replay manifest, or the declared arm policy for stored rows). Labels: frozen r26.2. Writes a JSON with the judged facts,
recovery / precision totals, critical facts and the per-document coverage. No model request.
Usage: score_replay.py <rows.json> <policy> <arm> <9|10> <out.json>"""
import json
import os
import pathlib
import sys

rows_path, policy, arm, ev, out_path = sys.argv[1:6]
DECL = json.loads(pathlib.Path("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json").read_text(encoding="utf-8"))
H = pathlib.Path("C:/t/iso/work/r2x/review25/harness-v4.3")
sys.path.insert(0, str(H))
import coverage_v4 as cv  # noqa: E402

TREE = {"9": "C:/t/iso/frozen-r12/backend", "10": "C:/t/iso/cand-r29/backend"}[ev]
MOD = {"9": "m2_eval5", "10": "m2_eval6"}[ev]
os.environ["AI_ENABLED"] = "false"
os.environ.setdefault("DATABASE_URL", "sqlite:///C:/t/iso/tmp/r29-score-no-db.db")
for k in [k for k in os.environ if k.startswith("AI_EVIDENCE_")]:
    os.environ.pop(k)
sys.path.insert(0, TREE)
os.chdir(TREE)
EV = __import__(f"scripts.{MOD}", fromlist=["x"])
assert pathlib.Path(EV.__file__).resolve().is_relative_to(pathlib.Path(TREE).resolve())
L = pathlib.Path(DECL["harness_dir"]) / DECL["labels"]["dir"]
REG = json.loads((L / DECL["labels"]["register"]).read_text(encoding="utf-8"))
PAGE = json.loads((L / DECL["labels"]["page"]).read_text(encoding="utf-8"))
planned = DECL["sources"]["sample"]["documents_planned"]
rows = json.loads(pathlib.Path(rows_path).read_text(encoding="utf-8"))
bctx = {"variant": "EV1", "profile": "default", "policy": policy}
ok_rows, elig, rejected = cv.eligible_rows(rows, planned, bctx)
result = EV.evaluate(REG, PAGE, ok_rows, PAGE.get("page1_corrections"), ai_context={"variant": "EV1", "profile": "default", "policies": [policy]})
docs = []
for p in planned:
    att, reason = cv.select_attempt(rows.get(p["doc"]), p, bctx)
    docs.append(cv.document_coverage(p, att, max_pages=4, reason=reason))
t = result["totals"]["evidence"]
judged = []
for d in result["documents"]:
    for j in d["layers"]["evidence"]["judged"]:
        judged.append({"doc": d["doc"], **{k: j.get(k) for k in ("page", "field", "value", "state", "how", "outcome", "truth", "group", "reader", "layer")}})
out = {"rows": rows_path, "policy": policy, "arm": arm, "evaluator": EV.EVALUATOR_VERSION, "tree": TREE,
       "eligibility": {k: v["state"] for k, v in elig.items()},
       "recovery": {f: x["recovery_counts"] for f, x in t["fields"].items()},
       "precision": {f: [x["precision_counts"].get("correct", 0), x["asserted_distinct"]] for f, x in t["fields"].items()},
       "critical": t["critical"], "coverage": docs, "coverage_summary": cv.summarize(docs), "judged": judged}
pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
pathlib.Path(out_path).write_text(json.dumps(out, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"arm": arm, "evaluator": EV.EVALUATOR_VERSION, "recovery": out["recovery"], "critical": len(out["critical"]),
                  "eligible": sum(1 for v in out["eligibility"].values() if v == "eligible")}))
