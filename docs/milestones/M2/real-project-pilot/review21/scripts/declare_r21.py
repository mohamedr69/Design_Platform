"""The four-arm declaration writer. PILOT_DRY=1: a DRY declaration over the synthetic stage (scripted provider; harness
plumbing only). Otherwise: the DRAFT declaration (marked NOT EXECUTED / NO NEW MODEL BUDGET APPROVED) bound to the
frozen sample, labels and workload -- never run by this task. No model request here."""
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys

R = pathlib.Path("C:/t/iso/work/r2x/review21")
A = pathlib.Path("C:/t/iso/work/r2x/ai-pilot")
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
ACC, SUC = pathlib.Path("C:/t/iso/frozen-r12"), pathlib.Path("C:/t/iso/cand-ai4")
DRY = os.environ.get("PILOT_DRY") == "1"
PY = sys.executable
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
posix = lambda p: str(p).replace("\\", "/")
git = lambda t, *a: subprocess.run(["git", "-C", str(t), *a], capture_output=True, text=True, check=True).stdout.strip()
ACC_COMMIT = "3d5607d99fcebf08ac45f5df937ad615ecc16fb3"
SUC_COMMIT = git(SUC, "rev-parse", "HEAD")
assert git(ACC, "rev-parse", "HEAD") == ACC_COMMIT and not git(ACC, "status", "--porcelain") and not git(SUC, "status", "--porcelain")
pdecl = json.loads((A / "PILOT-DECLARATION.json").read_text(encoding="utf-8"))
limits = pdecl["application_limits"]
os.environ.update({"AI_ENABLED": "false", "DATABASE_URL": "sqlite:///C:/t/iso/tmp/declare-no-db.db"})
KEYS = ("READER_VERSION", "EVIDENCE_POLICY_VERSION", "SCHEMA_VERSION", "PROMPTS", "AUDIT_RATE", "AUDIT_SEED", "MAX_PAGES_PER_DOCUMENT", "MAX_CALLS_PER_DOCUMENT",
        "GUARD_ENABLED", "TARGETED_ENABLED", "EFFICIENT_ENABLED", "SUPPORT_V2", "REQUIRED_FIRST", "DEADLINE_ENABLED", "ROI_ENABLED")


