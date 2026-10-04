"""Successor declaration (M2 Review 18 continuation), written BEFORE any request of the continuation. The original
aggregate allowance of 150 is NOT renewed: the pilot ledger is reconciled first (settled requests counted; refusals
that never left the process are not requests) and the successor's subcaps sum to at most the residual. H-06 is
reserved first (24 = BOQ-S 12 + BOQ-T 12). Nothing resumes e5a0a94 T or its closed scope. No model request here."""
import datetime
import hashlib
import json
import os
import pathlib
import sqlite3
import subprocess
import sys

R = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")
A = pathlib.Path("C:/t/iso/work/r2x/ai-pilot")
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
ACC, SUC = pathlib.Path("C:/t/iso/frozen-r12"), pathlib.Path("C:/t/iso/cand-ai2")
PY = sys.executable
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
posix = lambda p: str(p).replace("\\", "/")
git = lambda t, *a: subprocess.run(["git", "-C", str(t), *a], capture_output=True, text=True, check=True).stdout.strip()
DRY = os.environ.get("PILOT_DRY") == "1"

ACC_COMMIT = "3d5607d99fcebf08ac45f5df937ad615ecc16fb3"
SUB_BASE = "e5a0a94a4235282797bed302f6bb14acba70db01"
SUC_COMMIT = git(SUC, "rev-parse", "HEAD")
assert git(ACC, "rev-parse", "HEAD") == ACC_COMMIT and not git(ACC, "status", "--porcelain")
assert not git(SUC, "status", "--porcelain") and git(SUC, "rev-parse", "HEAD~1") == SUB_BASE
changed = git(SUC, "diff", "--name-only", ACC_COMMIT, SUC_COMMIT).splitlines()
assert all(f.startswith("backend/tests/") or f == "backend/app/ai/evidence_reader.py" for f in changed), changed
PILOT_DECL = A / "PILOT-DECLARATION.json"
pdecl = json.loads(PILOT_DECL.read_text(encoding="utf-8"))
limits = pdecl["application_limits"]
os.environ.update({"AI_ENABLED": "false", "DATABASE_URL": "sqlite:///C:/t/iso/tmp/declare-no-db.db"})


