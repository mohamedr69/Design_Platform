"""ORCH-10 (R42PORT-IMPL; v2's snapshot_r40.py re-pointed to the merged installation, with declaration-r32-v2, review39, the
work folders r39 / r40 and the merged installation's backend code added): a read-only snapshot of every frozen tree this
task must not modify.

Usage: snapshot_r42.py <out json>
Per tree: every file's relative path, size, mtime (UTC) and sha256 (sha256 only for the hashed trees; the work folders, the
orchestrator folder and four-arm-final are recorded by path, size and mtime). The AI ledger is opened mode=ro (uri=True)
only. The merged installation's .env is never opened (the backend/app code tree is hashed; data is not touched: the live
services own it). Writes only <out json>."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

P = C.PILOT
HASHED = {n: P / n for n in ("review39", "review38", "review36", "review34", "review33", "review31", "declaration-r32", "declaration-r32-v2",
                              "evaluator-offline-r32", "fresh-cohort-r32", "fresh-cohort-r32-reviewed", "fresh-cohort-r32-reviewed-2")}
HASHED |= {"MR-reviews": C.MR / "reviews", "MR-policy": None, "staging-r32": pathlib.Path("C:/t/r2x/r32-stage"),
           "merged-backend-app": C.EP / "backend" / "app"}
LISTED = {f"work-{n}": pathlib.Path(f"C:/t/iso/work/r2x/{n}") for n in ("r32", "r32b", "r32c", "r33", "r34", "r35", "r36", "r37", "r38", "r39", "r40")}
LISTED["MR-orchestrator"] = C.MR / "orchestrator"
LISTED["four-arm-final"] = P / "four-arm-final"


def walk(root: pathlib.Path, hashed: bool) -> dict:
    out = {}
    if not root.exists():
        return {"missing": True}
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            p = pathlib.Path(dirpath) / f
            st = os.stat(C.long_path(p))
            rec = {"size": st.st_size, "mtime_utc": datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).isoformat(timespec="seconds")}
            if hashed:
                rec["sha256"] = C.sha256_file(p)
            out[p.relative_to(root).as_posix()] = rec
    return out


def main(argv) -> int:
    out_path = pathlib.Path(argv[1])
    snap = {"taken_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "hashed_trees": {}, "listed_trees": {},
            "ai_ledger": C.ledger_counts() | {"opened": "file:...?mode=ro, uri=True"},
            "repos": {name: C.git_state(repo) | {"expected": head} for name, (repo, head) in (("candidate", C.CANDIDATE), ("baseline", C.BASELINE))},
            "response_ledger": {"path": C.RESPONSE_LEDGER.as_posix(), "size": C.RESPONSE_LEDGER.stat().st_size, "sha256": C.sha256_file(C.RESPONSE_LEDGER)},
            "policy": {n: C.sha256_file(C.MR / n) for n in C.POLICY}, "r40_work_records": {p: C.sha256_file(p) for p in C.R40_WORK_RECORDS},
            "cli_file": {"path": C.CLI_EXE.as_posix(), "sha256": C.sha256_file(C.CLI_EXE), "executed": False},
            "merged_env_file": {"path": C.MERGED_ENV_FILE.as_posix(), "exists": C.MERGED_ENV_FILE.exists(), "read": False},
            "live_run_folder_exists": C.RUN_FOLDER.exists(),
            "forbidden_files": {"roots": [P.as_posix(), C.MR.as_posix(), "C:/t"], "hits": C.forbidden_files()}}
    for name, root in HASHED.items():
        if root is None:
            continue
        files = walk(root, True)
        snap["hashed_trees"][name] = {"root": root.as_posix(), "files": len(files), "digest": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
                                      "entries": files}
    for name, root in LISTED.items():
        files = walk(root, False)
        snap["listed_trees"][name] = {"root": root.as_posix(), "files": len(files), "digest": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
                                      "entries": files}
    C.write_json(out_path, snap)
    print(json.dumps({"taken_utc": snap["taken_utc"], "ai_ledger": snap["ai_ledger"], "repos": snap["repos"], "response_ledger": snap["response_ledger"],
                      "forbidden_hits": snap["forbidden_files"]["hits"], "trees": {k: v["files"] for k, v in {**snap["hashed_trees"], **snap["listed_trees"]}.items()}}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