def identities(env):
    base = {k: v for k, v in os.environ.items() if not k.startswith("AI_EVIDENCE_")}
    code = f"import json,sys; sys.path.insert(0,'.'); from app.ai import evidence_reader as er; print(json.dumps({{k: getattr(er, k, None) for k in {KEYS!r}}}))"
    out = subprocess.run([PY, "-c", code], cwd=str(SUC / "backend"), env={**base, **env}, capture_output=True, text=True, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


COMMON = {"AI_EVIDENCE_VARIANT": "EV1", "AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_SUPPORT": "v2", "AI_EVIDENCE_SCHEDULING": "required_first", "AI_EVIDENCE_DEADLINE": "1"}
ARM_ENV = {"L1": {}, "L2": {"AI_EVIDENCE_ROI": "1"}, "L3": {"AI_EVIDENCE_TARGETED": "1"}, "L4": {"AI_EVIDENCE_ROI": "1", "AI_EVIDENCE_TARGETED": "1"}}
MEANING = {"L1": "whole-page discovery, X off", "L2": "title-block (ROI) discovery, X off", "L3": "whole-page discovery, X on", "L4": "ROI discovery, X on"}
arms = {}
for k, e in ARM_ENV.items():
    env = {**COMMON, **e}
    ids = identities(env)
    assert ids["GUARD_ENABLED"] and ids["SUPPORT_V2"] and ids["REQUIRED_FIRST"] and ids["DEADLINE_ENABLED"] and not ids["EFFICIENT_ENABLED"]
    assert ids["ROI_ENABLED"] == ("AI_EVIDENCE_ROI" in e) and ids["TARGETED_ENABLED"] == ("AI_EVIDENCE_TARGETED" in e)
    arms[k] = {"meaning": MEANING[k], "tree": posix(SUC), "commit": SUC_COMMIT, "env": env, "identities": ids}
assert len({(v["identities"]["READER_VERSION"], v["identities"]["EVIDENCE_POLICY_VERSION"]) for v in arms.values()}) == 4
off = identities({})
assert (off["READER_VERSION"], off["EVIDENCE_POLICY_VERSION"]) == ("evidence-reader-2026-09-29.7", "evidence-policy-2026-09-29.4"), "flags off != accepted"

if DRY:
    stage_root = pathlib.Path("C:/t/r2x/dry-runs/r21-stage")
    stage = json.loads((stage_root / "R21-DRY-STAGE.json").read_text(encoding="utf-8"))
    labels_dir, lab = "labels-dry", ("DRY-REGISTER-LABELS.json", "DRY-PAGE-LABELS.json", "DRY-UNCERTAINTY-AND-EXPOSURE.json")
    planned = [{"doc": f["doc_key"], "sha256": f["sha256"], "pages": f["pages"], "extension": f["extension"]} for f in stage["files"]]
    caps = {"A": 4, "L1": 30, "L2": 30, "L3": 30, "L4": 30}
    status = "DRY-RUN DECLARATION (scripted provider over a SYNTHETIC stage; harness plumbing only) -- not an experiment"
else:
    stage_root = pathlib.Path("C:/t/r2x/r21-stage")
    stage = json.loads((stage_root / "R21-STAGE.json").read_text(encoding="utf-8"))
    labels_dir, lab = "labels-r21", ("R21-REGISTER-LABELS.json", "R21-PAGE-LABELS.json", "R21-UNCERTAINTY-AND-EXPOSURE.json")
    planned = [{"doc": f["doc_key"], "sha256": f["sha256"], "pages": f["pages"], "extension": f["extension"]} for f in stage["files"]]
    work = json.loads((R / "workload/R21-WORKLOAD.json").read_text(encoding="utf-8"))
    caps = work["proposed_caps"]
    status = "DRAFT / NOT EXECUTED / NO NEW MODEL BUDGET APPROVED -- a proposal for the owner's budget decision; nothing in it may run before authorization"
LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"
COMMONL = {"per_request_input": 70000, "per_request_output": 20000, "input_tokens": 4000000, "output_tokens": 600000, "elapsed_s": 14400}
scopes = {k: {"scope": f"r21-four-arm-{'dry-' if DRY else ''}2026-09-30-{k}", "limits": dict(COMMONL, requests=v),
              "env": {"AI_LEDGER_PATH": LEDGER, "AI_LEDGER_SCOPE": f"r21-four-arm-{'dry-' if DRY else ''}2026-09-30-{k}", "AI_LEDGER_LIMITS": json.dumps(dict(COMMONL, requests=v))}}
          for k, v in caps.items()}
sel = json.loads((PILOT / "review06/evidence/round2/ROUND2-SELECTION.json").read_text(encoding="utf-8"))
cohort = {str(p["ep"]): str(p.get("cohort")) for p in sel["projects"]}
projects = sorted({p["doc"].split("/")[0][3:] for p in planned})
assert all("sealed" not in cohort.get(p, "sealed?") for p in projects), projects
decl = {
    "declared_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "name": "four-arm isolated accuracy experiment (R21)",
    "status": status, "executed": False, "new_model_budget_approved": False,
    "authorization": {"document": posix(MR / "OWNER-AI-PERMISSION-ROUND2.md"), "sha256": sha(MR / "OWNER-AI-PERMISSION-ROUND2.md"),
                      "scope_note": "the recorded Round 2 permission covers the cohort / provider; a NEW request allowance is required and NOT granted by this declaration",
                      "projects_resolved": {p: cohort.get(p) for p in projects}, "sealed": "not opened"},
    "code": {"accepted_app": {"commit": ACC_COMMIT, "tree": posix(ACC)}, "successor": {"commit": SUC_COMMIT, "tree": posix(SUC), "parent": "69ee75937bf190a0bf605dc0b79eecf29b0f3dc6",
             "evidence_reader_sha256": sha(SUC / "backend/app/ai/evidence_reader.py")},
             "evaluator": pdecl["code"]["evaluator"], "coverage_scorer": {"file": "score_arms_v3.py", "sha256": sha(R / "score_arms_v3.py"), "coverage_v3_sha256": sha(R / "coverage_v3.py")},
             "runners": {f: sha(R / f) for f in ("arm_a.py", "arm_shares.py", "arm_ev.py")}, "dry_provider": sha(A / "dry_provider.py"), "xtrack": sha("C:/t/iso/work/r2x/run/xtrack.py")},
    "arms": arms, "doc_arms": ["L1", "L2", "L3", "L4"], "common": {"G": True, "support": "v2 (rotation-correct clip + bounded local OCR)", "scheduling": "required_first",
                                                                   "deadline": "min(provider timeout, remaining job time); 20 s floor; OCR bound"},
    "pairs": {"ROI alone": ["L1", "L2"], "X on whole page": ["L1", "L3"], "X on ROI": ["L2", "L4"], "ROI under X": ["L3", "L4"]},
    "offline_replays": "on each arm's own captured responses: P0 (guard off, accepted text) -> P1 (+guard) -> P2 (+rotation clip) -> P3 (+local OCR): conditional "
                       "field-value re-validation on fixed responses, never a replay of requests, images, scheduling or deadlines",
    "expected_call_order": {"all arms": "per triggered page: discover_page (L1/L3) or discover_region (L2/L4) -> read_identity -> read_revision -> read_decision (when a block "
                            "was discovered); then, L3/L4 only, page by page: read_field_context for own identity, then revision, when not validated and no failure / refusal preceded"},
    "sources": {"stage": {"root": posix(stage_root), "manifest": stage_root.name and ("R21-DRY-STAGE.json" if DRY else "R21-STAGE.json"), "manifest_sha256": sha(stage_root / ("R21-DRY-STAGE.json" if DRY else "R21-STAGE.json"))},
                "sample": {"documents": {p["doc"]: p["sha256"] for p in planned}, "documents_planned": planned, "n_planned": len(planned)}},
    "stage": {"root": posix(stage_root), "manifest": "R21-DRY-STAGE.json" if DRY else "R21-STAGE.json", "manifest_sha256": sha(stage_root / ("R21-DRY-STAGE.json" if DRY else "R21-STAGE.json"))},
    "labels": {"dir": labels_dir, "register": lab[0], "page": lab[1], "uncertainty": lab[2], "files": {n: sha(R / labels_dir / n) for n in lab}},
    "provider": pdecl["provider"], "application_limits": limits,
    "ledger": {"file": LEDGER, "scopes": scopes, "caps": caps, "sum_caps": sum(caps.values()),
               "note": "a NEW scope family; the original 150-request experiment's residual is not used; nothing here is reserved until authorized"},
    "project_day": {"limit": 60, "rule": "after A: share(ep) = floor((60 - used(ep)) / 4) per arm; the worst-case schedule is in the workload table"},
    "stop_rules": ["critical acceptance by the arm's AI on a resolved label: stop the arm", "three consecutive provider failures", "any breaker / ledger / share / cap refusal: a budget stop, never raised",
                   "undeclared source, changed hash, sealed project, existing sandbox, changed declaration: refuse to start"],
    "cache_mode": "result cache on; arms start from copies of one A base; distinct reader / policy / prompt identities per arm: no cross-arm reuse",
}
if not DRY:
    decl["sample_rule"] = json.loads((R / "R21-SAMPLE.json").read_text(encoding="utf-8"))["rule"]
    decl["workload"] = work
p = pathlib.Path("C:/t/r2x/dry-runs/R21-DECLARATION.dry.json") if DRY else R / "R21-DECLARATION.draft.json"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(decl, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("declaration", p, sha(p))
for k, v in arms.items():
    print(k, v["identities"]["READER_VERSION"], "|", v["identities"]["EVIDENCE_POLICY_VERSION"])
