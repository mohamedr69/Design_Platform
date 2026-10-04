"""AI accuracy pilot: the frozen experiment declaration, written BEFORE any request of this pilot. It records sources,
labels, permission, arms (documents S / G / T after a common A base; BOQ-S / BOQ-T), code identities and hashes
(accepted app, candidate commit, r16.1 harness, BOQ queue, runners), provider / aliases, the application limits
(unchanged; asserted by every runner), the ledger scopes (one per arm; hard request caps summing to the 150-request
experiment cap; in the same ledger file as the earlier Round 2 scope, which is left untouched), the cross-track
project-day accounting and per-arm project shares, cache mode, run order, stop rules, coverage and evaluation
contracts. No model request is made here (the CLI is checked with --version only)."""
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys

W = pathlib.Path("C:/t/iso/work/r2x")
A = W / "ai-pilot"
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
ACC, CAND = pathlib.Path("C:/t/iso/frozen-r12"), pathlib.Path("C:/t/iso/cand-ai")
PY = sys.executable
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
posix = lambda p: str(p).replace("\\", "/")


def git(tree, *args):
    return subprocess.run(["git", "-C", str(tree), *args], capture_output=True, text=True, check=True).stdout.strip()


ACC_COMMIT, CAND_COMMIT = "3d5607d99fcebf08ac45f5df937ad615ecc16fb3", git(CAND, "rev-parse", "HEAD")
assert git(ACC, "rev-parse", "HEAD") == ACC_COMMIT and not git(ACC, "status", "--porcelain")
assert not git(CAND, "status", "--porcelain") and git(CAND, "rev-parse", "HEAD~1") == ACC_COMMIT
changed = git(CAND, "diff", "--name-only", ACC_COMMIT, CAND_COMMIT).splitlines()
assert sorted(changed) == ["backend/app/ai/evidence_reader.py", "backend/tests/test_ai_pilot_2026_09_30.py"], changed
SRC = ["backend/app/ai/evidence_reader.py", "backend/app/ai/budget.py", "backend/app/ai/ledger.py", "backend/app/ai/provider.py", "backend/app/ai/cache.py",
       "backend/app/services/document_control.py", "backend/app/services/design_sheet_extractor.py", "backend/scripts/m2_eval5.py", "backend/scripts/m2_eval4.py",
       "backend/scripts/m2_boq_eval.py", "backend/app/core/config.py"]
for f in SRC:
    if f != "backend/app/ai/evidence_reader.py":
        assert sha(ACC / f) == sha(CAND / f), f"{f} differs between the accepted tree and the candidate"

os.environ.update({"AI_ENABLED": "false", "DATABASE_URL": "sqlite:///C:/t/iso/tmp/declare-no-db.db"})
sys.path.insert(0, str(ACC / "backend"))
os.chdir(ACC / "backend")
from app.ai import ledger as lg  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.services import design_sheet_extractor as dse, document_control as dc  # noqa: E402
from scripts import m2_eval5  # noqa: E402

LIMIT_KEYS = ("ai_max_input_tokens_per_task", "ai_max_output_tokens_per_task", "ai_max_calls_per_document", "ai_max_calls_per_project_per_day",
              "ai_max_cost_per_job", "ai_max_elapsed_s_per_job", "ai_max_escalations_per_document", "ai_max_concurrency", "ai_max_retries",
              "ai_cli_timeout_s", "ai_price_input_per_million", "ai_price_output_per_million", "ai_price_cached_input_per_million", "ai_cache_ttl_days")
limits = {k: Settings.model_fields[k].default for k in LIMIT_KEYS}


