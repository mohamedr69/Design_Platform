"""AI accuracy pilot, BOQ-S / BOQ-T on the pilot design sheet (EP-22510 FA Design, hash-checked), accepted tree 3d5607d.
  S: the accepted EV1 selection (held rows + seeded 20 % audit) through the r16.1 harness `boq_harness.verify_sheet`.
  T: the declared risk-ordered queue (`boq_queue.risk_queue`), written to out/QUEUE.json BEFORE the first request,
     through `boq_queue.verify_queue` (the same r16.1 allowance, lock and attempt labelling).
One durable allowance per (scope, profile, document): 12 requests / 2 escalations / 120 s. The arm's own ledger scope,
the cross-track 60/day counter and the three-consecutive-failures stop apply; every model input / output is kept.
Scoring (r16.1 replay_core, unchanged) happens afterwards, not here.

Usage: pilot_boq.py <tag> <S|T> --declaration D --declaration-sha SHA"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import sys
import time

a = argparse.ArgumentParser()
a.add_argument("tag"); a.add_argument("arm")
a.add_argument("--declaration", required=True); a.add_argument("--declaration-sha", required=True)
args = a.parse_args()
assert args.arm in ("S", "T")
assert hashlib.sha256(pathlib.Path(args.declaration).read_bytes()).hexdigest() == args.declaration_sha, "the declaration changed"
decl = json.loads(pathlib.Path(args.declaration).read_text(encoding="utf-8"))
PILOT_DIR = pathlib.Path("C:/t/iso/work/r2x/ai-pilot")
ext_file = PILOT_DIR / decl["sources"]["boq_extraction_A"]["file"]
assert hashlib.sha256(ext_file.read_bytes()).hexdigest() == decl["sources"]["boq_extraction_A"]["sha256"]
for f, h in decl["code"]["boq_harness_r16"].items():
    assert hashlib.sha256((pathlib.Path("C:/t/iso/work/r2x/r16") / f).read_bytes()).hexdigest() == h, f
assert hashlib.sha256((PILOT_DIR / "boq_queue.py").read_bytes()).hexdigest() == decl["code"]["pilot_scripts"]["boq_queue.py"]
sys.path.insert(0, str(pathlib.Path("C:/t/iso/work/r2x/ai-pilot")))
import dry_provider as dry  # noqa: E402

RUNS = pathlib.Path(dry.DRY_RUNS if dry.DRY else "C:/t/r2x/runs")
ROOT = RUNS / args.tag
DB = ROOT / "db" / "boq.db"
if ROOT.exists():
    sys.exit(f"{ROOT} exists: a run is never repeated over its own sandbox")
for d in ("db", "cache", "library", "uploads", "out", "out/io"):
    (ROOT / d).mkdir(parents=True, exist_ok=True)
scope = decl["ledger"]["scopes"][f"BOQ-{args.arm}"]
if dry.DRY:
    scope = {**scope, "env": {**scope["env"], "AI_LEDGER_PATH": dry.DRY_LEDGER}}
for k in ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED"):
    os.environ.pop(k, None)
os.environ.update({"DATABASE_URL": f"sqlite:///{DB.as_posix()}", "CACHE_ROOT": str(ROOT / "cache"), "LIBRARY_ROOT": str(ROOT / "library"),
                   "UPLOADS_ROOT": str(ROOT / "uploads"), "AI_ENABLED": "true", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false",
                   "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false",
                   "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "LIBRARY_RESCAN_SECONDS": "0", **decl["provider"]["env"], **scope["env"]})
B = pathlib.Path(decl["code"]["accepted_app"]["tree"]) / "backend"
sys.path.insert(0, str(B)); os.chdir(B)
sys.path.insert(0, "C:/t/iso/work/r2x/run")
sys.path.insert(0, "C:/t/iso/work/r2x/r16")
sys.path.insert(0, str(PILOT_DIR))
import xtrack  # noqa: E402

if dry.DRY:
    xtrack.PATH = dry.DRY_XTRACK
from app.core.config import Settings, get_settings  # noqa: E402

st = get_settings()
assert DB.as_posix() in st.database_url and st.ai_enabled and st.ai_ledger_scope == scope["scope"]
for k, v in decl["application_limits"].items():
    assert getattr(st, k) == v == Settings.model_fields[k].default, f"application limit {k} is not the frozen default"
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app as api  # noqa: E402

with TestClient(api):
    pass
import pymupdf  # noqa: E402

import boq_harness as bh  # noqa: E402
import boq_queue as bq  # noqa: E402
from app.ai import evidence_reader as er  # noqa: E402
from app.ai.budget import open_budget  # noqa: E402
from app.ai.provider import get_provider  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.services import design_sheet_extractor as dse  # noqa: E402

if dry.DRY:
    dry.install()

for k, v in decl["arms"]["S"]["identities"].items():
    assert getattr(er, k, None) == v, f"{k} differs from the declaration"
sheet = decl["sources"]["boq_sheet"]
EP = sheet["doc_key"].split("/", 1)[0][3:]
LIMIT = decl["application_limits"]["ai_max_calls_per_project_per_day"]
track = f"pilot-BOQ-{args.arm}"
state = {"consecutive_failures": 0, "stopped": None, "xtrack_refusals": 0, "requests_io": 0}
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
    if state["stopped"] and not self.exhausted:
        self.exhausted = state["stopped"]
    took = False
    if not self.exhausted:
        took = xtrack.take(EP, track, kw.get("task", ""), LIMIT)
        if not took:
            state["xtrack_refusals"] += 1
            self.exhausted = "calls_per_project_per_day (across tracks)"
    before, n_log = self.calls, len(self.log)
    out = _original_call(self, **kw)
    new = self.log[n_log:]
    if took and self.calls == before:
        xtrack.release_last(EP, track)
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
extraction = json.loads(ext_file.read_text(encoding="utf-8"))[sheet["doc_key"]]
lines, issues = extraction["lines"], extraction["issues"]
cap = st.ai_max_calls_per_document
if args.arm == "T":
    queue = bq.risk_queue(lines, issues, sha256=sheet["sha256"], cap=cap, recheck_quantity_below=dse.RECHECK_QUANTITY_BELOW,
                          confirm_catalog_below=dse.CONFIRM_CATALOG_BELOW)
    selection = queue
else:
    sel = er.boq_rows_to_verify([dict(l, _accepted=True) for l in lines], [], variant="EV1", sha256=sheet["sha256"])
    selection = {"policy": "EV1 (accepted)", "held_issues": [i for i, s in enumerate(issues) if str(s.get("target") or "").startswith("boq_line:")],
                 "audit_lines": [next(i for i, l in enumerate(lines) if l.get("y_px") == r.get("y_px") and l.get("page") == r.get("page")) for r, _ in sel],
                 "harness_order": "accepted-line chunks first, then held-row chunks (boq_harness._work)"}
qp = ROOT / "out" / ("QUEUE.json" if args.arm == "T" else "SELECTION.json")
qp.write_text(json.dumps(selection, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
declared = {"file": qp.name, "sha256": hashlib.sha256(qp.read_bytes()).hexdigest(), "at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
print("declared order", declared, flush=True)
provider = get_provider()
assert provider.ready, provider.status
data = open("\\\\?\\" + sheet["staged_path"].replace("/", "\\"), "rb").read()
assert hashlib.sha256(data).hexdigest() == sheet["sha256"], "the sheet changed"
allowance = bh.DocAllowance(dry.DRY_ALLOWANCE if dry.DRY else "C:/t/r2x/ledger/ai-pilot-boq-allowance.sqlite")
t0 = time.perf_counter()
with SessionLocal() as db, pymupdf.open(stream=data, filetype="pdf") as pdf:
    run = er.EvidenceRun(db=db, project_id=None, provider=provider, budget=open_budget(db, None), variant="EV1")
    if args.arm == "T":
        results, info = bq.verify_queue(er, run, pdf, db=db, open_budget=open_budget, harness=bh, allowance=allowance, scope=scope["scope"], profile="BOQ-T",
                                        lines=lines, issues=issues, queue=queue, sha256=sheet["sha256"], max_calls_per_document=cap, render_dpi=dse.RENDER_DPI)
    else:
        n_log = len(run.log)
        results, info = bh.verify_sheet(er, run, pdf, db=db, open_budget=open_budget, allowance=allowance, scope=scope["scope"], profile="BOQ-S",
                                        lines=lines, issues=issues, variant="EV1", sha256=sheet["sha256"], max_calls_per_document=cap, render_dpi=dse.RENDER_DPI)
        # one log entry per row with geometry, in order: the request outcome of each row
        entries = iter(run.log[n_log:])
        results = [dict(r, request=(next(entries)["outcome"] if r.get("state") != "no_geometry" else "no_request")) for r in results]
    log = run.log
out = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "tag": args.tag, "arm": f"BOQ-{args.arm}", "track": track, "dry_run": dry.DRY,
       "declaration_sha256": args.declaration_sha, "sheet": sheet["doc_key"], "sha256": sheet["sha256"], "declared_order": declared, "seconds": round(time.perf_counter() - t0, 1),
       "reader": er.READER_VERSION, "policy": er.EVIDENCE_POLICY_VERSION, "prompt": er.PROMPTS["read_boq_row"], "allowance": info, "calls": run.calls,
       "cache_hits": run.cache_hits, "exhausted": run.exhausted, "log": log, "rows": results, "runner_state": state,
       "not_reached": (queue["not_reached"] if args.arm == "T" else None)}
import sqlite3  # noqa: E402

con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
usage = [dict(u) for u in con.execute("select id, project_id, task, model, input_tokens, output_tokens, cached_input_tokens, reasoning_tokens, estimated_cost, "
                                      "latency_ms, cache_hit, escalated, outcome, at from ai_usage order by id")]
con.close()
json.dump(out, open(ROOT / "out" / "BOQ.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(usage, open(ROOT / "out" / "usage.json", "w", encoding="utf-8"), indent=1, default=str)
print("done", out["arm"], "calls", run.calls, "rows", len(results), "exhausted", run.exhausted, "state", state)
