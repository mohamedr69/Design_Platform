"""R14-02 replay: every STORED small-batch BOQ verification result (r2x-small-boq-B / -C, read only; no model call) is
re-joined to truth and re-scored under the typed contract (boq_contract.py), against two truth versions kept apart:
  * original : review05/holdout/HOLDOUT-BOQ-LABELS.json (Review 05 AI-drafted labels, unchanged);
  * amended  : labels/r14/BOQ-LABELS.amended-r14.1.json (the same rows plus the AI source review's H-06 rulings).
Per row: the submitted outcome / truth / blind-right beside the corrected ones, including unchanged rows.

Every stored run is marked as obtained with the per-document budget deviation (R14-01). A TRUNCATION VIEW (not a run,
a counterfactual on the stored order of requests) shows which rows fell within the first 12 requests the declared
per-document limit would have allowed; everything after is 'would have been budget-refused'.

Also reported: where the frozen BOQ evaluator's own pairing (holdout-A-r12.json, evaluator .3, unchanged) and the
contract join assign different truth to the same emitted row."""
import collections
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, "C:/t/iso/frozen-r12/backend")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import boq_contract as bc  # noqa: E402

W = pathlib.Path("C:/t/iso/work/r2x")
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
KEY = "EP-8430/EP-8430 Commercial/EP-8430 PAVA Revised Design Sheet - 23.10.2017.pdf"
SHA = "719f8714d2a75673c8ba390a884a2d2889b2438fd587eaa2c42f62d75f344fec"
LIMIT = 12
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

extraction = [v for k, v in json.load(open(W / "boq/holdout-A-r12-extraction.json", encoding="utf-8")).items() if k.replace("\\", "/") == KEY][0]
emitted = []
for i, l in enumerate(extraction["lines"]):
    emitted.append({"id": f"L{i}", "page": l["page"], "y": l["y_px"], "part_number": l.get("catalog_no"), "quantity": l.get("quantity"),
                    "description": l.get("description"), "accepted": True, "bounds": None})
for i, s in enumerate(extraction["issues"]):
    if str(s.get("target") or "").startswith("boq_line:"):
        d = s["detail"]
        emitted.append({"id": f"I{i}", "page": s["page"], "y": (s["region"][1] + s["region"][3]) / 2, "part_number": d.get("catalog_no"),
                        "quantity": d.get("quantity"), "description": d.get("description"), "accepted": False, "bounds": [s["region"][1], s["region"][3]]})
by_id = {e["id"]: e for e in emitted}


def truth_rows(version: str) -> tuple[list, str]:
    if version == "original":
        f = PILOT / "review05/holdout/HOLDOUT-BOQ-LABELS.json"
        sheets = json.loads(f.read_text(encoding="utf-8"))["boq_design_sheets"]["sheets"]
    else:
        f = W / "labels/r14/BOQ-LABELS.amended-r14.1.json"
        sheets = json.loads(f.read_text(encoding="utf-8"))["sheets"]
    s = [x for x in sheets if x["ep"] == "8430"][0]
    rows = [dict(r, ordinal=i) for i, r in enumerate(s["rows"]) if r.get("kind") == "line"]
    return rows, sha(f)


def emitted_id(r: dict) -> str | None:
    row = r["row"]
    cands = [e for e in emitted if e["page"] == r["page"] and ((row.get("y_px") is not None and e["accepted"] and e["y"] == row["y_px"])
                                                              or (row.get("row_bounds") and not e["accepted"] and e["bounds"] == list(row["row_bounds"])))]
    return cands[0]["id"] if len(cands) == 1 else None


def classify(r, truth, join_state, reader_right, blind_right):
    if join_state == "ambiguous":
        return "held_ambiguous_join"
    if truth is None:
        return "extra_row"
    if r.get("accepted_by_reader") and reader_right is False:
        return {"conflict": "caught_wrong_accepted", "validated": "missed_wrong_accepted"}.get(r.get("state"), "wrong_accepted_unverified")
    if r.get("accepted_by_reader"):
        return {"validated": "confirmed_correct", "conflict": "questioned_correct"}.get(r.get("state"), "correct_unverified")
    return "held_blind_right" if blind_right else "held_blind_wrong" if blind_right is False else "held_unread"


