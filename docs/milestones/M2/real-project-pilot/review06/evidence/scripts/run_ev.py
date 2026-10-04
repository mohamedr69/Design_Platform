"""Review 06: the AI evidence stage (app.ai.evidence_reader.evidence_stage) as the application runs it, over a copy of
an AI-EV0 run's sandbox database -- so EV1 and EV2 start from the same deterministic + application-AI state and only
the variant differs. The EV0 run's cache root is used for the page cache (OCR text already made), read only in
effect: the stage makes no OCR of its own.

Usage: run_ev.py <ev0_tag> <tag> <variant EV1|EV2> <profile> --budget-json file [--eps a,b] [--limit-docs N]"""
import argparse, datetime, json, os, pathlib, shutil, sqlite3, sys, time

a = argparse.ArgumentParser()
a.add_argument("ev0"); a.add_argument("tag"); a.add_argument("variant"); a.add_argument("profile")
a.add_argument("--budget-json", required=True); a.add_argument("--eps"); a.add_argument("--limit-docs", type=int)
args = a.parse_args()
assert args.variant in ("EV1", "EV2")
SRC = pathlib.Path("C:/t/r6") / args.ev0; ROOT = pathlib.Path("C:/t/r6") / args.tag
(ROOT / "db").mkdir(parents=True, exist_ok=True); (ROOT / "out").mkdir(parents=True, exist_ok=True)
DB = ROOT / "db" / f"{args.profile}.db"
for ext in ("", "-wal", "-shm"):
    q = pathlib.Path(str(DB) + ext)
    if q.exists():
        q.unlink()
# a WAL-consistent snapshot of the EV0 database (the backup API reads through the WAL; a file copy would not)
_src = sqlite3.connect(f"file:{(SRC / 'db' / f'{args.profile}.db').as_posix()}?mode=ro", uri=True)
_dst = sqlite3.connect(str(DB))
_src.backup(_dst)
_dst.close(); _src.close()
budget = json.load(open(args.budget_json, encoding="utf-8"))
if not args.eps and budget.get("eps"):
    args.eps = budget["eps"]    # the declared scope (EXPERIMENT-DECLARATION-ADDENDUM-2)
env = {"DATABASE_URL": f"sqlite:///{DB.as_posix()}", "CACHE_ROOT": str(SRC / "cache"), "LIBRARY_ROOT": str(SRC / "library"), "UPLOADS_ROOT": str(SRC / "uploads"),
       "AI_ENABLED": "true", "AI_PROVIDER": "claude-code", "AI_MODEL_SMALL": "sonnet", "AI_MODEL_STANDARD": "opus", "AI_EVIDENCE_VARIANT": args.variant,
       "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false", "EXTRACTION_PROMOTE_OBSERVATIONS": "true" if args.profile == "promoted" else "false",
       "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false",
       "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "LIBRARY_RESCAN_SECONDS": "0"}
env.update({k: str(v) for k, v in budget["settings"].items()})
os.environ.update(env)
B = pathlib.Path(r"C:\t\iso\ep-platform\backend"); sys.path.insert(0, str(B)); os.chdir(B)
from app.core.config import get_settings  # noqa: E402
st = get_settings()
assert DB.as_posix() in st.database_url and st.ai_enabled and st.ai_evidence_variant == args.variant
from app.ai import evidence_reader as er  # noqa: E402

# The run's declared cap on fresh requests, enforced per call (not only between projects): once reached, every further
# call is a budget stop ("experiment cap"), recorded as such on its page -- never a negative.
_CAP = budget.get("max_total_calls")
_fresh = {"n": 0}
_original_call = er.EvidenceRun.call


def _capped_call(self, **kw):
    if _CAP is not None and _fresh["n"] >= _CAP and not self.exhausted:
        self.exhausted = "experiment cap"
    before = self.calls
    out = _original_call(self, **kw)
    _fresh["n"] += self.calls - before
    return out


er.EvidenceRun.call = _capped_call
from app.database import SessionLocal  # noqa: E402
from app.models import Project, ProjectDocument  # noqa: E402
started = time.perf_counter()
manifest = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "ev0": args.ev0, "tag": args.tag, "variant": args.variant,
            "profile": args.profile, "reader": er.READER_VERSION, "policy": er.EVIDENCE_POLICY_VERSION, "prompts": er.PROMPTS, "schema": er.SCHEMA_VERSION,
            "budget": budget, "projects": {}}
total_calls = 0
with SessionLocal() as db:
    projects = db.query(Project).order_by(Project.id).all()
    for project in projects:
        if args.eps and project.ep_number not in args.eps.split(","):
            continue
        rows = [r for r in db.query(ProjectDocument).filter(ProjectDocument.project_id == project.id, ProjectDocument.state == "fresh").order_by(ProjectDocument.id)
                if (r.path or "").lower().endswith(".pdf")]
        if args.limit_docs:
            rows = rows[: args.limit_docs]
        if budget.get("max_total_calls") is not None and total_calls >= budget["max_total_calls"]:
            manifest["projects"][project.ep_number] = {"skipped": "run cap reached before this project", "documents": len(rows)}
            continue
        t0 = time.perf_counter()
        counts = er.evidence_stage(db, project, [(r, pathlib.Path(r.path)) for r in rows], variant=args.variant)
        total_calls += counts.get("calls", 0)
        manifest["projects"][project.ep_number] = {**counts, "seconds": round(time.perf_counter() - t0, 1), "documents_in": len(rows)}
        print(project.ep_number, args.variant, counts, round(time.perf_counter() - t0, 1), "s", flush=True)
manifest["seconds"] = round(time.perf_counter() - started, 1)
con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True); con.row_factory = sqlite3.Row
rows = {}
for r in con.execute("select d.id, p.ep_number, d.relative_path, d.role, d.state, d.error, d.sha256, d.reference, d.revision, d.status, d.system_code, d.extracted from project_documents d join projects p on p.id = d.project_id"):
    rows[f"EP-{r['ep_number']}/{r['relative_path']}"] = {"id": r["id"], "ep": r["ep_number"], "role": r["role"], "state": r["state"], "error": r["error"], "sha256": r["sha256"],
                                                         "mirror": {"reference": r["reference"], "revision": r["revision"], "status": r["status"], "system_code": r["system_code"]},
                                                         "extracted": json.loads(r["extracted"]) if r["extracted"] else None}
usage = [dict(u) for u in con.execute("select project_id, task, model, input_tokens, output_tokens, cached_input_tokens, estimated_cost, latency_ms, cache_hit, escalated, outcome, at from ai_usage order by id")]
con.close()
manifest["ai_usage_rows"] = len(usage)
json.dump(manifest, open(ROOT / "out" / f"RUN-{args.profile}.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(rows, open(ROOT / "out" / f"rows-{args.profile}.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(usage, open(ROOT / "out" / f"usage-{args.profile}.json", "w", encoding="utf-8"), indent=1, default=str)
print("done", args.tag, "calls", total_calls, "seconds", manifest["seconds"])
