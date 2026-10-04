"""Pilot step 5 (BOQ / design sheets): the application's own BOQ path over the frozen sheets in a disposable sandbox,
with the model disabled (AI_ENABLED=false) -- the pilot's constraint. What the product does then is recorded
literally: a project per pilot project with its sheets attached, POST /projects/{id}/boq/ensure, the stored BOQ read
back from the database (items, warnings, extraction runs), then a second ensure (idempotence) and a boq-reread job.
Usage: boq_sandbox.py <scratch> <profile>"""
import json, os, sys, pathlib, time, datetime, sqlite3, shutil

S = pathlib.Path(sys.argv[1]); PROFILE = sys.argv[2]; ROOT = pathlib.Path("C:/t/pilot"); DB = ROOT / "db" / f"boq_{PROFILE}_candidateC.db"
for ext in ("", "-wal", "-shm"):
    p = pathlib.Path(str(DB) + ext)
    if p.exists(): p.unlink()
os.environ.update({"DATABASE_URL": f"sqlite:///{DB.as_posix()}", "CACHE_ROOT": str(ROOT / "cache_boq"), "LIBRARY_ROOT": str(ROOT / "library"), "UPLOADS_ROOT": str(ROOT / "uploads"),
                   "AI_ENABLED": "false", "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "ARCHIVE_SUBMITTAL_LIBRARY": "", "PROJECTS_ROOT": str(ROOT / "stage"), "PROJECTS_ROOT_AUTODETECT": "false",
                   "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false", "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "DOCUMENT_CLASSIFICATION_V2": "false",
                   "SYNC_FILE_WORKERS": "0", "EXTRACTION_PROMOTE_OBSERVATIONS": "true" if PROFILE == "promoted" else "false", "LIBRARY_RESCAN_SECONDS": "0"})
B = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend"); sys.path.insert(0, str(B)); os.chdir(B)
from app.core.config import get_settings  # noqa: E402
st = get_settings(); assert DB.as_posix() in st.database_url and not st.ai_enabled and str(ROOT) in st.cache_root
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
import app.routers.jobs as jobs_router  # noqa: E402
jobs_router.RUN_INLINE = True
frozen = json.load(open(S / "FROZEN-BOQ-SET.json", encoding="utf-8"))
by_ep = {}
for sheet in frozen["sheets"]:
    if sheet.get("staged_path"): by_ep.setdefault(sheet["ep"], []).append(sheet)
folders = {p["ep"]: p["folder"] for p in json.load(open(S / "PROJECT-INVENTORY.json", encoding="utf-8"))["projects"]}


def code_for(rel: str) -> str | None:
    name = pathlib.Path(rel).name.upper()
    for code in ("FAS", "EML", "ELS", "CBS", "PA", "ASPIRATION"):
        if code in name: return {"EML": "ELS", "ASPIRATION": "ASD"}.get(code, code)
    return None


out = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "profile": PROFILE, "database": str(DB), "model": "disabled (AI_ENABLED=false): the sheet read is a model-requiring branch", "projects": {}}
with TestClient(app) as client:
    login = client.post("/auth/login", json={"email": st.default_admin_email, "password": st.default_admin_password}); assert login.status_code == 200, login.text
    for ep, sheets in by_ep.items():
        stage = ROOT / "stage" / f"EP-{ep}"
        payload = {"ep_number": ep, "project_name": folders[ep][:80], "source_folder_path": str(stage),
                   "design_sheets": [{"system_code": code_for(s["relative_path"]), "document_path": s["staged_path"]} for s in sheets]}
        created = client.post("/projects", json=payload)
        entry = {"create_status": created.status_code, "sheets": [s["relative_path"] for s in sheets]}
        if created.status_code != 201:
            entry["create_error"] = created.text[:400]; out["projects"][ep] = entry; print(ep, "create", created.status_code, created.text[:200], flush=True); continue
        pid = created.json()["id"]; entry["project_id"] = pid
        t0 = time.perf_counter(); first = client.post(f"/projects/{pid}/boq/ensure"); entry["ensure_1"] = {"status": first.status_code, "seconds": round(time.perf_counter() - t0, 2), "body": first.json() if first.headers.get("content-type", "").startswith("application/json") else first.text[:400]}
        second = client.post(f"/projects/{pid}/boq/ensure"); entry["ensure_2"] = {"status": second.status_code, "body": second.json() if second.headers.get("content-type", "").startswith("application/json") else second.text[:400]}
        reread = client.post(f"/projects/{pid}/jobs/boq-reread"); entry["reread"] = {"status": reread.status_code, "body": reread.json() if reread.headers.get("content-type", "").startswith("application/json") else reread.text[:400]}
        if reread.status_code == 202:
            entry["reread"]["job"] = client.get(f"/jobs/{reread.json()['id']}").json()
        boq = client.get(f"/projects/{pid}/boq"); entry["boq_items"] = boq.json() if boq.status_code == 200 else boq.text[:300]
        out["projects"][ep] = entry
        print(ep, "ensure", first.status_code, {k: v for k, v in (entry["ensure_1"]["body"].items() if isinstance(entry["ensure_1"]["body"], dict) else [])} if False else (entry["ensure_1"]["body"] if not isinstance(entry["ensure_1"]["body"], dict) else {"extracted": entry["ensure_1"]["body"].get("extracted"), "items": len(entry["ensure_1"]["body"].get("items") or []), "warnings": entry["ensure_1"]["body"].get("warnings")}), "reread", reread.status_code, flush=True)
# reopened from the database
con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True); con.row_factory = sqlite3.Row
out["stored"] = {"projects": [dict(r) for r in con.execute("select id, ep_number, boq_extracted_at, boq_extraction_warnings, boq_version from projects")],
                 "design_sheets": [dict(r) for r in con.execute("select id, project_id, system_code, document_path from project_design_sheets")],
                 "boq_items": con.execute("select count(*) from project_boq_items").fetchone()[0],
                 "extraction_runs": [dict(r) for r in con.execute("select * from extraction_runs")],
                 "boq_candidates": [dict(r) for r in con.execute("select id, project_id, status from boq_candidates")] if con.execute("select name from sqlite_master where name='boq_candidates'").fetchone() else None,
                 "document_readings": con.execute("select count(*) from document_readings").fetchone()[0]}
con.close()
json.dump(out, open(S / f"BOQ-RUN-{PROFILE}.json", "w", encoding="utf-8"), indent=1, default=str)
print("done", {ep: (e.get("ensure_1", {}).get("status"), len((e.get("boq_items") or [])) if isinstance(e.get("boq_items"), list) else e.get("boq_items")) for ep, e in out["projects"].items()})
