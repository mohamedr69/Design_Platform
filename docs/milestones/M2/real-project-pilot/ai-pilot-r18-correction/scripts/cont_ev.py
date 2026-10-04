# DERIVED from ai-accuracy-pilot/pilot_ev.py by derive_runners.py -- document arms S / T2 of the continuation; labels and track names from the declaration
"""AI accuracy pilot, arms S / G / T: the evidence stage (app.ai.evidence_reader.evidence_stage) as the arm's tree runs it
(S: accepted 3d5607d; G / T: the candidate commit with its flags), over a WAL-consistent copy of the A base database (and a copy of its file caches), so
the three arms start from the same deterministic + application-AI state and only the evidence policy differs.
Adapted from the Round 2 runner r2x_ev.py; additions:
  * the arm's own ledger scope (hard request cap) and identities asserted against the declaration;
  * the per-arm project share (PILOT-SHARES.json, frozen after A) on top of the cross-track 60/day counter;
  * every model input and output kept: per request, the prompt text, each image part (PNG), the answer (or none), the
    log entry (model, tokens, latency, outcome) -- out/io/;
  * the stop rule: after each project the evaluator (.9, unchanged) scores the rows so far under the arm's context;
    a critical acceptance by the arm's AI on a RESOLVED label stops the arm (remaining projects not attempted);
  * three consecutive provider failures stop the run.

Usage: pilot_ev.py <A_tag> <tag> <S|G|T> --declaration D --declaration-sha SHA --shares PILOT-SHARES.json --shares-sha SHA"""
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
a.add_argument("a_tag"); a.add_argument("tag"); a.add_argument("arm")
a.add_argument("--declaration", required=True); a.add_argument("--declaration-sha", required=True)
a.add_argument("--shares", required=True); a.add_argument("--shares-sha", required=True)
args = a.parse_args()
assert hashlib.sha256(pathlib.Path(args.declaration).read_bytes()).hexdigest() == args.declaration_sha, "the declaration changed"
assert hashlib.sha256(pathlib.Path(args.shares).read_bytes()).hexdigest() == args.shares_sha, "the shares changed"
decl = json.loads(pathlib.Path(args.declaration).read_text(encoding="utf-8"))
shares = json.loads(pathlib.Path(args.shares).read_text(encoding="utf-8"))
assert shares["declaration_sha256"] == args.declaration_sha and shares["a_tag"] == args.a_tag
assert args.arm in decl["doc_arms"], args.arm
arm = decl["arms"][args.arm]
PILOT_DIR = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")
for n, h in decl["labels"]["files"].items():
    assert hashlib.sha256((PILOT_DIR / decl["labels"]["dir"] / n).read_bytes()).hexdigest() == h, f"label file {n} changed"
sys.path.insert(0, "C:/t/iso/work/r2x/ai-pilot")
import dry_provider as dry  # noqa: E402

RUNS = pathlib.Path(dry.DRY_RUNS if dry.DRY else "C:/t/r2x/runs")
SRC = RUNS / args.a_tag
ROOT = RUNS / args.tag
DB = ROOT / "db" / "default.db"
if ROOT.exists():
    sys.exit(f"{ROOT} exists: a run is never repeated over its own sandbox")
for d in ("db", "out", "out/io"):
    (ROOT / d).mkdir(parents=True, exist_ok=True)
a_run = json.loads((SRC / "out" / "RUN.json").read_text(encoding="utf-8"))
assert a_run["track"] == "A" and a_run["declaration_sha256"] == args.declaration_sha, "the source is not this declaration's A base"
_src = sqlite3.connect(f"file:{(SRC / 'db' / 'default.db').as_posix()}?mode=ro", uri=True)
_dst = sqlite3.connect(str(DB))
_src.backup(_dst)
_dst.close()
_src.close()
import shutil  # noqa: E402

for d in ("cache", "library", "uploads"):        # each arm its own copy of A's file caches: no arm writes into another's state
    shutil.copytree(SRC / d, ROOT / d)
scope = decl["ledger"]["scopes"][args.arm]
if dry.DRY:
    scope = {**scope, "env": {**scope["env"], "AI_LEDGER_PATH": dry.DRY_LEDGER}}
for k in ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED", "AI_EVIDENCE_EFFICIENT"):
    os.environ.pop(k, None)
