"""Write pkg-src/DRAFT-DECLARATION.json (R30-04): a DRAFT binding of the revised fresh-validation plan. Not for execution."""
import datetime
import hashlib
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
MR = "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap"
M2 = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2"
C_SW = {"AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_SUPPORT": "v2", "AI_EVIDENCE_SCHEDULING": "required_first", "AI_EVIDENCE_DEADLINE": "1", "AI_EVIDENCE_TARGETED": "1"}
d = {
    "name": "M2 fresh validation, accepted baseline vs Review 29 combined candidate (DRAFT)",
    "status": "DRAFT -- NOT FOR EXECUTION: no cohort chosen, no permission for Option B, no labels, no reviewed preparation package, no budget authorization",
    "drafted_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "executed": False, "budget_approved": False, "authorization": None,
    "code": {"baseline": {"commit": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3", "tree": "C:/t/iso/frozen-r12"},
             "candidate": {"commit": "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d", "tree": "C:/t/iso/cand-r29",
                           "evidence_reader_sha256": sha("C:/t/iso/cand-r29/backend/app/ai/evidence_reader.py")}},
    "arms": {"B": {"switches": {}, "meaning": "accepted path, evidence reader off"},
             "C": {"switches": {**C_SW, "AI_EVIDENCE_IDGUARD": "1", "AI_EVIDENCE_ADJUDICATE": "1", "AI_EVIDENCE_DECISION_REGION": "1", "AI_EVIDENCE_ASSOC": "1"},
                   "starts_from": "the database copy of B"},
             "R": {"switches": C_SW, "meaning": "reference (frozen L3 identity) evaluated by replay of the capture of C; reference-only requests executed once, recorded separately"}},
    "cohort": {"chosen": None,
               "options": {"A": "within-project: unseen documents of the 10 exploration projects (existing Round 2 permission; templates exposed; cannot close M2)",
                           "B": "fresh projects 22936, 19905, 20561, 16385, 29255, 24752 (alternates 25883, 19199, 28328, 26214); requires a new owner permission"},
               "fresh_candidates_sha256": sha(HERE / "FRESH-PROJECT-CANDIDATES.json"), "used_projects_sha256": sha(HERE / "M2-USED-PROJECTS.json"),
               "sealed": "excluded unless separately released by the owner for this exact run"},
    "selection": {"pool": {"review_signal": 40, "drawing_signal": 20, "other": 12, "per_project_max": 12, "seed": "m2-r30-pool-2026-10-02"},
                  "extension": {"review_signal": 36, "max_extensions": 1},
                  "run_set": {"decision_bearing_max": 16, "identity_revision_only_max": 8, "negative_controls": 4, "unsupported_controls": 2, "max_documents": 30,
                              "seed": "m2-r30-runset-2026-10-02", "uses": "frozen-label truth presence only; never a prediction or candidate output"},
                  "decision_out_of_scope_if_resolved_decision_documents_below": 12,
                  "freeze": "selection, labels, run-set manifest and replacement log hashed after replacements, before either arm runs",
                  "feasibility_sha256": sha(HERE / "FIELD-POPULATION.json")},
    "labels": {"status": "not drafted", "review": "independent of the drafter; owner-delegated AI review only if stated; human sign-off pending",
               "post_run": "no change; disputes in an immutable note that cannot change scores"},
    "evaluators": {"primary": {"version": "m2-pilot-eval-2026-10-02.10", "file": "C:/t/iso/cand-r29/backend/scripts/m2_eval6.py",
                               "sha256": sha("C:/t/iso/cand-r29/backend/scripts/m2_eval6.py")},
                   "secondary": {"version": "m2-pilot-eval-2026-09-29.9", "file": "C:/t/iso/frozen-r12/backend/scripts/m2_eval5.py",
                                 "sha256": sha("C:/t/iso/frozen-r12/backend/scripts/m2_eval5.py")},
                   "scorer": "to be built and independently reviewed in the preparation package (v4 eligibility contract, per-run policy binding)"},
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
    "analysis": {"unit": "document", "primary_population": "resolved labels; unresolved reported separately", "minimum_matched_per_claimed_field": 12,
                 "estimate": "paired difference of clean correctly associated recovery (0/1 per document and field)",
                 "uncertainty": {"method": "document-cluster bootstrap stratified by project", "resamples": 2000, "seed": "m2-r30-bootstrap-2026-10-02", "interval": "95% percentile"},
                 "request_normalized_benefit": "(net correct facts C-B) / (requests C-B) with bootstrap interval; >= 1/8 and interval excluding zero; the request difference is part of the policy",
                 "decision_coverage_gate": "C completed reads + verified absences (truth has no decision) >= B; wrong absences never count",
                 "concentration_rule": "no default if > 50% of the net gain of C in a field comes from one project or one layout stratum, or matched population < 12",
                 "default_selection": "never by this run"},
    "primary_outcomes": ["false or cross-page association count (.10, per fact): C vs B and C vs R",
                         "clean revision recovery lost or gained under PA: C vs R on identical responses",
                         "consultant decision under DR: completed reads, verified absences, wrong absences, accepted decisions (correct / wrong), held conflicts: C vs B and C vs R",
                         "critical acceptances on resolved and on unresolved truth: each arm",
                         "new requests and tokens (actual and estimated) used by DR and by the combined candidate"],
    "stochastic_control": {"design": "each identical prompt / image fingerprint executed once; B first, C from the database of B (shared requests inherited); C live once with full capture; R by replay of the capture of C, R-only requests live once as reference-only; seeded 15% variation probe of the fingerprints of C re-executed once, reported only",
                           "probe_seed": "m2-r30-variation-2026-10-02",
                           "not_claimed": "independent single reads never isolate a policy effect; B vs C rests on one realization of the reads of C"},
    "accounting": ["application-visible requests per arm and class", "provider-reported actual input / output", "cached input", "estimated charges for unknown-usage timeouts",
                   "refusals before dispatch", "timeouts", "breaker events"],
    "limits": {"caps": {"B": 16, "C": 240, "R_reference_only": 40, "variation_probe": 36}, "total_cap": 332,
               "per_request_estimate_thresholds": {"input": 90000, "output": 20000},
               "semantics": "estimates before dispatch; an actual overshoot opens the breaker for later requests; no hard actual-token bound for the CLI",
               "scope_estimate_thresholds": {"B": [400000, 80000], "C": [7000000, 1400000], "R": [1200000, 240000], "probe": [1100000, 220000]},
               "elapsed_s": {"B": 14400, "C": 259200, "R_and_probe_after_C": 86400}, "rolling_per_project_per_day": 60, "cost": "unknown"},
    "stop_rules": ["critical acceptance on a resolved label in C: terminal stop, never resumed", "three consecutive provider failures: terminal stop",
                   "breaker / ledger / allowance / counter refusal: budget stop, never raised", "binding difference or second writer: refused before dispatch"],
}
out = HERE / "pkg-src" / "DRAFT-DECLARATION.json"
out.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(sha(out))
