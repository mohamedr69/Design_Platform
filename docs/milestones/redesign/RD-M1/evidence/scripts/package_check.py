"""RD-M1 package validation. Read-only towards the repository, uploads and the live DB
(live DB opened mode=ro + query_only). Writes only three JSON files into the package.

usage: python package_check.py <package dir>    (expects ISO/hash/AFTER-T1.json to exist)
"""
import glob
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from q import run  # noqa: E402  (snapshot, query-only)

PKG = os.path.abspath(sys.argv[1])
EP = r"G:\dev (2)\dev\ep-platform"
PKG_REL = "docs/milestones/redesign/RD-M1/"
LIVE_DB = os.path.join(EP, "backend", "ep_platform.db")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


t0 = json.load(open(os.path.join(ROOT, "hash", "BASELINE-T0.json")))
t1 = json.load(open(os.path.join(ROOT, "hash", "AFTER-T1.json")))
checks = {}


def check(name, ok, **detail):
    checks[name] = {"pass": bool(ok), **detail}


# 1. working tree: application / tracked-or-untracked files
g0, g1 = t0["groups"]["ep_platform_git_visible"], t1["groups"]["ep_platform_git_visible"]
changed = [k for k in g0 if k in g1 and g0[k]["sha256"] != g1[k]["sha256"]]
removed = [k for k in g0 if k not in g1]
added = [k for k in g1 if k not in g0]
added_outside = [k for k in added if not k.startswith(PKG_REL)]
check("no_application_file_changes", not changed and not removed and not added_outside,
      files_compared=len(g0), changed=changed, removed=removed, added_inside_package=len(added) - len(added_outside),
      added_outside_package=added_outside)

# 2. uploads (source drawings, prior outputs, wall index, work-1), redesign library, .env
i0, i1 = t0["groups"]["ep_platform_ignored_relevant"], t1["groups"]["ep_platform_ignored_relevant"]
live_db = {"backend/ep_platform.db", "backend/ep_platform.db-wal", "backend/ep_platform.db-shm"}
diff_up = [k for k in i0 if k not in live_db and (k not in i1 or i0[k].get("sha256") != i1[k].get("sha256"))]
new_up = [k for k in i1 if k not in i0 and k not in live_db]
check("no_source_drawing_or_upload_changes", not diff_up and not new_up,
      files_compared=len([k for k in i0 if k not in live_db]), changed_or_removed=diff_up, added=new_up)
check("live_db_files_metadata", True, note="Live DB/WAL/SHM change through the owner's services (expected); content safety is check 8.",
      t0={k: i0.get(k) for k in live_db}, t1={k: i1.get(k) for k in live_db})

# 3. outer repo: only the owner's live service logs may change
o0, o1 = t0["groups"]["outer_repo_git_visible"], t1["groups"]["outer_repo_git_visible"]
o_changed = [k for k in o0 if k not in o1 or o0[k]["sha256"] != o1[k]["sha256"]]
o_unexpected = [k for k in o_changed if not k.endswith(".log")]
check("outer_repo_only_service_logs_changed", not o_unexpected, changed=o_changed, unexpected=o_unexpected,
      added=[k for k in o1 if k not in o0])

# 4. selected source hashes (GC-01) now vs T0 vs DB
src = {
    "source_dwg": "backend/uploads/EP-30880/ifc/60de2a377daa.dwg",
    "source_dxf": "backend/uploads/EP-30880/ifc/60de2a377daa.dxf",
    "review_pdf": "backend/uploads/EP-30880/review/66043c11fab9eaf5a1768ba2.pdf",
    "wall_index": "backend/uploads/EP-30880/redesign/walls-1-66043c11fab9eaf5-v1.pkl",
    "apply_script": "backend/uploads/EP-30880/redesign/work-1/redesign.scr",
    "apply_work_copy": "backend/uploads/EP-30880/redesign/work-1/redesign.dwg",
    "lib_CT2": "backend/app/redesign/library/CT2.dwg",
}
now = {k: sha(os.path.join(EP, v)) for k, v in src.items()}
rd = run("SELECT source_sha256 FROM project_redesign WHERE id=1")[0]["source_sha256"]
rv = run("SELECT source_sha256, pdf_path FROM project_drawing_reviews WHERE id=1")[0]
check("selected_source_hashes", all(now[k] == i0[v]["sha256"] for k, v in src.items())
      and now["source_dwg"] == rd == rv["source_sha256"] and now["apply_work_copy"] == now["source_dwg"]
      and now["apply_script"] == "e2daf55bfe7edf4f9d0f93d0c646135b5eb4c9119bfd7b3af37e854ef9d019a0",
      now=now, redesign_source_sha256=rd, review_source_sha256=rv["source_sha256"], review_pdf_path=rv["pdf_path"])

