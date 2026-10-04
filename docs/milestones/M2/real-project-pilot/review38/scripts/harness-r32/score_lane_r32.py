"""ORCH-05.1 / ORCH-08: one lane's application rows -> the normalised r32 lane of score_bcr_r32, OFFLINE.

Usage (cwd C:/t/iso/cand-r29/backend, AI disabled, read-only use of the tree):
  score_lane_r32.py <lane> <rows.json abs> <policy|none> <truth json abs> <run set json abs> <requests json abs> <out json abs>
                    [<LANE-x.json abs>]
  * facts: the FROZEN evaluator .10 emission functions (tripwire_r32.facts_from_row); judged per (pool id, page, field) by
    lane_judge_r32 against the r32 truth (literal_compare_r32);
  * eligibility and coverage: coverage_v4 (harness v4.3 copy) for C and R; B (policy none) counts as attempted;
  * ORCH-08: every document carries
      source_sha256    the row's sha256 (the bytes the facts came from; lane_judge's evidenced cross-page rule needs it)
      status           COMPLETE / INCOMPLETE / DEFERRED from the lane's own record (LANE-x.json documents; a document
                       the lane manifest does not list is INCOMPLETE 'not recorded by the lane' -- never silently dropped),
                       with its reason, retry time, event classes ('limit' / 'failure' / 'arm_policy') and pages;
      limit_pages      the pages an event touched ('*' = the whole document);
    and the lane carries 'credit': R and P are reference / report-only diagnostics and earn NO accuracy or recovery
    credit (A-09 point 6); their 'diagnostic_population' is the run set and its state is COMPLETE only when every
    document is COMPLETE.
No model request, no write except <out json>."""
import json
import os
import pathlib
import sys

lane, rows_path, policy, truth_path, runset_path, req_path, out_path = sys.argv[1:8]
manifest_path = sys.argv[8] if len(sys.argv) > 8 else None
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
statuses = (json.loads(pathlib.Path(manifest_path).read_text(encoding="utf-8")).get("documents") or {}) if manifest_path else None
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
    if statuses is None:
        st = {"status": "COMPLETE", "reason": "no lane record given (unit use)", "classes": [], "pages": {}, "retry_at": None}
    else:
        st = statuses.get(p["pool_id"]) or {"status": "INCOMPLETE", "reason": "not recorded by the lane", "classes": ["limit"], "pages": {"*": ["not_recorded"]},
                                            "retry_at": None}
    docs[p["pool_id"]] = {"doc_key": p["doc"], "attempted": (bool(cov.get("attempted")) or policy == "none") and row is not None,
                          "unsupported": cov["state"] == "unsupported_input", "facts": facts, "source_sha256": (row or {}).get("sha256"),
                          "coverage": {pg: {k.split(":", 1)[1]: v for k, v in cls.items() if k.startswith("own:")} for pg, cls in (cov.get("pages") or {}).items()},
                          "eligibility": (elig.get(p["doc"]) or {}).get("state"), "row_state": (rows.get(p["doc"]) or {}).get("state"),
                          "status": st["status"], "status_reason": st.get("reason"), "status_classes": st.get("classes") or [],
                          "retry_at_utc": st.get("retry_at_utc"), "limit_pages": sorted((st.get("pages") or {}).keys()),
                          "limit_kinds": st.get("kinds") or []}
reference = lane in ("R", "P")
states = [d["status"] for d in docs.values()]
out = {"lane": lane, "rows": rows_path, "policy": policy, "evaluator_emission": EV.EVALUATOR_VERSION, "documents": docs,
       "requests": requests.get("requests") or {}, "tokens": requests.get("tokens"), "rejected_evidence": rejected,
       "credit": "none: reference / report-only diagnostic, never accuracy or recovery credit (A-09 point 6)" if reference else "scored",
       "diagnostic_population": {"documents": len(docs), "complete": sum(1 for s in states if s == "COMPLETE"),
                                 "state": "COMPLETE" if all(s == "COMPLETE" for s in states) else ("DEFERRED" if "DEFERRED" in states else "INCOMPLETE")},
       "scorer": "score_lane_r32", "reference_set_statement": "reference set independently AI-reviewed (Claude agents), not human-signed"}
pathlib.Path(out_path).write_text(json.dumps(out, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"lane": lane, "documents": len(docs), "attempted": sum(1 for d in docs.values() if d["attempted"]),
                  "facts": sum(len(d["facts"]) for d in docs.values()), "status": out["diagnostic_population"]}))