def identities(tree: pathlib.Path, env: dict) -> dict:
    code = ("import json,os,sys; sys.path.insert(0,'.'); from app.ai import evidence_reader as er; "
            "print(json.dumps({'READER_VERSION': er.READER_VERSION, 'EVIDENCE_POLICY_VERSION': er.EVIDENCE_POLICY_VERSION, 'SCHEMA_VERSION': er.SCHEMA_VERSION, "
            "'PROMPTS': er.PROMPTS, 'AUDIT_RATE': er.AUDIT_RATE, 'AUDIT_SEED': er.AUDIT_SEED, 'MAX_PAGES_PER_DOCUMENT': er.MAX_PAGES_PER_DOCUMENT, "
            "'MAX_CALLS_PER_DOCUMENT': er.MAX_CALLS_PER_DOCUMENT, 'GUARD_ENABLED': getattr(er, 'GUARD_ENABLED', None), "
            "'TARGETED_ENABLED': getattr(er, 'TARGETED_ENABLED', None)}))")
    base = {k: v for k, v in os.environ.items() if k not in ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED")}
    out = subprocess.run([PY, "-c", code], cwd=str(tree / "backend"), env={**base, "AI_ENABLED": "false", **env}, capture_output=True, text=True, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


ARM_ENV = {"S": {}, "G": {"AI_EVIDENCE_GUARD": "1"}, "T": {"AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_TARGETED": "1"}}
ARM_TREE = {"S": ACC, "G": CAND, "T": CAND}
ARM_MEANING = {
 "S": "unchanged baseline: the accepted application (3d5607d), existing targeted EV1 policy",
 "G": "S + the guard only: a bare revision token (Rev.0, REV 01, R1 ...) is never validated as a document identity; it is kept as a raw "
      "revision-token observation with no target. Candidate commit, AI_EVIDENCE_GUARD=1",
 "T": "G + targeted verification: (a) region support read from the rotation-correct text layer, or local Tesseract OCR of the read region "
      "when the page has no text there; (b) one independent context read (task read_field_context: a wider crop, or the whole page when no "
      "region was found) of an own identity / revision that discovery or the deterministic reader proposed and the blind read did not validate "
      "(never after a failed or budget-refused request). Structured evidence (literal, printed label, role, region, legibility); the answer "
      "joins the readings and the UNCHANGED acceptance rule decides (agreement of all legible readings + region support + no deterministic "
      "conflict); a role other than the own role holds. Candidate commit, AI_EVIDENCE_GUARD=1 AI_EVIDENCE_TARGETED=1",
}
arms = {}
for k in ("S", "G", "T"):
    ids = identities(ARM_TREE[k], ARM_ENV[k])
    arms[k] = {"meaning": ARM_MEANING[k], "tree": posix(ARM_TREE[k]), "commit": ACC_COMMIT if k == "S" else CAND_COMMIT,
               "env": {"AI_EVIDENCE_VARIANT": "EV1", **ARM_ENV[k]}, "identities": ids}
assert arms["S"]["identities"]["GUARD_ENABLED"] is None and arms["G"]["identities"]["GUARD_ENABLED"] is True and arms["T"]["identities"]["TARGETED_ENABLED"] is True
assert len({arms[k]["identities"]["EVIDENCE_POLICY_VERSION"] for k in arms}) == 3, "each arm has its own policy identity (no cache reuse)"

stage = json.loads(pathlib.Path("C:/t/r2x/pilot-stage/PILOT-STAGE.json").read_text(encoding="utf-8"))
sample = json.loads((A / "PILOT-SAMPLE.json").read_text(encoding="utf-8"))
assert {f["doc_key"]: f["sha256"] for f in stage["files"]} == {d["doc_key"]: d["sha256"] for d in sample["documents"]}
m = json.loads((W / "EXPLORATION-MANIFEST.json").read_text(encoding="utf-8"))
boq_doc = [b for b in m["boq_candidates"] + m["documents"] if (b.get("sha256") or "").startswith("6153dfe701f5")][0]
sel = json.loads((PILOT / "review06/evidence/round2/ROUND2-SELECTION.json").read_text(encoding="utf-8"))
cohort = {str(p["ep"]): str(p.get("cohort")) for p in sel["projects"]}
projects = sorted({d["ep"] for d in sample["documents"]} | {boq_doc["ep"], "8430"})
assert all("sealed" not in cohort[p] for p in projects), "a sealed project"

LEDGER_FILE = "C:/t/r2x/ledger/r2x-ledger.sqlite"
COMMON = {"per_request_input": 70000, "per_request_output": 20000, "input_tokens": 4000000, "output_tokens": 600000, "elapsed_s": 14400}
CAPS = {"A": 12, "S": 36, "G": 36, "T": 42, "BOQ-S": 12, "BOQ-T": 12}
assert sum(CAPS.values()) == 150
scopes = {}
for k, v in CAPS.items():
    L = dict(COMMON, requests=v)
    scopes[k] = {"scope": f"ai-pilot-2026-09-30-{k}", "limits": L,
                 "env": {"AI_LEDGER_PATH": LEDGER_FILE, "AI_LEDGER_SCOPE": f"ai-pilot-2026-09-30-{k}", "AI_LEDGER_LIMITS": json.dumps(L)}}
import sqlite3  # noqa: E402

con = sqlite3.connect(f"file:{LEDGER_FILE}?mode=ro", uri=True)
existing = [r[0] for r in con.execute("select scope from scopes")]
earlier = {r[0]: r[1] for r in con.execute("select scope, count(*) from entries group by scope")}
con.close()
DRY = os.environ.get("PILOT_DRY") == "1"
assert DRY or not any(s["scope"] in existing for s in scopes.values()), "a pilot scope exists already"
sys.path.insert(0, str(W / "run"))
import xtrack  # noqa: E402

usage_now = {ep: xtrack.used(ep) for ep in projects}
RUNNERS = ["make_pilot_stage.py", "pilot_a.py", "pilot_shares.py", "pilot_ev.py", "pilot_boq.py", "boq_queue.py", "tests/test_boq_queue.py",
           "select_pilot.py", "labels_pilot.py", "patch_candidate.py", "patch_candidate_2.py", "zoom.py", "dry_provider.py", "score_pilot.py"]
TO = A / "tests-out"
TESTS = {"files": {f.name: sha(f) for f in sorted(TO.iterdir()) if f.is_file()},
         "summary": {"candidate full suite, flags off (e5a0a94)": "1681 passed, 2 failed, 35 skipped -- both failures reproduce on the accepted 3d5607d "
                     "(ACCEPTED-two-failures: test_ep_archive_models::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index FOREIGN KEY; "
                     "test_proposed_materials::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it extra catalogue items): pre-existing, unrelated",
                     "focused AI / evidence modules (14), flags off": "216 passed", "focused, G": "216 passed",
                     "focused, T": "213 passed, 3 failed -- expected T-only scripted-sequence differences (the extra targeted request is appended / consumes the "
                                   "next scripted answer): test_evidence_reader_r7::test_escalation_keeps_the_earlier_disagreement (one more reading 'blind_context'), "
                                   "test_m2_review08::test_identity_completes_while_revision_times_out_and_decision_is_refused_by_budget (revision 'completed' / decision "
                                   "'budget' instead of 'failed:timeout'), test_m2_review10::test_a_known_revision_constraint_holds_a_decision_without_an_ai_identity "
                                   "(decision 'candidate' instead of 'validated': more conservative). None is a new acceptance",
                     "pilot BOQ queue tests (tests/test_boq_queue.py)": "8 passed",
                     "dry run (scripted provider)": "A, shares, S, G, T, BOQ-S, BOQ-T and score_pilot ran end to end in C:/t/r2x/dry-runs; business hashes S = G = T = A"}}
decl = {
 "declared_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
 "dry_run_before_declaration": "the runners' plumbing was exercised end to end with a scripted provider (PILOT_DRY=1: C:/t/r2x/dry-runs, own ledger / counter / allowance files, no model request) before this declaration",
 "name": "M2 targeted AI accuracy pilot (2026-09-30)",
 "status": "DIAGNOSTIC PILOT on AI-drafted PROVISIONAL labels; not M2 acceptance; not a generalization claim; no variant adoption",
 "question": "can targeted AI recover supported identities, revisions and consultant decisions currently missed or held, without new false accepted facts or wrong associations?",
 "comparisons": {"S->G": "the guard effect only (a validator fix, not AI)", "G->T": "the targeted verification effect; T gains are attributed by route: "
                 "region support (text-layer rotation / local OCR) versus the targeted context read",
                 "BOQ-S->BOQ-T": "the declared risk-ordered row queue versus the accepted EV1 row selection, one 12-request allowance each; "
                                 "also compared at BOQ-S's request count (T's queue prefix)"},
 "authorization": {"document": posix(MR / "OWNER-AI-PERMISSION-ROUND2.md"), "sha256": sha(MR / "OWNER-AI-PERMISSION-ROUND2.md"),
                   "reused_not_requested_again": True,
                   "frozen_selection": {"file": "review06/evidence/round2/ROUND2-SELECTION.json", "sha256": sha(PILOT / "review06/evidence/round2/ROUND2-SELECTION.json")},
                   "projects_resolved": {p: cohort[p] for p in projects}, "sealed": "ten sealed projects: not opened, rendered or sent",
                   "task": {"file": posix(MR / "reviews/M2-review-17/TASK-TARGETED-AI-ACCURACY.md"), "sha256": sha(MR / "reviews/M2-review-17/TASK-TARGETED-AI-ACCURACY.md")},
                   "review_17": {"file": posix(MR / "reviews/M2-review-17/REVIEW-17-REPORT.md"), "sha256": sha(MR / "reviews/M2-review-17/REVIEW-17-REPORT.md")},
                   "sandbox_project_policy": "sandbox projects use the application default ai_policy 'allowed' on the strength of this permission; live projects are not read or changed"},
 "code": {"accepted_app": {"commit": ACC_COMMIT, "tree": posix(ACC), "clean": True, "source_sha256": {f: sha(ACC / f) for f in SRC}},
          "candidate": {"repository": "C:/t/iso/ep-platform (scratch clone; not the owner repository)", "tree": posix(CAND), "branch": git(CAND, "rev-parse", "--abbrev-ref", "HEAD"),
                        "commit": CAND_COMMIT, "parent": ACC_COMMIT, "clean": True, "changed_files": {f: sha(CAND / f) for f in changed},
                        "diff_sha256": hashlib.sha256(subprocess.run(["git", "-C", str(CAND), "diff", "--binary", ACC_COMMIT, CAND_COMMIT], capture_output=True).stdout).hexdigest(),
                        "default_behaviour": "flags unset: byte-identical accepted behaviour (flag-gated; version strings unchanged)",
                        "the_function_that_changes": "app.ai.evidence_reader: validate_value (G guard), _read_page (T: region_texts_v2 support + targeted read), "
                                                     "new helpers bare_revision_token / _local_ocr / region_texts_v2 / _targeted_read; nothing outside evidence_reader"},
          "evaluator": {"module": "scripts.m2_eval5", "version": m2_eval5.EVALUATOR_VERSION, "sha256": sha(ACC / "backend/scripts/m2_eval5.py"), "tree": posix(ACC)},
          "parser": dc.PARSER_VERSION, "design_sheet_extractor": dse.PARSER_VERSION, "ledger": lg.LEDGER_VERSION,
          "boq_harness_r16": {f: sha(W / "r16" / f) for f in ("boq_harness.py", "boq_contract.py", "replay_core.py")},
          "xtrack": sha(W / "run/xtrack.py"), "pilot_scripts": {f: sha(A / f) for f in RUNNERS}},
 "offline_tests": TESTS,
 "arms": arms,
 "sources": {"exploration_manifest_sha256": sha(W / "EXPLORATION-MANIFEST.json"),
             "sample": {"file": "PILOT-SAMPLE.json", "sha256": sha(A / "PILOT-SAMPLE.json"), "documents": {d["doc_key"]: d["sha256"] for d in sample["documents"]},
                        "pages": "every page (<= 3 per document; the reader's 4-page scope covers all)"},
             "boq_sheet": {"doc_key": boq_doc["doc_key"], "sha256": boq_doc["sha256"], "staged_path": boq_doc["staged_path"], "cohort": cohort[boq_doc["ep"]]},
             "boq_extraction_A": {"file": "boq/PILOT-BOQ-A-extraction.json", "sha256": sha(A / "boq/PILOT-BOQ-A-extraction.json"),
                                  "made_by": "the accepted AI-off design-sheet extractor (3d5607d), before any label comparison"}},
 "stage": {"root": "C:/t/r2x/pilot-stage", "manifest_sha256": sha("C:/t/r2x/pilot-stage/PILOT-STAGE.json")},
 "labels": {"files": {n: sha(A / "labels" / n) for n in ("PILOT-PAGE-LABELS.json", "PILOT-REGISTER-LABELS.json", "PILOT-BOQ-LABELS.json", "PILOT-UNCERTAINTY-AND-EXPOSURE.json")},
            "status": "AI-drafted proposals written before any pilot prediction; not reviewed by a person; PROVISIONAL",
            "resolved_for_stop_rule": "a label with confidence 'high' and no entry in the uncertainty register",
            "unchanged_unresolved": "F09 / F10 / F06 revision, +SL23I/+SL231, the footer role: not in this sample, not ruled on"},
 "provider": {"adapter": "claude-code (the existing evaluation provider)", "cli_version": subprocess.run("claude --version", shell=True, capture_output=True, text=True).stdout.strip()[:60],
              "aliases": {"small": "sonnet", "standard": "opus"}, "env": {"AI_PROVIDER": "claude-code", "AI_MODEL_SMALL": "sonnet", "AI_MODEL_STANDARD": "opus"},
              "actual_model": "recorded per response"},
 "application_limits": limits,
 "application_limits_note": "the accepted defaults, NOT overridden (asserted by every runner): 12 requests / 2 escalations / 120 s per document job; "
                            "60 per project per day (applied across tracks by xtrack); concurrency 2; CLI timeout 300 s",
 "ledger": {"version": lg.LEDGER_VERSION, "file": LEDGER_FILE, "scopes": scopes, "total_requests_cap": 150,
            "earlier_scopes": {s: f"{n} entries, left untouched (not reset, amended or reused)" for s, n in earlier.items()},
            "enforcement": {"requests": "hard, reserved before dispatch", "elapsed_s": "hard for new requests",
                            "tokens": "CLI adapter: ESTIMATE plus breaker, NOT provider-enforced"},
            "mismatch": "a handle with different limits for an existing scope is refused (ledger .2); no scope is reset"},
 "project_day": {"limit": 60, "counter": "C:/t/r2x/ledger/project-day.sqlite (xtrack), shared with the earlier Round 2 tracks",
                 "reconciled_at_declaration": usage_now,
                 "EP-8430": "60 used 2026-09-29 18:52-19:00 UTC: FULL until 2026-09-30 ~18:52-19:00 UTC",
                 "A_base": "A's worst case is its scope cap (12); every pilot project has >= 46 left, so A cannot breach 60; its actual requests are recorded afterwards",
                 "arm_shares": "after A, pilot_shares.py freezes share(ep) = floor((60 - used(ep)) / 3) for S, G and T alike (written and hashed before S); "
                               "an arm's request beyond its share of a project is refused as a budget stop, so an earlier arm cannot starve a later one",
                 "boq": "EP-22510: BOQ-S + BOQ-T <= 24 after the document arms; checked by xtrack at each request"},
 "pricing": "unknown (no valid price configured; prices 0.0): cost reported as UNKNOWN, never zero; the CLI's total_cost_usd is not used",
 "cache_mode": "application result cache ON. A is a new sandbox. S, G and T each start from a WAL-consistent copy of A's database; the evidence "
               "cache key includes the policy / reader / prompt identities, which differ per arm, so no arm can reuse another's evidence. "
               "BOQ-S and BOQ-T have their own new sandboxes. Cache hits are recorded as cache hits (no request, no tokens).",
 "run_order": ["A: pilot_a.py (accepted app path, AI enabled, evidence variant off)", "pilot_shares.py", "S: pilot_ev.py S", "G: pilot_ev.py G",
               "T: pilot_ev.py T", "BOQ-S: pilot_boq.py S", "BOQ-T: pilot_boq.py T"],
 "project_order": "by project id as A creates them (EP numbers sorted); documents by id",
 "boq": {"sheet": boq_doc["doc_key"], "labels": "labels/PILOT-BOQ-LABELS.json (kind 'line' rows are the replay truth; the part_only battery row is reported separately)",
         "S_policy": "the accepted EV1 selection (every held row + the seeded 20 % audit of accepted rows) through boq_harness.verify_sheet, unchanged",
         "T_policy": "boq_queue.risk_queue (queue ai-pilot-boq-queue-2026-09-30.1): held rows; accepted rows with reader uncertainty signals (application "
                     "thresholds RECHECK_QUANTITY_BELOW / CONFIRM_CATALOG_BELOW = 90); a seeded audit of 2 confident rows; residual seeded audit to the cap. "
                     "Written to disk before the first request; one row per request; one allowance",
         "allowance": "per (scope, profile, document): 12 requests / 2 escalations / 120 s, durable (r16.1 DocAllowance / DurableBudget)",
         "matcher": "accepted r16.1 boq_contract + replay_core, unchanged",
         "h06_control": {"sheet": "EP-8430/EP-8430 Commercial/EP-8430 PAVA Revised Design Sheet - 23.10.2017.pdf", "status": "DECLARED, NOT RUN IN THIS WINDOW",
                         "reason": "EP-8430's rolling-24-hour project allowance is full (60/60) until about 2026-09-30 19:00 UTC; any request now would breach "
                                   "the 60/project/day limit. Its stored r2x-small BOQ-B/-C replays remain the diagnostic history (printed quantities 1, 1, 1; control 2)"},
         "claims": "verified rows are listed; unreached rows are listed; no full-sheet verification claim when any row was not reached"},
 "stop_rules": ["an evaluator-flagged critical automatic acceptance by the arm's AI on a RESOLVED label (checked after each project): stop the arm; the "
                "remaining projects are not attempted; the counterexample is preserved",
                "three consecutive provider failures (transport, timeout, refusal)", "an undeclared source, changed hash, sealed project, existing sandbox or "
                "changed declaration: the runner refuses to start", "any ledger / project-day / share / per-document refusal: a budget stop, recorded; nothing is raised or reset"],
 "evaluation": {"documents": "scripts.m2_eval5 (evaluator .9, unchanged) with labels/PILOT-REGISTER-LABELS.json + labels/PILOT-PAGE-LABELS.json; ai_context per arm "
                             "{variant EV1, profile default, policies [the arm's EVIDENCE_POLICY_VERSION]}; A scored with no AI context",
                "metrics": ["supported raw-observation correctness", "automatic-acceptance precision and critical false accepts", "correctly associated accepted recovery",
                            "correct-but-held and ambiguous / unresolved", "unread / failed / budget / not attempted", "requests, time, actual tokens, cost status"],
                "breakdowns": ["field", "project", "document type (stratum)", "arm", "resolved vs provisional-uncertain labels"],
                "success": "an evidence-supported G->T recovery gain with no new critical false acceptance on resolved labels, controls preserved, complete usage accounting",
                "otherwise": "no gain / unsafe / inconclusive"},
}
p = pathlib.Path("C:/t/r2x/dry-runs/PILOT-DECLARATION.dry.json") if DRY else A / "PILOT-DECLARATION.json"
if DRY:
    decl["status"] = "DRY-RUN DECLARATION (scripted provider, no model request) -- not the experiment's declaration"
    p.parent.mkdir(parents=True, exist_ok=True)
elif p.exists():
    sys.exit("the declaration is frozen; write an addendum")
p.write_text(json.dumps(decl, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("declaration", sha(p))
for k, v in arms.items():
    print(k, v["identities"]["READER_VERSION"], "|", v["identities"]["EVIDENCE_POLICY_VERSION"], "|", v["identities"]["PROMPTS"].get("read_field_context"))
print("usage now", usage_now, "| earlier scopes", earlier)
