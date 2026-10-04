"""Round 2 exploration, profiles B (EV1) and C (EV2): the evidence stage (app.ai.evidence_reader.evidence_stage) as the
frozen candidate runs it, over a WAL-consistent copy of the profile-A sandbox database, so B and C start from the same
deterministic + application-AI state and only the variant differs. Adapted from the Review 07 runner (run_evf.py);
differences: the frozen-r12 tree; application limits unchanged (asserted); the declared ledger scope; and two stops
of this runner, each recorded on the page as a budget stop, never a negative:
  * the application's per-project daily limit applied ACROSS tracks (xtrack.py): a request is refused once the
    project's rolling-24-hour total over all tracks reaches it;
  * three consecutive provider failures (transport / timeout / refusal) stop the run.

Usage: r2x_ev.py <A_tag> <tag> <EV1|EV2> --declaration DECL.json --declaration-sha SHA"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import sqlite3
import sys
import time

a = argparse.ArgumentParser()
a.add_argument("a_tag"); a.add_argument("tag"); a.add_argument("variant")
a.add_argument("--declaration", required=True); a.add_argument("--declaration-sha", required=True)
args = a.parse_args()
assert args.variant in ("EV1", "EV2")
assert hashlib.sha256(pathlib.Path(args.declaration).read_bytes()).hexdigest() == args.declaration_sha, "the declaration changed"
decl = json.loads(pathlib.Path(args.declaration).read_text(encoding="utf-8"))
SRC = pathlib.Path("C:/t/r2x/runs") / args.a_tag
ROOT = pathlib.Path("C:/t/r2x/runs") / args.tag
DB = ROOT / "db" / "default.db"
if DB.exists():
    sys.exit(f"{DB} exists: a run is never repeated over its own sandbox (preserve it; use a new tag)")
(ROOT / "db").mkdir(parents=True, exist_ok=True)
(ROOT / "out").mkdir(parents=True, exist_ok=True)
a_run = json.loads((SRC / "out" / "RUN.json").read_text(encoding="utf-8"))
assert a_run["track"] == "A" and a_run["declaration_sha256"] == args.declaration_sha, "the source is not this declaration's profile-A run"
# a WAL-consistent snapshot of the profile-A database (the backup API reads through the WAL; a file copy would not)
_src = sqlite3.connect(f"file:{(SRC / 'db' / 'default.db').as_posix()}?mode=ro", uri=True)
_dst = sqlite3.connect(str(DB))
_src.backup(_dst)
_dst.close()
_src.close()
env = {"DATABASE_URL": f"sqlite:///{DB.as_posix()}", "CACHE_ROOT": str(SRC / "cache"), "LIBRARY_ROOT": str(SRC / "library"), "UPLOADS_ROOT": str(SRC / "uploads"),
       "AI_ENABLED": "true", "AI_EVIDENCE_VARIANT": args.variant, "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false",
       "EXTRACTION_PROMOTE_OBSERVATIONS": "false", "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "COMPLIANCE_KNOWLEDGE_SOURCE": "",
       "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false", "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "LIBRARY_RESCAN_SECONDS": "0",
       **decl["provider"]["env"], **decl["ledger"]["env"]}
os.environ.update(env)
B = pathlib.Path(decl["candidate"]["worktree"]) / "backend"
sys.path.insert(0, str(B)); os.chdir(B)
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import xtrack  # noqa: E402
from app.core.config import Settings, get_settings  # noqa: E402

st = get_settings()
assert DB.as_posix() in st.database_url and st.ai_enabled and st.ai_evidence_variant == args.variant
for k, v in decl["application_limits"].items():
    assert getattr(st, k) == v == Settings.model_fields[k].default, f"application limit {k} is not the frozen default"
from app.ai import evidence_reader as er  # noqa: E402

assert pathlib.Path(er.__file__).resolve().is_relative_to(B.resolve())
for k, v in decl["identities"]["evidence_reader"].items():
    assert getattr(er, k) == v, f"{k} differs from the declaration"
from app.database import SessionLocal  # noqa: E402
from app.models import Project, ProjectDocument  # noqa: E402

LIMIT = decl["application_limits"]["ai_max_calls_per_project_per_day"]
track = {"EV1": "B", "EV2": "C"}[args.variant]
ep_of = {}
state = {"consecutive_failures": 0, "stopped": None, "xtrack_refusals": 0}
_original_call = er.EvidenceRun.call


def _guarded_call(self, **kw):
    ep = ep_of.get(self.project_id)
    if state["stopped"] and not self.exhausted:
        self.exhausted = state["stopped"]
    took = False
    if not self.exhausted:
        took = xtrack.take(ep, track, kw.get("task", ""), LIMIT)
        if not took:
            state["xtrack_refusals"] += 1
            self.exhausted = "calls_per_project_per_day (across tracks)"
    before, n_log = self.calls, len(self.log)
    out = _original_call(self, **kw)
    new = self.log[n_log:]
    if took and self.calls == before:
        xtrack.release_last(ep, track)          # a cache hit or a refusal: no request was made
    for entry in new:
        if entry.get("cache_hit") or str(entry.get("outcome", "")).startswith("budget"):
            continue
        if entry.get("outcome") == "ok":
            state["consecutive_failures"] = 0
        else:
            state["consecutive_failures"] += 1
            if state["consecutive_failures"] >= 3 and not state["stopped"]:
                state["stopped"] = "stop: three consecutive provider failures"
    return out


er.EvidenceRun.call = _guarded_call
started = time.perf_counter()
manifest = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "a_tag": args.a_tag, "tag": args.tag, "track": track,
            "variant": args.variant, "declaration_sha256": args.declaration_sha, "reader": er.READER_VERSION, "policy": er.EVIDENCE_POLICY_VERSION,
            "prompts": er.PROMPTS, "schema": er.SCHEMA_VERSION, "projects": {}}
total_calls = 0
with SessionLocal() as db:
    for project in db.query(Project).order_by(Project.id).all():
        ep_of[project.id] = project.ep_number
        rows = [r for r in db.query(ProjectDocument).filter(ProjectDocument.project_id == project.id, ProjectDocument.state == "fresh").order_by(ProjectDocument.id)
                if (r.path or "").lower().endswith(".pdf")]
        t0 = time.perf_counter()
        counts = er.evidence_stage(db, project, [(r, pathlib.Path(r.path)) for r in rows], variant=args.variant)
        total_calls += counts.get("calls", 0)
        manifest["projects"][project.ep_number] = {**counts, "seconds": round(time.perf_counter() - t0, 1), "documents_in": len(rows)}
        print(project.ep_number, args.variant, counts, round(time.perf_counter() - t0, 1), "s", flush=True)
manifest.update({"seconds": round(time.perf_counter() - started, 1), "runner_state": state})
con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
rows = {}
for r in con.execute("select d.id, p.ep_number, d.relative_path, d.role, d.state, d.error, d.sha256, d.reference, d.revision, d.status, d.system_code, d.extracted "
                     "from project_documents d join projects p on p.id = d.project_id"):
    rows[f"EP-{r['ep_number']}/{r['relative_path']}"] = {"id": r["id"], "ep": r["ep_number"], "role": r["role"], "state": r["state"], "error": r["error"], "sha256": r["sha256"],
                                                         "mirror": {"reference": r["reference"], "revision": r["revision"], "status": r["status"],
                                                                    "system_code": r["system_code"]},
                                                         "extracted": json.loads(r["extracted"]) if r["extracted"] else None}
usage = [dict(u) for u in con.execute("select u.id, p.ep_number, u.task, u.model, u.input_tokens, u.output_tokens, u.cached_input_tokens, u.reasoning_tokens, "
                                      "u.estimated_cost, u.latency_ms, u.cache_hit, u.escalated, u.outcome, u.at from ai_usage u left join projects p on p.id = u.project_id order by u.id")]
tables = {t: con.execute(f"select count(*) from {t}").fetchone()[0] for t in
          ("project_documents", "project_submittals", "project_shop_drawings", "background_jobs", "project_actions", "ai_usage", "document_readings")}
con.close()
manifest.update({"tables": tables, "ai_usage_rows": len(usage), "fresh_requests_this_track": sum(1 for u in usage if not u["cache_hit"] and str(u["task"]).startswith("evidence:"))})
json.dump(manifest, open(ROOT / "out" / "RUN.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(rows, open(ROOT / "out" / "rows.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(usage, open(ROOT / "out" / "usage.json", "w", encoding="utf-8"), indent=1, default=str)
print("done", args.tag, args.variant, "calls", total_calls, "seconds", manifest["seconds"], "state", state)