def identities(tree, env):
    code = ("import json,sys; sys.path.insert(0,'.'); from app.ai import evidence_reader as er; "
            "print(json.dumps({k: getattr(er, k, None) for k in ('READER_VERSION','EVIDENCE_POLICY_VERSION','SCHEMA_VERSION','PROMPTS','AUDIT_RATE',"
            "'AUDIT_SEED','MAX_PAGES_PER_DOCUMENT','MAX_CALLS_PER_DOCUMENT','GUARD_ENABLED','TARGETED_ENABLED','EFFICIENT_ENABLED')}))")
    base = {k: v for k, v in os.environ.items() if not k.startswith("AI_EVIDENCE_")}
    out = subprocess.run([PY, "-c", code], cwd=str(tree / "backend"), env={**base, **env}, capture_output=True, text=True, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


T2_ENV = {"AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_TARGETED": "1", "AI_EVIDENCE_EFFICIENT": "1"}
arms = {"S": {"meaning": "unchanged baseline: accepted application 3d5607d, existing EV1 policy (the same S as the pilot, re-run on the continuation sample)",
              "tree": posix(ACC), "commit": ACC_COMMIT, "env": {"AI_EVIDENCE_VARIANT": "EV1"}, "identities": identities(ACC, {})},
        "T2": {"meaning": "the successor candidate: G (guard) + T .2 (R18-01 completion, R18-02 gate, required-first scheduling) + E (located discovery "
                          "for drawing sheets, located-absence outcomes, job-deadline-bound request / OCR timeouts)",
               "tree": posix(SUC), "commit": SUC_COMMIT, "env": {"AI_EVIDENCE_VARIANT": "EV1", **T2_ENV}, "identities": identities(SUC, T2_ENV)}}
assert arms["S"]["identities"]["EVIDENCE_POLICY_VERSION"] != arms["T2"]["identities"]["EVIDENCE_POLICY_VERSION"]
# the successor's flags-off identity equals the accepted one (no silent change of S behaviour)
assert identities(SUC, {})["EVIDENCE_POLICY_VERSION"] == arms["S"]["identities"]["EVIDENCE_POLICY_VERSION"]

# --- ledger reconciliation: the residual of the ORIGINAL 150 ------------------------------------------------------------
LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"
con = sqlite3.connect(f"file:{LEDGER}?mode=ro", uri=True)
pilot_scopes = [s["scope"] for s in pdecl["ledger"]["scopes"].values()]
settled = {s: con.execute("select count(*) from entries where scope = ? and state = 'settled'", (s,)).fetchone()[0] for s in pilot_scopes}
open_res = {s: con.execute("select count(*) from entries where scope = ? and state not in ('settled', 'refused')", (s,)).fetchone()[0] for s in pilot_scopes}
refused = {s: con.execute("select count(*) from entries where scope = ? and state = 'refused'", (s,)).fetchone()[0] for s in pilot_scopes}
existing = [r[0] for r in con.execute("select scope from scopes")]
other_new = [r for r in con.execute("select scope, count(*) from entries where scope like 'ai-pilot-r18%' group by scope")]
con.close()
used = sum(settled.values()) + sum(open_res.values())
residual = 150 - used
assert residual == 78 and not other_new, (residual, other_new)
CAPS = {"BOQ-S": 12, "BOQ-T": 12, "A": 4, "S": 21, "T2": 29}          # H-06 reserved first; documents from the rest
assert sum(CAPS.values()) <= residual
COMMON = {"per_request_input": 70000, "per_request_output": 20000, "input_tokens": 4000000, "output_tokens": 600000, "elapsed_s": 14400}
scopes = {}
for k, v in CAPS.items():
    L = dict(COMMON, requests=v)
    name = f"ai-pilot-r18-2026-09-30-{'H06-' + k[4:] if k.startswith('BOQ') else k}"
    assert DRY or name not in existing, name
    scopes[k] = {"scope": name, "limits": L, "env": {"AI_LEDGER_PATH": LEDGER, "AI_LEDGER_SCOPE": name, "AI_LEDGER_LIMITS": json.dumps(L)}}
sys.path.insert(0, "C:/t/iso/work/r2x/run")
import xtrack  # noqa: E402

sample = json.loads((R / "CONTINUATION-SAMPLE.json").read_text(encoding="utf-8"))
stage = json.loads(pathlib.Path("C:/t/r2x/cont-stage/CONT-STAGE.json").read_text(encoding="utf-8"))
assert {f["doc_key"]: f["sha256"] for f in stage["files"]} == {d["doc_key"]: d["sha256"] for d in sample["documents"]}
sel = json.loads((PILOT / "review06/evidence/round2/ROUND2-SELECTION.json").read_text(encoding="utf-8"))
cohort = {str(p["ep"]): str(p.get("cohort")) for p in sel["projects"]}
H06_KEY = "EP-8430/EP-8430 Commercial/EP-8430 PAVA Revised Design Sheet - 23.10.2017.pdf"
H06_PATH = "C:/t/holdout/stage/EP-8430/EP-8430 Commercial/EP-8430 PAVA Revised Design Sheet - 23.10.2017.pdf"
H06_SHA = "719f8714d2a75673c8ba390a884a2d2889b2438fd587eaa2c42f62d75f344fec"
assert sha(H06_PATH) == H06_SHA
projects = sorted({d["ep"] for d in sample["documents"]} | {"8430"})
assert all("sealed" not in cohort[p] for p in projects)
usage_now = {p: xtrack.used(p) for p in projects}
LBL = R / "labels-continuation"
RUNNERS = ["cont_stage.py", "cont_a.py", "cont_shares.py", "cont_ev.py", "cont_boq.py", "derive_runners.py", "score_cont.py", "select_continuation.py",
           "labels_continuation.py", "labels_v2.py", "rescore_v2.py", "locator_eval.py", "patch_successor.py", "patch_successor_2.py", "patch_successor_3.py",
           "repair_tests.py", "declare_continuation.py"]
now = datetime.datetime.now(datetime.timezone.utc)
decl = {
 "declared_at_utc": now.isoformat(timespec="seconds"),
 "name": "M2 Review 18 correction + efficiency-first continuation (2026-09-30)",
 "status": ("DRY-RUN DECLARATION (scripted provider) -- not the experiment's" if DRY else
            "DIAGNOSTIC continuation on AI-drafted PROVISIONAL labels; not M2 acceptance; not a generalization claim; no variant adoption"),
 "authorization": {"document": posix(MR / "OWNER-AI-PERMISSION-ROUND2.md"), "sha256": sha(MR / "OWNER-AI-PERMISSION-ROUND2.md"), "reused_not_requested_again": True,
                   "projects_resolved": {p: cohort[p] for p in projects}, "sealed": "ten sealed projects: not opened, rendered or sent",
                   "task": {"file": posix(MR / "reviews/M2-review-18/TASK-AI-PILOT-CORRECTION-AND-CONTINUATION.md"),
                            "sha256": sha(MR / "reviews/M2-review-18/TASK-AI-PILOT-CORRECTION-AND-CONTINUATION.md")},
                   "review_18": {"file": posix(MR / "reviews/M2-review-18/REVIEW-18-REPORT.md"), "sha256": sha(MR / "reviews/M2-review-18/REVIEW-18-REPORT.md")},
                   "allowance": "no new 150: the residual of the original aggregate (reconciled below)"},
 "code": {"accepted_app": {"commit": ACC_COMMIT, "tree": posix(ACC), "clean": True},
          "submitted_baseline": {"commit": SUB_BASE, "evidence_reader_sha256": "ae66397826d12714de44746765b2c5daf8a86b7619a3bdd172c1197845eb4335"},
          "successor": {"repository": "C:/t/iso/ep-platform (scratch clone; not the owner repository)", "tree": posix(SUC), "commit": SUC_COMMIT,
                        "parent": SUB_BASE, "changed_files_vs_accepted": {f: sha(SUC / f) for f in changed},
                        "diff_vs_e5a0a94_sha256": hashlib.sha256(subprocess.run(["git", "-C", str(SUC), "diff", "--binary", SUB_BASE, SUC_COMMIT], capture_output=True).stdout).hexdigest()},
          "evaluator": pdecl["code"]["evaluator"], "boq_harness_r16": pdecl["code"]["boq_harness_r16"], "boq_queue_sha256": sha(A / "boq_queue.py"),
          "xtrack": sha("C:/t/iso/work/r2x/run/xtrack.py"), "dry_provider": sha(A / "dry_provider.py"),
          "scripts": {f: sha(R / f) for f in RUNNERS if (R / f).exists()}},
 "offline_tests": {"files": {f.name: sha(f) for f in sorted((R / "tests-out").iterdir()) if f.is_file()},
                   "summary": {"focused modules (15) flags off / G / T": "246 / 246 / 246 passed (the three T failures of e5a0a94 now pass on their semantic end conditions)",
                               "focused, T+E with the whole-sheet frame shim (tests/_e_frame_shim.py)": "246 passed",
                               "focused, T+E without the shim": "227 passed, 19 failed: every failure is an existing persisted-stage test scripting discovery "
                                                                "regions in the WHOLE page's frame on an A2 drawing sheet; with the shim (the located area = the whole "
                                                                "sheet, nothing else changed) all 246 pass -- frame dependence of the scripts, not an E defect",
                               "r16.1 BOQ harness / allowance / overlay / association tests": "66 passed", "BOQ queue tests": "8 passed",
                               "reviewer probes on the successor": "all four as required (probes/on-successor)"}},
 "arms": arms, "doc_arms": ["S", "T2"],
 "expected_call_order": {
     "S": "per triggered page: discover_page (full page, 1600 px) -> read_identity -> read_revision -> read_decision (when discovery shows a block)",
     "T2": "per document: every triggered page's required reads first -- discover_region (drawing sheet: located title-block crop, <= 1568 px) or "
           "discover_page (other pages) -> read_identity -> read_revision -> read_decision -- then, page by page, the optional "
           "read_field_context (identity, then revision) only where a proposed own field is not validated and no failure / refusal / "
           "budget stop preceded it; every request's timeout = min(300 s, the job's remaining time); none started with < 20 s left"},
 "sources": {"sample": {"file": "CONTINUATION-SAMPLE.json", "sha256": sha(R / "CONTINUATION-SAMPLE.json"),
                        "documents": {d["doc_key"]: d["sha256"] for d in sample["documents"]},
                        "roles": {d["doc_key"]: d["role"] for d in sample["documents"]}},
             "boq_sheet": {"doc_key": H06_KEY, "sha256": H06_SHA, "staged_path": H06_PATH, "cohort": cohort["8430"]},
             "boq_extraction_A": {"file": "C:/t/iso/work/r2x/boq/holdout-A-r12-extraction.json", "sha256": sha("C:/t/iso/work/r2x/boq/holdout-A-r12-extraction.json")},
             "h06_labels": {"file": "C:/t/iso/work/r2x/labels/r14/BOQ-LABELS.amended-r14.1.json", "sha256": sha("C:/t/iso/work/r2x/labels/r14/BOQ-LABELS.amended-r14.1.json"),
                            "verified_geometry": "the four H-06 row positions verified by byte-identical crop regeneration (Review 14), used by the r16.1 join",
                            "use": "EVALUATION ONLY -- never in the prompt, the queue or the selection"}},
 "stage": {"root": "C:/t/r2x/cont-stage", "manifest": "CONT-STAGE.json", "manifest_sha256": sha("C:/t/r2x/cont-stage/CONT-STAGE.json")},
 "labels": {"dir": "labels-continuation", "register": "CONT-REGISTER-LABELS.json", "page": "CONT-PAGE-LABELS.json",
            "uncertainty": "CONT-UNCERTAINTY-AND-EXPOSURE.json", "files": {n: sha(LBL / n) for n in ("CONT-REGISTER-LABELS.json", "CONT-PAGE-LABELS.json", "CONT-UNCERTAINTY-AND-EXPOSURE.json")},
            "v2": {n: sha(R / "labels-v2" / n) for n in ("PILOT-REGISTER-LABELS.v2.json", "PILOT-PAGE-LABELS.v2.json", "PILOT-UNCERTAINTY-AND-EXPOSURE.v2.json", "LABEL-CHANGES-v2.json")},
            "status": "controls: v2 (v1 + Review 18 AI source review of four pages); new: Claude-drafted before prediction; PROVISIONAL",
            "resolved_for_stop_rule": "confidence 'high' and no uncertainty entry"},
 "provider": pdecl["provider"], "application_limits": limits,
 "ledger": {"file": LEDGER, "reconciliation": {"pilot_settled_by_scope": settled, "pilot_open_reservations": open_res,
                                               "pilot_refused_not_requests": refused, "used_of_150": used, "residual": residual},
            "scopes": scopes, "subcaps": CAPS, "sum_subcaps": sum(CAPS.values()),
            "closed_scope": "ai-pilot-2026-09-30-T stays closed by its breaker; it is not resumed, reset or renamed",
            "token_contract": "total reported input INCLUDING cached input (the existing breaker, 70,000 per request); cached / uncached shown as diagnostics only",
            "enforcement": {"requests": "hard, reserved before dispatch", "elapsed": "hard for new requests (ledger 14,400 s; job 120 s)",
                            "tokens": "estimate + breaker after completion (CLI), NOT provider-enforced", "in_flight": "a running CLI request is killed at its "
                            "timeout (subprocess timeout; its usage is then unknown and charged at the estimate); a grandchild process of a CLI wrapper may outlive the kill"}},
 "project_day": {"limit": 60, "reconciled_at_declaration": usage_now, "arm_shares": "after the continuation A base: share(ep) = floor((60 - used(ep)) / 2) for S and T2",
                 "h06": "EP-8430 is 60/60 in its rolling window at declaration; the H-06 runner refuses to start until 12 fit (EP-8430 calls expire 2026-09-30 "
                        "18:52:31-19:00:02 UTC: 12 fit from 18:53:57 UTC, 24 from 18:55:21 UTC)"},
 "pricing": "unknown (no valid price configured): cost UNKNOWN, never zero",
 "cache_mode": "application result cache ON; new sandboxes: cont-A (new), S and T2 each from a WAL-consistent copy of cont-A (and a copy of its file caches); "
               "arms have different policy / reader / prompt identities, so no cross-arm reuse; no pilot evidence (G or T) is loaded into a continuation arm",
 "offline_replays": "labelled OFFLINE and separate: the reviewer probes on e5a0a94 and the successor; the stored pilot results under labels v1 / v2; the "
                    "confirmed Rev.0 acceptance through the guard; the locator evaluation. None is a new model result.",
 "run_order": ["cont-A: cont_a.py", "cont_shares.py", "S: cont_ev.py S", "T2: cont_ev.py T2", "H-06 BOQ-S: cont_boq.py S (when EP-8430 fits)", "H-06 BOQ-T: cont_boq.py T (when EP-8430 fits)"],
 "stop_rules": ["an evaluator-flagged critical acceptance by the arm's AI on a RESOLVED label (checked after each project): stop the arm",
                "three consecutive provider failures", "a breaker or any ledger / project-day / share / per-document refusal: a budget stop, recorded, never raised",
                "an undeclared source, changed hash, sealed project, existing sandbox or changed declaration: the runner refuses"],
 "evaluation": {"documents": "scripts.m2_eval5 (evaluator .9, unchanged) on the continuation labels; contexts {EV1, default, the arm's policy}",
                "report": ["precision numerator / denominator", "correctly associated recovery", "held evidence", "false accepts", "budget / timeout / not-attempted",
                           "latency and requests per task (discovery timing: S vs T2, and S's pilot timings for the controls)", "complete planned coverage and the matched completed subset"],
                "h06": "r16.1 replay_core + boq_contract (unchanged) with the r14.1 amended labels and the verified geometry; the three wrong-quantity targets and the "
                       "control are identified in the evaluation only; reached / unreached rows; comparison at equal requests and at each arm's cap"},
}
p = pathlib.Path("C:/t/r2x/dry-runs/CONT-DECLARATION.dry.json") if DRY else R / "CONT-DECLARATION.json"
if not DRY and p.exists():
    sys.exit("the declaration is frozen")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(decl, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("declaration", p, sha(p))
print({k: (v["identities"]["READER_VERSION"], v["identities"]["EVIDENCE_POLICY_VERSION"]) for k, v in arms.items()})
print("residual", residual, "caps", CAPS, "usage", usage_now)
