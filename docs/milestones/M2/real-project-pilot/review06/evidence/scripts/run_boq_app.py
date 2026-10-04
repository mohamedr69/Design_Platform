"""Review 06 BOQ: the application's own Design Sheet path in a sandbox (C:/t/r6/<tag>), over the four eligible sheets
(projects with an explicit `allowed` AI policy). --ai: AI-EV0 (the model path, app.ai.sheet_reader); without: the
model-disabled application behaviour. POST /projects/{id}/boq/ensure (twice: idempotence), a boq-reread job (no
removal), the stored BOQ read back; then the sheet's reading as the app combines it (the router's _read_design_sheet,
from the stored reading: no new call) is written in the BOQ evaluator's extraction shape for scoring.
Usage: run_boq_app.py <tag> [--ai] [--budget-json f]"""
import argparse, dataclasses, datetime, json, os, pathlib, sqlite3, sys, time

a = argparse.ArgumentParser(); a.add_argument("tag"); a.add_argument("--ai", action="store_true"); a.add_argument("--budget-json")
args = a.parse_args()
ROOT = pathlib.Path("C:/t/r6") / args.tag; DB = ROOT / "db" / "boq.db"
for d in ("db", "cache", "library", "uploads", "out"):
    (ROOT / d).mkdir(parents=True, exist_ok=True)
for ext in ("", "-wal", "-shm"):
    p = pathlib.Path(str(DB) + ext)
    if p.exists():
        p.unlink()
env = {"DATABASE_URL": f"sqlite:///{DB.as_posix()}", "CACHE_ROOT": str(ROOT / "cache"), "LIBRARY_ROOT": str(ROOT / "library"), "UPLOADS_ROOT": str(ROOT / "uploads"),
       "AI_ENABLED": "true" if args.ai else "false", "AI_PROVIDER": "claude-code", "AI_MODEL_SMALL": "sonnet", "AI_MODEL_STANDARD": "opus", "AI_EVIDENCE_VARIANT": "off",
       "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "ARCHIVE_SUBMITTAL_LIBRARY": "", "PROJECTS_ROOT": "C:/t/pilot/stage", "PROJECTS_ROOT_AUTODETECT": "false",
       "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false", "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "DOCUMENT_CLASSIFICATION_V2": "false",
       "SYNC_FILE_WORKERS": "0", "LIBRARY_RESCAN_SECONDS": "0"}
if args.budget_json:
    env.update({k: str(v) for k, v in json.load(open(args.budget_json, encoding="utf-8"))["settings"].items()})
os.environ.update(env)
B = pathlib.Path(r"C:\t\iso\ep-platform\backend"); sys.path.insert(0, str(B)); os.chdir(B)
from app.core.config import get_settings  # noqa: E402
st = get_settings(); assert DB.as_posix() in st.database_url and st.ai_enabled is args.ai and str(ROOT) in st.cache_root
import app  # noqa: E402
assert pathlib.Path(app.__file__).resolve().is_relative_to(B.resolve())
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app as api  # noqa: E402
import app.routers.jobs as jobs_router  # noqa: E402
jobs_router.RUN_INLINE = True
STAGE = pathlib.Path(r"C:\t\pilot\stage")
SHEETS = {"30784": [("FAS", "01- EP-30784 Scan/EP-30784 FAS Design.pdf"), ("ELS", "01- EP-30784 Scan/EP-30784 EML Design.pdf")],
          "30088": [("FAS", "01. Commercial Document/EP-30088 Design Sheet FAS.pdf"), ("ELS", "01. Commercial Document/EP-30088 Design Sheet ELS.pdf")]}
out = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "tag": args.tag, "ai": args.ai, "database": str(DB), "projects": {}}
extractions = {}


def body(r):
    return r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:400]


