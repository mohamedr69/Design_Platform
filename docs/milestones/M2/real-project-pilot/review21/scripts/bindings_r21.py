"""Frozen source bindings of the R21 package (read-only): accepted / reviewed (69ee759) / frozen R21 candidate commits and
file hashes, the candidate diff, the H-06 control binding (unchanged; the R21 reader is not bound into it), the sample /
stage / labels-manifest / workload / declaration hashes, and the Review 20 reviewer files. Writes bindings/SOURCE-BINDINGS.json
and candidate/69ee759-to-<frozen>.diff / .patch."""
import hashlib
import json
import pathlib
import subprocess

R = pathlib.Path("C:/t/iso/work/r2x/review21")
R18 = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True, check=True).stdout.strip()
SUC = "C:/t/iso/cand-ai4"
frozen = (R / "FROZEN-COMMIT.txt").read_text().strip()
assert git(SUC, "rev-parse", "HEAD") == frozen and not git(SUC, "status", "--porcelain")
assert git("C:/t/iso/cand-ai3", "rev-parse", "HEAD") == "69ee75937bf190a0bf605dc0b79eecf29b0f3dc6" and not git("C:/t/iso/cand-ai3", "status", "--porcelain")
assert git("C:/t/iso/frozen-r12", "rev-parse", "HEAD") == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3" and not git("C:/t/iso/frozen-r12", "status", "--porcelain")
(R / "pkg-src/candidate").mkdir(parents=True, exist_ok=True)
diff = subprocess.run(["git", "-C", SUC, "diff", "--binary", "69ee759", frozen], capture_output=True).stdout
(R / f"pkg-src/candidate/69ee759-to-{frozen[:7]}.diff").write_bytes(diff)
(R / f"pkg-src/candidate/{frozen[:7]}.patches").write_bytes(subprocess.run(["git", "-C", SUC, "format-patch", "--stdout", f"69ee759..{frozen}"], capture_output=True).stdout)
changed = git(SUC, "diff", "--name-only", "69ee759", frozen).splitlines()
app_changed = [f for f in changed if not f.startswith("backend/tests/")]
assert app_changed == ["backend/app/ai/evidence_reader.py"], app_changed
decl = json.loads((R18 / "CONT-DECLARATION.json").read_text(encoding="utf-8"))
out = {"accepted": {"commit": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3", "tree": "C:/t/iso/frozen-r12", "clean": True},
       "reviewed_r19_candidate": {"commit": "69ee75937bf190a0bf605dc0b79eecf29b0f3dc6", "tree": "C:/t/iso/cand-ai3", "clean": True},
       "frozen_r21_candidate": {"commit": frozen, "tree": SUC, "branch": git(SUC, "rev-parse", "--abbrev-ref", "HEAD"), "parent": "69ee75937bf190a0bf605dc0b79eecf29b0f3dc6",
                                "clean": True, "changed_files": {f: sha(f"{SUC}/{f}") for f in changed}, "application_files_changed": app_changed,
                                "diff_sha256": hashlib.sha256(diff).hexdigest(), "repository": "C:/t/iso/ep-platform (scratch clone; not the owner checkout)",
                                "commits": git(SUC, "log", "--oneline", "69ee759..HEAD").splitlines()},
       "h06_control_binding_unchanged": {"declaration": str(R18 / "CONT-DECLARATION.json").replace("\\", "/"), "sha256": sha(R18 / "CONT-DECLARATION.json"),
                                         "runner_matches": sha(R18 / "cont_boq.py") == decl["code"]["scripts"]["cont_boq.py"], "boq_arm_reader": decl["arms"]["S"]["commit"],
                                         "boq_queue_sha256": decl["code"]["boq_queue_sha256"], "note": "the R21 reader is not bound into the H-06 control"},
       "r21": {"sample": sha(R / "R21-SAMPLE.json"), "page_classes": sha(R / "R21-PAGE-CLASSES.json"), "stage_manifest": sha("C:/t/r2x/r21-stage/R21-STAGE.json"),
               "labels_manifest": sha(R / "labels-r21/LABEL-MANIFEST.json"), "exposure": sha(R / "labels-r21/EXPOSURE.json"), "workload": sha(R / "workload/R21-WORKLOAD.json"),
               "draft_declaration": sha(R / "R21-DECLARATION.draft.json"), "dry_declaration": sha("C:/t/r2x/dry-runs/R21-DECLARATION.dry.json"),
               "scripts": {f: sha(R / f) for f in ("patch_r21.py", "patch_r21_2.py", "coverage_v3.py", "score_arms_v3.py", "arm_a.py", "arm_shares.py", "arm_ev.py",
                                                    "declare_r21.py", "select_r21_sample.py", "make_r21_stage.py", "workload_r21.py", "label_manifest_r21.py")}},
       "reviewer_files_review20": {p.name: sha(p) for p in sorted((MR / "reviews/M2-review-20").glob("*")) if p.is_file()}}
(R / "bindings").mkdir(exist_ok=True)
(R / "bindings/SOURCE-BINDINGS.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print("frozen", frozen, "| app files changed vs 69ee759:", app_changed, "| commits:", out["frozen_r21_candidate"]["commits"])