env = {"DATABASE_URL": f"sqlite:///{DB.as_posix()}", "CACHE_ROOT": str(ROOT / "cache"), "LIBRARY_ROOT": str(ROOT / "library"), "UPLOADS_ROOT": str(ROOT / "uploads"),
       "AI_ENABLED": "true", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false", "EXTRACTION_PROMOTE_OBSERVATIONS": "false", "DATASHEET_LIBRARIES": "{}",
       "ARCHIVE_DATASHEET_LIBRARIES": "{}", "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false",
       "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "LIBRARY_RESCAN_SECONDS": "0", **decl["provider"]["env"], **scope["env"], **arm["env"]}
os.environ.update(env)
B = pathlib.Path(arm["tree"]) / "backend"
sys.path.insert(0, str(B)); os.chdir(B)
sys.path.insert(0, "C:/t/iso/work/r2x/run")
import subprocess  # noqa: E402

assert subprocess.run(["git", "-C", str(B.parent), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() == arm["commit"]
assert not subprocess.run(["git", "-C", str(B.parent), "status", "--porcelain"], capture_output=True, text=True).stdout.strip(), "the arm's tree is dirty"
import xtrack  # noqa: E402

if dry.DRY:
    xtrack.PATH = dry.DRY_XTRACK
from app.core.config import Settings, get_settings  # noqa: E402

st = get_settings()
assert DB.as_posix() in st.database_url and st.ai_enabled and st.ai_evidence_variant == "EV1" and st.ai_ledger_scope == scope["scope"]
for k, v in decl["application_limits"].items():
    assert getattr(st, k) == v == Settings.model_fields[k].default, f"application limit {k} is not the frozen default"
from app.ai import evidence_reader as er  # noqa: E402

if dry.DRY:
    dry.install()

assert pathlib.Path(er.__file__).resolve().is_relative_to(B.resolve())
for k, v in arm["identities"].items():
    assert getattr(er, k, None) == v, f"{k} differs from the declaration"
from app.database import SessionLocal  # noqa: E402
from app.models import Project, ProjectDocument  # noqa: E402
from scripts import m2_eval5 as EV  # noqa: E402

assert hashlib.sha256(pathlib.Path(EV.__file__).read_bytes()).hexdigest() == decl["code"]["evaluator"]["sha256"], "evaluator differs"
LIMIT = decl["application_limits"]["ai_max_calls_per_project_per_day"]
SHARE = shares["shares"]
track = f"cont-{args.arm}"
REG = json.loads((PILOT_DIR / decl["labels"]["dir"] / decl["labels"]["register"]).read_text(encoding="utf-8"))
PAGE = json.loads((PILOT_DIR / decl["labels"]["dir"] / decl["labels"]["page"]).read_text(encoding="utf-8"))
UNC = json.loads((PILOT_DIR / decl["labels"]["dir"] / decl["labels"]["uncertainty"]).read_text(encoding="utf-8"))
unresolved = {u["doc"] for u in UNC["uncertainty"]} | {d["doc"] for d in REG["documents"] if d.get("confidence") != "high"}
CONTEXT = {"variant": "EV1", "profile": "default", "policies": [arm["identities"]["EVIDENCE_POLICY_VERSION"]], "declared": f"pilot arm {args.arm}"}
ep_of = {}
state = {"consecutive_failures": 0, "stopped": None, "xtrack_refusals": 0, "share_refusals": 0, "per_ep": {}, "requests_io": 0}
_original_call = er.EvidenceRun.call
IO = ROOT / "out" / "io"


def _save_io(kw, data, entries):
    state["requests_io"] += 1
    n = state["requests_io"]
    parts = []
    for i, p in enumerate(kw.get("parts") or []):
        if hasattr(p, "png"):
            name = f"{n:03d}-{kw.get('task')}-p{kw.get('page')}-{i}-{p.label}.png"
            (IO / name).write_bytes(p.png)
            parts.append({"label": p.label, "image": name, "sha256": hashlib.sha256(p.png).hexdigest()})
        else:
            parts.append({"label": p.label, "text": p.text})
    rec = {"n": n, "sha256": kw.get("sha256"), "task": kw.get("task"), "page": kw.get("page"), "reason": kw.get("reason"), "tier": kw.get("tier", "small"),
           "schema": kw.get("schema"), "parts": parts, "answer": data, "log": entries}
    with open(ROOT / "out" / "io.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def _guarded_call(self, **kw):
    ep = ep_of.get(self.project_id)
    if state["stopped"] and not self.exhausted:
        self.exhausted = state["stopped"]
    took = False
    if not self.exhausted:
        if state["per_ep"].get(ep, 0) >= SHARE[ep]:
            state["share_refusals"] += 1
            self.exhausted = f"per-arm project share ({SHARE[ep]})"
        else:
            took = xtrack.take(ep, track, kw.get("task", ""), LIMIT)
            if not took:
                state["xtrack_refusals"] += 1
                self.exhausted = "calls_per_project_per_day (across tracks)"
    before, n_log = self.calls, len(self.log)
    out = _original_call(self, **kw)
    new = self.log[n_log:]
    if took and self.calls == before:
        xtrack.release_last(ep, track)          # a cache hit or a refusal: no request was made
    if self.calls > before:
        state["per_ep"][ep] = state["per_ep"].get(ep, 0) + (self.calls - before)
    if any(not e.get("cache_hit") and not str(e.get("outcome", "")).startswith("budget") for e in new):
        _save_io(kw, out, new)
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


def dump_rows():
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = {}
    for r in con.execute("select d.id, p.ep_number, d.relative_path, d.role, d.state, d.error, d.sha256, d.reference, d.revision, d.status, d.system_code, d.extracted "
                         "from project_documents d join projects p on p.id = d.project_id"):
        rows[f"EP-{r['ep_number']}/{r['relative_path']}".replace("\\", "/")] = {
            "id": r["id"], "ep": r["ep_number"], "role": r["role"], "state": r["state"], "error": r["error"], "sha256": r["sha256"],
            "mirror": {"reference": r["reference"], "revision": r["revision"], "status": r["status"], "system_code": r["system_code"]},
            "extracted": json.loads(r["extracted"]) if r["extracted"] else None}
    con.close()
    return rows


def tripwire(done_eps: set) -> list:
    """Critical automatic acceptances by this arm's AI on resolved labels, over the projects done so far."""
    docs = [d for d in REG["documents"] if d["ep"] in done_eps]
    ev = EV.evaluate({**REG, "documents": docs}, PAGE, dump_rows(), PAGE.get("page1_corrections"), ai_context=CONTEXT)
    return [c for c in ev["totals"]["introduced_ai_errors"] if c["doc"] not in unresolved]


started = time.perf_counter()
manifest = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "a_tag": args.a_tag, "tag": args.tag, "arm": args.arm,
            "track": track, "dry_run": dry.DRY, "declaration_sha256": args.declaration_sha, "shares_sha256": args.shares_sha, "identities": arm["identities"],
            "commit": arm["commit"], "tree": arm["tree"], "context": CONTEXT, "projects": {}, "not_attempted": [], "tripwire": []}
with SessionLocal() as db:
    done = set()
    for project in db.query(Project).order_by(Project.id).all():
        ep_of[project.id] = project.ep_number
        rows = [r for r in db.query(ProjectDocument).filter(ProjectDocument.project_id == project.id, ProjectDocument.state == "fresh").order_by(ProjectDocument.id)
                if (r.path or "").lower().endswith(".pdf")]
        if state["stopped"] and state["stopped"].startswith("stop: critical"):
            manifest["not_attempted"].append({"ep": project.ep_number, "documents": [r.relative_path for r in rows], "reason": state["stopped"]})
            continue
        t0 = time.perf_counter()
        n_before = state["per_ep"].get(project.ep_number, 0)
        counts = er.evidence_stage(db, project, [(r, pathlib.Path(r.path)) for r in rows], variant="EV1")
        db.commit()
        done.add(project.ep_number)
        manifest["projects"][project.ep_number] = {**counts, "seconds": round(time.perf_counter() - t0, 1), "documents_in": len(rows),
                                                   "requests": state["per_ep"].get(project.ep_number, 0) - n_before, "share": SHARE[project.ep_number]}
        crit = tripwire(done)
        manifest["tripwire"].append({"after": project.ep_number, "critical_on_resolved": crit})
        if crit and not state["stopped"]:
            state["stopped"] = f"stop: critical acceptance on a resolved label after EP-{project.ep_number}"
        print(project.ep_number, args.arm, counts, manifest["projects"][project.ep_number]["requests"], "req", round(time.perf_counter() - t0, 1), "s",
              "| critical", len(crit), flush=True)
manifest.update({"seconds": round(time.perf_counter() - started, 1), "runner_state": state})
rows = dump_rows()
con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
usage = [dict(u) for u in con.execute("select u.id, p.ep_number, u.task, u.model, u.input_tokens, u.output_tokens, u.cached_input_tokens, u.reasoning_tokens, "
                                      "u.estimated_cost, u.latency_ms, u.cache_hit, u.escalated, u.outcome, u.at from ai_usage u left join projects p on p.id = u.project_id order by u.id")]
tables = {t: con.execute(f"select count(*) from {t}").fetchone()[0] for t in
          ("project_documents", "project_submittals", "project_shop_drawings", "background_jobs", "project_actions", "ai_usage", "document_readings")}
business = {}
for t in ("project_submittals", "project_shop_drawings", "project_actions"):
    business[t] = hashlib.sha256(json.dumps([list(r) for r in con.execute(f"select * from {t} order by id")], default=str).encode()).hexdigest()
business["project_documents_role"] = hashlib.sha256(json.dumps([list(r) for r in con.execute("select id, role from project_documents order by id")]).encode()).hexdigest()
con.close()
manifest.update({"tables": tables, "business_hashes": business, "ai_usage_rows": len(usage),
                 "fresh_requests_this_arm": sum(1 for u in usage if not u["cache_hit"] and str(u["task"]).startswith("evidence:"))})
json.dump(manifest, open(ROOT / "out" / "RUN.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(rows, open(ROOT / "out" / "rows.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(usage, open(ROOT / "out" / "usage.json", "w", encoding="utf-8"), indent=1, default=str)
print("done", args.tag, args.arm, "requests", sum(state["per_ep"].values()), "seconds", manifest["seconds"], "state",
      {k: v for k, v in state.items() if k != "per_ep"}, state["per_ep"])
