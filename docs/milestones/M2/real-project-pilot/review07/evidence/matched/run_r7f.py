"""Review 06 sandbox run: the isolated candidate's own sync / processing / persistence path over staged copies, in a
disposable sandbox under C:/t/r6/<tag> (database, cache, library, uploads). Projects are created through the API
(TestClient, no server); the sync-documents job runs inline with its processing; every row's stored reading is then
dumped from the database, reopened.

Usage: run_r6.py <stage_root> <tag> <profile default|promoted> [--eps a,b] [--ai EVx|app] [--budget-json file]
  --ai app : the application's existing AI path (AI_ENABLED=true, evidence reader off)   = AI-EV0 with a real model
  --ai EV1 / EV2 : the application's AI path plus the evidence reader variant
  (no --ai): AI disabled -- the deterministic / model-disabled track."""
import argparse, datetime, json, os, pathlib, sqlite3, sys, time

a = argparse.ArgumentParser()
a.add_argument("stage"); a.add_argument("tag"); a.add_argument("profile"); a.add_argument("--eps"); a.add_argument("--ai")
a.add_argument("--budget-json"); a.add_argument("--fresh-db", action="store_true", default=True)
args = a.parse_args()
STAGE = pathlib.Path(args.stage); ROOT = pathlib.Path("C:/t/r7") / args.tag; DB = ROOT / "db" / f"{args.profile}.db"
for d in ("db", "cache", "library", "uploads", "out"):
    (ROOT / d).mkdir(parents=True, exist_ok=True)
for ext in ("", "-wal", "-shm"):
    p = pathlib.Path(str(DB) + ext)
    if p.exists():
        p.unlink()
env = {"DATABASE_URL": f"sqlite:///{DB.as_posix()}", "CACHE_ROOT": str(ROOT / "cache"), "LIBRARY_ROOT": str(ROOT / "library"), "UPLOADS_ROOT": str(ROOT / "uploads"),
       "AI_ENABLED": "false", "AI_EVIDENCE_VARIANT": "off", "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "ARCHIVE_SUBMITTAL_LIBRARY": "",
       "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false", "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false",
       "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "DOCUMENT_CLASSIFICATION_V2": "false", "SYNC_FILE_WORKERS": "0",
       "EXTRACTION_PROMOTE_OBSERVATIONS": "true" if args.profile == "promoted" else "false", "LIBRARY_RESCAN_SECONDS": "0"}
if args.ai:
    env.update({"AI_ENABLED": "true", "AI_PROVIDER": "claude-code", "AI_MODEL_SMALL": "sonnet", "AI_MODEL_STANDARD": "opus",
                "AI_EVIDENCE_VARIANT": args.ai if args.ai in ("EV1", "EV2") else "off"})
    if args.budget_json:
        env.update({k: str(v) for k, v in json.load(open(args.budget_json, encoding="utf-8"))["settings"].items()})
os.environ.update(env)
B = pathlib.Path(r"C:\t\iso\frozen-r7\backend"); sys.path.insert(0, str(B)); os.chdir(B)
from app.core.config import get_settings  # noqa: E402
st = get_settings()
assert DB.as_posix() in st.database_url and str(ROOT) in st.cache_root and str(ROOT) in st.library_root and str(ROOT) in st.uploads_root, "sandbox roots not in force"
assert st.extraction_promote_observations is (args.profile == "promoted") and st.ai_enabled is bool(args.ai)
import app  # noqa: E402
assert pathlib.Path(app.__file__).resolve().is_relative_to(B.resolve()), app.__file__
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app as api  # noqa: E402
import app.routers.jobs as jobs_router  # noqa: E402
from app.services import document_control  # noqa: E402
jobs_router.RUN_INLINE = True
eps = sorted(p.name for p in STAGE.iterdir() if p.is_dir() and p.name.startswith("EP-"))
if args.eps:
    eps = [e for e in eps if e[3:] in args.eps.split(",")]
manifest = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "tag": args.tag, "profile": args.profile, "stage": str(STAGE),
            "database": str(DB), "parser": document_control.PARSER_VERSION, "ai": args.ai,
            "settings": {k: getattr(st, k) for k in ("extraction_promote_observations", "ai_enabled", "ai_provider", "ai_model_small", "ai_model_standard",
                                                     "ai_evidence_variant", "sync_file_workers", "tesseract_cmd", "ai_max_calls_per_document",
                                                     "ai_max_calls_per_project_per_day", "ai_max_elapsed_s_per_job", "ai_max_escalations_per_document",
                                                     "ai_price_input_per_million", "ai_price_output_per_million", "ai_max_concurrency")}, "projects": {}}
with TestClient(api) as client:
    login = client.post("/auth/login", json={"email": st.default_admin_email, "password": st.default_admin_password}); assert login.status_code == 200, login.text
    for ep in eps:
        t0 = time.perf_counter()
        created = client.post("/projects", json={"ep_number": ep[3:], "project_name": ep, "source_folder_path": str(STAGE / ep), "design_sheets": []})
        assert created.status_code == 201, created.text
        pid = created.json()["id"]
        job = client.post(f"/projects/{pid}/jobs/sync-documents").json()
        result = client.get(f"/jobs/{job['id']}").json()
        processing = client.get(f"/jobs/{result['result']['processing_job_id']}").json() if (result.get("result") or {}).get("processing_job_id") else None
        manifest["projects"][ep] = {"project_id": pid, "seconds": round(time.perf_counter() - t0, 1), "sync_job": {k: result.get(k) for k in ("status", "error")},
                                    "processing_job": {k: (processing or {}).get(k) for k in ("status", "error")}, "processing_result": (processing or {}).get("result")}
        print(ep, args.profile, "processing", (processing or {}).get("status"), {k: ((processing or {}).get("result") or {}).get(k) for k in ("planned", "processed", "failed", "partial", "read_by_ai", "ai_evidence")}, round(time.perf_counter() - t0, 1), "s", flush=True)
con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True); con.row_factory = sqlite3.Row
rows = {}
for r in con.execute("select d.id, p.ep_number, d.relative_path, d.role, d.state, d.error, d.sha256, d.size, d.reference, d.revision, d.status, d.system_code, d.extracted from project_documents d join projects p on p.id = d.project_id"):
    rows[f"EP-{r['ep_number']}/{r['relative_path']}"] = {"id": r["id"], "ep": r["ep_number"], "role": r["role"], "state": r["state"], "error": r["error"], "sha256": r["sha256"], "size": r["size"],
                                                         "mirror": {"reference": r["reference"], "revision": r["revision"], "status": r["status"], "system_code": r["system_code"]},
                                                         "extracted": json.loads(r["extracted"]) if r["extracted"] else None}
usage = [dict(u) for u in con.execute("select project_id, task, model, input_tokens, output_tokens, cached_input_tokens, estimated_cost, latency_ms, cache_hit, escalated, outcome, at from ai_usage order by id")]
tables = {t: con.execute(f"select count(*) from {t}").fetchone()[0] for t in ("project_documents", "project_submittals", "project_shop_drawings", "background_jobs", "project_actions", "ai_usage", "document_readings")}
con.close()
manifest.update({"tables": tables, "rows": len(rows), "ai_usage_rows": len(usage)})
out = ROOT / "out"
json.dump(manifest, open(out / f"RUN-{args.profile}.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(rows, open(out / f"rows-{args.profile}.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(usage, open(out / f"usage-{args.profile}.json", "w", encoding="utf-8"), indent=1, default=str)
print("done", args.tag, args.profile, tables, "rows", len(rows))
