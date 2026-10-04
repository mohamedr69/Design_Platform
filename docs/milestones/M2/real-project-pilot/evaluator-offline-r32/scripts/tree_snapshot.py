"""ORCH-06 (R35EVAL-IMPL): modification-time snapshot of the frozen trees and the candidate tree.

Usage: tree_snapshot.py <out json abs> [<label>]
Read-only: walks each tree with os.walk and records, per tree, the file count, the newest file and every file whose
mtime is after the task start (2026-10-03T13:46:07Z) or after the frozen cutoff (2026-10-03T13:50:00Z).
Writes only <out json>."""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import sys

START_UTC = "2026-10-03T13:46:07Z"
FROZEN_CUTOFF_UTC = "2026-10-03T13:50:00Z"
PILOT = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot"
MR = "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap"
TREES = {
    "candidate_cand_r29": ("C:/t/iso/cand-r29", START_UTC, ()),
    "review34": (f"{PILOT}/review34", FROZEN_CUTOFF_UTC, ()),
    "review33": (f"{PILOT}/review33", FROZEN_CUTOFF_UTC, ()),
    "review31": (f"{PILOT}/review31", FROZEN_CUTOFF_UTC, ()),
    "fresh_cohort_r32": (f"{PILOT}/fresh-cohort-r32", FROZEN_CUTOFF_UTC, ()),
    "fresh_cohort_r32_reviewed": (f"{PILOT}/fresh-cohort-r32-reviewed", FROZEN_CUTOFF_UTC, ()),
    "fresh_cohort_r32_reviewed_2": (f"{PILOT}/fresh-cohort-r32-reviewed-2", FROZEN_CUTOFF_UTC, ()),
    "four_arm_final": (f"{PILOT}/four-arm-final", FROZEN_CUTOFF_UTC, ()),
    "review_folders_MR_reviews": (f"{MR}/reviews", FROZEN_CUTOFF_UTC, ()),
    "staging_r32_stage": ("C:/t/r2x/r32-stage", FROZEN_CUTOFF_UTC, ()),
    "ep_platform_backend_excluding_venv": ("C:/Users/moham/Desktop/dev/dev/ep-platform/backend", FROZEN_CUTOFF_UTC, ("venv",)),
}


def _epoch(utc: str) -> float:
    return datetime.datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()


def _iso(ts: float) -> str:
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def snapshot_tree(root: str, cutoff_utc: str, skip_top: tuple = ()) -> dict:
    cutoff = _epoch(cutoff_utc)
    start = _epoch(START_UTC)
    count, newest, after_cutoff, after_start, unreadable = 0, (0.0, None), [], [], []
    rootp = pathlib.Path(root)
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: unreadable.append(str(e.filename))):
        if pathlib.Path(dirpath) == rootp and skip_top:
            dirnames[:] = [d for d in dirnames if d not in skip_top]
        for name in filenames:
            p = os.path.join(dirpath, name)
            try:
                m = os.stat(p).st_mtime
            except OSError:
                unreadable.append(p)
                continue
            count += 1
            if m > newest[0]:
                newest = (m, p.replace("\\", "/"))
            if m > cutoff:
                after_cutoff.append({"path": p.replace("\\", "/"), "mtime_utc": _iso(m)})
            if m > start:
                after_start.append({"path": p.replace("\\", "/"), "mtime_utc": _iso(m)})
    return {"root": root, "cutoff_utc": cutoff_utc, "skipped_top_level": list(skip_top), "files": count,
            "newest": {"path": newest[1], "mtime_utc": _iso(newest[0]) if newest[1] else None},
            "modified_after_cutoff": sorted(after_cutoff, key=lambda x: x["path"]),
            "modified_after_task_start": sorted(after_start, key=lambda x: x["path"]), "unreadable": unreadable[:50],
            "unreadable_count": len(unreadable)}


def snapshot(label: str = "") -> dict:
    return {"label": label, "taken_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "task_start_utc": START_UTC, "frozen_cutoff_utc": FROZEN_CUTOFF_UTC,
            "trees": {k: snapshot_tree(root, cut, skip) for k, (root, cut, skip) in TREES.items()}}


if __name__ == "__main__":
    out = pathlib.Path(sys.argv[1])
    assert out.is_absolute(), out
    snap = snapshot(sys.argv[2] if len(sys.argv) > 2 else "")
    out.write_text(json.dumps(snap, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: {"files": v["files"], "after_cutoff": len(v["modified_after_cutoff"]),
                          "after_start": len(v["modified_after_task_start"]), "newest": v["newest"]["mtime_utc"]}
                      for k, v in snap["trees"].items()}, indent=1))
