"""Review 31 (R31-05): the immutable binding manifest of the preparation package. It is written ONCE (an existing file is
never overwritten) and records the sha256 of every selector, harness, scorer, stop-logic and dry-run file, the frozen
candidate and baseline commits and their evaluator / reader files, the coverage contract, the threshold sources, the dry
run outputs and the recorded B database. The draft declaration v2 binds this manifest by its own sha256; a later
authorization must name the declaration hash, and a preflight must re-verify every entry before any dispatch.
Writes C:/t/iso/work/r2x/r31/BINDING-MANIFEST.json."""
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "BINDING-MANIFEST.json"
if OUT.exists():
    sys.exit("BINDING-MANIFEST.json exists: the binding manifest is immutable")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()  # noqa: E731
MR = "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap"
M2 = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2"
DRY = HERE / "dry-run" / "t3"
groups = {
    "selector": ["selector_core.py", "used_sets.py", "select_fresh_projects_r31.py", "reconcile_r30_picks.py", "test_selector_core.py",
                 "FRESH-PROJECTS-R31.json", "R30-PICKS-RECONCILED.json", "feasibility_r31.py", "FEASIBILITY-R31.json"],
    "harness": ["harness/capture_store.py", "harness/test_capture_store.py", "harness/state_check.py", "harness/test_state_check.py",
                "harness/run_lane.py", "harness/dry_run.py"],
    "stop_logic": ["harness/stop_rules.py", "harness/test_stop_rules.py"],
    "scorer": ["harness/score_bcr.py", "harness/test_score_bcr.py", "harness/score_lane.py"],
    "tests_junit": ["tests/selector.xml", "tests/harness-pure.xml", "tests/capture-store.xml"],
}
files = {g: {f: sha(HERE / f) for f in fs} for g, fs in groups.items()}
files["dry_run_outputs"] = {f"dry-run/t3/{p.name}": sha(p) for p in sorted(DRY.iterdir()) if p.is_file()}
git = lambda tree, *a: subprocess.run(["git", "-C", tree, *a], capture_output=True, text=True, check=True).stdout.strip()  # noqa: E731
code = {
    "candidate": {"commit": git("C:/t/iso/cand-r29", "rev-parse", "HEAD"), "tree": "C:/t/iso/cand-r29", "clean": git("C:/t/iso/cand-r29", "status", "--porcelain") == "",
                  "evidence_reader.py": sha("C:/t/iso/cand-r29/backend/app/ai/evidence_reader.py"),
                  "evaluator .10 scripts/m2_eval6.py": sha("C:/t/iso/cand-r29/backend/scripts/m2_eval6.py")},
    "baseline": {"commit": git("C:/t/iso/frozen-r12", "rev-parse", "HEAD"), "tree": "C:/t/iso/frozen-r12", "clean": git("C:/t/iso/frozen-r12", "status", "--porcelain") == "",
                 "evaluator .9 scripts/m2_eval5.py": sha("C:/t/iso/frozen-r12/backend/scripts/m2_eval5.py")},
    "coverage_contract": {"file": "C:/t/iso/work/r2x/review25/harness-v4.3/coverage_v4.py", "sha256": sha("C:/t/iso/work/r2x/review25/harness-v4.3/coverage_v4.py")},
}
thresholds = {"AI-ACCURACY-POLICY.md": sha(f"{MR}/AI-ACCURACY-POLICY.md"), "MASTER-ROADMAP.md": sha(f"{MR}/MASTER-ROADMAP.md"),
              "M2-ACCEPTANCE-REPORT.md": sha(f"{M2}/M2-ACCEPTANCE-REPORT.md"), "review21/ANALYSIS-PLAN.md": sha(f"{M2}/real-project-pilot/review21/ANALYSIS-PLAN.md")}
dry_inputs = {"B database (final-A), recorded after the four-arm run": json.loads((HERE.parent / "run-final" / "POST-RUN-BINDINGS.json").read_text(encoding="utf-8"))["sandbox_databases"]["A"],
              "B database (final-A), now": sha("C:/t/r2x/runs/final-A/db/default.db"),
              "L3 captures io.jsonl": sha("C:/t/r2x/runs/final-L3/out/io.jsonl"),
              "four-arm declaration v2": sha(HERE.parent / "r27" / "FINAL-DECLARATION.v2.json"),
              "capture store of the dry run (not packaged, 41 MB of crops)": json.loads((DRY / "DRY-RUN-REPORT.json").read_text(encoding="utf-8"))["store"]["capture_sha256"]}
assert dry_inputs["B database (final-A), recorded after the four-arm run"] == dry_inputs["B database (final-A), now"]
assert code["candidate"]["clean"] and code["baseline"]["clean"]
m = {"name": "Review 31 preparation binding manifest", "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
     "immutable": "written once; a changed file is a new manifest with a new hash, never an edit", "files_root": str(HERE),
     "files": files, "code": code, "threshold_sources": thresholds, "dry_run_inputs": dry_inputs,
     "model_requests": 0, "gpt_bridge": "disabled; not part of the workflow"}
OUT.write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(sha(OUT))
