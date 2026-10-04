"""Frozen bindings of the review23 package: the harness v4.1 source hashes and versions (FROZEN-HARNESS.json; the scoring
files are byte-identical to the frozen v4 of review22), the unchanged trees (no application change), the r16.1 allowance
module, the Review 23 reviewer files (hash-checked, never written), the review22 package's frozen harness, and the earlier
packages' manifests. Writes bindings/SOURCE-BINDINGS.json and bindings/FROZEN-HARNESS.json."""
import hashlib
import json
import pathlib
import subprocess
import sys

R = pathlib.Path("C:/t/iso/work/r2x/review23")
H = R / "harness-v4.1"
PKG22 = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review22")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True, check=True).stdout.strip()
FROZEN = "719e8de661b8b10427ef6cff5d2d277a53b64dc6"
for t, c in (("C:/t/iso/frozen-r12", "3d5607d99fcebf08ac45f5df937ad615ecc16fb3"), ("C:/t/iso/cand-ai3", "69ee75937bf190a0bf605dc0b79eecf29b0f3dc6"), ("C:/t/iso/cand-ai4", FROZEN)):
    assert git(t, "rev-parse", "HEAD") == c and not git(t, "status", "--porcelain"), t
FILES = sorted(p.name for p in H.iterdir() if p.is_file() and p.suffix in (".py", ".sh"))
sys.path.insert(0, str(H))
import coverage_v4, score_arms_v4  # noqa: E402
src = (H / "arm_ev.py").read_text(encoding="utf-8")
ver = lambda key: next(l.split("=", 1)[1].strip().split("#")[0].strip().strip('"') for l in src.splitlines() if l.startswith(key + " ="))
v22 = json.loads((PKG22 / "bindings/FROZEN-HARNESS.json").read_text(encoding="utf-8"))
unchanged = {f: sha(H / f) == v22["files"].get(f) for f in ("coverage_v4.py", "score_arms_v4.py", "xtrack2.py", "schedule_sim.py", "arm_a.py", "workload_r22.py", "declare_r22.py", "test_harness_v4.py")}
frozen = {"harness": "harness-v4.1", "contract_version": coverage_v4.CONTRACT_VERSION, "scorer_version": score_arms_v4.SCORER_VERSION, "runner_version": ver("RUNNER_VERSION"),
          "lifecycle_contract": ver("LIFECYCLE_CONTRACT"), "scheduling_rule_version": "whole-project-reservation-2026-09-30.v4", "files": {f: sha(H / f) for f in FILES},
          "changed_vs_review22_v4": [f for f in FILES if v22["files"].get(f) not in (None, sha(H / f))], "new_vs_review22_v4": [f for f in FILES if f not in v22["files"]],
          "scoring_files_unchanged_vs_review22": unchanged,
          "durable_allowance_module": {"file": "C:/t/iso/work/r2x/r16/boq_harness.py", "sha256": sha("C:/t/iso/work/r2x/r16/boq_harness.py")},
          "evaluator": {"file": "C:/t/iso/frozen-r12/backend/scripts/m2_eval5.py", "sha256": sha("C:/t/iso/frozen-r12/backend/scripts/m2_eval5.py")}}
rev = MR / "reviews/M2-review-23"
reviewer = {p.name: sha(p) for p in sorted(rev.iterdir()) if p.is_file()}
copies = {p.name: sha(p) for p in sorted((R / "repro/reviewer-copy").iterdir()) if p.is_file() and p.name != "SHA256SUMS.txt"}
out = {"accepted": {"commit": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3", "tree": "C:/t/iso/frozen-r12", "clean": True},
       "reviewed_r19_candidate": {"commit": "69ee75937bf190a0bf605dc0b79eecf29b0f3dc6", "tree": "C:/t/iso/cand-ai3", "clean": True},
       "frozen_r21_candidate": {"commit": FROZEN, "tree": "C:/t/iso/cand-ai4", "clean": True, "unchanged_in_this_task": True, "evidence_reader_sha256": sha("C:/t/iso/cand-ai4/backend/app/ai/evidence_reader.py")},
       "application_change": "none (harness runner lifecycle, tests and documents only)",
       "harness_v4_1": frozen, "review22_frozen_harness": {"sha256_of_file": sha(PKG22 / "bindings/FROZEN-HARNESS.json"), "runner_version": v22["runner_version"], "arm_ev_sha256": v22["files"]["arm_ev.py"]},
       "reviewer_files_review23": reviewer, "reviewer_copies_hash_checked": copies, "reviewer_copies_match": all(reviewer.get(n) == h for n, h in copies.items()),
       "reviewer_arm_ev_equals_review22_frozen": reviewer.get("arm_ev.py") == v22["files"]["arm_ev.py"],
       "h06_control_binding_unchanged": {"declaration": "C:/t/iso/work/r2x/ai-pilot-r18/CONT-DECLARATION.json", "sha256": sha("C:/t/iso/work/r2x/ai-pilot-r18/CONT-DECLARATION.json"),
                                         "scorer": sha("C:/t/iso/work/r2x/ai-pilot-r18/score_cont.py"), "runner": sha("C:/t/iso/work/r2x/ai-pilot-r18/cont_boq.py")},
       "earlier_package_manifests": {pk: sha(PKG22.parent / pk / "evidence/EVIDENCE-MANIFEST.json") for pk in
                                     ("review13", "review14", "review15", "review16", "ai-accuracy-pilot", "ai-pilot-r18-correction", "review19", "review20", "review21", "review22")},
       "labels_r21_files": {p.name: sha(p) for p in sorted((PKG22.parent / "review21/labels-r21").glob("*.json"))},
       "dry_inputs_unchanged": {"r22_dry_declaration": sha("C:/t/r2x/dry-runs/r22/R22-DECLARATION.dry.json") == v22["dry_declaration"], "r22_dry_stage": sha("C:/t/r2x/dry-runs/r22-stage/R22-DRY-STAGE.json") == v22["dry_stage_manifest"],
                               "labels_dry_r22": all(sha(PKG22 / "labels-dry-r22" / n) == h for n, h in v22["labels_dry_r22"].items())}}
(R / "bindings").mkdir(exist_ok=True)
(R / "bindings/SOURCE-BINDINGS.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
(R / "bindings/FROZEN-HARNESS.json").write_text(json.dumps(frozen, indent=1) + "\n", encoding="utf-8")
print("runner", frozen["runner_version"], "lifecycle", frozen["lifecycle_contract"], "| changed vs v4:", frozen["changed_vs_review22_v4"], "| new:", frozen["new_vs_review22_v4"],
      "| scoring unchanged", all(unchanged.values()), "| reviewer copies match", out["reviewer_copies_match"], "| reviewer arm_ev == v4 frozen", out["reviewer_arm_ev_equals_review22_frozen"])
