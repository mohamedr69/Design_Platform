"""R21 workload and budget table, built from EVERY selected page (R21-STAGE.json + R21-PAGE-CLASSES.json) and the
observed per-task rates of the durable ledger (review20/workload/OBSERVED-WORKLOAD.json; price unknown, no dollar
amount). Expected and upper-bound requests / tokens per arm, per project and per page; the A base's own provider calls;
the long-file controls' supported pages; retries / escalations; the 60-per-project rolling-day WORST-CASE schedule; the
proposed caps and the frozen balanced execution order; how incomplete paired arms enter the all-planned comparison.
Writes workload/R21-WORKLOAD.json."""
import collections
import json
import pathlib

R = pathlib.Path("C:/t/iso/work/r2x/review21")
stage = json.loads(pathlib.Path("C:/t/r2x/r21-stage/R21-STAGE.json").read_text(encoding="utf-8"))["files"]
classes = json.loads((R / "R21-PAGE-CLASSES.json").read_text(encoding="utf-8"))["pages"]
obs = json.loads(pathlib.Path("C:/t/iso/work/r2x/review20/workload/OBSERVED-WORKLOAD.json").read_text(encoding="utf-8"))["tasks"]
MAX_PAGES, DOC_CAP, ESC_CAP, DAY = 4, 12, 2, 60
by_doc = collections.defaultdict(list)
for p in classes:
    by_doc[p["doc_key"]].append(p)
# observed per-task means (input includes cached; p90 for the upper bound)
T = {k: obs[k] for k in ("discover_page", "discover_region", "read_identity", "read_revision", "read_decision", "read_field_context", "read_submittal_form")}
tok = lambda k, q="mean": (T[k]["input_total_incl_cached"][q] or 0)
out_tok = lambda k: T[k]["output"]["mean"] or 0
# per triggered in-scope page (EV1: pages with title-block / form cues and no deterministic identity, or the 20 % audit):
# expected trigger rate from the observed arms: S 2.14 and T2 2.29 requests per single-page document => ~1 triggered page
# per document at ~2.2 requests; the continuation had budget stops and no-region reads, so the upper bound is the cap
EXP = {"discovery": 1.0, "read_identity": 0.85, "read_revision": 0.8, "read_decision": 0.15, "targeted": 0.6, "escalation": 0.0}
rows, per_project = [], collections.defaultdict(lambda: collections.defaultdict(float))
totals = collections.defaultdict(lambda: collections.defaultdict(float))
for f in stage:
    ep = f["doc_key"].split("/")[0][3:]
    pages = [p for p in by_doc.get(f["doc_key"], []) if p["in_scope"]]
    if f["extension"] != ".pdf":
        rows.append({"doc": f["doc_key"], "ep": ep, "role": f["role"], "pages_in_scope": 0, "pages_beyond_scope": 0, "shape": "unsupported_input", "per_arm": {}})
        continue
    n_in, n_beyond = len(pages), (f["pages"] or 0) - len(pages)
    drawing = sum(1 for p in pages if p["size"] == "drawing_sheet")
    per_arm = {}
    for arm in ("L1", "L2", "L3", "L4"):
        roi, x = arm in ("L2", "L4"), arm in ("L3", "L4")
        req = n_in * (EXP["discovery"] + EXP["read_identity"] + EXP["read_revision"] + EXP["read_decision"]) + (n_in * EXP["targeted"] if x else 0)
        req = min(req, DOC_CAP)
        disc_in = sum((tok("discover_region") if (roi and p["size"] == "drawing_sheet") else tok("discover_page")) for p in pages)
        reads_in = n_in * (EXP["read_identity"] * tok("read_identity") + EXP["read_revision"] * tok("read_revision") + EXP["read_decision"] * tok("read_decision"))
        tgt_in = n_in * EXP["targeted"] * tok("read_field_context") if x else 0
        up_in = sum((tok("discover_region", "p90") if (roi and p["size"] == "drawing_sheet") else tok("discover_page", "p90")) for p in pages) + (DOC_CAP - n_in) * tok("read_identity", "p90")
        per_arm[arm] = {"expected_requests": round(req, 2), "upper_bound_requests": DOC_CAP, "expected_input_tokens": round(disc_in + reads_in + tgt_in),
                        "upper_bound_input_tokens": round(up_in), "expected_output_tokens": round(n_in * (out_tok("discover_page") + out_tok("read_identity") + out_tok("read_revision")) + (n_in * EXP["targeted"] * out_tok("read_field_context") if x else 0))}
        per_project[ep][arm] += req
        for k in ("expected_requests", "expected_input_tokens", "upper_bound_input_tokens", "expected_output_tokens"):
            totals[arm][k] += per_arm[arm][k]
        totals[arm]["upper_bound_requests"] += DOC_CAP
    rows.append({"doc": f["doc_key"], "ep": ep, "role": f["role"], "pages_in_scope": n_in, "pages_beyond_scope": n_beyond, "drawing_pages": drawing,
                 "page_classes": [(p["page"], p["size"], p["rotation"], p["text"], p["screen_off_title_block_decision"]) for p in pages], "per_arm": per_arm})
