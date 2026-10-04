"""Review 06 BOQ AI variants: blind row verification (app.ai.evidence_reader.verify_boq_rows) of the deterministic
reader's rows on the eligible sheets, with the real provider, in a sandbox database (result cache + usage). Then each
verified row is joined to the frozen BOQ evaluator's pairing of the same extraction (truth per emitted row), and the
verification is scored: a wrong accepted row caught (conflict) or missed (validated); a correct accepted row confirmed
or needlessly questioned; a held row's blind reading right or wrong.
Usage: run_boq_ev.py <tag> <EV1|EV2> <scored.json from m2_boq_eval> <extraction.json> --budget-json f"""
import argparse, collections, datetime, json, os, pathlib, sys, time

a = argparse.ArgumentParser(); a.add_argument("tag"); a.add_argument("variant"); a.add_argument("scored"); a.add_argument("extraction")
a.add_argument("--budget-json", required=True); a.add_argument("--eps", default="30784,30088")
args = a.parse_args()
ROOT = pathlib.Path("C:/t/r6") / args.tag
for d in ("db", "cache", "library", "uploads", "out"):
    (ROOT / d).mkdir(parents=True, exist_ok=True)
DB = ROOT / "db" / "boq-ev.db"
# an existing run database is resumed, not deleted: answers already paid for come back as cache hits, and the cap
# counts every fresh request the run has made (below)
budget = json.load(open(args.budget_json, encoding="utf-8"))
os.environ.update({"DATABASE_URL": f"sqlite:///{DB.as_posix()}", "CACHE_ROOT": str(ROOT / "cache"), "LIBRARY_ROOT": str(ROOT / "library"),
                   "UPLOADS_ROOT": str(ROOT / "uploads"), "AI_ENABLED": "true", "AI_PROVIDER": "claude-code", "AI_MODEL_SMALL": "sonnet",
                   "AI_MODEL_STANDARD": "opus", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false", "DATASHEET_LIBRARIES": "{}",
                   "ARCHIVE_DATASHEET_LIBRARIES": "{}", "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false",
                   "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "LIBRARY_RESCAN_SECONDS": "0",
                   **{k: str(v) for k, v in budget["settings"].items()}})
B = pathlib.Path(r"C:\t\iso\ep-platform\backend"); sys.path.insert(0, str(B)); os.chdir(B)
from app.core.config import get_settings  # noqa: E402
st = get_settings(); assert DB.as_posix() in st.database_url and st.ai_enabled
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

_CAP = budget.get("max_total_calls")
import sqlite3 as _sq  # noqa: E402

_c = _sq.connect(str(DB)); _fresh = {"n": _c.execute("select count(*) from ai_usage where task like 'evidence:%' and cache_hit = 0").fetchone()[0]}; _c.close()
_original_call = er.EvidenceRun.call


def _capped_call(self, **kw):
    # the declared cap enforced per call: past it, each further row is a budget stop, recorded, never a negative
    if _CAP is not None and _fresh["n"] >= _CAP:
        self.exhausted = "experiment cap"
    before = self.calls
    out = _original_call(self, **kw)
    _fresh["n"] += self.calls - before
    return out


er.EvidenceRun.call = _capped_call

scored = {f"EP-{s['ep']}/{s['relative_path']}": s for s in json.load(open(args.scored, encoding="utf-8"))["sheets"]}
extractions = json.load(open(args.extraction, encoding="utf-8"))
sets = {}
for f in (r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\FROZEN-BOQ-SET.json",):
    for s in json.load(open(f, encoding="utf-8"))["sheets"]:
        sets[f"EP-{s['ep']}/{s['relative_path']}"] = s
provider = get_provider()
assert provider.ready, provider.status


def norm(t):
    return er.norm(t)


out = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "variant": args.variant, "reader": er.READER_VERSION,
       "policy": er.EVIDENCE_POLICY_VERSION, "prompt": er.PROMPTS["read_boq_row"], "budget": budget, "sheets": {}}
