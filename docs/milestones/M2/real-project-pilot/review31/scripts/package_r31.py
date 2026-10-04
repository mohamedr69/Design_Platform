"""Assemble docs/milestones/M2/real-project-pilot/review31/ (NEW folder, never rebuilt in place) and write its manifest
LAST. Copies only; nothing in review30/, review29/, four-arm-final/ or any earlier package is touched."""
import hashlib
import json
import pathlib
import shutil
import sys

R = pathlib.Path(__file__).resolve().parent
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review31")
FINAL = "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()  # noqa: E731
if PKG.exists():
    sys.exit("the package folder exists; never rebuilt in place")


def cp(src, dst):
    d = PKG / dst
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, d)


for f in ("CORRECTION-REPORT.md", "COHORT-PROPOSAL.md", "FIELD-POPULATION-FEASIBILITY.v2.md", "REVISED-FRESH-VALIDATION-PLAN.v2.md", "STOP-AND-SAFETY-RULES.md",
          "DRY-RUN-REPORT.md", "BUDGET-DECISION-CARD.v2.md", "COMMANDS.md"):
    cp(R / "pkg-src" / f, f)
for f in ("DRAFT-DECLARATION.v2.json", "BINDING-MANIFEST.json"):
    cp(R / f, f)
for f in ("FRESH-PROJECTS-R31.json", "R30-PICKS-RECONCILED.json"):
    cp(R / f, f"cohort/{f}")
cp(R / "FEASIBILITY-R31.json", "field-population/FEASIBILITY-R31.json")
DRY = R / "dry-run" / "t3"
for p in sorted(DRY.iterdir()):
    if p.is_file() and not p.name.startswith("rows-"):
        cp(p, f"dry-run/{p.name}")
for f in ("selector_core.py", "used_sets.py", "select_fresh_projects_r31.py", "reconcile_r30_picks.py", "test_selector_core.py", "feasibility_r31.py",
          "make_bindings_r31.py", "make_draft_declaration_v2.py", "package_r31.py", "verify_r31_package.py", "append_response_r31.py"):
    cp(R / f, f"scripts/{f}")
for f in ("capture_store.py", "test_capture_store.py", "state_check.py", "test_state_check.py", "stop_rules.py", "test_stop_rules.py", "score_bcr.py",
          "test_score_bcr.py", "score_lane.py", "run_lane.py", "dry_run.py"):
    cp(R / "harness" / f, f"scripts/harness/{f}")
for f in ("selector.xml", "harness-pure.xml", "capture-store.xml"):
    cp(R / "tests" / f, f"tests/{f}")
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*")) if p.is_file()}
not_packaged = {f"dry-run/t3/{p.name}": sha(p) for p in sorted(DRY.iterdir()) if p.is_file() and p.name.startswith("rows-")}
(PKG / "evidence").mkdir(exist_ok=True)
(PKG / "evidence/EVIDENCE-MANIFEST.json").write_text(json.dumps({
    "package": "review31 (Review 31: selector, experiment contracts, dry run, binding manifest; preparation only)",
    "candidate_head": FINAL, "historical_commits": {"a4ce6a3": "first candidate commit (superseded by C1 revision 2)"},
    "not_packaged_hashes": {**not_packaged, "capture store of the dry run (41 MB of crops)": json.loads((DRY / "DRY-RUN-REPORT.json").read_text(encoding="utf-8"))["store"]["capture_sha256"]},
    "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 3), "MB")