pdf_docs = sum(1 for r in rows if r["pages_in_scope"])
# the A base: the accepted application's own AI path (submittal form reader) -- observed 2 / 12 and 1 / 7 documents
a_expected, a_cap = round(pdf_docs * 3 / 19, 1), 8
caps = {"A": a_cap}
for arm in ("L1", "L2", "L3", "L4"):
    caps[arm] = int(round(totals[arm]["expected_requests"] * 1.35 / 5.0) * 5)
core_expected = sum(totals[a]["expected_requests"] for a in ("L1", "L2", "L3", "L4")) + a_expected
worst_per_project_per_arm = {ep: sum(1 for r in rows if r["ep"] == ep and r["pages_in_scope"]) * DOC_CAP for ep in per_project}
schedule = {"rule": "an arm processes a project on a rolling day only if the project's remaining day allowance covers the WORST case of that arm for that "
                    "project (12 x its PDF documents); otherwise the project is deferred for that arm to the next rolling day (never a partial project, never a raised cap)",
            "worst_case_per_project_per_arm": worst_per_project_per_arm,
            "worst_case_days": max(1, max((v for v in worst_per_project_per_arm.values()), default=0) * 4 // DAY + 1),
            "expected_per_project_all_arms": {ep: round(sum(v.values()), 1) for ep, v in per_project.items()},
            "expected_days": 1 if all(sum(v.values()) + a_expected <= DAY for v in per_project.values()) else 2,
            "frozen_order": ["A", "L1", "L2", "L3", "L4"],
            "pairs_first": "L1 and L2 are completed (or deferred per project) before L3 and L4, so the ROI contrast is complete first; within an arm, projects in EP order, documents in stage order",
            "incomplete_pairs": "a document an arm could not attempt (deferred beyond the run window, share refusal, cap, breaker) stays in the all-planned denominator as "
                                "not_attempted / budget for that arm; each pair's analysis reports (a) all planned, (b) documents attempted by both arms of the pair, (c) "
                                "field-specific read-in-both sets, all with document IDs; a pair with fewer than 12 attempted-by-both documents is reported INCONCLUSIVE"}
budget = {"price": "UNKNOWN: no dollar amount", "core_expected_requests": round(core_expected), "core_proposed_caps": caps, "core_cap_total": sum(caps.values()),
          "core_expected_input_tokens_incl_cached": round(sum(totals[a]["expected_input_tokens"] for a in ("L1", "L2", "L3", "L4")) + a_expected * tok("read_submittal_form")),
          "core_upper_bound_input_tokens": round(sum(totals[a]["upper_bound_input_tokens"] for a in ("L1", "L2", "L3", "L4"))),
          "core_expected_output_tokens": round(sum(totals[a]["expected_output_tokens"] for a in ("L1", "L2", "L3", "L4"))),
          "absolute_ceiling_requests": pdf_docs * DOC_CAP * 4 + a_cap, "escalations": "EV1 makes none; the cap of 2 per document stays declared",
          "retries": "the CLI adapter does not retry; a timeout is one request charged at its estimate (45,544 input) with unknown usage",
          "timeouts_observed": {k: T[k]["timeouts"] for k in ("discover_page", "discover_region")},
          "optional_arm_L1_minus_D": "excluded from the core (its question -- the deadline policy alone -- does not justify ~55 more requests here)",
          "offline_replays": "0 requests (P0..P3 on each arm's captured responses)",
          "note": "the proposed caps are NOT an approved allocation and NOT a guarantee that all four arms finish: a cap below worst case means arms may stop "
                  "with documents not attempted; those documents enter the all-planned comparison as budget stops"}
out = {"stage_files": len(stage), "pdf_documents": pdf_docs, "pages_total": sum(f["pages"] or 0 for f in stage), "pages_in_scope": sum(r["pages_in_scope"] for r in rows),
       "pages_beyond_scope": sum(r["pages_beyond_scope"] for r in rows), "assumptions": {"expected_reads_per_triggered_page": EXP, "observed_rates": {k: {"input_mean": tok(k), "input_p90": tok(k, "p90"), "output_mean": out_tok(k), "latency_p50_ms": T[k]["latency_ms"]["p50"]} for k in T},
       "trigger_rate_note": "EV1 selects pages with form / title-block cues and no deterministic identity, plus a seeded 20 % audit; the expected table assumes every in-scope page is triggered (conservative)"},
       "per_document": rows, "per_project": {ep: {a: round(v, 1) for a, v in arms.items()} for ep, arms in per_project.items()},
       "per_arm_totals": {a: {k: round(v, 1) for k, v in t.items()} for a, t in totals.items()}, "a_base": {"expected_requests": a_expected, "cap": a_cap},
       "schedule": schedule, "proposed_caps": caps, "budget": budget}
(R / "workload").mkdir(exist_ok=True)
(R / "workload/R21-WORKLOAD.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("pdf docs", pdf_docs, "pages in scope", out["pages_in_scope"], "beyond", out["pages_beyond_scope"])
for a, t in totals.items():
    print(a, {k: round(v) for k, v in t.items()}, "cap", caps[a])
print("core expected", budget["core_expected_requests"], "caps", caps, "total cap", budget["core_cap_total"], "ceiling", budget["absolute_ceiling_requests"])
print("worst per project per arm", worst_per_project_per_arm, "| expected per project", schedule["expected_per_project_all_arms"], "| days expected/worst", schedule["expected_days"], schedule["worst_case_days"])
