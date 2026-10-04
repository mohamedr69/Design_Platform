"""The FINAL four-arm declaration, version 2 (Review 27 correction; offline; no model request). Same design, harness,
sample, caps and limits as version 1 (aec4d4df..., superseded, kept unchanged); rebinds the labels to r26.2 (independent
AI source review applied) and states the ledger's token semantics correctly (estimates reserved before dispatch, actual
usage recorded after, overshoot opens a breaker; the CLI cannot enforce actual token bounds).
--- version 1 docstring follows ---
The FINAL four-arm declaration for the owner's budget decision (offline; no model request). It keeps the reviewed R21
design (four arms L1..L4 on candidate 719e8de, A base on accepted 3d5607d, the frozen 27-document sample / R21 stage, the
evaluator .9) and binds it to:
  * the reviewed harness v4.3 (review25 package, accepted by Review 26): runner arm_ev.py (v4.2, lifecycle contract v2),
    provider journal validator-2, scorer / coverage v4, the r16.1 durable allowance, the rolling-day counter, the A runner
    and the two modules it imports from review22/harness-v4 -- every file by sha256;
  * the frozen R26 reference labels (labels-r26, manifest hashed), harness_dir = this folder;
  * a NEW ledger scope family (no existing scope; the original run's remaining 22 requests are not used);
  * the revised proposal limits: request caps unchanged (688), token caps unchanged, document-arm scope elapsed limit
    96 h instead of 4 h (the 4 h limit could not hold the declared rolling-day deferral schedule -- see BUDGET-PROPOSAL).
PILOT_DRY=1 writes a DRY variant (same content, status DRY-PREFLIGHT) to <PILOT_DRY_ROOT>/FINAL-DECLARATION.dry.json for
the scripted preflight; the live file is written only without PILOT_DRY. Status: PROPOSAL / NOT EXECUTED / NO MODEL BUDGET
APPROVED -- nothing in it may run before the owner's explicit authorization."""
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys

R = pathlib.Path(__file__).resolve().parent              # C:/t/iso/work/r2x/r27 (harness_dir for labels-r26.2)
H = pathlib.Path("C:/t/iso/work/r2x/review25/harness-v4.3")
PKG25 = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review25")
PKG22 = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review22")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
ACC, SUC = pathlib.Path("C:/t/iso/frozen-r12"), pathlib.Path("C:/t/iso/cand-ai4")
ACC_COMMIT, SUC_COMMIT = "3d5607d99fcebf08ac45f5df937ad615ecc16fb3", "719e8de661b8b10427ef6cff5d2d277a53b64dc6"
DRY = os.environ.get("PILOT_DRY") == "1"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
posix = lambda p: str(p).replace("\\", "/")
git = lambda t, *a: subprocess.run(["git", "-C", str(t), *a], capture_output=True, text=True, check=True).stdout.strip()
assert git(ACC, "rev-parse", "HEAD") == ACC_COMMIT and not git(ACC, "status", "--porcelain")
assert git(SUC, "rev-parse", "HEAD") == SUC_COMMIT and not git(SUC, "status", "--porcelain")
frozen = json.loads((PKG25 / "bindings/FROZEN-HARNESS.json").read_text(encoding="utf-8"))
RUN_FILES = ("arm_ev.py", "arm_a.py", "coverage_v4.py", "score_arms_v4.py", "provider_journal.py", "dry_provider2.py", "xtrack2.py", "schedule_sim.py")
for f in RUN_FILES:
    assert sha(H / f) == frozen["files"][f] == sha(PKG25 / "harness-v4.3" / f), f"{f} differs from the reviewed v4.3"
A_IMPORTS = {"C:/t/iso/work/r2x/review22/harness-v4/dry_provider2.py": None, "C:/t/iso/work/r2x/review22/harness-v4/xtrack2.py": None}
for p in A_IMPORTS:
    A_IMPORTS[p] = sha(p)
    assert sha(p) == sha(PKG22 / "harness-v4" / pathlib.Path(p).name), p          # equal to the reviewed review22 package copy