# 5. evidence image bindings
ri = json.load(open(os.path.join(PKG, "evidence", "E17-render-index.json")))
bad = []
n = 0
for r in ri:
    for fn, h in r["sha256"].items():
        n += 1
        p = os.path.join(PKG, r["folder"], fn)
        if not os.path.isfile(p) or sha(p) != h:
            bad.append(fn)
check("evidence_image_bindings", not bad and n == 26, images=n, mismatched=bad)

# 6. DB ids referenced
snap_sha = json.load(open(os.path.join(ROOT, "hash", "DB-SNAPSHOT-INFO.json")))["snapshot_sha256"]
text = "".join(open(p, encoding="utf-8").read() for p in glob.glob(os.path.join(PKG, "*.md")) + [os.path.join(PKG, "FAILURE-INVENTORY.csv")])
change_ids = set(re.findall(r"\b[0-9a-f]{16}\b", text)) | set(re.findall(r"if:[0-9a-f]{12}:(?:CT1|CT2|CR)\d", text))
stored = {c["id"]: c for c in json.loads(run("SELECT changes FROM project_redesign WHERE id=1")[0]["changes"])}
known_hashes = [v.get("sha256", "") for grp in t0["groups"].values() for v in grp.values()] + [
    "e2daf55bfe7edf4f9d0f93d0c646135b5eb4c9119bfd7b3af37e854ef9d019a0", snap_sha]
hash_prefixes = sorted(i for i in change_ids if any(h.startswith(i) for h in known_hashes))
change_ids -= set(hash_prefixes)
missing_changes = sorted(i for i in change_ids if i not in stored)
job_ids = [96, 99, 101, 102, 103, 118, 119, 120, 121]
jobs = {r["id"]: r for r in run("SELECT id, kind, status FROM background_jobs WHERE id IN (%s)" % ",".join(map(str, job_ids)))}
ai_ids = [686, 687, 688, 689, 690, 728, 729]
ai = run("SELECT id FROM ai_usage WHERE task='fa_drawing_redesign' AND id IN (%s)" % ",".join(map(str, ai_ids)))
d895 = stored.get("d89599d510abfedf", {})
others = {
    "project_5_ep": run("SELECT ep_number FROM projects WHERE id=5")[0]["ep_number"],
    "ifc_drawing_1": run("SELECT filename FROM project_ifc_drawings WHERE id=1 AND project_id=5")[0]["filename"],
    "activity_max_972": run("SELECT max(id) m FROM activity_events")[0]["m"],
}
check("db_ids_referenced", not missing_changes and len(jobs) == len(job_ids) and len(ai) == len(ai_ids)
      and (d895.get("remove") or {}).get("handle") == "5DD10" and others["project_5_ep"] == "30880",
      change_ids_checked=len(change_ids), missing_change_ids=missing_changes, hash_prefixes_excluded=hash_prefixes,
      jobs={k: f"{v['kind']}/{v['status']}" for k, v in jobs.items()}, ai_usage_ids_found=[r["id"] for r in ai], **others)

