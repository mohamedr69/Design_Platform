"""ORCH-05.1 (Review 33 C-5, R33-06): one lane's application rows -> the normalised r32 lane of score_bcr_r32, OFFLINE.
Replaces the four-arm-bound review31 score_lane.py for the r32 run (that file is unchanged).

Usage (cwd C:/t/iso/cand-r29/backend, AI disabled, read-only use of the tree):
  score_lane_r32.py <lane> <rows.json abs> <policy|none> <truth json abs> <run set json abs> <requests json abs> <out json abs>
  * facts: the FROZEN evaluator .10 emission functions (tripwire_r32.facts_from_row: register records, deterministic
    observations, and -- with the lane's AI context (variant EV1, profile default, the lane's policy) -- the AI evidence
    groups); judged per (pool id, page, field) by lane_judge_r32 against the r32 truth (literal_compare_r32);
  * eligibility and coverage: coverage_v4 (harness v4.3 copy) for C and R (bound to the planned staged sha256 and the
    lane's context); B (policy none) counts as attempted, as in Review 31;
  * the document key EP-<ep>/<relative_path> is mapped to its pool id through the run set (SOURCE-MANIFEST keys).
No model request, no write except <out json>."""
import json
import os
import pathlib
import sys

lane, rows_path, policy, truth_path, runset_path, req_path, out_path = sys.argv[1:8]
for p in (rows_path, truth_path, runset_path, req_path, out_path):
    assert pathlib.Path(p).is_absolute(), p
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["AI_ENABLED"] = "false"
for k in [k for k in os.environ if k.startswith("AI_EVIDENCE_")]:
    os.environ.pop(k)
os.environ.setdefault("DATABASE_URL", "sqlite:///C:/t/iso/tmp/r33-score-no-db.db")
import coverage_v4 as cv  # noqa: E402
import tripwire_r32 as TW  # noqa: E402

EV = TW.load_evaluator()
truth = json.loads(pathlib.Path(truth_path).read_text(encoding="utf-8"))
runset = json.loads(pathlib.Path(runset_path).read_text(encoding="utf-8"))
rows = {k.replace("\\", "/"): v for k, v in json.loads(pathlib.Path(rows_path).read_text(encoding="utf-8")).items()}
requests = json.loads(pathlib.Path(req_path).read_text(encoding="utf-8"))
planned = [{"doc": d["doc_key"], "pool_id": d["pool_id"], "sha256": truth["documents"][d["pool_id"]]["staged_sha256"],
            "pages": truth["documents"][d["pool_id"]]["page_count"], "extension": ".pdf"} for d in runset]
ctx = {"variant": "EV1", "profile": "default", "policy": policy}
ai_context = None if policy == "none" else {"variant": "EV1", "profile": "default", "policies": [policy]}
ok_rows, elig, rejected = cv.eligible_rows(rows, planned, ctx if policy != "none" else None)
docs = {}
for p in planned:
    row = ok_rows.get(p["doc"])
    att, reason = cv.select_attempt(rows.get(p["doc"]), p, ctx) if policy != "none" else (None, "evidence reader off")
    cov = cv.document_coverage(p, att, max_pages=4, reason=reason)
    facts = TW.facts_from_row(EV, row, ai_context, p["doc"]) if row else []
    docs[p["pool_id"]] = {"doc_key": p["doc"], "attempted": (bool(cov.get("attempted")) or policy == "none") and row is not None,
                          "unsupported": cov["state"] == "unsupported_input", "facts": facts,
                          "coverage": {pg: {k.split(":", 1)[1]: v for k, v in cls.items() if k.startswith("own:")} for pg, cls in (cov.get("pages") or {}).items()},
                          "eligibility": (elig.get(p["doc"]) or {}).get("state"), "row_state": (rows.get(p["doc"]) or {}).get("state")}
out = {"lane": lane, "rows": rows_path, "policy": policy, "evaluator_emission": EV.EVALUATOR_VERSION, "documents": docs,
       "requests": requests.get("requests") or {}, "tokens": requests.get("tokens"), "rejected_evidence": rejected,
       "scorer": "score_lane_r32", "reference_set_statement": "reference set independently AI-reviewed (Claude agents), not human-signed"}
pathlib.Path(out_path).write_text(json.dumps(out, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"lane": lane, "documents": len(docs), "attempted": sum(1 for d in docs.values() if d["attempted"]),
                  "facts": sum(len(d["facts"]) for d in docs.values())}))
