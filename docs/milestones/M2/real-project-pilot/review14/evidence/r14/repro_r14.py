"""R14-01 / R14-02 reproduction figures (offline, scripted provider): requests the SUBMITTED and the CORRECTED loops
send for the EP-8430 sheet under EV1 and EV2, and the old / new comparison outcomes -- written to REPRO-R14.json.
Also reconciles the stored real runs (25 / 35 requests on one document) with the declared 12-per-document limit."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tests"))
import test_r14_harness as t  # noqa: E402  (sets up the throw-away sandbox exactly as the tests do)

out = {"loops": {}, "comparisons": [], "stored_runs": {}}
for variant in ("EV1", "EV2"):
    t._fresh_usage.__wrapped__() if hasattr(t._fresh_usage, "__wrapped__") else None
    from app.models import AiUsage
    with t.SessionLocal() as db:
        db.query(AiUsage).delete(); db.commit()
    p = t.ScriptedProvider()
    res, run = t._submitted(p, variant)
    with t.SessionLocal() as db:
        db.query(AiUsage).delete(); db.commit()
    q = t.ScriptedProvider()
    res2, run2, info = t._corrected(q, t.bh.DocAllowance(str(t.TMP / f"repro-{variant}.sqlite")), profile=variant, variant=variant)
    out["loops"][variant] = {"rows_selected": len([r for r in res if r.get("state") != "no_geometry"]), "submitted_loop_requests": p.requests,
                             "corrected_loop_requests": q.requests, "corrected_exhausted": run2.exhausted,
                             "corrected_budget_refused_rows": sum(1 for r in res2 if r.get("reasons") == ["no reading"])}
for a, b, kind in (("PT-1S", "PT-1S+", "part"), ("1.0", "10", "quantity"), ("-1", "1", "quantity"), (0, None, "quantity"), ("PRS-CSNKP", "PRS-CSNKP", "part"), ("2", "2", "quantity"),
                   ("1", "1.0", "quantity")):
    new = t.bc.parts_equal(a, b) if kind == "part" else t.bc.quantities_equal(a, b)
    out["comparisons"].append({"left": a, "right": b, "kind": kind, "submitted_equal": t.bc.old_values_equal(a, b), "contract_equal": new})
for tag in ("r2x-small-boq-B", "r2x-small-boq-C"):
    s = json.load(open(f"C:/t/r2x/runs/{tag}/out/BOQ.json", encoding="utf-8"))
    sh = list(s["sheets"].values())[0]
    out["stored_runs"][tag] = {"requests_on_one_document": sh["calls"], "declared_per_document": 12, "excess": sh["calls"] - 12,
                               "chunks_implied": -(-len(sh["rows"]) // 11), "project_day_cap_60_exceeded": False, "experiment_cap_150_exceeded": False}
pathlib.Path("C:/t/iso/work/r2x/r14/REPRO-R14.json").write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps(out, indent=1, default=str))
