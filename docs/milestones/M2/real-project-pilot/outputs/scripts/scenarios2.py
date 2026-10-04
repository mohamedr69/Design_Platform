"""Pilot step 5c (second run, corrected): the persistence contracts on real sampled documents in the sandbox (copies).
Budgets as the reader applies them: PAGE_SCAN_LIMIT stops a file that showed nothing in its first pages,
REPLY_SEARCH_LIMIT stops a non-drawing file that has records (a submittal package's later pages are not searched for
replies), OCR_PAGE_LIMIT leaves OCR out on later scanned pages -- each a "bounded" reading with the pages left recorded.
A record on a page a later, narrower reading skips is carried with its provenance. The interruption is the job's own
cancellation (JobContext.check raising Cancelled between files), not a reader error. Usage: scenarios2.py <scratch> <profile>"""
import json, os, sys, pathlib, time, datetime, sqlite3, shutil

S = pathlib.Path(sys.argv[1]); PROFILE = sys.argv[2]; ROOT = pathlib.Path("C:/t/pilot"); DB = ROOT / "db" / f"scenarios2_{PROFILE}.db"; TREE = ROOT / "scenarios2"
if TREE.exists(): shutil.rmtree(TREE)
for ext in ("", "-wal", "-shm"):
    p = pathlib.Path(str(DB) + ext)
    if p.exists(): p.unlink()
os.environ.update({"DATABASE_URL": f"sqlite:///{DB.as_posix()}", "CACHE_ROOT": str(ROOT / "cache_scn2"), "LIBRARY_ROOT": str(ROOT / "library"), "UPLOADS_ROOT": str(ROOT / "uploads"),
                   "AI_ENABLED": "false", "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "ARCHIVE_SUBMITTAL_LIBRARY": "", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false",
                   "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false", "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "DOCUMENT_CLASSIFICATION_V2": "false",
                   "SYNC_FILE_WORKERS": "0", "EXTRACTION_PROMOTE_OBSERVATIONS": "true" if PROFILE == "promoted" else "false", "LIBRARY_RESCAN_SECONDS": "0"})
B = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend"); sys.path.insert(0, str(B)); os.chdir(B)
from app.core.config import get_settings  # noqa: E402
st = get_settings(); assert DB.as_posix() in st.database_url and not st.ai_enabled and str(ROOT) in st.cache_root
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
import app.routers.jobs as jobs_router  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import ProjectDocument  # noqa: E402
from app.services import document_control as dc, jobs as jobs_service  # noqa: E402
import unittest.mock as um  # noqa: E402
jobs_router.RUN_INLINE = True
frozen = json.load(open(S / "FROZEN-SAMPLE.json", encoding="utf-8"))
docs = [d for d in frozen["documents"] if d.get("staged_path") and d["extension"] == ".pdf" and not d.get("open_error")]
rows_default = json.load(open(S / "rows-default.json", encoding="utf-8")) if (S / "rows-default.json").is_file() else {}


def key_of(d): return f"EP-{d['ep']}/{d['relative_path']}".replace("\\", "/")


rows_default = {k.replace("\\", "/"): v for k, v in rows_default.items()}


def records_of(d):
    r = rows_default.get(key_of(d)) or {}
    return ((r.get("extracted") or {}).get("records") or [])


def pick(pred, n=1):
    return [d for d in docs if pred(d)][:n]


# a package: a non-drawing file (submittal / reply / approval) with a record on a page beyond 3, from the default run
def late_record(d):
    recs = records_of(d)
    return bool(recs) and all(r.get("category") != "drawings" for r in recs) and any((r.get("page") or 1) > 3 for r in recs) and (d.get("pages") or 0) > 4 and not d.get("scan_like")


chosen = {"text_cover": pick(lambda d: d["stratum"] in ("shop_drawing", "submittal", "reply") and not d.get("scan_like") and (d.get("pages") or 0) <= 6 and records_of(d)),
          "scan": pick(lambda d: d.get("scan_like") and (d.get("pages") or 0) <= 4 and records_of(d)) or pick(lambda d: d.get("scan_like") and (d.get("pages") or 0) <= 4),
          "package": pick(late_record) or pick(lambda d: d["stratum"] in ("submittal", "reply", "approval_sample", "spec_compliance") and (d.get("pages") or 0) > 6 and not d.get("scan_like") and records_of(d)),
          "scan_package": pick(lambda d: d.get("scan_like") and (d.get("pages") or 0) > 14)}
TREE.mkdir(parents=True); paths = {}
for name, lst in chosen.items():
    if not lst: continue
    d = lst[0]; dst = TREE / f"05- Documents/{name}-{pathlib.Path(d['relative_path']).name}"; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(d["staged_path"], dst); paths[name] = (dst, d)
log = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "profile": PROFILE, "database": str(DB),
       "chosen": {k: {"doc": key_of(v[1]), "pages": v[1].get("pages"), "scan_like": v[1].get("scan_like"), "records_in_default_run": [(r.get("reference"), r.get("category"), r.get("page")) for r in records_of(v[1])]} for k, v in paths.items()}, "steps": []}


def touch(p: pathlib.Path):
    later = time.time() + 5; os.utime(p, (later, later))


def bump(p: pathlib.Path, tag: bytes):
    p.write_bytes(p.read_bytes() + b"\n%pilot-" + tag + b"\n"); touch(p)


def reopen(pid):
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True); con.row_factory = sqlite3.Row
    rows = {r["relative_path"]: {"state": r["state"], "error": r["error"], "sha256": r["sha256"], "mirror": [r["reference"], r["revision"], r["status"]], "extracted": json.loads(r["extracted"]) if r["extracted"] else None}
            for r in con.execute("select relative_path, state, error, sha256, reference, revision, status, extracted from project_documents where project_id=?", (pid,))}
    jobs_ = [dict(r) for r in con.execute("select id, kind, status, error, cancel_requested from background_jobs order by id desc limit 3")]
    con.close(); return rows, jobs_


def summary_of(r):
    ex = r["extracted"] or {}; cov = ex.get("coverage") or {}
    return {"state": r["state"], "error": (r["error"] or "")[:80], "mirror": r["mirror"], "outcome": cov.get("outcome"), "stop": cov.get("stop_reason"), "visited": len(cov.get("pages_visited") or []), "skipped": len(cov.get("pages_skipped") or []),
            "ocr": cov.get("ocr"), "records": [(rec.get("reference"), rec.get("status"), rec.get("page"), sorted(rec.get("flags") or []), (rec.get("retained") or {}).get("parser_version") if rec.get("retained") else None) for rec in ex.get("records") or []],
            "attempt": (ex.get("attempt") or {}).get("outcome"), "stale": ex.get("stale"), "retained": ex.get("retained"), "parser": ex.get("parser_version"), "profile": ex.get("profile"), "read_sha": ex.get("read_sha256")}


def step(name, client, pid, note="", **extra):
    job = client.post(f"/projects/{pid}/jobs/sync-documents").json(); res = client.get(f"/jobs/{job['id']}").json()
    proc = client.get(f"/jobs/{res['result']['processing_job_id']}").json() if (res.get("result") or {}).get("processing_job_id") else None
    rows, jobs_ = reopen(pid)
    summary = {k: summary_of(r) for k, r in rows.items()}
    entry = {"step": name, "note": note, "sync": {k: res.get(k) for k in ("status", "error")}, "sync_counts": {k: (res.get("result") or {}).get(k) for k in ("new", "changed", "unchanged", "already_pending", "removed", "pending", "stale")},
             "processing": {k: (proc or {}).get(k) for k in ("status", "error")}, "processing_result": {k: v for k, v in ((proc or {}).get("result") or {}).items() if k not in ("drawings", "telemetry")}, "jobs": jobs_, "rows": summary, **extra}
    log["steps"].append(entry)
    print(name, "->", {k.split("/")[-1][:22]: (v["state"], v["outcome"], v["stop"], len(v["records"]), v["attempt"], sorted({f for rec in v["records"] for f in rec[3]})) for k, v in summary.items()}, flush=True)
    return rows


