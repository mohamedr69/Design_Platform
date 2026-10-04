"""Pilot step 5: the application's own sync / registry / processing / persistence path over the staged trees, in a
disposable sandbox (database, cache, library, uploads all under C:/t/pilot), one database per profile. Projects are
created through the API (TestClient, no server), the sync-documents job runs inline, processing follows as the job
does it; then every row's stored reading is dumped from the database, reopened.

Usage: run_sandbox.py <scratch> <profile default|promoted> [ep,ep,...]"""
import json, os, sys, pathlib, time, datetime, sqlite3

S = pathlib.Path(sys.argv[1]); PROFILE = sys.argv[2]; ONLY = sys.argv[3].split(",") if len(sys.argv) > 3 else None
ROOT = pathlib.Path("C:/t/pilot"); DB = ROOT / "db" / f"{PROFILE}-candidateC.db"
for d in ("db", "cache", "library", "uploads", "out"):
    (ROOT / d).mkdir(parents=True, exist_ok=True)
for ext in ("", "-wal", "-shm"):
    p = pathlib.Path(str(DB) + ext)
    if p.exists():
        p.unlink()
os.environ.update({"DATABASE_URL": f"sqlite:///{DB.as_posix()}", "CACHE_ROOT": str(ROOT / "cache"), "LIBRARY_ROOT": str(ROOT / "library"), "UPLOADS_ROOT": str(ROOT / "uploads"),
                   "AI_ENABLED": "false", "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "ARCHIVE_SUBMITTAL_LIBRARY": "", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false",
                   "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false", "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "DOCUMENT_CLASSIFICATION_V2": "false",
                   "SYNC_FILE_WORKERS": "0", "EXTRACTION_PROMOTE_OBSERVATIONS": "true" if PROFILE == "promoted" else "false", "LIBRARY_RESCAN_SECONDS": "0"})
B = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend"); sys.path.insert(0, str(B)); os.chdir(B)
from app.core.config import get_settings  # noqa: E402
st = get_settings()
assert DB.as_posix() in st.database_url and str(ROOT) in st.cache_root and str(ROOT) in st.library_root and str(ROOT) in st.uploads_root, "sandbox roots not in force"
assert st.extraction_promote_observations is (PROFILE == "promoted") and not st.ai_enabled
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
import app.routers.jobs as jobs_router  # noqa: E402
jobs_router.RUN_INLINE = True
frozen = json.load(open(S / "FROZEN-SAMPLE.json", encoding="utf-8"))
manifest = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "profile": PROFILE, "database": str(DB), "settings": {"promote": st.extraction_promote_observations, "ai": st.ai_enabled, "workers": st.sync_file_workers, "tesseract": st.tesseract_cmd}, "projects": {}}
with TestClient(app) as client:
    login = client.post("/auth/login", json={"email": st.default_admin_email, "password": st.default_admin_password}); assert login.status_code == 200, login.text
    for p in frozen["projects"]:
        if ONLY and p["ep"] not in ONLY:
            continue
        stage = ROOT / "stage" / f"EP-{p['ep']}"
        if not stage.is_dir():
            manifest["projects"][p["ep"]] = {"skipped": "no staged files"}; continue
        t0 = time.perf_counter()
        created = client.post("/projects", json={"ep_number": p["ep"], "project_name": p["folder"][:80], "source_folder_path": str(stage), "design_sheets": []})
        assert created.status_code == 201, created.text
        pid = created.json()["id"]
        job = client.post(f"/projects/{pid}/jobs/sync-documents").json()
        result = client.get(f"/jobs/{job['id']}").json()
        processing = client.get(f"/jobs/{result['result']['processing_job_id']}").json() if result.get("result", {}).get("processing_job_id") else None
        status = client.get(f"/projects/{pid}/documents/status").json()
        manifest["projects"][p["ep"]] = {"project_id": pid, "cohort": p["cohort"], "seconds": round(time.perf_counter() - t0, 1), "sync_job": {k: result.get(k) for k in ("status", "error")}, "sync_result": result.get("result"),
                                         "processing_job": {k: (processing or {}).get(k) for k in ("status", "error")}, "processing_result": (processing or {}).get("result"), "documents_status": status}
        print(p["ep"], PROFILE, "sync", result.get("status"), "processing", (processing or {}).get("status"), (processing or {}).get("result", {}) and {k: (processing or {}).get("result", {}).get(k) for k in ("planned", "processed", "failed", "partial", "unavailable", "unchanged_after_hash")}, round(time.perf_counter() - t0, 1), "s", flush=True)
# dump every row, reopened
con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True); con.row_factory = sqlite3.Row
rows = {}
for r in con.execute("select d.id, d.project_id, p.ep_number, d.relative_path, d.filename, d.role, d.state, d.error, d.sha256, d.size, d.reference, d.revision, d.status, d.system_code, d.last_processed_at, d.extracted from project_documents d join projects p on p.id = d.project_id"):
    ex = json.loads(r["extracted"]) if r["extracted"] else None
    rows[f"EP-{r['ep_number']}/{r['relative_path']}"] = {"id": r["id"], "ep": r["ep_number"], "role": r["role"], "state": r["state"], "error": r["error"], "sha256": r["sha256"], "size": r["size"],
                                                         "mirror": {"reference": r["reference"], "revision": r["revision"], "status": r["status"], "system_code": r["system_code"]},
                                                         "last_processed_at": r["last_processed_at"], "extracted": ex}
tables = {t: con.execute(f"select count(*) from {t}").fetchone()[0] for t in ("project_documents", "project_submittals", "project_shop_drawings", "project_boq_items", "background_jobs", "document_dependencies", "project_actions")}
con.close()
manifest["tables"] = tables; manifest["rows"] = len(rows)
json.dump(manifest, open(S / f"RUN-{PROFILE}.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(rows, open(S / f"rows-{PROFILE}.json", "w", encoding="utf-8"), indent=1, default=str)
print("done", PROFILE, tables, "rows", len(rows))