totals = collections.Counter()
calls = 0
with SessionLocal() as db:
    for key, extraction in extractions.items():
        if not any(f"EP-{ep}/" in key for ep in args.eps.split(",")):
            continue
        if budget.get("max_total_calls") is not None and calls >= budget["max_total_calls"]:
            out["sheets"][key] = {"skipped": "run cap reached"}
            continue
        sheet = sets[key]
        path = pathlib.Path(sheet["staged_path"])
        run = er.EvidenceRun(db=db, project_id=None, provider=provider, budget=open_budget(db, None), variant=args.variant)
        # one budget per sheet is too small for a whole table: rows are verified in blocks of the per-document call limit
        t0 = time.perf_counter()
        with pymupdf.open(path) as pdf:
            results = []
            lines = extraction.get("lines") or []
            issues = extraction.get("issues") or []
            selected = er.boq_rows_to_verify([dict(l, _accepted=True) for l in lines], [], variant=args.variant, sha256=sheet["sha256"])
            # held rows + selected accepted rows, verified through the same function, in chunks with a fresh per-sheet budget
            chunk = max(1, st.ai_max_calls_per_document - 1)
            accepted_selected = [r for r, _ in selected]
            held_issues = [i for i in issues if str(i.get("target") or "").startswith("boq_line:")]
            work = [{"lines": [dict(l) for l in accepted_selected[i:i + chunk]], "issues": []} for i in range(0, len(accepted_selected), chunk)]
            work += [{"lines": [], "issues": held_issues[i:i + chunk]} for i in range(0, len(held_issues), chunk)]
            for part in work:
                run.budget = open_budget(db, None)
                run.exhausted = run.exhausted if run.exhausted == "experiment cap" else None
                results += er.verify_boq_rows(run, pdf, sha256=sheet["sha256"], extraction={"lines": part["lines"], "issues": part["issues"], "geometry_lines": lines},
                                              render_dpi=dse.RENDER_DPI, preselected=True)
                db.commit()
        calls += run.calls
        # join to truth through the evaluator's pairs: (page, part, quantity, description) of the emitted row
        pairs = scored[key]["pairs"]
        judged = []
        for r in results:
            row = r["row"]
            match = [p for p in pairs if p.get("emitted") and int(p.get("page") or (p.get("emitted") or {}).get("page") or 0) == int(r["page"])
                     and norm(p["emitted"].get("part_number")) == norm(row.get("part_number"))
                     and norm(p["emitted"].get("quantity")) == norm(row.get("quantity"))
                     and bool(p["emitted"].get("accepted")) == bool(r.get("accepted_by_reader"))]
            if len(match) > 1:
                match = [p for p in match if norm(p["emitted"].get("description"))[:12] == norm(row.get("description"))[:12]] or match[:1]
            truth = match[0].get("truth") if match else None
            fields = (match[0].get("fields") or {}) if match else {}
            reader_right = all(fields.get(f) in ("tp", "tn") for f in ("part_number", "quantity")) if match else None
            blind = r.get("blind") or {}
            blind_right = None
            if truth is not None and blind:
                blind_right = (norm(blind.get("part_number")) == norm(truth.get("part_number")) or (not truth.get("part_number") and not blind.get("part_number"))) \
                    and norm(blind.get("quantity")) == norm(truth.get("quantity"))
            outcome = ("no_truth_match" if not match else "extra_row" if truth is None else
                       ("caught_wrong_accepted" if r.get("state") == "conflict" else "missed_wrong_accepted" if r.get("state") == "validated" else "wrong_accepted_unverified")
                       if r.get("accepted_by_reader") and reader_right is False else
                       ("confirmed_correct" if r.get("state") == "validated" else "questioned_correct" if r.get("state") == "conflict" else "correct_unverified")
                       if r.get("accepted_by_reader") else
                       ("held_blind_right" if blind_right else "held_blind_wrong" if blind_right is False else "held_unread"))
            totals[outcome] += 1
            judged.append({**r, "truth": truth, "reader_fields": fields, "blind_right": blind_right, "outcome": outcome})
        out["sheets"][key] = {"seconds": round(time.perf_counter() - t0, 1), "calls": run.calls, "cache_hits": run.cache_hits, "log": run.log, "rows": judged,
                              "outcomes": dict(collections.Counter(j["outcome"] for j in judged))}
        print(key[-50:], args.variant, "calls", run.calls, out["sheets"][key]["outcomes"], round(time.perf_counter() - t0, 1), "s", flush=True)
out["totals"] = dict(totals); out["calls"] = calls
json.dump(out, open(ROOT / "out" / f"BOQ-{args.variant}.json", "w", encoding="utf-8"), indent=1, default=str)
print("done", args.variant, dict(totals), "calls", calls)