with TestClient(app) as client:
    login = client.post("/auth/login", json={"email": st.default_admin_email, "password": st.default_admin_password}); assert login.status_code == 200
    pid = client.post("/projects", json={"ep_number": "99002", "project_name": "pilot scenarios 2", "source_folder_path": str(TREE), "design_sheets": []}).json()["id"]
    step("1 first read", client, pid)
    for p, _ in paths.values(): touch(p)
    step("2 unchanged rerun (touched)", client, pid, "same bytes: unchanged after hash, readings reused")
    if "text_cover" in paths:
        src, d = paths["text_cover"]; dup = src.parent / "Archive" / src.name; dup.parent.mkdir(exist_ok=True); shutil.copyfile(src, dup)
        step("3 duplicate copy", client, pid, "the same bytes under another path: the reading copied, its own row")
        good = src.read_bytes(); src.write_bytes(b"%PDF-1.4 damaged in the pilot sandbox"); touch(src)
        step("4 corrupt replacement", client, pid, "the file replaced by a non-PDF: failed attempt, last reading kept, stale")
        step("5 retry, nothing changed", client, pid, "a failed row whose file has not changed: is it planned again?")
        touch(src); step("5b retry after a touch", client, pid, "the same corrupt bytes, newer mtime: planned again, still failed")
        src.write_bytes(good); touch(src)
        step("6 restored", client, pid, "the good bytes back: read (or the duplicate's reading reused), attempt cleared")
        src.unlink()
        step("7 file removed", client, pid, "gone from the folder: removed by the sync")
        src.write_bytes(good); touch(src)
        step("8 file back", client, pid)
    if "scan" in paths:
        src, d = paths["scan"]
        with um.patch.object(dc, "_ocr_text", side_effect=RuntimeError("pilot: synthetic OCR failure")), um.patch.object(dc, "_ocr_regions_text", side_effect=RuntimeError("pilot: synthetic OCR failure")):
            bump(src, b"ocr"); step("9 scan re-read with OCR failing", client, pid, "changed bytes, OCR raises: partial attempt beside the kept reading")
        step("10a partial, nothing changed", client, pid, "a partial row whose file has not changed: planned again?")
        touch(src); step("10b OCR back after a touch", client, pid, "the partial attempt retried and superseded")
    if "package" in paths:
        src, d = paths["package"]
        with um.patch.object(dc, "PAGE_SCAN_LIMIT", 400), um.patch.object(dc, "REPLY_SEARCH_LIMIT", 400):
            bump(src, b"wide"); step("11 wide read of the package", client, pid, "every page visited", limits=400)
        with um.patch.object(dc, "PAGE_SCAN_LIMIT", 3), um.patch.object(dc, "REPLY_SEARCH_LIMIT", 3):
            bump(src, b"narrow"); step("12 narrow read (limits 3) of changed bytes", client, pid, "bounded: records on the pages now skipped carried from the earlier reading of other bytes (unverified)", limits=3)
            touch(src); step("13 narrow read again, same bytes", client, pid, "unchanged after hash: the bounded reading stands", limits=3)
            bump(src, b"narrow2"); step("13b narrow read of changed bytes again", client, pid, "repeated bounded run: carried records keep their original provenance, never restamped", limits=3)
        with um.patch.object(dc, "PAGE_SCAN_LIMIT", 400), um.patch.object(dc, "REPLY_SEARCH_LIMIT", 400):
            bump(src, b"wide2"); step("14 wide read again", client, pid, "the pages read: nothing carried", limits=400)
        s = SessionLocal(); row = s.query(ProjectDocument).filter(ProjectDocument.project_id == pid, ProjectDocument.relative_path.like("%/package-%")).one()
        ex = dict(row.extracted); ex["parser_version"] = "parse-older"; row.extracted = ex; s.commit(); s.close()
        with um.patch.object(dc, "PAGE_SCAN_LIMIT", 3), um.patch.object(dc, "REPLY_SEARCH_LIMIT", 3):
            bump(src, b"parser"); step("15 narrow read after a parser change", client, pid, "the older parser's records on skipped pages held (carried_other_parser): not current, decision withheld", limits=3)
        with um.patch.object(dc, "PAGE_SCAN_LIMIT", 400), um.patch.object(dc, "REPLY_SEARCH_LIMIT", 400):
            bump(src, b"parser2"); step("16 wide read by the current parser", client, pid, "cleared", limits=400)
        other = PROFILE != "promoted"
        with um.patch.object(dc, "_promote_default", lambda: other), um.patch.object(dc, "PAGE_SCAN_LIMIT", 400), um.patch.object(dc, "REPLY_SEARCH_LIMIT", 400):
            bump(src, b"profile"); step("17 wide read under the other profile", client, pid, limits=400, profile="promoted" if other else "default")
        with um.patch.object(dc, "PAGE_SCAN_LIMIT", 3), um.patch.object(dc, "REPLY_SEARCH_LIMIT", 3):
            bump(src, b"profile2"); step("18 narrow read under this profile", client, pid, "the other profile's records on skipped pages held (carried_other_profile)", limits=3)
    if "scan_package" in paths:
        src, d = paths["scan_package"]
        with um.patch.object(dc, "OCR_PAGE_LIMIT", 2):
            bump(src, b"ocrbudget"); step("18b scanned package under an OCR budget of 2", client, pid, "bounded by the OCR budget: pages visited, OCR left out on the later ones", ocr_limit=2)
    # interruption: the job's own cancellation between files (JobContext.check), then the next sync resumes
    if len(paths) >= 2:
        for p, _ in paths.values(): bump(p, b"interrupt")
        calls = {"n": 0}; real_check = jobs_service.JobContext.check
        def check(self):
            calls["n"] += 1
            if calls["n"] == 2:
                raise jobs_service.Cancelled("pilot: stop requested after the first file")
            return real_check(self)
        with um.patch.object(jobs_service.JobContext, "check", check):
            step("19 cancelled after the first file", client, pid, "the finished file written; the rest left pending; the job cancelled")
        step("20 resumed", client, pid, "the pending files read; the finished one not read again")
json.dump(log, open(S / f"SCENARIOS2-{PROFILE}.json", "w", encoding="utf-8"), indent=1, default=str)
print("scenarios2 done", len(log["steps"]))
