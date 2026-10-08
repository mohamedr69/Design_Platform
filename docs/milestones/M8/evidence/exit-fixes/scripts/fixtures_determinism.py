"""ORCH-044 evidence (U2M8V-03): make_fixtures.py writes the same bytes on
every run. Runs the script N times (default 8), each under another
PYTHONHASHSEED (including 4, 7 and 10, which reordered the CLASSES before
the fix) and once without one, into a scratch copy of the fixture folder,
and compares every file's sha256 with the committed blob (git cat-file,
independent of the checkout's line-end conversion) and with the other runs.

Run from the worktree root:
    python -B docs/milestones/M8/evidence/exit-fixes/scripts/fixtures_determinism.py OUT.json [SCRATCH]
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
FIXTURES = ROOT / "backend" / "tests" / "fixtures_m8"
SEEDS = ["4", "7", "10", "0", "1", "12345", "99", None]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(rel: str) -> bytes | None:
    r = subprocess.run(["git", "cat-file", "blob", f"HEAD:{rel}"], cwd=ROOT, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def main(out: str, scratch: str = "C:/t/tmp/m8b/fx") -> None:
    work = Path(scratch)
    runs = []
    for k, seed in enumerate(SEEDS):
        target = work / f"run{k}"
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        shutil.copy2(FIXTURES / "make_fixtures.py", target / "make_fixtures.py")
        env = dict(os.environ)
        env.pop("PYTHONHASHSEED", None)
        if seed is not None:
            env["PYTHONHASHSEED"] = seed
        subprocess.run([sys.executable, "-B", str(target / "make_fixtures.py")], cwd=target, env=env, check=True,
                       capture_output=True)
        runs.append({"seed": seed, "files": {p.name: sha(p.read_bytes()) for p in sorted(target.glob("*.dxf"))}})
    names = sorted(runs[0]["files"])
    committed = {}
    for n in names:
        data = blob(f"backend/tests/fixtures_m8/{n}")
        committed[n] = sha(data) if data is not None else None
    identical = all(r["files"] == runs[0]["files"] for r in runs)
    result = {"runs": len(runs), "seeds": SEEDS, "files": len(names), "all_runs_identical": identical,
              "equal_to_committed_blob": {n: runs[0]["files"][n] == committed[n] for n in names},
              "worktree_equal": {n: sha((FIXTURES / n).read_bytes()) == runs[0]["files"][n] for n in names},
              "sha256": runs[0]["files"], "committed_blob_sha256": committed}
    Path(out).write_text(json.dumps(result, indent=1), encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)
    print(json.dumps({k: result[k] for k in ("runs", "files", "all_runs_identical")}, indent=1))
    print("equal to committed:", sum(result["equal_to_committed_blob"].values()), "of", len(names))


if __name__ == "__main__":
    main(*sys.argv[1:3])
