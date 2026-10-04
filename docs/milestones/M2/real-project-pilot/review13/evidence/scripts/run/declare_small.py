"""Round 2 exploration: the frozen experiment declaration for the SMALL matched batch, written before any model request
of this round. It records identities, source and proposed-truth hashes, the permission and project resolution,
provider / aliases, the application limits (unchanged), the ledger scope, pricing status, cache mode, the A/B/C
mapping, run order, stop conditions and the gate before the remaining batch. No model request is made here: the
provider's readiness is checked with the CLI's --version only."""
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys

W = pathlib.Path("C:/t/iso/work/r2x")
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
WT = pathlib.Path("C:/t/iso/frozen-r12")


def sha(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


head = subprocess.run(["git", "-C", str(WT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
dirty = subprocess.run(["git", "-C", str(WT), "status", "--porcelain"], capture_output=True, text=True, check=True).stdout.strip()
assert head == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3" and not dirty, (head, dirty)
os.environ.update({"AI_ENABLED": "false", "DATABASE_URL": "sqlite:///C:/t/iso/tmp/declare-no-db.db"})
sys.path.insert(0, str(WT / "backend")); os.chdir(WT / "backend")
from app.ai import evidence_reader as er, ledger as lg  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.services import design_sheet_extractor as dse, document_control as dc  # noqa: E402
from scripts import m2_boq_eval, m2_eval5  # noqa: E402

LIMIT_KEYS = ("ai_max_input_tokens_per_task", "ai_max_output_tokens_per_task", "ai_max_calls_per_document", "ai_max_calls_per_project_per_day",
              "ai_max_cost_per_job", "ai_max_elapsed_s_per_job", "ai_max_escalations_per_document", "ai_max_concurrency", "ai_max_retries",
              "ai_cli_timeout_s", "ai_price_input_per_million", "ai_price_output_per_million", "ai_price_cached_input_per_million", "ai_cache_ttl_days")
limits = {k: Settings.model_fields[k].default for k in LIMIT_KEYS}
cli = subprocess.run("claude --version", shell=True, capture_output=True, text=True)
sb = json.loads((W / "SMALL-BATCH.json").read_text(encoding="utf-8"))
stage = json.loads(pathlib.Path("C:/t/r2x/small-stage/SMALL-STAGE.json").read_text(encoding="utf-8"))
sel = json.loads((PILOT / "review06/evidence/round2/ROUND2-SELECTION.json").read_text(encoding="utf-8"))
cohort = {str(p["ep"]): str(p.get("cohort")) for p in sel["projects"]}
projects = sorted({f["doc_key"].split("/", 1)[0][3:] for f in stage["files"]} | {"8430"})
assert all("sealed" not in cohort[p] for p in projects), "a sealed project in the batch"
LEDGER_LIMITS = {"requests": 150, "per_request_input": 70000, "per_request_output": 20000, "input_tokens": 4000000, "output_tokens": 600000, "elapsed_s": 14400}
boq_inputs = {"C:/t/iso/work/r2x/boq/holdout-A-r12.json": None, "C:/t/iso/work/r2x/boq/holdout-A-r12-extraction.json": None,
              str(PILOT / "review05/holdout/HOLDOUT-BOQ-SET.json").replace("\\", "/"): None, str(PILOT / "review05/holdout/HOLDOUT-BOQ-LABELS.json").replace("\\", "/"): None}
boq_inputs = {k: sha(k) for k in boq_inputs}
src_files = ["backend/app/ai/evidence_reader.py", "backend/app/ai/ledger.py", "backend/app/ai/budget.py", "backend/app/ai/provider.py", "backend/app/ai/cache.py",
             "backend/app/services/document_control.py", "backend/app/services/design_sheet_extractor.py", "backend/scripts/m2_eval5.py",
             "backend/scripts/m2_eval4.py", "backend/scripts/m2_boq_eval.py", "backend/app/core/config.py"]
decl = {
 "declared_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
 "name": "r2x-small: Round 2 exploration, small matched A/B/C batch (M2 Review 13 follow-up)",
 "scope_statement": "exploration on exposed + exploration projects only; no sealed content; not a generalization claim; no winning variant while truth is unconfirmed",
 "candidate": {"commit": head, "worktree": str(WT).replace("\\", "/"), "tree_clean": True, "freeze_manifest": "review12/evidence/freeze/FREEZE-R12.json",
               "freeze_manifest_sha256": sha(PILOT / "review12/evidence/freeze/FREEZE-R12.json"), "accepted_by": "reviewer Review 13 (M2-REREVIEW.md), on 3d5607d",
               "source_sha256": {f: sha(WT / f) for f in src_files}},
 "identities": {"evidence_reader": {"READER_VERSION": er.READER_VERSION, "EVIDENCE_POLICY_VERSION": er.EVIDENCE_POLICY_VERSION, "SCHEMA_VERSION": er.SCHEMA_VERSION,
                                    "PROMPTS": er.PROMPTS, "AUDIT_RATE": er.AUDIT_RATE, "AUDIT_SEED": er.AUDIT_SEED,
                                    "MAX_PAGES_PER_DOCUMENT": er.MAX_PAGES_PER_DOCUMENT, "MAX_CALLS_PER_DOCUMENT": er.MAX_CALLS_PER_DOCUMENT},
                "ledger": lg.LEDGER_VERSION, "parser": dc.PARSER_VERSION, "design_sheet_extractor": dse.PARSER_VERSION,
                "evaluator": m2_eval5.EVALUATOR_VERSION, "boq_evaluator": m2_boq_eval.BOQ_EVALUATOR_VERSION},
 "authorization": {"document": str(MR / "OWNER-AI-PERMISSION-ROUND2.md").replace("\\", "/"), "sha256": sha(MR / "OWNER-AI-PERMISSION-ROUND2.md"),
                   "summary": "owner reply (Yes), 2026-09-29: model use for documents of the existing 34 frozen Round 2 projects through the existing evaluation provider; reused, not asked again",
                   "frozen_selection": {"file": "review06/evidence/round2/ROUND2-SELECTION.json", "sha256": sha(PILOT / "review06/evidence/round2/ROUND2-SELECTION.json")},
                   "projects_resolved": {p: cohort[p] for p in projects},
                   "sealed_excluded": sorted(p for p, c in cohort.items() if "sealed" in c),
                   "sandbox_project_policy": "sandbox projects are created with the application default ai_policy 'allowed' (models.py), on the strength of this permission; live projects.ai_policy is not read or changed",
                   "not_authorized": ["sealed holdout content", "live settings / services / data", "production processing or promotion", "M3"]},
 "sources": {"exploration_manifest_sha256": sha(W / "EXPLORATION-MANIFEST.json"), "small_batch": {"file": "SMALL-BATCH.json", "sha256": sha(W / "SMALL-BATCH.json"), "seed": sb["seed"]},
             "stage": {"root": "C:/t/r2x/small-stage", "manifest_sha256": sha("C:/t/r2x/small-stage/SMALL-STAGE.json"),
                       "files": {f["doc_key"]: f["sha256"] for f in stage["files"]}},
             "boq_sheet": {"doc_key": sb["boq_exposed"][0]["doc_key"], "cohort": "exposed (Review 05 holdout, H-06)"}},
 "stage": {"root": "C:/t/r2x/small-stage"},
 "proposed_truth": {"status": "AI-DRAFTED PROPOSALS, written before any prediction for these documents; no human review yet; every metric is PROVISIONAL",
                    "page_labels": {"file": "labels/SMALL-BATCH-LABELS.json", "sha256": sha(W / "labels/SMALL-BATCH-LABELS.json")},
                    "register_labels_derived": {"file": "labels/SMALL-BATCH-REGISTER-LABELS.json", "sha256": sha(W / "labels/SMALL-BATCH-REGISTER-LABELS.json")},
                    "boq_labels": {"file": "review05/holdout/HOLDOUT-BOQ-LABELS.json", "sha256": boq_inputs[str(PILOT / "review05/holdout/HOLDOUT-BOQ-LABELS.json").replace("\\", "/")],
                                   "status": "Review 05 AI-drafted labels; the H-06 quantity (printed 1) is crop-confirmed in C:/t/r2x/worklist/h06, still pending human confirmation"}},
 "provider": {"adapter": "claude-code (the Claude Code CLI; the existing evaluation provider)", "cli_version": (cli.stdout or cli.stderr).strip()[:80],
              "aliases": {"small": "sonnet", "standard": "opus"}, "actual_model": "recorded per response (ai_usage.model / ledger entries.model), never inferred",
              "env": {"AI_PROVIDER": "claude-code", "AI_MODEL_SMALL": "sonnet", "AI_MODEL_STANDARD": "opus"}},
 "application_limits": limits,
 "application_limits_note": "the frozen candidate's defaults, NOT overridden (Review 07 raised the per-project day limit and job time to 300; this round does not). "
                            "ai_max_input/output_tokens_per_task gate the application's reservation ESTIMATE (the evidence reader reserves 4,000 input), not actual usage; "
                            "ai_max_cost_per_job is inert while unpriced. The per-project day limit (60) is applied across all tracks by xtrack.py.",
 "ledger": {"version": lg.LEDGER_VERSION, "path": "C:/t/r2x/ledger/r2x-ledger.sqlite", "scope": "r2x-small-2026-09-29", "limits": LEDGER_LIMITS,
            "shared_by": "every track of this batch (A application path, B, C, BOQ-B, BOQ-C), across processes",
            "env": {"AI_LEDGER_PATH": "C:/t/r2x/ledger/r2x-ledger.sqlite", "AI_LEDGER_SCOPE": "r2x-small-2026-09-29", "AI_LEDGER_LIMITS": json.dumps(LEDGER_LIMITS)},
            "enforcement": {"requests": "hard (reserved before dispatch; a refused request is never sent)", "elapsed_s": "hard for new requests",
                            "per_request_input / per_request_output / input_tokens / output_tokens": "CLI adapter: ESTIMATE plus circuit breaker, NOT provider-enforced caps; a completed request cannot be made smaller"},
            "previous_scope": {"r7-matched": "C:/t/r7/ledger/matched.sqlite: 120 settled + 1 refused = exhausted; NOT reset, amended or reused. The file is Review 07 evidence and is not opened for writing (ledger .2 would add a column to it); Round 2 therefore uses its own ledger file"}},
 "pricing": {"status": "unknown: no trustworthy price configured (prices 0.0); cost is reported as UNKNOWN, never zero; the CLI's total_cost_usd is not used",
             "spend_cap": "not establishable (no valid pricing / account control) -- the request cap and time caps are the binding controls"},
 "cache_mode": "application result cache ON with its keys (reader / prompt / schema / policy / variant / tier / model). Each track starts from a sandbox with no evidence-cache entries: "
               "B and C start from a copy of A's database, which holds only A's application-path caches; A's and the deterministic track's sandboxes are new. "
               "Cache hits are recorded as cache hits (no request, no tokens).",
 "profiles": {"det": "AI disabled: the deterministic track (no model request), a reference only",
              "A": "AI_EVIDENCE_VARIANT=off with AI enabled: the application's existing AI path (submittal form / sheet readers) -- baseline",
              "B": "EV1: targeted triggers (form_or_title_block_without_identity, identity_without_revision, decision_block_unread, flagged_by_reader, unexplained_empty_document) "
                   "+ the seeded 20% audit of confident pages (AUDIT_RATE 0.2, seed by sha256 and page); BOQ: held rows + 20% audit of accepted rows",
              "C": "EV2: broad verification of every confident page + standard-tier escalation (<=2 per document); BOQ: every row",
              "verifier_blindness": "blind readers see the page / crop only, never the first reader's values (evidence_reader contract; BOQ crops carry the row, not its values)"},
 "run_order": ["det: r2x_ev0.py C:/t/r2x/small-stage r2x-small-det", "A: r2x_ev0.py C:/t/r2x/small-stage r2x-small-A --ai",
               "B: r2x_ev.py r2x-small-A r2x-small-B EV1", "C: r2x_ev.py r2x-small-A r2x-small-C EV2",
               "BOQ-B: r2x_boq.py r2x-small-boq-B EV1", "BOQ-C: r2x_boq.py r2x-small-boq-C EV2"],
 "boq": {"sheets": [sb["boq_exposed"][0]["doc_key"].replace("\\", "/")], "scored": "C:/t/iso/work/r2x/boq/holdout-A-r12.json",
         "extraction": "C:/t/iso/work/r2x/boq/holdout-A-r12-extraction.json", "set": str(PILOT / "review05/holdout/HOLDOUT-BOQ-SET.json").replace("\\", "/"),
         "inputs_sha256": boq_inputs},
 "stop_conditions": ["ledger refusal (requests / elapsed / token breaker): no further request in the scope; each later read is a recorded budget stop",
                     "application limits (per document calls / escalations / elapsed, per project day) as the application enforces them",
                     "per-project rolling-24-hour total across all tracks reaches 60 (xtrack.py): further requests for that project are budget stops",
                     "three consecutive provider failures (transport, timeout, refusal): the run stops",
                     "a stage project outside the declaration, a sealed project, a changed source / truth / declaration hash: the runner refuses to start",
                     "a sandbox that already exists: the runner refuses (runs are never repeated in place; failed or stopped runs are preserved)"],
 "partial_results": "kept as they are; a budget-stopped page is 'budget', never absent or negative; failed and stopped attempts stay in the outputs and the ledger",
 "continuation": "the remaining exploration batch runs only after the small-batch gate passes, under a new declaration (or addendum) naming its own scope, "
                 "within the same application limits and the cross-track project-day limit; nothing in this scope is reset",
 "small_batch_gate": ["every staged document persisted in every track (rows == stage files)", "no business-row change between A and B / C (project_submittals, project_shop_drawings counts equal)",
                      "ledger settled + unknown-usage requests == fresh ai_usage requests over all tracks", "no authentication / configuration failure of the provider",
                      "outputs scored by evaluator .9 against the PROVISIONAL labels, with truth status stated"],
 "evaluation": {"documents": "scripts.m2_eval5 (evaluator .9) --labels SMALL-BATCH-REGISTER-LABELS.json --page-labels SMALL-BATCH-LABELS.json --rows <track rows.json>",
                "boq": "row outcomes of r2x_boq.py joined to the m2_boq_eval pairs of the AI-off extraction",
                "goals": "0 critical false accepts; >= 90% correct automatic recovery of critical fields; 98% for other fields (reported, not claimed on provisional truth)"},
}
p = W / "run" / "EXPERIMENT-DECLARATION-SMALL.json"
if p.exists():
    sys.exit("the declaration exists already: it is frozen; write an addendum instead")
p.write_text(json.dumps(decl, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("declaration sha256", sha(p))
print("cli", decl["provider"]["cli_version"], "| projects", decl["authorization"]["projects_resolved"])
