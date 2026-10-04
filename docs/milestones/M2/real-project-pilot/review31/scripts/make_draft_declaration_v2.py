"""Write C:/t/iso/work/r2x/r31/DRAFT-DECLARATION.v2.json (R31-02 / R31-03 / R31-04): a DRAFT binding of the revised
fresh-validation plan v2. NOT FOR EXECUTION. It supersedes the Review 30 draft and binds the Review 31 binding manifest by
its sha256. Written once (an existing file is never overwritten)."""
import datetime
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "DRAFT-DECLARATION.v2.json"
if OUT.exists():
    sys.exit("DRAFT-DECLARATION.v2.json exists")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()  # noqa: E731
MR = "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap"
M2 = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2"
FP = json.loads((HERE / "FRESH-PROJECTS-R31.json").read_text(encoding="utf-8"))
C_SW = {"AI_EVIDENCE_VARIANT": "EV1", "AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_SUPPORT": "v2", "AI_EVIDENCE_SCHEDULING": "required_first",
        "AI_EVIDENCE_DEADLINE": "1", "AI_EVIDENCE_TARGETED": "1"}
CAP_EQ = 240
d = {
    "name": "M2 fresh validation v2, accepted baseline vs Review 29 combined candidate (DRAFT)",
    "status": "DRAFT -- NOT FOR EXECUTION: no owner permission for the proposed cohort, no labels, preparation package not yet independently reviewed, no budget authorization",
    "supersedes": {"file": "review30/DRAFT-DECLARATION.json", "sha256": sha(HERE.parent / "r30" / "pkg-src" / "DRAFT-DECLARATION.json")},
    "drafted_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "executed": False, "budget_approved": False, "authorization": None,
    "binding_manifest": {"file": "BINDING-MANIFEST.json", "sha256": sha(HERE / "BINDING-MANIFEST.json"),
                         "preflight": "every entry re-verified before any dispatch; any difference refuses the run"},
    "code": {"baseline": {"commit": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3", "tree": "C:/t/iso/frozen-r12"},
             "candidate": {"commit": "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d", "tree": "C:/t/iso/cand-r29", "frozen": True}},
    "arms": {"B": {"switches": {}, "meaning": "accepted path, evidence reader off", "runs": "first"},
             "C": {"switches": {**C_SW, "AI_EVIDENCE_IDGUARD": "1", "AI_EVIDENCE_ADJUDICATE": "1", "AI_EVIDENCE_DECISION_REGION": "1", "AI_EVIDENCE_ASSOC": "1"},
                   "starts_from": "a copy of the frozen B database; harness/state_check.py must pass (recorded B file hash, equal logical content, no C-policy or unattributed evidence, no evidence-task cache row)"},
             "R": {"switches": C_SW, "meaning": "reference (L3 identity); served the capture of C by content key whatever its outcome; a request C never made is sent once as reference-only (lane R)",
                   "role": "offline contrast only; never a gate input except decision coverage C >= R; never a live stop"},
             "P": {"meaning": "variation probe: seeded 15 % of the answered C dispatches re-sent once in lane P", "seed": "m2-r30-variation-2026-10-02",
                   "role": "reported only; never served to B or C; never a score"}},
    "shared_response_contract": {"implementation": "harness/capture_store.py (tested: harness/test_capture_store.py, 21 tests)",
                                 "content_key": "doc sha256, page, task, tier, profile, variant, model alias, model override, effort, max output, system hash, prompt text, image sha256s, schema hash",
                                 "bound_key": "lane + policy + content key",
                                 "rules": ["one provider dispatch per identical bound fingerprint (reserve before dispatch, BEGIN IMMEDIATE, unique key)",
                                           "B and C never share; any difference in source hash, page, crop, prompt, tier, profile, variant or policy is a new fingerprint",
                                           "R is served the capture of C by content key (answer, failure or interrupted) and never re-sends it; R-only requests never reach B or C",
                                           "P writes only lane-P rows",
                                           "a reserved row without an answer is charged and never re-sent (served as interrupted_charged)",
                                           "every served answer keeps its original lane, policy, dispatch seq, time, model and usage"]},
    "cohort": {"proposed": {"picked": [r["ep"] for r in FP["picked"]], "alternates_in_seeded_order": [r["ep"] for r in FP["alternates"]]},
               "permission": "REQUIRED: a new written owner permission naming these EP numbers (download, staging, labelling, provider use)",
               "selection_file_sha256": sha(HERE / "FRESH-PROJECTS-R31.json"), "review30_reconciliation_sha256": sha(HERE / "R30-PICKS-RECONCILED.json"),
               "sealed": "excluded unless separately released by the owner for this exact run", "within_project_option": "cannot close M2; not proposed"},
    "selection": {"pool": {"review_signal": 40, "drawing_signal": 20, "other": 12, "per_project_max": 12, "seed": "m2-r30-pool-2026-10-02"},
                  "extensions": [{"name": "extension-1", "review_signal": 36, "cumulative_per_project_max": 18, "seed": "m2-r31-extension-1-2026-10-02"},
                                 {"name": "extension-2", "review_signal": 36, "cumulative_per_project_max": 24, "seed": "m2-r31-extension-2-2026-10-02"}],
                  "alternates": "entered in the seeded order of the proposal only when the picked projects' paths are exhausted under the cap",
                  "population_gate": {"implementation": "harness/score_bcr.py population_gate", "minimum_resolved_independently_reviewed_per_field": 12,
                                      "fields": ["identity", "revision", "decision"],
                                      "rule": "checked after the independent label review of each stage and before any prediction: all three >= 12 -> select the run set; else the next extension; after extension-2 still short -> PREPARATION BLOCKED (no dispatch); there is no partial closure run"},
                  "run_set": {"decision_bearing": "all resolved decision-bearing documents, up to 16 (at least 12 by the gate)",
                              "identity_revision_top_up": "resolved identity / revision documents without a decision, up to 8, until each reaches 16",
                              "negative_controls": 4, "unsupported_controls": 2, "max_documents": 30, "seed": "m2-r30-runset-2026-10-02",
                              "uses": "frozen-label truth presence only; never a prediction or candidate output"},
                  "freeze": "selection, labels, run-set manifest and replacement log hashed after replacements, before either arm runs",
                  "feasibility_sha256": sha(HERE / "FEASIBILITY-R31.json")},
    "labels": {"status": "not drafted",
               "review": "independent of the drafter: the owner delegated independent label review to the Codex reviewer; it is recorded as owner-delegated independent AI review, never as human sign-off",
               "post_run": "no change; disputes in an immutable note that cannot change scores"},
    "evaluators": {"primary": {"version": "m2-pilot-eval-2026-10-02.10", "file": "C:/t/iso/cand-r29/backend/scripts/m2_eval6.py", "sha256": sha("C:/t/iso/cand-r29/backend/scripts/m2_eval6.py")},
                   "scorer": {"file": "harness/score_bcr.py", "sha256": sha(HERE / "harness" / "score_bcr.py"), "tests": "harness/test_score_bcr.py (13 tests)"},
                   "lane_scoring": {"file": "harness/score_lane.py", "sha256": sha(HERE / "harness" / "score_lane.py")}},
    "thresholds_verbatim": [
        {"source": "AI-ACCURACY-POLICY.md section 1", "sha256": sha(f"{MR}/AI-ACCURACY-POLICY.md"),
         "text": "Target zero observed errors among adjudicated automatically accepted critical facts, with at least 90% correct automatic recovery on clear applicable facts in the expanded M2 evaluation. Preserve the existing 98% minimum accepted-precision gate for other evaluated fields."},
        {"source": "M2-ACCEPTANCE-REPORT.md Correction 5 targets", "sha256": sha(f"{M2}/M2-ACCEPTANCE-REPORT.md"),
         "text": [">= 98 % precision, accepted critical fields", ">= 90 % recovery of readable critical fields", "zero unresolved critical false acceptance"]},
        {"source": "MASTER-ROADMAP.md M2", "sha256": sha(f"{MR}/MASTER-ROADMAP.md"),
         "text": "Completion additionally requires measured benefit from the selected AI profile, no unresolved critical false acceptance, correct automatic recovery and explicit cost/latency/review burden."},
        {"source": "review21/ANALYSIS-PLAN.md section 5", "sha256": sha(f"{M2}/real-project-pilot/review21/ANALYSIS-PLAN.md"),
         "text": ["an ROI arm's consultant-decision coverage (completed read or verified absence, **including decisions outside the title block**) must be \u2265 the matching WP arm's. Unknown (`located_incomplete`) is not coverage.",
                  "\u2265 1 correctly associated fact per 8 extra requests at equal caps, no new false accept, interval excluding zero"]}],
    "analysis": {"unit": "document", "primary_population": "resolved, independently reviewed labels; unresolved reported separately", "minimum_matched_per_field": 12,
                 "estimate": "paired difference of clean correctly associated recovery (0/1 per document and field)",
                 "uncertainty": {"method": "document-cluster bootstrap stratified by project", "resamples": 2000, "seed": "m2-r30-bootstrap-2026-10-02", "interval": "95% percentile"},
                 "request_normalised_gate": {"applies_as_quoted": "at equal caps: B and C have the SAME maximum allowance (requests, scope token thresholds, elapsed)",
                                             "extra_requests": "application-visible requests of C (inherited from B + its own) minus those of B; the difference is the policy cost",
                                             "passes": "net correct facts x 8 >= extra requests, no new false acceptance, bootstrap interval of the net gain per document excluding zero",
                                             "no_natural_policy_gate": "no unequal-cap variant of the gate is defined; the scorer refuses it as not applicable"},
                 "decision_coverage_gate": "completed reads + verified absences (truth has no decision) of C >= those of B AND >= those of R; wrong absences and located_incomplete never count",
                 "thresholds": "zero critical acceptance on resolved truth in C; accepted precision >= 0.98 per field; clean recovery >= 0.90 per field",
                 "concentration_rule": "not eligible if > 50% of the net gain of C in a field comes from one project or one stratum",
                 "outcomes": ["ELIGIBLE FOR A SEPARATE SELECTION DECISION", "NOT ELIGIBLE", "INCOMPLETE", "INVALID", "PREPARATION BLOCKED"],
                 "default_selection": "never by this run"},
    "primary_outcomes": ["false or cross-page association count (.10, per fact): C vs B and C vs R",
                         "clean revision recovery lost or gained under PA: C vs R on identical responses",
                         "consultant decision under DR: completed reads, verified absences, wrong absences, accepted decisions (correct / wrong), held conflicts: C vs B and C vs R",
                         "critical acceptances on resolved and on unresolved truth: each lane",
                         "new requests and tokens (actual and estimated) used by DR and by the combined candidate"],
    "limits": {"caps": {"B": CAP_EQ, "C": CAP_EQ, "R_reference_only": 40, "variation_probe": 36}, "total_cap": CAP_EQ * 2 + 40 + 36,
               "equal_allowance": "B and C: same request cap (8 per document x 30), same scope token thresholds, same elapsed bound",
               "expected_use": {"B": "about 6", "C": "about 135", "R": "about 10", "P": "about 20"},
               "per_request_estimate_thresholds": {"input": 90000, "output": 20000},
               "semantics": "estimates before dispatch; an actual overshoot opens the breaker for later requests; no hard actual-token bound for the CLI",
               "scope_estimate_thresholds": {"B": [7000000, 1400000], "C": [7000000, 1400000], "R": [1200000, 240000], "probe": [1100000, 220000]},
               "elapsed_s": {"B": 259200, "C": 259200, "R_and_probe_after_C": 86400}, "rolling_per_project_per_day": 60, "cost": "unknown (never zero)"},
    "stop_rules": {"implementation": "harness/stop_rules.py (tested: harness/test_stop_rules.py, 8 tests)",
                   "rules": ["B, critical acceptance on resolved truth: B terminal; comparison INVALID (baseline incomplete); C does not start or stops",
                             "C, critical acceptance on resolved truth: C terminal, never resumed; comparison RESULT = candidate failed the safety gate",
                             "R or P, critical acceptance on resolved truth: a reference finding; no live arm stops; never reported as a live safety stop",
                             "critical acceptance on unresolved truth, any lane: reported, never a stop",
                             "three consecutive provider failures in a lane: that lane terminal; B -> INVALID; C -> INCOMPLETE; R / P -> only that lane",
                             "breaker / ledger / allowance / counter refusal: budget stop of that lane, never raised or reset; B or C -> INCOMPLETE",
                             "failure streaks are per lane: an R or P failure never counts toward B or C",
                             "binding difference or second writer: refused before dispatch",
                             "tripwire: evaluated after every document of B and C against the frozen labels"]},
    "dry_run": {"report": "dry-run/t3/DRY-RUN-REPORT.json", "sha256": sha(HERE / "dry-run" / "t3" / "DRY-RUN-REPORT.json"), "model_requests": 0},
    "gpt_bridge": "disabled; not part of the workflow",
}
OUT.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(sha(OUT))
