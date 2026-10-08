"""R43-42 (review45, new): the PRE-BINDING of the drill run (the --binding the drill verifies with preflight_r32.verify_binding):
the review45 harness (package and the run copy the drill runs from), the run set, the truth, the three staged PDFs, the
drill criterion and the superseded harness manifest, each {path: sha256}. Read-only; writes only <out json>.
Usage: <bound python> -B r45_prebinding.py <run copy harness dir> <out json>"""
from __future__ import annotations

import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r45common as C  # noqa: E402

STAGED = {p: pathlib.Path(f"C:/t/r2x/r32-stage/files/{p}.pdf") for p in ("F009", "F020", "F030")}


def main(run_harness: str, out: str) -> int:
    run_h = pathlib.Path(run_harness)
    pkg_h = C.REVIEW45 / "scripts" / "harness-r32"
    files = {
        "harness_r45_package": {p.as_posix(): C.sha256_file(p) for p in sorted(pkg_h.glob("*.py"))},
        "harness_r45_run_copy": {p.as_posix(): C.sha256_file(p) for p in sorted(run_h.glob("*.py"))},
        "inputs": {(C.PILOT / "review34/RUN-SET-PROPOSAL.json").as_posix(): C.sha256_file(C.PILOT / "review34/RUN-SET-PROPOSAL.json"),
                   (C.PILOT / "review34/dry-run/TRUTH-R32.json").as_posix(): C.sha256_file(C.PILOT / "review34/dry-run/TRUTH-R32.json")},
        "staged_documents": {p.as_posix(): C.sha256_file(p) for p in STAGED.values()},
        "criterion": {(C.REVIEW45 / "DRILL-CRITERION.md").as_posix(): C.sha256_file(C.REVIEW45 / "DRILL-CRITERION.md")},
        "superseded_harness_manifest": {C.BINDING43.as_posix(): C.sha256_file(C.BINDING43)}}
    pairs = {(pathlib.Path(a).name, b) for a, b in files["harness_r45_package"].items()}
    run_pairs = {(pathlib.Path(a).name, b) for a, b in files["harness_r45_run_copy"].items()}
    rec = {"name": "R43-42 pre-binding of the dry baseline-facts drill run (verified by preflight_r32.verify_binding before the drill)",
           "written_local": C.now_local(), "files": files, "run_copy_equals_package": pairs == run_pairs,
           "statement": "binds code and inputs of one dry drill run; authorizes nothing"}
    if not rec["run_copy_equals_package"]:
        raise SystemExit("refused: the run copy differs from the package")
    if files["superseded_harness_manifest"][C.BINDING43.as_posix()] != C.BINDING43_SHA:
        raise SystemExit("refused: the review43 harness manifest is not f35355aa...")
    C.write_json(out, rec)
    print(json.dumps({"groups": {k: len(v) for k, v in files.items()}, "run_copy_equals_package": rec["run_copy_equals_package"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
