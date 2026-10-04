"""Assemble docs/milestones/M2/real-project-pilot/review29/ (NEW folder, never rebuilt in place): the reports, the frozen
candidate's patches / changed files / source hashes, the patcher, the contract freezes, the defect reproduction, the
offline replay evidence, the test logs and the scripts; then the evidence manifest."""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

R = pathlib.Path(__file__).resolve().parent
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review29")
CAND = pathlib.Path("C:/t/iso/cand-r29")
BASE719 = pathlib.Path("C:/t/iso/cand-ai4")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
git = lambda t, *a: subprocess.run(["git", "-C", str(t), *a], capture_output=True, text=True, check=True).stdout
if PKG.exists():
    sys.exit("the package folder exists; never rebuilt in place")
head = git(CAND, "rev-parse", "HEAD").strip()
assert not git(CAND, "status", "--porcelain").strip(), "the candidate tree is dirty"


def cp(src, dst):
    d = PKG / dst
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, d)


for f in ("CORRECTION-REPORT.md", "CHANGE-MAP.md", "CONTRACTS.md", "TESTS-AND-REGRESSIONS.md", "OFFLINE-REPLAY.md", "FRESH-VALIDATION-PLAN.md", "COMMANDS.md"):
    cp(R / "pkg-src" / f, f)
# candidate: patches, changed files, source hashes
(PKG / "candidate").mkdir(parents=True)
changed = [l for l in git(CAND, "diff", "--name-only", "719e8de", head).splitlines() if l]
for i, c in enumerate(git(CAND, "rev-list", "--reverse", f"719e8de..{head}").split(), 1):
    (PKG / "candidate" / f"{i:02d}-{c[:7]}.patch").write_bytes(subprocess.run(["git", "-C", str(CAND), "format-patch", "-1", "--stdout", c], capture_output=True, check=True).stdout)
for f in changed:
    cp(CAND / f, f"candidate/files/{f}")
tracked = [l for l in git(CAND, "ls-files").splitlines() if l]
hashes = {f: sha(CAND / f) for f in tracked if (CAND / f).is_file()}
untouched_equal = {f: sha(BASE719 / f) == h for f, h in hashes.items() if f not in changed and (BASE719 / f).is_file()}
(PKG / "candidate" / "SOURCE-HASHES.json").write_text(json.dumps({
    "candidate_tree": str(CAND), "branch": git(CAND, "rev-parse", "--abbrev-ref", "HEAD").strip(), "head": head, "parent": "719e8de661b8b10427ef6cff5d2d277a53b64dc6",
    "commits": git(CAND, "log", "--format=%H %s", f"719e8de..{head}").splitlines(), "changed_files": {f: hashes.get(f) for f in changed},
    "untouched_files": len(untouched_equal), "untouched_files_byte_equal_to_cand_ai4_719e8de": all(untouched_equal.values()),
    "untouched_mismatches": [f for f, ok in untouched_equal.items() if not ok], "all_tracked": hashes}, indent=1) + "\n", encoding="utf-8")
for f in ("apply_patch.py", "block_flags.py", "block_guard.py", "block_decision.py", "make_eval6.py"):
    cp(R / "patch" / f, f"patch/{f}")
for f in ("CONTRACT-FREEZE.json", "CONTRACT-FREEZE-R1.json", "CONTRACT-FREEZE-R2.json"):
    cp(R / "logs" / f, f"contracts/{f}")
for f in ("STORED-EVIDENCE-DUMP.txt", "FROZEN-OUTCOMES.json"):
    cp(R / "repro" / f, f"repro/{f}")
cp(R / "repro_dump.py", "repro/repro_dump.py")
for p in sorted((R / "replay").glob("*.json")):
    cp(p, f"replay/{p.name}")
for p in sorted(pathlib.Path("C:/t/r2x/r29-replay").glob("*/out/REPLAY.json")):
    cp(p, f"replay/manifests/{p.parent.parent.name}-REPLAY.json")
for p in sorted((R / "scores").glob("*.json")):
    cp(p, f"replay/scores/{p.name}")
for f in ("replay-all.status", "ANALYSIS.log", "NEW-ACCEPTANCES.log", "REPLAY-CANDIDATE-HEAD.txt"):
    cp(R / "logs" / f, f"replay/logs/{f}")
for f in ("FOCUSED-final.xml", "FOCUSED-final.log", "FOCUSED-final-EXIT.txt", "FOCUSED-MODULES.txt", "FULL-final-candidate.xml", "FULL-final-candidate.log",
          "FULL-final-candidate-EXIT.txt", "FINAL-candidate-HEAD.txt", "FINAL-candidate-status-before.txt", "FINAL-candidate-status-after.txt",
          "FULL-baseline.xml", "FULL-baseline.log", "FULL-baseline-EXIT.txt", "FULL-baseline-HEAD.txt", "FULL-baseline-status-after.txt",
          "FULL-candidate.xml", "FULL-candidate.log", "FULL-candidate-EXIT.txt", "FULL-candidate-HEAD.txt", "FAILURE-COMPARISON.json", "R29-TESTS.log", "R29-TESTS.xml",
          "FULL-baseline-rerun.xml", "FULL-baseline-rerun.log", "FULL-baseline-rerun-EXIT.txt", "FULL-baseline-rerun-HEAD.txt",
          "FULL-baseline-rerun-status-before.txt", "FULL-baseline-rerun-status-after.txt", "FAILURE-COMPARISON-stalled-baseline.json"):
    if (R / "logs" / f).exists():
        cp(R / "logs" / f, f"tests/{f}")
for f in ("replay_arm.py", "compare_fidelity.py", "score_replay.py", "analyze_replays.py", "new_acceptances.py", "decision_absence.py", "run_all_replays.sh", "rerun_replays_final.sh",
          "run_full_suites.sh", "run_final_suites.sh", "run_focused.sh", "run_baseline_rerun.sh", "failure_compare.py", "package_r29.py", "verify_r29_package.py", "append_response_r29.py"):
    if (R / f).exists():
        cp(R / f, f"scripts/{f}")
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*")) if p.is_file()}
(PKG / "evidence").mkdir(exist_ok=True)
(PKG / "evidence/EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "review29 (bounded offline accuracy candidate)", "candidate_head": head, "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 2), "MB; candidate", head)
