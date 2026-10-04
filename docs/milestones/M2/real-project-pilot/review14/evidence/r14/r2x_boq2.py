"""CORRECTED BOQ runner (R14-01 / R14-02; not executed with a real provider in the Review 14 correction task).
Differences from r2x_boq.py (preserved as submitted): the sheet is verified by r14/boq_harness.verify_sheet -- ONE
application budget per (declaration scope, profile, document) across chunks, retries and resumes, persisted in
C:/t/r2x/ledger/doc-allowance.sqlite, no per-document stop cleared -- and the raw results are written unscored: truth
joining and scoring are done by the typed contract (r14/boq_contract.py, as r14/replay_boq.py does).

Round 2 exploration, BOQ profiles B (EV1: held rows + the frozen 20 % audit of accepted rows) and C (EV2: every row):
blind row verification (app.ai.evidence_reader.verify_boq_rows) of the frozen candidate's deterministic rows, with the
real provider, in a sandbox database. Each verified row is joined to the frozen BOQ evaluator's pairing of the same
extraction (profile A = the AI-off extraction, boq/holdout-A-r12*.json) and judged: a wrong accepted row caught
(conflict) or missed (validated); a correct accepted row confirmed or questioned; a held row's blind reading right or
wrong. Adapted from the Review 06 runner (run_boq_ev.py): the frozen-r12 tree, application limits unchanged, the
declared ledger scope, the cross-track project-day limit and the three-consecutive-failures stop (as r2x_ev.py).
Verifier input is blind: the crop of the row, never the reader's values (the function's contract).

Usage: r2x_boq2.py <tag> <EV1|EV2> --declaration DECL.json --declaration-sha SHA"""
import argparse
import collections
import datetime
import hashlib
import json
import os
import pathlib
import sys
import time

a = argparse.ArgumentParser()
a.add_argument("tag"); a.add_argument("variant")
a.add_argument("--declaration", required=True); a.add_argument("--declaration-sha", required=True)
args = a.parse_args()
assert args.variant in ("EV1", "EV2")
assert hashlib.sha256(pathlib.Path(args.declaration).read_bytes()).hexdigest() == args.declaration_sha, "the declaration changed"
decl = json.loads(pathlib.Path(args.declaration).read_text(encoding="utf-8"))
boq = decl["boq"]
for f, sha in boq["inputs_sha256"].items():
    assert hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest() == sha, f"{f} changed"
ROOT = pathlib.Path("C:/t/r2x/runs") / args.tag
DB = ROOT / "db" / "boq.db"
if DB.exists():
    sys.exit(f"{DB} exists: a run is never repeated over its own sandbox (preserve it; use a new tag)")
for d in ("db", "cache", "library", "uploads", "out"):
    (ROOT / d).mkdir(parents=True, exist_ok=True)
os.environ.update({"DATABASE_URL": f"sqlite:///{DB.as_posix()}", "CACHE_ROOT": str(ROOT / "cache"), "LIBRARY_ROOT": str(ROOT / "library"),
                   "UPLOADS_ROOT": str(ROOT / "uploads"), "AI_ENABLED": "true", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false",
                   "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false",
                   "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "LIBRARY_RESCAN_SECONDS": "0", **decl["provider"]["env"], **decl["ledger"]["env"]})
B = pathlib.Path(decl["candidate"]["worktree"]) / "backend"
sys.path.insert(0, str(B)); os.chdir(B)
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import xtrack  # noqa: E402
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'r14'))
import boq_harness as bh  # noqa: E402
from app.core.config import Settings, get_settings  # noqa: E402

st = get_settings()
assert DB.as_posix() in st.database_url and st.ai_enabled
for k, v in decl["application_limits"].items():
    assert getattr(st, k) == v == Settings.model_fields[k].default, f"application limit {k} is not the frozen default"
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app as api  # noqa: E402

with TestClient(api):
    pass    # startup: the sandbox database's schema
