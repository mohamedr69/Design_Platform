"""ORCH-06C (R36HARNESS-IMPL): assemble PILOT/review36/ from the work folder (refuses if the package folder exists).
Usage: assemble_review36.py
Copies byte for byte: the bound harness (scripts/harness-r32/), the task scripts (scripts/), the patched parity scripts
(scripts/parity-r36/), the junit of the whole-suite twin run (tests/), of the bound-copy run (tests/bound-copy/) and of the
new tests against the review34 module (tests/new-tests-on-review34-module/) with their guard reports, the work records
(evidence/), and COMMANDS.md. H1-WHATIF-RESULT.json, CHANGE-RECORD.md, BINDING-MANIFEST-R36.json,
COMMANDS-AND-AUDIT-LOG.md, PACKAGE-CHECK.json and EVIDENCE-MANIFEST.json are written by their own steps afterwards."""
import hashlib
import json
import pathlib
import shutil

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
PKG = PILOT / "review36"
WORK = pathlib.Path("C:/t/iso/work/r2x/r36")
SCRIPTS = ["audit_r36.py", "copy_harness_r36.py", "apply_h1_fix_r36.py", "h1_test_addition_r36.txt", "make_suite_twin_r36.py", "run_tests_r36.py",
           "snapshot_r36.py", "make_parity_copy_r36.py", "judge_all_rows_r36.py", "h1_whatif_r36.py", "make_binding_r36.py",
           "verify_review36_package.py", "package_r36.py", "append_response_r36.py", "pytest-plugins/r36_write_guard.py",
           "assemble_review36.py", "make_change_record_r36.py"]
COPIES = {"COMMANDS.md": "COMMANDS.md",
          "evidence/COPY-RECORD.json": "evidence-work/COPY-RECORD.json", "evidence/TWIN-RECORD.json": "evidence-work/TWIN-RECORD.json",
          "evidence/PARITY-COPY-RECORD.json": "evidence-work/PARITY-COPY-RECORD.json", "evidence/SNAPSHOT-BEFORE.json": "evidence-work/SNAPSHOT-BEFORE.json",
          "evidence/TESTS-TWIN.json": "evidence-work/TESTS-TWIN-2.json", "evidence/TESTS-BOUND.json": "evidence-work/TESTS-BOUND-4.json",
          "evidence/superseded/TESTS-TWIN-1-guard-defect.json": "evidence-work/TESTS-TWIN-1.json",
          "evidence/superseded/TESTS-BOUND-3-earlier-guard.json": "evidence-work/TESTS-BOUND-3.json"}
TREES = {"tests": "test-runs/twin-2/junit", "tests/bound-copy": "test-runs/bound-4/junit",
         "tests/new-tests-on-review34-module": "test-runs/new-tests-on-review34-module"}


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def put(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "xb") as fh:
        fh.write(pathlib.Path(src).read_bytes())
    assert sha(src) == sha(dst), dst


def main():
    if PKG.exists():
        raise SystemExit(f"refused: {PKG} exists")
    PKG.mkdir()
    n = 0
    for p in sorted((WORK / "harness-r32").iterdir()):
        put(p, PKG / "scripts" / "harness-r32" / p.name)
        n += 1
    for s in SCRIPTS:
        put(WORK / s, PKG / "scripts" / s)
        n += 1
    for p in sorted((WORK / "parity" / "scripts").iterdir()):
        put(p, PKG / "scripts" / "parity-r36" / p.name)
        n += 1
    for dst, src in COPIES.items():
        put(WORK / src, PKG / dst)
        n += 1
    for dst, src in TREES.items():
        for p in sorted((WORK / src).rglob("*")):
            if p.is_file():
                put(p, PKG / dst / p.relative_to(WORK / src))
                n += 1
    print(json.dumps({"package": PKG.as_posix(), "files": n}, indent=1))


if __name__ == "__main__":
    main()
