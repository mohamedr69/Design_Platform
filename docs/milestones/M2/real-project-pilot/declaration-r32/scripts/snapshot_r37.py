"""ORCH-07 (R37DECL-IMPL): before / after snapshot of every frozen tree this task must not modify.

Usage: snapshot_r37.py <out json (absolute, new)> <label>
Records per file: size, sha256 and mtime (UTC); plus the candidate / baseline git state, the AI ledger (read-only), the
response ledger hash, the live run folder's absence and the dispatch-authorization file search. Read-only everywhere."""
from __future__ import annotations

import datetime
import os
import pathlib
import sys

import r37common as C

TREES = {
    "review36": C.PILOT / "review36", "review34": C.PILOT / "review34", "review33": C.PILOT / "review33", "review31": C.PILOT / "review31",
    "evaluator-offline-r32": C.PILOT / "evaluator-offline-r32", "fresh-cohort-r32": C.PILOT / "fresh-cohort-r32",
    "fresh-cohort-r32-reviewed": C.PILOT / "fresh-cohort-r32-reviewed", "fresh-cohort-r32-reviewed-2": C.PILOT / "fresh-cohort-r32-reviewed-2",
    "four-arm-final": C.PILOT / "four-arm-final", "MR-reviews": C.MR / "reviews", "r32-stage": pathlib.Path("C:/t/r2x/r32-stage"),
    "work-r32": pathlib.Path("C:/t/iso/work/r2x/r32"), "work-r32b": pathlib.Path("C:/t/iso/work/r2x/r32b"),
    "work-r32c": pathlib.Path("C:/t/iso/work/r2x/r32c"), "work-r33": pathlib.Path("C:/t/iso/work/r2x/r33"),
    "work-r34": pathlib.Path("C:/t/iso/work/r2x/r34"), "work-r35": pathlib.Path("C:/t/iso/work/r2x/r35"),
    "work-r36": pathlib.Path("C:/t/iso/work/r2x/r36"),
}
SINGLE_FILES = {"AI-ACCURACY-POLICY.md": C.MR / "AI-ACCURACY-POLICY.md",
                "AI-ACCURACY-POLICY-AMENDMENT-R32-01.md": C.MR / "AI-ACCURACY-POLICY-AMENDMENT-R32-01.md",
                "MASTER-ROADMAP.md": C.MR / "MASTER-ROADMAP.md", "M2-ACCEPTANCE-REPORT.md": C.M2 / "M2-ACCEPTANCE-REPORT.md",
                "review21/ANALYSIS-PLAN.md": C.PILOT / "review21/ANALYSIS-PLAN.md", "candidate config.py": pathlib.Path("C:/t/iso/cand-r29/backend/app/core/config.py")}
AUTH_SEARCH_ROOTS = [C.PILOT, C.MR, pathlib.Path("C:/t/r2x"), C.WORK, C.SCRATCH]


def _mtime(p) -> str:
    return datetime.datetime.fromtimestamp(os.stat(p).st_mtime, datetime.timezone.utc).isoformat(timespec="seconds")


def tree_digest(root: pathlib.Path) -> dict:
    files, denied = {}, []
    for dirpath, dirs, names in os.walk(root, onerror=lambda e: denied.append(str(e.filename))):
        dirs.sort()
        for n in sorted(names):
            p = pathlib.Path(dirpath) / n
            rel = p.relative_to(root).as_posix()
            try:
                files[rel] = {"size": p.stat().st_size, "sha256": C.sha256_file(p), "mtime_utc": _mtime(p)}
            except OSError as exc:
                denied.append(f"{rel}: {exc}")
    latest = max((v["mtime_utc"] for v in files.values()), default=None)
    return {"root": root.as_posix(), "files": files, "file_count": len(files), "latest_mtime_utc": latest, "unreadable": denied,
            "digest": C.sha256_bytes("\n".join(f"{k} {v['sha256']} {v['size']}" for k, v in sorted(files.items())).encode("utf-8"))}


def snapshot(label: str) -> dict:
    out = {"label": label, "at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "trees": {k: tree_digest(v) for k, v in TREES.items()},
           "single_files": {k: {"path": v.as_posix(), "sha256": C.sha256_file(v), "mtime_utc": _mtime(v)} for k, v in SINGLE_FILES.items()},
           "git": {"candidate": C.git_state(C.CANDIDATE[0]), "baseline": C.git_state(C.BASELINE[0])},
           "ai_ledger": C.ledger_state(), "response_ledger": {"path": C.RESPONSE_LEDGER.as_posix(), "sha256": C.sha256_file(C.RESPONSE_LEDGER),
                                                                "bytes": C.RESPONSE_LEDGER.stat().st_size},
           "live_sandbox_listing": sorted(p.name for p in C.LIVE_SANDBOX_BASE.iterdir()) if C.LIVE_SANDBOX_BASE.exists() else None,
           "dispatch_authorization_files": C.authorization_files(AUTH_SEARCH_ROOTS)}
    for t in out["trees"].values():
        t["files_listing_sha256"] = t["digest"]
    return out


def compare(before: dict, after: dict) -> dict:
    diffs = {}
    for k, b in before["trees"].items():
        a = after["trees"][k]
        changed = sorted(f for f in set(b["files"]) | set(a["files"]) if b["files"].get(f, {}).get("sha256") != a["files"].get(f, {}).get("sha256")
                         or b["files"].get(f, {}).get("mtime_utc") != a["files"].get(f, {}).get("mtime_utc"))
        if changed:
            diffs[k] = changed
    singles = sorted(k for k in before["single_files"] if before["single_files"][k] != after["single_files"][k])
    return {"trees_unchanged": not diffs, "tree_differences": diffs, "single_files_unchanged": not singles, "single_file_differences": singles}


if __name__ == "__main__":
    target = pathlib.Path(sys.argv[1])
    assert target.is_absolute()
    snap = snapshot(sys.argv[2])
    sha = C.write_json_once(target, snap)
    print({"written": target.as_posix(), "sha256": sha, "trees": {k: v["file_count"] for k, v in snap["trees"].items()},
           "ledger": {k: snap["ai_ledger"][k] for k in ("entries", "scopes", "limit_amendments")}, "auth_files": snap["dispatch_authorization_files"],
           "git": snap["git"], "response": snap["response_ledger"]["sha256"]})