pdecl = json.loads((pathlib.Path("C:/t/iso/work/r2x/ai-pilot") / "PILOT-DECLARATION.json").read_text(encoding="utf-8"))
limits = pdecl["application_limits"]
os.environ.update({"AI_ENABLED": "false", "DATABASE_URL": "sqlite:///C:/t/iso/tmp/declare-no-db.db"})
KEYS = ("READER_VERSION", "EVIDENCE_POLICY_VERSION", "SCHEMA_VERSION", "PROMPTS", "AUDIT_RATE", "AUDIT_SEED", "MAX_PAGES_PER_DOCUMENT", "MAX_CALLS_PER_DOCUMENT",
        "GUARD_ENABLED", "TARGETED_ENABLED", "EFFICIENT_ENABLED", "SUPPORT_V2", "REQUIRED_FIRST", "DEADLINE_ENABLED", "ROI_ENABLED")


def identities(env):
    base = {k: v for k, v in os.environ.items() if not k.startswith("AI_EVIDENCE_")}
    code = f"import json,sys; sys.path.insert(0,'.'); from app.ai import evidence_reader as er; print(json.dumps({{k: getattr(er, k, None) for k in {KEYS!r}}}))"
    out = subprocess.run([sys.executable, "-c", code], cwd=str(SUC / "backend"), env={**base, **env}, capture_output=True, text=True, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


COMMON = {"AI_EVIDENCE_VARIANT": "EV1", "AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_SUPPORT": "v2", "AI_EVIDENCE_SCHEDULING": "required_first", "AI_EVIDENCE_DEADLINE": "1"}
ARM_ENV = {"L1": {}, "L2": {"AI_EVIDENCE_ROI": "1"}, "L3": {"AI_EVIDENCE_TARGETED": "1"}, "L4": {"AI_EVIDENCE_ROI": "1", "AI_EVIDENCE_TARGETED": "1"}}
MEANING = {"L1": "whole-page discovery, X off", "L2": "title-block (ROI) discovery, X off", "L3": "whole-page discovery, X on", "L4": "ROI discovery, X on"}
arms = {}
for k, e in ARM_ENV.items():
    ids = identities({**COMMON, **e})
    assert ids["GUARD_ENABLED"] and ids["SUPPORT_V2"] and ids["REQUIRED_FIRST"] and ids["DEADLINE_ENABLED"] and not ids["EFFICIENT_ENABLED"]
    assert ids["ROI_ENABLED"] == ("AI_EVIDENCE_ROI" in e) and ids["TARGETED_ENABLED"] == ("AI_EVIDENCE_TARGETED" in e)
    arms[k] = {"meaning": MEANING[k], "tree": posix(SUC), "commit": SUC_COMMIT, "env": {**COMMON, **e}, "identities": ids}
assert len({(v["identities"]["READER_VERSION"], v["identities"]["EVIDENCE_POLICY_VERSION"]) for v in arms.values()}) == 4
off = identities({})
assert (off["READER_VERSION"], off["EVIDENCE_POLICY_VERSION"]) == ("evidence-reader-2026-09-29.7", "evidence-policy-2026-09-29.4"), "flags off != accepted"
stage_root = pathlib.Path("C:/t/r2x/r21-stage")
stage = json.loads((stage_root / "R21-STAGE.json").read_text(encoding="utf-8"))
planned = [{"doc": f["doc_key"], "sha256": f["sha256"], "pages": f["pages"], "extension": f["extension"]} for f in stage["files"]]
LAB = R / "labels-r26.2"
lab = ("R26.2-REGISTER-LABELS.json", "R26.2-PAGE-LABELS.json", "R26.2-UNCERTAINTY-AND-EXPOSURE.json")
lman = json.loads((LAB / "LABEL-MANIFEST.r26.2.json").read_text(encoding="utf-8"))
for n in lab:
    assert sha(LAB / n) == lman["files"][n], n
workload = json.loads((PKG22 / "workload/R22-WORKLOAD.json").read_text(encoding="utf-8"))
caps = dict(workload["proposed_caps"]["caps"])
assert caps == {"A": 8, "L1": 160, "L2": 160, "L3": 180, "L4": 180} and sum(caps.values()) == 688
FAMILY = os.environ.get("PILOT_SCOPE_FAMILY", "m2-four-arm-final-2026-10-01" + ("-dry" if DRY else ""))
LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"
TOKENS = {"per_request_input": 70000, "per_request_output": 20000, "input_tokens": 4000000, "output_tokens": 600000}
ELAPSED = {"A": 14400, "L1": 345600, "L2": 345600, "L3": 345600, "L4": 345600}     # revised: 96 h per document-arm scope (was 14,400 s)
scopes = {k: {"scope": f"{FAMILY}-{k}", "limits": dict(TOKENS, elapsed_s=ELAPSED[k], requests=v),
              "env": {"AI_LEDGER_PATH": LEDGER, "AI_LEDGER_SCOPE": f"{FAMILY}-{k}", "AI_LEDGER_LIMITS": json.dumps(dict(TOKENS, elapsed_s=ELAPSED[k], requests=v))}}
          for k, v in caps.items()}
sel = json.loads((pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot") / "review06/evidence/round2/ROUND2-SELECTION.json").read_text(encoding="utf-8"))
cohort = {str(p["ep"]): str(p.get("cohort")) for p in sel["projects"]}
projects = sorted({p["doc"].split("/")[0][3:] for p in planned})
assert all("sealed" not in cohort.get(p, "sealed?") for p in projects), projects
decl = {
    "declared_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "name": "four-arm isolated accuracy experiment - FINAL proposal v2 (R21 design, harness v4.3, labels r26.2)",
    "supersedes": {"declaration_sha256": "aec4d4df3d400126b95c17938aafe267d9444baba04a8bb4ddedce088edef998", "reason": "Independent M2 Review 27 (R27-01 token wording, R27-02 independent label review); an approval of the superseded hash does not carry over", "kept_unchanged": True},
    "status": ("DRY-PREFLIGHT VARIANT (scripted provider only) of the final proposal" if DRY else
               "PROPOSAL / NOT EXECUTED / NO MODEL BUDGET APPROVED - submitted for the owner's budget decision; nothing may run before an explicit authorization"),
    "executed": False, "new_model_budget_approved": False, "harness_contract": frozen["contract_version"], "harness_dir": posix(R),
    "authorization": {"document": posix(MR / "OWNER-AI-PERMISSION-ROUND2.md"), "sha256": sha(MR / "OWNER-AI-PERMISSION-ROUND2.md"),
                      "scope_note": "the recorded Round 2 permission covers the cohort and provider; it is NOT a budget approval. A new request allowance for these scopes is required and NOT granted by this declaration",
                      "projects_resolved": {p: cohort.get(p) for p in projects}, "sealed": "not opened"},
    "code": {"accepted_app": {"commit": ACC_COMMIT, "tree": posix(ACC)},
             "successor": {"commit": SUC_COMMIT, "tree": posix(SUC), "evidence_reader_sha256": sha(SUC / "backend/app/ai/evidence_reader.py")},
             "evaluator": {"file": posix(ACC / "backend/scripts/m2_eval5.py"), "sha256": sha(ACC / "backend/scripts/m2_eval5.py"), "version": "m2-pilot-eval-2026-09-29.9"},
             "harness": {"dir": posix(H), "reviewed_package": posix(PKG25), "frozen_harness_sha256": sha(PKG25 / "bindings/FROZEN-HARNESS.json"),
                         "accepted_by": "Independent Review 26 (R25-01 accepted as corrected)", "files": {f: sha(H / f) for f in RUN_FILES},
                         "versions": {k: frozen[k] for k in ("contract_version", "scorer_version", "runner_version", "lifecycle_contract", "journal_version", "validator_revision", "scheduling_rule_version")}},
             "a_runner_imports": A_IMPORTS,
             "durable_allowance": frozen["durable_allowance_module"]},
    "arms": arms, "doc_arms": ["L1", "L2", "L3", "L4"],
    "common": {"G": True, "support": "v2", "scheduling": "required_first", "deadline": "min(provider timeout, remaining job time); 20 s floor; OCR bound"},
    "pairs": {"ROI alone": ["L1", "L2"], "X on whole page": ["L1", "L3"], "X on ROI": ["L2", "L4"], "ROI under X": ["L3", "L4"]},
    "sources": {"stage": {"root": posix(stage_root), "manifest": "R21-STAGE.json", "manifest_sha256": sha(stage_root / "R21-STAGE.json")},
                "sample": {"documents": {p["doc"]: p["sha256"] for p in planned}, "documents_planned": planned, "n_planned": len(planned),
                           "sample_sha256": stage["sample_sha256"], "rule_file_sha256": sha("C:/t/iso/work/r2x/review21/R21-SAMPLE.json")}},
    "stage": {"root": posix(stage_root), "manifest": "R21-STAGE.json", "manifest_sha256": sha(stage_root / "R21-STAGE.json")},
    "labels": {"dir": "labels-r26.2", "register": lab[0], "page": lab[1], "uncertainty": lab[2], "files": {n: sha(LAB / n) for n in lab},
               "manifest": "LABEL-MANIFEST.r26.2.json", "manifest_sha256": sha(LAB / "LABEL-MANIFEST.r26.2.json"), "version": lman["labels_version"],
               "independent_review_bindings": lman["independent_review_bindings"],
               "provenance": lman["provenance"], "frozen_before_any_prediction": True},
    "provider": pdecl["provider"], "application_limits": limits,
    "ledger": {"file": LEDGER, "scopes": scopes, "caps": caps, "sum_caps": sum(caps.values()), "scope_family": FAMILY,
               "note": "NEW scope family; the original 150-request experiment's remaining 22 requests are not used; each scope's limits are persisted on first use and cannot change without a recorded amendment",
               "limit_semantics": {"requests": "hard ceiling on APPLICATION-VISIBLE requests (one complete() each), counted at reservation before dispatch; one CLI request can contain several provider-internal turns",
                                   "tokens": "reservation thresholds on ESTIMATES before dispatch; actual usage is recorded after the response; an overshoot (per-request or aggregate) opens the circuit breaker so no FURTHER request is dispatched. The claude-code CLI adapter cannot enforce actual input / output token bounds; a single request can exceed them; timeout / unknown usage is charged at the estimate",
                                   "elapsed": "measured from the scope's first use; a proposal value, not a completion guarantee",
                                   "cost": "unknown (no authoritative price for the declared provider)",
                                   "contract": "frozen candidate backend/app/ai/ledger.py module docstring, reserve() and settle(); independent probe TOKEN-LIMIT-PROBE.json (Review 27)"}},
    "project_day": {"limit": 60, "rule_version": frozen["scheduling_rule_version"],
                    "rule": "before a project-arm batch the runner checks the project's rolling 24 h capacity (60 minus every track's requests in the last 24 h, the A base included) against the batch's worst case (remaining durable allowance of every pending PDF); if it does not fit the project is persisted as deferred and zero requests are sent; a later --resume takes deferred projects in declared order"},
    "lifecycle": {"contract": frozen["lifecycle_contract"], "terminal_stops": ["critical acceptance on a resolved label", "three consecutive completed provider failures"],
                  "resume": "plain --resume continues deferral / interruption; a terminal stop is never resumed (exit 4); indeterminate provider evidence refuses (exit 5)"},
    "stop_rules": ["critical acceptance by the arm's AI on a resolved label (eligible evidence only): terminal stop", "three consecutive completed provider failures: terminal stop",
                   "any breaker / ledger / allowance / counter refusal: a budget stop, never raised",
                   "undeclared source, changed hash, sealed project, existing sandbox without --resume, existing allowance under a new tag, second writer, changed declaration: refuse before any dispatch"],
    "cache_mode": "result cache on; arms start from copies of one A base; distinct reader / policy / prompt identities per arm: no cross-arm reuse",
    "workload": {"source": posix(PKG22 / "workload/R22-WORKLOAD.json"), "sha256": sha(PKG22 / "workload/R22-WORKLOAD.json"),
                 "three_request_figures": workload["budget"]["three_request_figures"], "revision_note": "see BUDGET-PROPOSAL v2: elapsed-limit revision; token thresholds act on estimates with a post-response breaker, so actual tokens can exceed them before the breaker stops further requests"},
}
p = (pathlib.Path(os.environ.get("PILOT_DRY_ROOT", "C:/t/r2x/dry-runs/r27-check")) / "FINAL-DECLARATION.v2.dry.json") if DRY else (R / "FINAL-DECLARATION.v2.json")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(decl, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("declaration", p, sha(p))
for k, v in arms.items():
    print(k, v["identities"]["READER_VERSION"], "|", v["identities"]["EVIDENCE_POLICY_VERSION"])
