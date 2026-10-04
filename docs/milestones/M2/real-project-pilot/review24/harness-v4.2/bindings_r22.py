"""Frozen bindings of the review22 package (read-only): the harness v4 source hashes and contract / scorer / runner
versions (FROZEN-HARNESS.json), the accepted / reviewed / frozen R21 candidate trees (unchanged: no application change in
this task), the reviewed r16.1 durable-allowance module, the Review 22 reviewer files (byte copies hash-checked, never
written), the R21 package inputs this package builds on (sample, stage, labels manifest, R21 workload), the dry stage /
labels / declaration, and the earlier packages' manifests. Writes bindings/SOURCE-BINDINGS.json and bindings/FROZEN-HARNESS.json."""
import hashlib
import json
import pathlib
import subprocess

R = pathlib.Path("C:/t/iso/work/r2x/review22")
H = R / "harness-v4"
R21 = pathlib.Path("C:/t/iso/work/r2x/review21")
PKG21 = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review21")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True, check=True).stdout.strip()
FROZEN = "719e8de661b8b10427ef6cff5d2d277a53b64dc6"
for t, c in (("C:/t/iso/frozen-r12", "3d5607d99fcebf08ac45f5df937ad615ecc16fb3"), ("C:/t/iso/cand-ai3", "69ee75937bf190a0bf605dc0b79eecf29b0f3dc6"), ("C:/t/iso/cand-ai4", FROZEN)):
    assert git(t, "rev-parse", "HEAD") == c and not git(t, "status", "--porcelain"), t
HARNESS_FILES = ["coverage_v4.py", "score_arms_v4.py", "arm_ev.py", "arm_a.py", "dry_provider2.py", "xtrack2.py", "schedule_sim.py", "workload_r22.py", "declare_r22.py",
                 "make_dry_stage_r22.py", "dry_labels_r22.py", "runner_probes.py", "test_harness_v4.py", "test_runner_v4.py", "patch_probe_fixes.py", "patch_probe_fixes_2.py",
                 "replay_deltas.py", "run_canonical_chain.sh", "bindings_r22.py"]
import sys  # noqa: E402
sys.path.insert(0, str(H))
import coverage_v4, score_arms_v4  # noqa: E402
arm_src = (H / "arm_ev.py").read_text(encoding="utf-8")
runner_version = next(l.split("=")[1].strip().strip('"') for l in arm_src.splitlines() if l.startswith("RUNNER_VERSION ="))
frozen = {"harness": "harness-v4", "contract_version": coverage_v4.CONTRACT_VERSION, "scorer_version": score_arms_v4.SCORER_VERSION, "runner_version": runner_version,
          "scheduling_rule_version": "whole-project-reservation-2026-09-30.v4", "files": {f: sha(H / f) for f in HARNESS_FILES},
          "durable_allowance_module": {"file": "C:/t/iso/work/r2x/r16/boq_harness.py", "sha256": sha("C:/t/iso/work/r2x/r16/boq_harness.py"), "reviewed_in": "review16 (r16.1)"},
          "labels_dry_r22": {n: sha(R / "labels-dry-r22" / n) for n in ("DRY-REGISTER-LABELS.json", "DRY-PAGE-LABELS.json", "DRY-UNCERTAINTY-AND-EXPOSURE.json")},
          "dry_stage_manifest": sha("C:/t/r2x/dry-runs/r22-stage/R22-DRY-STAGE.json"), "dry_declaration": sha("C:/t/r2x/dry-runs/r22/R22-DECLARATION.dry.json"),
          "evaluator": {"file": "C:/t/iso/frozen-r12/backend/scripts/m2_eval5.py", "sha256": sha("C:/t/iso/frozen-r12/backend/scripts/m2_eval5.py")}}
