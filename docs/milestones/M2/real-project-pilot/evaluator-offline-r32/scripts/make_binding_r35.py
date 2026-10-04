"""ORCH-06: write BINDING-MANIFEST-R35.json (what this parity test is bound to).
Usage: make_binding_r35.py <run full json abs>      (reads; writes only <package>/BINDING-MANIFEST-R35.json)
The candidate modules are those the full run actually opened inside C:/t/iso/cand-r29 (from its audit record), hashed now.
git is called with GIT_OPTIONAL_LOCKS=0 so that no lock file is created in the candidate's .git directory."""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_r35 as C  # noqa: E402

STATUS_BEFORE = {"checked_at_utc": "2026-10-03T13:46Z (task start, with the first hash checks)", "head": C.CANDIDATE_HEAD, "porcelain": ""}


def git(*args) -> str:
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    return subprocess.run(["git", "-C", str(C.CANDIDATE), *args], capture_output=True, text=True, env=env, check=True).stdout


def main(argv):
    run = json.loads(pathlib.Path(argv[1]).read_text(encoding="utf-8"))
    opened = [r["path"] for r in run["guard"]["files_opened_for_reading_outside_python"] if r["exists"]]
    cand = sorted({p for p in opened if p.lower().startswith("c:/t/iso/cand-r29/") and p.endswith(".py")})
    cand_pyc = sorted({p for p in opened if p.lower().startswith("c:/t/iso/cand-r29/") and p.endswith(".pyc")})
    # a module loaded from a valid cached .pyc never opens its .py: bind the source of every such module too
    for pyc in cand_pyc:
        q = pathlib.Path(pyc)
        src = (q.parent.parent / (q.name.split(".")[0] + ".py")).as_posix()
        if pathlib.Path(src).exists():
            cand = sorted(set(cand) | {src.lower()})
    head = git("rev-parse", "HEAD").strip()
    status = git("status", "--porcelain")
    package_files = {}
    for rel in ("SYNTHETIC-PREDICTIONS.json", "PARITY-MATRIX.json", "EVALUATOR-TEST-REPORT.md", "evidence/RUN-SUMMARY.json",
                "evidence/NORMALISER-EXPERIMENT.json"):
        package_files[rel] = C.sha256_file(C.PACKAGE / rel)
    for p in sorted((C.PACKAGE / "scripts").glob("*.py")) + sorted((C.PACKAGE / "tests").glob("*.py")):
        package_files[p.relative_to(C.PACKAGE).as_posix()] = C.sha256_file(p)
    rs = C.REVIEW34 / "RUN-SET-PROPOSAL.json"
    manifest = {
        "kind": "BINDING-MANIFEST-R35", "task": "ORCH-06 (Review 33 C-6)", "agent": "R35EVAL-IMPL",
        "statement": C.SYNTHETIC_STATEMENT, "reference_set_statement": C.REFERENCE_SET_STATEMENT,
        "candidate": {"path": str(C.CANDIDATE).replace("\\", "/"), "head_expected": C.CANDIDATE_HEAD, "head_now": head,
                      "status_before": STATUS_BEFORE, "status_porcelain_now": status, "status_now_empty": status == "",
                      "never_written": True},
        "evaluator": {"path": "C:/t/iso/cand-r29/backend/scripts/m2_eval6.py", "sha256": C.sha256_file(C.CANDIDATE / "backend/scripts/m2_eval6.py"),
                      "version": run["evaluator"]["evaluator_version"], "register_evaluator_version": run["evaluator"]["register_evaluator_version"],
                      "evidence_reader_version": run["evaluator"]["reader_version"], "evidence_policy_version": run["evaluator"]["evidence_policy_version"],
                      "invocation": run["evaluator"]["invocation"], "ai_context_by_channel": run["evaluator"]["ai_context_by_channel"]},
        "candidate_modules_imported": {p: C.sha256_file(p) for p in cand},
        "candidate_cached_bytecode_read": {p: C.sha256_file(p) for p in cand_pyc},
        "candidate_modules_expected": dict(sorted(C.CANDIDATE_MODULES.items())),
        "review34_inputs": {k: {"path": str(C.FROZEN[k][0]).replace("\\", "/"), "sha256": C.FROZEN[k][1]}
                            for k in ("review34_manifest", "labels_eval_input", "truth_r32", "converter_reconciliation")} |
                           {"run_set_proposal (annotation only)": {"path": str(rs).replace("\\", "/"), "sha256": C.sha256_file(rs)}},
        "review34_harness_modules": {f"scripts/harness-r32/{m}.py": h for m, h in sorted(C.HARNESS_MODULES.items())},
        "reference_set": {k: {"path": str(C.FROZEN[k][0]).replace("\\", "/"), "sha256": C.FROZEN[k][1]}
                          for k in ("reference_set_reviewed_2", "label_conventions_r32")},
        "reviews": {k: {"path": str(C.FROZEN[k][0]).replace("\\", "/"), "sha256": C.FROZEN[k][1]} for k in ("review33", "review34", "review35")},
        "fixtures": {"path": "SYNTHETIC-PREDICTIONS.json", "sha256": package_files["SYNTHETIC-PREDICTIONS.json"],
                     "count": run["fixtures"]["count"]},
        "package_files": package_files,
        "ai_ledger": {"path": C.AI_LEDGER, "entries": 483, "scopes": 17, "opened": "read-only (mode=ro, uri=True)"},
        "response_ledger_before": {"path": str(C.RESPONSE_LEDGER).replace("\\", "/"),
                                   "sha256": "cc1edc4d38d54db3aae951f898106e487df68dc32112d34bd8615ed162873084"},
    }
    sha = C.write_json(manifest, C.PACKAGE / "BINDING-MANIFEST-R35.json")
    print(json.dumps({"binding_manifest_sha256": sha, "candidate_modules": len(cand), "head": head, "status_empty": status == ""}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
