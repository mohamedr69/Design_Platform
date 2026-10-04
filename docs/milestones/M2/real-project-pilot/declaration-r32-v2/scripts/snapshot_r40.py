"""ORCH-09 (R40DECL-IMPL; review39's snapshot_r39.py with review39 hashed, work r39 listed, the response ledger hashed and a
search for authorization, token and run files added): read-only snapshot of every frozen tree this task must not modify.

Usage: snapshot_r40.py <out json>
Per tree: every file's relative path, size, mtime (UTC) and sha256 (sha256 only for the hashed trees; the work folders
r32..r39, the orchestrator folder and four-arm-final are recorded by path, size and mtime). The AI ledger is opened
mode=ro (uri=True) only. Writes only <out json>."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import sqlite3
import subprocess
import sys

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
RESPONSE = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/M2-REVIEW-RESPONSE.md")
HASHED = {
    "review39": PILOT / "review39", "review38": PILOT / "review38", "review36": PILOT / "review36", "review34": PILOT / "review34",
    "review33": PILOT / "review33", "review31": PILOT / "review31",
    "declaration-r32": PILOT / "declaration-r32", "evaluator-offline-r32": PILOT / "evaluator-offline-r32",
    "fresh-cohort-r32": PILOT / "fresh-cohort-r32", "fresh-cohort-r32-reviewed": PILOT / "fresh-cohort-r32-reviewed",
    "fresh-cohort-r32-reviewed-2": PILOT / "fresh-cohort-r32-reviewed-2", "MR-reviews": MR / "reviews",
    "staging-r32": pathlib.Path("C:/t/r2x/r32-stage"),
}
LISTED = {f"work-{n}": pathlib.Path(f"C:/t/iso/work/r2x/{n}") for n in ("r32", "r32b", "r32c", "r33", "r34", "r35", "r36", "r37", "r38", "r39")}
LISTED["MR-orchestrator"] = MR / "orchestrator"
LISTED["four-arm-final"] = PILOT / "four-arm-final"
LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"
REPOS = {"candidate": ("C:/t/iso/cand-r29", "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d"),
         "baseline": ("C:/t/iso/frozen-r12", "3d5607d99fcebf08ac45f5df937ad615ecc16fb3")}
# the search for anything this task must never create (names only; nothing is opened)
SEARCH_ROOTS = (PILOT, pathlib.Path("C:/t"))
FORBIDDEN_NAMES = ("OWNER-DISPATCH-AUTHORIZATION",)
FORBIDDEN_SUFFIXES = (".RUN.json",)


def _long(p) -> str:
    return "\\\\?\\" + str(p).replace("/", "\\")


def sha(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk(root: pathlib.Path, hashed: bool) -> dict:
    out = {}
    if not root.exists():
        return {"missing": True}
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            p = pathlib.Path(dirpath) / f
            try:
                st = os.stat(_long(p))
            except OSError:
                st = p.stat()
            rel = p.relative_to(root).as_posix()
            rec = {"size": st.st_size, "mtime_utc": datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).isoformat(timespec="seconds")}
            if hashed:
                rec["sha256"] = sha(_long(p))
            out[rel] = rec
    return out


def ledger() -> dict:
    con = sqlite3.connect(f"file:{LEDGER}?mode=ro", uri=True)
    try:
        return {"entries": con.execute("select count(*) from entries").fetchone()[0], "scopes": con.execute("select count(*) from scopes").fetchone()[0],
                "limit_amendments": con.execute("select count(*) from limit_amendments").fetchone()[0],
                "scope_names_sha256": hashlib.sha256("|".join(r[0] for r in con.execute("select scope from scopes order by scope")).encode()).hexdigest(),
                "opened": "file:...?mode=ro, uri=True"}
    finally:
        con.close()


def repos() -> dict:
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    out = {}
    for name, (repo, want) in REPOS.items():
        head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, env=env).stdout.strip()
        dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True, env=env).stdout.strip()
        out[name] = {"tree": repo, "head": head, "expected": want, "clean": not dirty}
    return out


def forbidden_files() -> dict:
    hits, searched = [], 0
    for root in SEARCH_ROOTS:
        for dirpath, _dirs, files in os.walk(root):
            for f in files:
                searched += 1
                if any(f.startswith(n) for n in FORBIDDEN_NAMES) or any(f.endswith(s) for s in FORBIDDEN_SUFFIXES):
                    hits.append((pathlib.Path(dirpath) / f).as_posix())
    return {"roots": [r.as_posix() for r in SEARCH_ROOTS], "files_searched": searched, "names": list(FORBIDDEN_NAMES),
            "suffixes": list(FORBIDDEN_SUFFIXES), "hits": sorted(hits)}


def main(argv) -> int:
    out_path = pathlib.Path(argv[1])
    snap = {"taken_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "hashed_trees": {}, "listed_trees": {},
            "ai_ledger": ledger(), "repos": repos(),
            "response_ledger": {"path": RESPONSE.as_posix(), "size": RESPONSE.stat().st_size, "sha256": sha(RESPONSE)},
            "forbidden_files": forbidden_files()}
    for name, root in HASHED.items():
        files = walk(root, True)
        snap["hashed_trees"][name] = {"root": root.as_posix(), "files": len(files), "digest": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
                                      "entries": files}
    for name, root in LISTED.items():
        files = walk(root, False)
        snap["listed_trees"][name] = {"root": root.as_posix(), "files": len(files), "digest": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
                                      "entries": files}
    out_path.write_text(json.dumps(snap, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"taken_utc": snap["taken_utc"], "ai_ledger": snap["ai_ledger"], "repos": snap["repos"], "response_ledger": snap["response_ledger"],
                      "forbidden_hits": snap["forbidden_files"]["hits"], "files_searched": snap["forbidden_files"]["files_searched"],
                      "trees": {k: v["files"] for k, v in {**snap["hashed_trees"], **snap["listed_trees"]}.items()}}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