rev = MR / "reviews/M2-review-22"
reviewer = {p.name: sha(p) for p in sorted(rev.iterdir()) if p.is_file()}
copies = {p.name: sha(p) for p in sorted((R / "repro/reviewer-copy").iterdir()) if p.is_file()}
out = {"accepted": {"commit": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3", "tree": "C:/t/iso/frozen-r12", "clean": True},
       "reviewed_r19_candidate": {"commit": "69ee75937bf190a0bf605dc0b79eecf29b0f3dc6", "tree": "C:/t/iso/cand-ai3", "clean": True},
       "frozen_r21_candidate": {"commit": FROZEN, "tree": "C:/t/iso/cand-ai4", "clean": True, "unchanged_in_this_task": True,
                                "evidence_reader_sha256": sha("C:/t/iso/cand-ai4/backend/app/ai/evidence_reader.py"),
                                "r21_report_prose_id_correction": "review21/CORRECTION-AND-PREP-REPORT.md section 1 printed the stale short ID 58ff6fc; the frozen commit was and is 719e8de (candidate/FROZEN-COMMIT.txt and bindings in that package); the R21 package is not altered"},
       "application_change": "none (harness, tests and documents only)",
       "harness_v4": frozen,
       "submitted_r21_harness": {f: sha(R / "harness-r21" / f) for f in ("coverage_v3.py", "score_arms_v3.py", "arm_ev.py", "arm_a.py", "arm_shares.py", "test_harness_v3.py", "test_coverage_v3_draft_compat.py")},
       "submitted_r21_harness_equals_package": all(sha(R / "harness-r21" / f) == sha(PKG21 / "scripts" / f) for f in ("coverage_v3.py", "score_arms_v3.py", "arm_ev.py", "arm_a.py", "arm_shares.py")),
       "reviewer_files_review22": reviewer, "reviewer_copies_hash_checked": copies, "reviewer_copies_match": all(reviewer.get(n) == h for n, h in copies.items()),
       "r21_inputs": {"sample": sha(R21 / "R21-SAMPLE.json"), "page_classes": sha(R21 / "R21-PAGE-CLASSES.json"), "stage_manifest": sha("C:/t/r2x/r21-stage/R21-STAGE.json"),
                      "labels_r21_files": {p.name: sha(p) for p in sorted((R21 / "labels-r21").glob("*.json"))}, "r21_workload": sha(R21 / "workload/R21-WORKLOAD.json"),
                      "r21_draft_declaration": sha(R21 / "R21-DECLARATION.draft.json"), "r21_dry_declaration": sha("C:/t/r2x/dry-runs/R21-DECLARATION.dry.json")},
       "h06_control_binding_unchanged": {"declaration": "C:/t/iso/work/r2x/ai-pilot-r18/CONT-DECLARATION.json", "sha256": sha("C:/t/iso/work/r2x/ai-pilot-r18/CONT-DECLARATION.json"),
                                         "scorer": sha("C:/t/iso/work/r2x/ai-pilot-r18/score_cont.py"), "runner": sha("C:/t/iso/work/r2x/ai-pilot-r18/cont_boq.py")},
       "earlier_package_manifests": {pk: sha(PKG21.parent / pk / "evidence/EVIDENCE-MANIFEST.json") for pk in
                                     ("review13", "review14", "review15", "review16", "ai-accuracy-pilot", "ai-pilot-r18-correction", "review19", "review20", "review21")},
       "workload_v2": sha(R / "workload/R22-WORKLOAD.json") if (R / "workload/R22-WORKLOAD.json").exists() else None,
       "draft_declaration_v2": sha(R / "R22-DECLARATION.draft.json") if (R / "R22-DECLARATION.draft.json").exists() else None}
(R / "bindings").mkdir(exist_ok=True)
(R / "bindings/SOURCE-BINDINGS.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
(R / "bindings/FROZEN-HARNESS.json").write_text(json.dumps(frozen, indent=1) + "\n", encoding="utf-8")
print("frozen harness", frozen["contract_version"], frozen["scorer_version"], frozen["runner_version"], "| reviewer copies match", out["reviewer_copies_match"], "| r21 harness equals package", out["submitted_r21_harness_equals_package"])
