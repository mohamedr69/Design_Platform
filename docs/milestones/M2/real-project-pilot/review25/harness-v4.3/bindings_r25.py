"""Frozen bindings of the review25 package, written BEFORE the final validation: the harness v4.3 source hashes and versions
(FROZEN-HARNESS.json; the scoring files are byte-identical to review22's frozen v4, the delta is against review24's v4.2), the unchanged trees (no application change), the r16.1 allowance
module, the Review 23 reviewer files (hash-checked, never written), the review22 package's frozen harness, and the earlier
packages' manifests. Writes bindings/SOURCE-BINDINGS.json and bindings/FROZEN-HARNESS.json."""
import hashlib
import json
import pathlib
import subprocess
import sys

R = pathlib.Path("C:/t/iso/work/r2x/review25")
H = R / "harness-v4.3"
PKG22 = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review22")
PKG23 = PKG22.parent / "review24"   # the predecessor frozen harness (v4.2); name kept for the derived code
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
v23 = json.loads((PKG23 / "bindings/FROZEN-HARNESS.json").read_text(encoding="utf-8"))
unchanged = {f: sha(H / f) == v22["files"].get(f) for f in ("coverage_v4.py", "score_arms_v4.py", "xtrack2.py", "schedule_sim.py", "arm_a.py", "workload_r22.py", "declare_r22.py", "test_harness_v4.py")}
frozen = {"harness": "harness-v4.3", "frozen_before_final_validation": True, "journal_version": __import__("provider_journal").JOURNAL_VERSION, "validator_revision": __import__("provider_journal").VALIDATOR_REVISION, "contract_version": coverage_v4.CONTRACT_VERSION, "scorer_version": score_arms_v4.SCORER_VERSION, "runner_version": ver("RUNNER_VERSION"),
          "lifecycle_contract": ver("LIFECYCLE_CONTRACT"), "scheduling_rule_version": "whole-project-reservation-2026-09-30.v4", "files": {f: sha(H / f) for f in FILES},
          "changed_vs_review24_v4_2": [f for f in FILES if v23["files"].get(f) not in (None, sha(H / f))], "new_vs_review24_v4_2": [f for f in FILES if f not in v23["files"]],
          "arm_ev_unchanged_vs_v4_2": sha(H / "arm_ev.py") == v23["files"]["arm_ev.py"],
          "scoring_files_unchanged_vs_review22": unchanged,
          "durable_allowance_module": {"file": "C:/t/iso/work/r2x/r16/boq_harness.py", "sha256": sha("C:/t/iso/work/r2x/r16/boq_harness.py")},
          "evaluator": {"file": "C:/t/iso/frozen-r12/backend/scripts/m2_eval5.py", "sha256": sha("C:/t/iso/frozen-r12/backend/scripts/m2_eval5.py")}}
rev = MR / "reviews/M2-review-25"
reviewer = {p.name: sha(p) for p in sorted(rev.iterdir()) if p.is_file()}
copies = {p.name: sha(p) for p in sorted((R / "repro/reviewer-copy").iterdir()) if p.is_file() and p.name != "SHA256SUMS.txt" and not p.name.endswith(".r24.py")}
r24_copy_ok = sha(R / "repro/reviewer-copy/test_provider_boundary.r24.py") == sha(MR / "reviews/M2-review-24/test_provider_boundary.py")   # the original R24 regressions, from the Review 24 folder
out = {"accepted": {"commit": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3", "tree": "C:/t/iso/frozen-r12", "clean": True},
       "reviewed_r19_candidate": {"commit": "69ee75937bf190a0bf605dc0b79eecf29b0f3dc6", "tree": "C:/t/iso/cand-ai3", "clean": True},
       "frozen_r21_candidate": {"commit": FROZEN, "tree": "C:/t/iso/cand-ai4", "clean": True, "unchanged_in_this_task": True, "evidence_reader_sha256": sha("C:/t/iso/cand-ai4/backend/app/ai/evidence_reader.py")},
       "application_change": "none (harness journal validator, tests and documents only)",
       "harness_v4_2": frozen, "review22_frozen_harness": {"sha256_of_file": sha(PKG22 / "bindings/FROZEN-HARNESS.json"), "runner_version": v22["runner_version"]},
       "review24_frozen_harness": {"sha256_of_file": sha(PKG23 / "bindings/FROZEN-HARNESS.json"), "runner_version": v23["runner_version"], "arm_ev_sha256": v23["files"]["arm_ev.py"], "provider_journal_sha256": v23["files"]["provider_journal.py"]},
       "reviewer_files_review25": reviewer, "reviewer_copies_hash_checked": copies, "reviewer_copies_match": all(reviewer.get(n) == h for n, h in copies.items()) and r24_copy_ok, "r24_regressions_copy_matches_review24_folder": r24_copy_ok,
       "reviewer_runner_equals_review24_frozen": reviewer.get("arm_ev.py") == v23["files"]["arm_ev.py"] and reviewer.get("provider_journal.py") == v23["files"]["provider_journal.py"],
       "h06_control_binding_unchanged": {"declaration": "C:/t/iso/work/r2x/ai-pilot-r18/CONT-DECLARATION.json", "sha256": sha("C:/t/iso/work/r2x/ai-pilot-r18/CONT-DECLARATION.json"),
                                         "scorer": sha("C:/t/iso/work/r2x/ai-pilot-r18/score_cont.py"), "runner": sha("C:/t/iso/work/r2x/ai-pilot-r18/cont_boq.py")},
       "earlier_package_manifests": {pk: sha(PKG22.parent / pk / "evidence/EVIDENCE-MANIFEST.json") for pk in
                                     ("review13", "review14", "review15", "review16", "ai-accuracy-pilot", "ai-pilot-r18-correction", "review19", "review20", "review21", "review22", "review23", "review24")},
       "labels_r21_files": {p.name: sha(p) for p in sorted((PKG22.parent / "review21/labels-r21").glob("*.json"))},
       "dry_inputs_unchanged": {"r22_dry_declaration": sha("C:/t/r2x/dry-runs/r22/R22-DECLARATION.dry.json") == v22["dry_declaration"], "r22_dry_stage": sha("C:/t/r2x/dry-runs/r22-stage/R22-DRY-STAGE.json") == v22["dry_stage_manifest"],
                               "labels_dry_r22": all(sha(PKG22 / "labels-dry-r22" / n) == h for n, h in v22["labels_dry_r22"].items())}}
(R / "bindings").mkdir(exist_ok=True)
(R / "bindings/SOURCE-BINDINGS.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
(R / "bindings/FROZEN-HARNESS.json").write_text(json.dumps(frozen, indent=1) + "\n", encoding="utf-8")
print("runner", frozen["runner_version"], "validator", frozen["validator_revision"], "| changed vs v4.2:", frozen["changed_vs_review24_v4_2"], "| new:", frozen["new_vs_review24_v4_2"], "| arm_ev unchanged", frozen["arm_ev_unchanged_vs_v4_2"],
      "| scoring unchanged", all(unchanged.values()), "| reviewer copies match", out["reviewer_copies_match"], "| reviewer runner == v4.2 frozen", out["reviewer_runner_equals_review24_frozen"])
