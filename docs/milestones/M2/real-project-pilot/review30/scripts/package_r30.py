"""Assemble docs/milestones/M2/real-project-pilot/review30/ (NEW folder, never rebuilt in place) and write its manifest
LAST (after every other file is in place). Copies only; nothing in review29/ or any earlier package is touched."""
import hashlib
import json
import pathlib
import shutil
import sys

R = pathlib.Path(__file__).resolve().parent
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review30")
FINAL = "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if PKG.exists():
    sys.exit("the package folder exists; never rebuilt in place")


def cp(src, dst):
    d = PKG / dst
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, d)


for f in ("CORRECTION-REPORT.md", "COHORT-OPTIONS.md", "FIELD-POPULATION-FEASIBILITY.md", "REVISED-FRESH-VALIDATION-PLAN.md", "DRAFT-DECLARATION.json",
          "BUDGET-DECISION-CARD.md", "COMMANDS.md"):
    cp(R / "pkg-src" / f, f)
for p in sorted((R / "pkg-src" / "review29-overlay").glob("*.md")):
    cp(p, f"review29-overlay/{p.name}")
for f in ("FRESH-PROJECT-CANDIDATES.json", "M2-USED-PROJECTS.json"):
    cp(R / f, f"cohort/{f}")
for f in ("FIELD-POPULATION.json", "R26-FIELD-RATES.json"):
    cp(R / f, f"field-population/{f}")
cp(R / "CHECKER-TESTS.xml", "tests/CHECKER-TESTS.xml")
for f in ("r30_checks.py", "test_r30_checks.py", "select_fresh_projects.py", "feasibility.py", "make_draft_declaration.py", "package_r30.py", "verify_r30_package.py"):
    cp(R / f, f"scripts/{f}")
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*")) if p.is_file()}
(PKG / "evidence").mkdir(exist_ok=True)
(PKG / "evidence/EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "review30 (Review 29 package corrections and fresh-validation design)",
                                                                 "candidate_head": FINAL, "historical_commits": {"a4ce6a3": "first candidate commit (superseded by C1 revision 2)"},
                                                                 "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 3), "MB")