# 7. code line references (curated: file, line, expected substring)
B = os.path.join(EP, "backend", "app")
REFS = [
    ("redesign/service.py", 435, '"library": (LIBRARY / f"{code}.dwg").resolve().as_posix()'),
    ("redesign/service.py", 600, "def _merge_interfaces"),
    ("redesign/service.py", 667, "def _drawn"),
    ("redesign/service.py", 670, 'c.get("source") != INTERFACE'),
    ("redesign/service.py", 825, "EXISTING_RADIUS_M = 0.25"),
    ("redesign/service.py", 880, "def coordinate"),
    ("redesign/service.py", 1059, 'fixed[c["page"]].append(c)'),
    ("redesign/service.py", 1134, 'old.get("moved") or old.get("edited")'),
    ("redesign/service.py", 1312, "stale = [c for c in row.changes"),
    ("redesign/service.py", 1314, 'not c["insert"].get("library")'),
    ("redesign/service.py", 1376, "refresh(db, project, drawing, row)"),
    ("redesign/service.py", 1390, "if project.source_folder_path:"),
    ("redesign/service.py", 1401, "row.output_path"),
    ("redesign/service.py", 1425, "review.build(db, project, drawing)"),
    ("redesign/service.py", 528, 'px, py = _page(sh["geometry"], *anchor)'),
    ("redesign/service.py", 282, 'if "|" in o["block"]'),
    ("redesign/cad.py", 114, 'if insert.get("library"):'),
    ("redesign/cad.py", 120, "(entdel (entlast))"),
    ("redesign/cad.py", 167, "copy.stat().st_mtime <= before"),
    ("redesign/walls.py", 164, "NOT_WALLS.search(entity.dxf.get(\"layer\""),
    ("redesign/ai.py", 74, '"candidate": candidate if 1 <= candidate <= candidates else 0'),
    ("review/geometry.py", 75, "def to_model"),
    ("review/service.py", 400, "if _fit(project, drawing, row):"),
    ("services/jobs.py", 106, "MAX_ATTEMPTS = 2"),
    ("services/jobs.py", 351, "def recover_stale"),
    ("core/config.py", 149, "Never the archive itself"),
    ("interfaces/service.py", 621, '"anchor": (it["x"], it["y"])'),
    ("routers/redesign.py", 163, "service.state(db, project, drawing_id)"),
    ("ifc/services/runners.py", 266, "def _redesign"),
]
ref_bad = []
for rel, line, sub in REFS:
    lines = open(os.path.join(B, rel), encoding="utf-8").read().splitlines()
    if line > len(lines) or sub not in lines[line - 1]:
        ref_bad.append(f"{rel}:{line}")
fe = open(os.path.join(EP, "frontend", "src", "pages", "ProjectRedesignPage.tsx"), encoding="utf-8").read().splitlines()
if "Placed, to approve" not in fe[291]:
    ref_bad.append("ProjectRedesignPage.tsx:292")
check("code_line_references", not ref_bad, curated_checked=len(REFS) + 1, failed=ref_bad)

# 8. live DB: no change caused by this task (read-only probe)
c = sqlite3.connect("file:" + urllib.parse.quote(LIVE_DB.replace("\\", "/")) + "?mode=ro", uri=True)
c.execute("PRAGMA query_only=ON")
live = {
    "redesign_row": c.execute("SELECT status, output_status, updated_at FROM project_redesign WHERE id=1").fetchone(),
    "max_job_id": c.execute("SELECT max(id) FROM background_jobs").fetchone()[0],
    "max_activity_id": c.execute("SELECT max(id) FROM activity_events").fetchone()[0],
    "max_ai_usage_id": c.execute("SELECT max(id) FROM ai_usage").fetchone()[0],
    "redesign_result_cache_rows": c.execute("SELECT count(*) FROM result_cache WHERE task='fa_drawing_redesign'").fetchone()[0],
}
live["probe_total_changes"] = c.total_changes
c.close()
check("live_db_not_changed_by_audit",
      live["redesign_row"][2] == "2026-10-03 15:28:00.097343" and live["max_job_id"] == 121 and live["max_activity_id"] == 972
      and live["max_ai_usage_id"] == 729 and live["redesign_result_cache_rows"] == 33 and live["probe_total_changes"] == 0,
      live=live, note="All audit DB access: backup API from a mode=ro source + mode=ro/query_only queries; snapshot total_changes 0.")

