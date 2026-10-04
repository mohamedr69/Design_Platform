"""ORCH-06C (R36HARNESS-IMPL): read-only snapshot of every frozen tree this task must not write, the AI ledger (read-only
URI), the response ledger hash and the candidate / baseline git state.
Usage: snapshot_r36.py <out json (absolute)> <label>
Per tree: file count, a digest over (relative path, size, mtime_ns) of every file (.git folders excluded), the newest file
and every file modified after the frozen cutoff 2026-10-03T15:30:00Z. Two snapshots with equal digests prove that no file
was added, removed or modified in between. Writes only <out json>."""
import datetime
import hashlib
import json
import os
import pathlib
import sqlite3
import subprocess
import sys

PILOT = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot"
MR = "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap"
AI_LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"
RESPONSE = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/M2-REVIEW-RESPONSE.md"
CUTOFF_UTC = "2026-10-03T15:30:00Z"
TREES = {
    "review34": f"{PILOT}/review34", "review33": f"{PILOT}/review33", "review31": f"{PILOT}/review31",
    "evaluator_offline_r32": f"{PILOT}/evaluator-offline-r32", "fresh_cohort_r32": f"{PILOT}/fresh-cohort-r32",
    "fresh_cohort_r32_reviewed": f"{PILOT}/fresh-cohort-r32-reviewed", "fresh_cohort_r32_reviewed_2": f"{PILOT}/fresh-cohort-r32-reviewed-2",
    "four_arm_final": f"{PILOT}/four-arm-final", "review_folders_MR_reviews": f"{MR}/reviews", "staging_r32_stage": "C:/t/r2x/r32-stage",
    "candidate_cand_r29": "C:/t/iso/cand-r29", "baseline_frozen_r12": "C:/t/iso/frozen-r12",
    "work_r32": "C:/t/iso/work/r2x/r32", "work_r32b": "C:/t/iso/work/r2x/r32b", "work_r32c": "C:/t/iso/work/r2x/r32c",
    "work_r33": "C:/t/iso/work/r2x/r33", "work_r34": "C:/t/iso/work/r2x/r34", "work_r35": "C:/t/iso/work/r2x/r35",
    "sandbox_r33": "C:/t/r2x/r33-sandbox", "sandbox_r34": "C:/t/r2x/r34-sandbox",
}
FILES = {"ai_ledger_main_file": AI_LEDGER}


def _epoch(utc):
    return datetime.datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()


def _iso(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def tree(root):
    cut = _epoch(CUTOFF_UTC)
    h, n, newest, after, missing = hashlib.sha256(), 0, (0.0, None), [], not os.path.exists(root)
    entries = []
    for dp, dn, fn in os.walk(root):
        dn[:] = sorted(d for d in dn if d != ".git")
        for f in sorted(fn):
            p = os.path.join(dp, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            rel = os.path.relpath(p, root).replace("\\", "/")
            entries.append((rel, st.st_size, st.st_mtime_ns))
            n += 1
            if st.st_mtime > newest[0]:
                newest = (st.st_mtime, rel)
            if st.st_mtime > cut:
                after.append({"path": rel, "mtime_utc": _iso(st.st_mtime)})
    for e in sorted(entries):
        h.update(f"{e[0]}|{e[1]}|{e[2]}\n".encode("utf-8"))
    return {"root": root, "exists": not missing, "files": n, "digest": h.hexdigest(),
            "newest": {"path": newest[1], "mtime_utc": _iso(newest[0]) if newest[1] else None}, "modified_after_cutoff": after}


def ledger():
    con = sqlite3.connect(f"file:{AI_LEDGER}?mode=ro", uri=True)
    try:
        return {"entries": con.execute("select count(*) from entries").fetchone()[0],
                "scopes": con.execute("select count(*) from scopes").fetchone()[0],
                "limit_amendments": con.execute("select count(*) from limit_amendments").fetchone()[0],
                "scope_names_sha256": hashlib.sha256("|".join(r[0] for r in con.execute("select scope from scopes order by scope")).encode()).hexdigest(),
                "opened": "file:...?mode=ro, uri=True"}
    finally:
        con.close()


def git(repo):
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, env=env).stdout.strip()
    dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True, env=env).stdout.strip()
    return {"head": head, "clean": dirty == "", "porcelain": dirty.splitlines()[:20]}


def main(out, label):
    out = pathlib.Path(out)
    assert out.is_absolute()
    snap = {"label": label, "taken_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "frozen_cutoff_utc": CUTOFF_UTC, "trees": {k: tree(v) for k, v in TREES.items()},
            "files": {k: {"path": v, "sha256": hashlib.sha256(pathlib.Path(v).read_bytes()).hexdigest(),
                          "mtime_utc": _iso(os.stat(v).st_mtime)} for k, v in FILES.items()},
            "ai_ledger": ledger(),
            "response_ledger": {"path": RESPONSE, "sha256": hashlib.sha256(pathlib.Path(RESPONSE).read_bytes()).hexdigest(),
                                "bytes": os.path.getsize(RESPONSE)},
            "git": {"C:/t/iso/cand-r29": git("C:/t/iso/cand-r29"), "C:/t/iso/frozen-r12": git("C:/t/iso/frozen-r12")}}
    text = json.dumps(snap, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(out, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(json.dumps({"ai_ledger": snap["ai_ledger"], "response": snap["response_ledger"]["sha256"],
                      "after_cutoff": {k: len(v["modified_after_cutoff"]) for k, v in snap["trees"].items() if v["modified_after_cutoff"]},
                      "files": {k: v["files"] for k, v in snap["trees"].items()}, "git": {k: (v["head"][:8], v["clean"]) for k, v in snap["git"].items()}},
                     indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