import pymupdf  # noqa: E402

from app.ai import evidence_reader as er  # noqa: E402
from app.ai.budget import open_budget  # noqa: E402
from app.ai.provider import get_provider  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.services import design_sheet_extractor as dse  # noqa: E402

for k, v in decl["identities"]["evidence_reader"].items():
    assert getattr(er, k) == v, f"{k} differs from the declaration"
LIMIT = decl["application_limits"]["ai_max_calls_per_project_per_day"]
track = {"EV1": "B-boq", "EV2": "C-boq"}[args.variant]
state = {"consecutive_failures": 0, "stopped": None, "xtrack_refusals": 0, "ep": None}
_original_call = er.EvidenceRun.call


def _guarded_call(self, **kw):
    ep = state["ep"]
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
    if took and self.calls == before:
        xtrack.release_last(ep, track)
    for entry in self.log[n_log:]:
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
scored = {f"EP-{s['ep']}/{s['relative_path']}".replace("\\", "/"): s for s in json.load(open(boq["scored"], encoding="utf-8"))["sheets"]}
extractions = {k.replace("\\", "/"): v for k, v in json.load(open(boq["extraction"], encoding="utf-8")).items()}
sheets = {f"EP-{s['ep']}/{s['relative_path']}".replace("\\", "/"): s for s in json.load(open(boq["set"], encoding="utf-8"))["sheets"]}
provider = get_provider()
assert provider.ready, provider.status

out = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "track": track, "variant": args.variant,
       "declaration_sha256": args.declaration_sha, "reader": er.READER_VERSION, "policy": er.EVIDENCE_POLICY_VERSION, "prompt": er.PROMPTS["read_boq_row"], "sheets": {}}

calls = 0
with SessionLocal() as db:
    for key in boq["sheets"]:
        sheet, extraction = sheets[key], extractions[key]
        state["ep"] = sheet["ep"]
        path = pathlib.Path(sheet["staged_path"])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == sheet["sha256"]
        run = er.EvidenceRun(db=db, project_id=None, provider=provider, budget=open_budget(db, None), variant=args.variant)
        t0 = time.perf_counter()
        with pymupdf.open(path) as pdf:
            results, info = bh.verify_sheet(er, run, pdf, db=db, open_budget=open_budget, allowance=bh.DocAllowance("C:/t/r2x/ledger/doc-allowance.sqlite"),
                                            scope=decl["ledger"]["env"]["AI_LEDGER_SCOPE"], profile=args.variant, lines=extraction.get("lines") or [],
                                            issues=extraction.get("issues") or [], variant=args.variant, sha256=sheet["sha256"],
                                            max_calls_per_document=st.ai_max_calls_per_document, render_dpi=dse.RENDER_DPI)
        calls += run.calls
        out["sheets"][key] = {"seconds": round(time.perf_counter() - t0, 1), "calls": run.calls, "cache_hits": run.cache_hits, "exhausted": run.exhausted,
                              "document_budget": info, "log": run.log, "rows": results, "scored": False}
        print(key[-50:], args.variant, "calls", run.calls, "exhausted", run.exhausted, round(time.perf_counter() - t0, 1), "s", flush=True)
import sqlite3  # noqa: E402

con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
usage = [dict(u) for u in con.execute("select id, project_id, task, model, input_tokens, output_tokens, cached_input_tokens, reasoning_tokens, estimated_cost, "
                                      "latency_ms, cache_hit, escalated, outcome, at from ai_usage order by id")]
con.close()
out.update({"calls": calls, "runner_state": state, "harness": bh.HARNESS_VERSION})
json.dump(out, open(ROOT / "out" / "BOQ.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(usage, open(ROOT / "out" / "usage.json", "w", encoding="utf-8"), indent=1, default=str)
print("done", args.variant, "calls", calls, "state", state, "(unscored: score with the typed contract)")