with TestClient(api) as client:
    assert client.post("/auth/login", json={"email": st.default_admin_email, "password": st.default_admin_password}).status_code == 200
    for ep, sheets in SHEETS.items():
        paths = {str(STAGE / f"EP-{ep}" / rel): rel for _, rel in sheets}
        created = client.post("/projects", json={"ep_number": ep, "project_name": f"EP-{ep}", "source_folder_path": str(STAGE / f"EP-{ep}"),
                                                 "design_sheets": [{"system_code": c, "document_path": str(STAGE / f"EP-{ep}" / rel)} for c, rel in sheets]})
        assert created.status_code == 201, created.text
        pid = created.json()["id"]
        entry = {"project_id": pid}
        t0 = time.perf_counter()
        first = client.post(f"/projects/{pid}/boq/ensure")
        b1 = body(first)
        entry["ensure_1"] = {"status": first.status_code, "seconds": round(time.perf_counter() - t0, 1),
                             "items": len(b1.get("items") or []) if isinstance(b1, dict) else None,
                             "warnings": b1.get("warnings") if isinstance(b1, dict) else b1}
        items_before = client.get(f"/projects/{pid}/boq").json()
        second = client.post(f"/projects/{pid}/boq/ensure")
        b2 = body(second)
        entry["ensure_2"] = {"status": second.status_code, "items": len(b2.get("items") or []) if isinstance(b2, dict) else None}
        reread = client.post(f"/projects/{pid}/jobs/boq-reread")
        entry["reread"] = {"status": reread.status_code,
                           "job": client.get(f"/jobs/{reread.json()['id']}").json() if reread.status_code == 202 else body(reread)}
        items_after = client.get(f"/projects/{pid}/boq").json()
        before_ids = {i["id"] for i in items_before}
        after_ids = {i["id"] for i in items_after}
        entry["items_before_reread"] = len(items_before)
        entry["items_after_reread"] = len(items_after)
        entry["no_removal"] = {"before": len(before_ids), "kept": len(before_ids & after_ids), "removed": sorted(before_ids - after_ids)}
        from app.database import SessionLocal
        from app.models import Project
        from app.routers import projects as projects_router
        with SessionLocal() as db:
            project = db.get(Project, pid)
            for sheet in project.design_sheets:
                t1 = time.perf_counter()
                result = projects_router._read_design_sheet(db, project, sheet)
                key = f"EP-{ep}/" + paths[sheet.document_path].replace("/", "\\")
                extractions[key] = {"seconds": round(time.perf_counter() - t1, 1), "state": getattr(result, "state", None),
                                    "reader": getattr(result, "reader", None), "failure": result.failure,
                                    "outcome": str(getattr(result, "outcome", None)),
                                    "lines": [dataclasses.asdict(l) for l in result.lines],
                                    "issues": [dataclasses.asdict(i) if dataclasses.is_dataclass(i) else dict(i) for i in result.issues],
                                    "notes": list(getattr(result, "notes", []) or [])}
        out["projects"][ep] = entry
        print(ep, "ensure", entry["ensure_1"]["status"], entry["ensure_1"]["items"], "items", entry["ensure_1"]["seconds"], "s; reread",
              entry["reread"]["status"], "items before/after", entry["items_before_reread"], entry["items_after_reread"], flush=True)
con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
out["stored"] = {"boq_items": con.execute("select count(*) from project_boq_items").fetchone()[0],
                 "projects": [dict(r) for r in con.execute("select id, ep_number, boq_extracted_at, boq_extraction_warnings, boq_version from projects")],
                 "document_readings": [dict(r) for r in con.execute("select * from document_readings")]}
for r in out["stored"]["document_readings"]:
    r.pop("reading", None)
usage = [dict(u) for u in con.execute("select project_id, task, model, input_tokens, output_tokens, cached_input_tokens, estimated_cost, latency_ms, cache_hit, escalated, outcome, at from ai_usage order by id")]
con.close()
out["ai_usage_rows"] = len(usage)
json.dump(out, open(ROOT / "out" / "BOQ-RUN.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(extractions, open(ROOT / "out" / "boq-extraction.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(usage, open(ROOT / "out" / "usage.json", "w", encoding="utf-8"), indent=1, default=str)
print("done", args.tag, out["stored"]["boq_items"], "items;", len(usage), "ai_usage rows")
