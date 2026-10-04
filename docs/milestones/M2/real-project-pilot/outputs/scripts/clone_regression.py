"""Pilot step 5b (regression controls, ordinary workflow): a WAL-consistent clone of the live database (SQLite backup
API from a read-only connection), then the application's own sync + processing job -- reconciliation included, as the
document worker runs it -- for EP-30784 and EP-30088 on that clone, with business snapshots and record dumps before and
after. Originals under OneDrive are read by the app (read-only); every write goes to the clone / sandbox roots.
Usage: clone_regression.py <scratch> <profile>"""
import json, os, sys, pathlib, sqlite3, subprocess, time, datetime, shutil

S = pathlib.Path(sys.argv[1]); PROFILE = sys.argv[2]; ROOT = pathlib.Path("C:/t/pilot"); R = S / f"clone_{PROFILE}"; R.mkdir(parents=True, exist_ok=True)
LIVE = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend\ep_platform.db"); CLONE = ROOT / "db" / f"clone_{PROFILE}.db"
for ext in ("", "-wal", "-shm"):
    p = pathlib.Path(str(CLONE) + ext)
    if p.exists(): p.unlink()
src = sqlite3.connect(f"file:{LIVE.as_posix()}?mode=ro", uri=True); dst = sqlite3.connect(str(CLONE))
src.backup(dst); dst.close()
wal_before = pathlib.Path(str(LIVE) + "-wal"); info = {"live": str(LIVE), "live_wal_bytes": wal_before.stat().st_size if wal_before.exists() else 0, "clone": str(CLONE), "clone_bytes": CLONE.stat().st_size,
                                                       "backup": "sqlite3 backup API from a mode=ro connection: a consistent snapshot including the WAL", "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
src.close()
env = dict(os.environ)
env.update({"DATABASE_URL": f"sqlite:///{CLONE.as_posix()}", "CACHE_ROOT": str(ROOT / "cache"), "LIBRARY_ROOT": str(ROOT / "library"), "UPLOADS_ROOT": str(ROOT / "uploads"),
            "AI_ENABLED": "false", "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "ARCHIVE_SUBMITTAL_LIBRARY": "", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false",
            "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false", "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "DOCUMENT_CLASSIFICATION_V2": "false",
            "SYNC_FILE_WORKERS": "0", "EXTRACTION_PROMOTE_OBSERVATIONS": "true" if PROFILE == "promoted" else "false", "PYTHONIOENCODING": "utf-8", "LIBRARY_RESCAN_SECONDS": "0"})
B = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend"); PY = B / "venv" / "Scripts" / "python.exe"
timeline = []


def run(args, log):
    t0 = time.perf_counter()
    with open(log, "w", encoding="utf-8") as h:
        rc = subprocess.run([str(PY)] + args, cwd=B, env=env, stdout=h, stderr=subprocess.STDOUT).returncode
    timeline.append({"at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "cmd": " ".join(args)[:120], "rc": rc, "seconds": round(time.perf_counter() - t0, 1)}); print(rc, round(time.perf_counter() - t0, 1), "s", args[0], flush=True)


def dump(tag):
    con = sqlite3.connect(f"file:{CLONE.as_posix()}?mode=ro", uri=True); con.row_factory = sqlite3.Row; out = {}
    for r in con.execute("select d.id, d.project_id, d.relative_path, d.role, d.state, d.error, d.sha256, d.reference, d.revision, d.status, d.last_processed_at, d.extracted from project_documents d where d.project_id in (1, 4)"):
        ex = json.loads(r["extracted"]) if r["extracted"] else {}
        out[str(r["id"])] = {"project_id": r["project_id"], "path": r["relative_path"], "role": r["role"], "state": r["state"], "error": r["error"], "sha256": r["sha256"], "mirror": [r["reference"], r["revision"], r["status"]],
                             "last_processed_at": r["last_processed_at"], "parser_version": ex.get("parser_version"), "profile": ex.get("profile"), "attempt": ex.get("attempt"), "stale": ex.get("stale"), "retained": ex.get("retained"),
                             "coverage_outcome": (ex.get("coverage") or {}).get("outcome"), "records": ex.get("records") or [], "observations": ex.get("observations") or [], "form": bool(ex.get("form"))}
    con.close(); json.dump(out, open(R / f"records_{tag}.json", "w", encoding="utf-8"), indent=1, default=str)


for pid in ("1", "4"):
    run(["scripts/business_snapshot.py", pid, str(R / f"snapshot_before_p{pid}.json")], R / f"snapshot_before_p{pid}.log")
dump("before")
# the ordinary workflow: the sync job (and the processing job it queues), as the API runs it, inline
runner = R / "run_jobs.py"
runner.write_text('''import os, sys, json, time
sys.path.insert(0, r"C:\\\\Users\\\\moham\\\\Desktop\\\\dev\\\\dev\\\\ep-platform\\\\backend")
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import get_settings
import app.routers.jobs as jobs_router
jobs_router.RUN_INLINE = True
st = get_settings(); out = {}
with TestClient(app) as client:
    login = client.post("/auth/login", json={"email": st.default_admin_email, "password": st.default_admin_password}); assert login.status_code == 200, login.text
    for pid in (1, 4):
        t0 = time.perf_counter()
        job = client.post(f"/projects/{pid}/jobs/sync-documents").json()
        res = client.get(f"/jobs/{job['id']}").json()
        proc = client.get(f"/jobs/{res['result']['processing_job_id']}").json() if (res.get("result") or {}).get("processing_job_id") else None
        out[pid] = {"seconds": round(time.perf_counter() - t0, 1), "sync": {k: res.get(k) for k in ("status", "error", "result")}, "processing": {k: (proc or {}).get(k) for k in ("status", "error", "result")}}
        print(pid, res.get("status"), (proc or {}).get("status"), (proc or {}).get("result"), flush=True)
json.dump(out, open(sys.argv[1], "w"), indent=1, default=str)
''', encoding="utf-8")
run([str(runner), str(R / "jobs_sync1.json")], R / "jobs_sync1.log")
for pid in ("1", "4"):
    run(["scripts/business_snapshot.py", pid, str(R / f"snapshot_after_sync1_p{pid}.json")], R / f"snapshot_after_sync1_p{pid}.log")
dump("after_sync1")
# A parser upgrade reaches unchanged files only through the extract-only repair (the ordinary sync re-reads changed
# files): repair every reading not made by the current parser and profile, then the ordinary sync again, which
# reconciles (shop drawings, floors) from the new readings -- the domain path, as the worker runs it.
# Only the sampled rows are repaired: the two folders hold 6.7 GB of PDFs, mostly OneDrive placeholders, and the pilot
# does not bulk-download; the sampled originals are already hydrated (they were hashed and staged from them).
frozen = json.load(open(S / "FROZEN-SAMPLE.json", encoding="utf-8"))
con = sqlite3.connect(f"file:{CLONE.as_posix()}?mode=ro", uri=True)
registry = {}
for pid_, rid, rel, role, state in con.execute("select project_id, id, relative_path, role, state from project_documents where project_id in (1, 4)"):
    registry[(str(pid_), rel.replace("/", "\\").lower())] = (rid, role, state)
con.close()
ids = {"1": [], "4": []}; missing = []; matched = []
for d in frozen["documents"]:
    if d["ep"] not in ("30784", "30088"): continue
    pid = "1" if d["ep"] == "30784" else "4"
    hit = registry.get((pid, d["relative_path"].replace("/", "\\").lower()))
    if hit:
        ids[pid].append(str(hit[0])); matched.append({"pid": pid, "id": hit[0], "role": hit[1], "state": hit[2], "path": d["relative_path"]})
    else:
        missing.append(d["relative_path"])
info["matched"] = matched
info["repair_scope"] = {"rows": {k: len(v) for k, v in ids.items()}, "not_in_live_registry": missing}
for pid in ("1", "4"):
    if not ids[pid]: continue
    run(["scripts/repair_extraction.py", "--project", pid, "--ids", ",".join(ids[pid]), "--select", "parser-outdated", "--apply", "--manifest", str(R / f"repair_p{pid}.json")], R / f"repair_p{pid}.log")
for pid in ("1", "4"):
    run(["scripts/business_snapshot.py", pid, str(R / f"snapshot_after_repair_p{pid}.json")], R / f"snapshot_after_repair_p{pid}.log")
dump("after_repair")
run([str(runner), str(R / "jobs_sync2.json")], R / "jobs_sync2.log")
for pid in ("1", "4"):
    run(["scripts/business_snapshot.py", pid, str(R / f"snapshot_after_p{pid}.json")], R / f"snapshot_after_p{pid}.log")
dump("after")
json.dump({"clone": info, "profile": PROFILE, "environment": {k: env[k] for k in ("DATABASE_URL", "CACHE_ROOT", "UPLOADS_ROOT", "AI_ENABLED", "EXTRACTION_PROMOTE_OBSERVATIONS", "SYNC_FILE_WORKERS")}, "timeline": timeline}, open(R / "clone_run.json", "w", encoding="utf-8"), indent=1)
print("done")