frozen_pairs = [p for s in json.load(open(W / "boq/holdout-A-r12.json", encoding="utf-8"))["sheets"] if s["ep"] == "8430" for p in s["pairs"]]
out = {"contract": bc.CONTRACT_VERSION, "sheet": KEY, "sha256": SHA, "runs": {}}
for version in ("original", "amended"):
    truth, truth_sha = truth_rows(version)
    j = bc.join_rows(emitted, truth)
    t_by = {t["ordinal"]: t for t in truth}
    pair_of = {e: (t, st) for e, t, st in j["pairs"]}
    out.setdefault("joins", {})[version] = {"truth_sha256": truth_sha, "pairs": len(j["pairs"]), "ambiguous": sum(1 for p in j["pairs"] if p[2] == "ambiguous"),
                                           "unmatched_emitted": j["unmatched_emitted"], "unmatched_truth": j["unmatched_truth"]}
    for tag in ("r2x-small-boq-B", "r2x-small-boq-C"):
        f = pathlib.Path(f"C:/t/r2x/runs/{tag}/out/BOQ.json")
        stored = json.loads(f.read_text(encoding="utf-8"))
        sheet = stored["sheets"][[k for k in stored["sheets"]][0]]
        rows = []
        for n, r in enumerate(sheet["rows"]):
            eid = emitted_id(r)
            t_ord, st = pair_of.get(eid, (None, None))
            truth_row = t_by.get(t_ord)
            e = by_id.get(eid) or {}
            reader_right = (bc.parts_equal(e.get("part_number"), truth_row.get("part_number")) and bc.quantities_equal(e.get("quantity"), truth_row.get("quantity"))) if truth_row else None
            blind = r.get("blind") or {}
            blind_right = (bc.parts_equal(blind.get("part_number"), truth_row.get("part_number")) and bc.quantities_equal(blind.get("quantity"), truth_row.get("quantity"))) \
                if (truth_row and blind) else None
            new = classify(r, truth_row, st, reader_right, blind_right)
            request_no = n + 1        # the stored rows are in request order (one request per row; the budget-refused rows had none)
            made_request = not (r.get("reasons") == ["no reading"] and r.get("state") == "unverified")
            frozen = [p for p in frozen_pairs if p.get("emitted") and bc.parts_equal(p["emitted"].get("part_number"), e.get("part_number"))
                      and bc.quantities_equal(p["emitted"].get("quantity"), e.get("quantity")) and bool(p["emitted"].get("accepted")) == e.get("accepted")]
            rows.append({"request_order": request_no, "made_request": made_request, "emitted_id": eid, "y": e.get("y"), "accepted_by_reader": r.get("accepted_by_reader"),
                         "emitted": {"part_number": e.get("part_number"), "quantity": e.get("quantity"), "description": e.get("description")},
                         "blind": blind or None, "verifier_state": r.get("state"),
                         "before": {"truth": r.get("truth"), "blind_right": r.get("blind_right"), "outcome": r.get("outcome")},
                         "after": {"truth_ordinal": t_ord, "join": st, "truth": {k: truth_row.get(k) for k in ("part_number", "quantity", "description")} if truth_row else None,
                                   "reader_right": reader_right, "blind_right": blind_right, "outcome": new},
                         "changed": {"truth": (r.get("truth") or {}).get("quantity") != (truth_row or {}).get("quantity") or
                                     (r.get("truth") or {}).get("part_number") != (truth_row or {}).get("part_number"),
                                     "outcome": r.get("outcome") != new, "blind_right": r.get("blind_right") != blind_right},
                         "frozen_evaluator_pair_truth_differs": bool(frozen) and truth_row is not None and len(frozen) == 1 and
                         not (bc.parts_equal(frozen[0]["truth"].get("part_number"), truth_row.get("part_number")) and bc.quantities_equal(frozen[0]["truth"].get("quantity"), truth_row.get("quantity"))),
                         "within_declared_12": request_no <= LIMIT})
        before = collections.Counter(r["before"]["outcome"] for r in rows)
        after = collections.Counter(r["after"]["outcome"] for r in rows)
        trunc = collections.Counter(r["after"]["outcome"] if r["within_declared_12"] else "would_have_been_budget_refused" for r in rows)
        out["runs"][f"{tag}|{version}"] = {
            "stored_run": str(f), "stored_run_sha256": sha(f), "truth_version": version,
            "budget_deviation": f"OBTAINED WITH THE PER-DOCUMENT BUDGET DEVIATION (R14-01): {sheet['calls']} requests on one document against the declared 12; "
                                "each chunk had its own 12-call budget",
            "requests_made": sheet["calls"], "before": dict(before), "after": dict(after),
            "rows_changed_outcome": sum(r["changed"]["outcome"] for r in rows), "rows_changed_truth": sum(r["changed"]["truth"] for r in rows),
            "rows_changed_blind_right": sum(r["changed"]["blind_right"] for r in rows),
            "truncation_view_first_12_requests": {"note": "counterfactual on the stored request order, not a run", **dict(trunc)},
            "rows": rows}
p = W / "r14/REPLAY-BOQ.json"
p.write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
for k, v in out["runs"].items():
    print(k, "| before", v["before"], "| after", v["after"], "| changed outcome", v["rows_changed_outcome"], "truth", v["rows_changed_truth"],
          "blind", v["rows_changed_blind_right"], "| first-12 view", v["truncation_view_first_12_requests"])
print("joins", {k: {kk: vv for kk, vv in v.items() if kk != "truth_sha256"} for k, v in out["joins"].items()})