# 9. no private names in the package (names derived at run time, never written here)
jobs_all = run("SELECT DISTINCT worker_id FROM background_jobs WHERE worker_id IS NOT NULL")
hosts = {w["worker_id"].split(":")[1] for w in jobs_all if not w["worker_id"].split(":")[1].isdigit()}  # "inline:<pid>" ids carry PIDs
pname = run("SELECT project_name FROM projects WHERE id=5")[0]["project_name"] or ""
needles = [h for h in hosts if h] + [os.environ.get("USERNAME", "")] + [w for w in re.findall(r"[A-Z]{5,}", pname)]
pa_user = None
for cc in stored.values():
    lib = (cc.get("insert") or {}).get("library") or ""
    m = re.match(r"<PC-A user profile>/]+)/", lib)
    if m:
        pa_user = m.group(1)
        break
if pa_user:
    needles.append(pa_user)
hits = []
for p in glob.glob(os.path.join(PKG, "**", "*"), recursive=True):
    if os.path.isfile(p) and not p.endswith(".png"):
        t = open(p, encoding="utf-8", errors="replace").read()
        for nd in needles:
            if nd and re.search(r"(?<![A-Za-z])" + re.escape(nd) + r"(?![A-Za-z])", t, re.I):
                hits.append(os.path.relpath(p, PKG))
        # organisation-name variants: the sibling clone folder and OneDrive org (independent review round 1, note 3)
        if re.search(r"[A-Z]{4,}-AL-[A-Z]{4,}---AI-PLATFORM|OneDrive - <org>", t):
            hits.append(os.path.relpath(p, PKG))
check("no_private_names_in_package", not hits, names_checked=len([n for n in needles if n]), files_with_hits=sorted(set(hits)))

# 10. required files
REQ = ["RD-M1-REPORT.md", "CURRENT-PIPELINE.md", "BASELINE-MANIFEST.json", "GOLDEN-CASE-SELECTION.md", "FAILURE-INVENTORY.csv",
       "FAILURE-INVENTORY.md", "REPRODUCTION-RUNBOOK.md", "TEST-RESULTS.md", "DATA-SAFETY-REPORT.md",
       "NEXT-MILESTONE-HANDOFF.md", "COMMANDS.md", "evidence", "renders", "crops"]

# BASELINE-MANIFEST.json
code_keys = [k for k in g0 if any(s in k for s in ("backend/app/redesign/", "backend/app/routers/redesign.py",
            "backend/app/review/", "backend/app/interfaces/", "backend/app/ifc/services/runners.py", "backend/app/services/jobs.py",
            "backend/app/core/config.py", "backend/app/compliance/assist.py", "backend/tests/test_redesign.py",
            "backend/tests/test_drawing_review.py", "backend/tests/test_fa_interfaces.py", "backend/tests/test_ifc_worker_and_ai.py",
            "backend/tests/conftest.py", "frontend/src/pages/ProjectRedesignPage.tsx",
            "backend/alembic/versions/c5e7a9b1d3f5_drawing_redesign.py"))]
snap = json.load(open(os.path.join(ROOT, "hash", "DB-SNAPSHOT-INFO.json")))
status_lines = open(os.path.join(ROOT, "hash", "git-status-ep-T0.txt"), encoding="utf-8").read().splitlines()
baseline = {
    "milestone": "RD-M1", "taken_at_T0": t0["taken_at"], "checked_at_T1": t1["taken_at"],
    "repository": EP, "git_head": "13eb73ce85e5ac55c14303efe9d8511090ace723", "git_branch": "main",
    "outer_repository": {"path": r"G:\dev (2)\dev", "head": "e2d8cfdb8376599562f6ec91f519c2efb7d43f54", "branch": "master",
                         "gitlink_ep_platform": "d3bea8b481a04af0fff7fc4c1bc86abb48c6df80"},
    "working_tree_status_T0": status_lines,
    "full_hash_baseline": {"file": "BASELINE-T0.json (kept in the isolated area; not packaged: lists other projects' upload names)",
                           "sha256": sha(os.path.join(ROOT, "hash", "BASELINE-T0.json")),
                           "counts": {k: len(v) for k, v in t0["groups"].items()}},
    "code_files": {k: g0[k] for k in sorted(code_keys)},
    "redesign_library": {k: i0[k] for k in i0 if "redesign/library" in k},
    "runtime": {"python": "CPython 3.12.10 (Desktop venv launcher; G venv points to a missing Python 3.13)",
                "node": "v24.14.0", "vite": "^8.2.2", "autocad": "AutoCAD 2027 Core Console, build 26.0.118.0.0",
                "libs": {"ezdxf": "1.4.4", "pymupdf": "1.28.2", "pillow": "12.3.0", "sqlalchemy": "2.0.36", "fastapi": "0.115.6", "pytest": "8.3.4"}},
    "database": {"type": "SQLite WAL", "live_path": "backend/ep_platform.db (relative DATABASE_URL, DATA_ROOT unset)",
                 "snapshot": {k: snap[k] for k in ("snapshot_sha256", "snapshot_size", "snapshot_started_utc", "snapshot_finished_utc",
                                                    "method", "integrity_check", "alembic_version", "source_journal_mode",
                                                    "snapshot_total_changes_during_checks", "sqlite_version")},
                 "table_count": len(snap["table_counts"]), "table_counts": snap["table_counts"]},
    "config_non_secret": {"AI_ENABLED": True, "AI_PROVIDER": "claude-code", "drawing_review_model": "claude-opus-5-5",
                          "drawing_review_parallel": 2, "drawing_review_timeout_s": 600, "redesign_prompt_version": "drawing-redesign-2026-10-02.4",
                          "redesign_feature_flag": None, "project_5_ai_policy": "allowed"},
    "services": {"G_copy": {"api": "127.0.0.1:8001", "vite": [5174, 5175], "workers": ["sync_worker", "ifc_worker"]},
                 "Desktop_copy": {"api": "127.0.0.1:8000", "vite": [5173], "workers": ["sync_worker", "document_worker", "ifc_worker"]}},
    "golden_case": {"GC-01": {"project_id": 5, "ep": "30880", "drawing_id": 1, "redesign_id": 1, "review_id": 1,
                              "source_sha256": rd, "files": {k: {"path": v.replace("backend/uploads/EP-30880/", "GC01:"), "sha256": now[k]}
                                                             for k, v in src.items()}}},
}
json.dump(baseline, open(os.path.join(PKG, "BASELINE-MANIFEST.json"), "w", encoding="utf-8", newline="\n"), indent=1)

missing_req = [r for r in REQ if not os.path.exists(os.path.join(PKG, r))]
check("required_files_present", not missing_req, missing=missing_req)
result = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "all_pass": all(v["pass"] for v in checks.values()), "checks": checks}
json.dump(result, open(os.path.join(PKG, "PACKAGE-CHECK.json"), "w", encoding="utf-8", newline="\n"), indent=1, default=str)

# PACKAGE-MANIFEST.json (all files except itself)
files = {}
for p in sorted(glob.glob(os.path.join(PKG, "**", "*"), recursive=True)):
    if os.path.isfile(p) and os.path.basename(p) != "PACKAGE-MANIFEST.json":
        files[os.path.relpath(p, PKG).replace(os.sep, "/")] = {"sha256": sha(p), "size": os.path.getsize(p)}
json.dump({"package": PKG_REL, "files": len(files), "bytes": sum(v["size"] for v in files.values()), "entries": files},
          open(os.path.join(PKG, "PACKAGE-MANIFEST.json"), "w", encoding="utf-8", newline="\n"), indent=1)
print(json.dumps({k: v["pass"] for k, v in checks.items()}, indent=1), "\nall_pass:", result["all_pass"])
