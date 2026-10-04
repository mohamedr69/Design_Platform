"""ORCH-05.1 step 3 (after prepare_r33.py and make_binding_r33.py): the dry run. NO model request, no provider, no
prediction, no ledger scope. Usage: dry_run_r33.py <stamp> <binding manifest> <binding sha256>
Writes PILOT/review33/dry-run/:
  INGEST-72.json            sandbox ingestion of all 72 staged files (registration only) + state check
  runner/                   runner_r32 --mode dry over RUN-SET-PROPOSAL.json (reader 'none') with the resume drill
  SCORER-SCENARIOS.json     score_bcr_r32 + concentration_r32 on SYNTHETIC lane results built from the truth (not predictions)
  GUARD-CHECK.json          the dispatch guard's refusal and the absence of the owner's authorization file
  DRY-RUN-REPORT.json       everything above with the AI ledger counts before and after"""
import copy
import datetime
import hashlib
import json
import pathlib
import shutil
import sqlite3
import subprocess
import sys

R33 = pathlib.Path("C:/t/iso/work/r2x/r33")
sys.path.insert(0, str(R33 / "harness-r32"))
import concentration_r32 as K  # noqa: E402
import dispatch_guard_r32 as DG  # noqa: E402
import inputs_r32 as I  # noqa: E402
import labels_adapter_r32 as A  # noqa: E402
import run_set_selector_r32 as RS  # noqa: E402
import runner_r32 as RN  # noqa: E402
import sandbox_ingest_r32 as SI  # noqa: E402
import score_bcr_r32 as S  # noqa: E402

PKG = I.PILOT / "review33"
DRY = PKG / "dry-run"
PY = SI.PY


def ledger():
    con = sqlite3.connect(f"file:{I.AI_LEDGER}?mode=ro", uri=True)
    try:
        return {"entries": con.execute("select count(*) from entries").fetchone()[0], "scopes": con.execute("select count(*) from scopes").fetchone()[0],
                "limit_amendments": con.execute("select count(*) from limit_amendments").fetchone()[0],
                "scope_names_sha256": hashlib.sha256("|".join(r[0] for r in con.execute("select scope from scopes order by scope")).encode()).hexdigest()}
    finally:
        con.close()


def write(obj, path):
    text = json.dumps(obj, sort_keys=True, indent=1, default=str, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---- synthetic lane results over the real truth (values copied from the truth or deliberately wrong; no reader) ---------
WORD = {"approved": "approved", "approved as noted": "ANN", "revise and resubmit": "rejected", "rejected": "rejected"}


def lane(name, truth, docs, *, correct=lambda r: False, extra=None, own=0, inherited=0):
    out = {}
    for pid in docs:
        facts, cov = [], {}
        for r in A.doc_rows(truth, pid):
            if r["truth_kind"] == "value" and correct(r):
                facts.append({"page": r["page"], "field": r["field"], "value": WORD[r["class"]] if r["field"] == "decision" else r["literal"], "state": "accepted"})
                if r["field"] == "decision":
                    cov.setdefault(r["page"], {})["decision"] = "completed_read"
            elif r["field"] == "decision" and r["truth_kind"] == "absent" and correct(r):
                cov.setdefault(r["page"], {})["decision"] = "discovery_absent"
        facts += (extra or {}).get(pid, [])
        out[pid] = {"attempted": True, "unsupported": False, "facts": facts, "coverage": cov}
    return {"lane": name, "documents": out, "requests": {"own_dispatched": own, "inherited_from_b": inherited}, "synthetic": True}


def scenarios(truth, docs):
    ids = sorted(docs)
    B = lane("B", truth, ids, own=24)
    allc = lambda r: True  # noqa: E731
    sc = {}
    C1 = lane("C", truth, ids, correct=allc, own=100, inherited=24)
    sc["S1 uniform gain (C clean on every scorable value row)"] = (B, C1, None)
    only = {p for p in ids if truth["documents"][p]["project"] == "EP-27331"} | set(ids[:2])
    sc["S2 gain concentrated in EP-27331"] = (B, lane("C", truth, ids, correct=lambda r: r["pool_id"] in only, own=100, inherited=24), None)
    wrong_rev = [r for r in truth["rows"].values() if r["pool_id"] in docs and r["field"] == "revision" and r["truth_kind"] == "value"][0]
    C3 = lane("C", truth, ids, correct=lambda r: not (r is wrong_rev), own=100, inherited=24,
              extra={wrong_rev["pool_id"]: [{"page": wrong_rev["page"], "field": "revision", "value": "99", "state": "accepted"}]})
    sc[f"S3 one wrong revision acceptance in C ({wrong_rev['pool_id']} p{wrong_rev['page']})"] = (B, C3, None)
    neg = [p for p in ids if truth["documents"][p]["decision_control"] == "negative"][0]
    C4 = lane("C", truth, ids, correct=allc, own=100, inherited=24, extra={neg: [{"page": "1", "field": "decision", "value": "approved", "state": "accepted"}]})
    sc[f"S4 a decision false acceptance on negative control {neg}"] = (B, C4, None)
    ns = [r for r in truth["rows"].values() if r["pool_id"] in docs and r["truth_kind"] == "not_scorable"]
    extra5 = {}
    for r in ns:
        extra5.setdefault(r["pool_id"], []).append({"page": r["page"], "field": r["field"], "value": "ZZ-NOT-A-CANDIDATE", "state": "accepted"})
    sc[f"S5 acceptances on every NOT_SCORABLE run-set row ({len(ns)} rows)"] = (B, lane("C", truth, ids, correct=allc, own=100, inherited=24, extra=extra5), None)
    dec3 = [p for p in ids if A.has_fact(truth, p, "decision")][:3]
    sc["S6 small decision gain (3 documents)"] = (B, lane("C", truth, ids, correct=lambda r: r["field"] != "decision" or r["pool_id"] in dec3, own=100, inherited=24), None)
    out = {}
    for name, (b, c, r) in sc.items():
        res = S.evaluate(b, c, r, truth, caps={"B": 240, "C": 240}, extensions_used=0, docs=set(ids))
        out[name] = {"outcome_by_field": res["outcome_by_field"],
                     "reasons": {f: v["reasons_not_eligible"] for f, v in res["fields"].items()},
                     "matched": {f: res["paired"][f]["matched"] for f in A.FIELDS},
                     "paired": {f: res["paired"][f]["paired_difference"] for f in A.FIELDS},
                     "request_gate": {k: res["request_gate"].get(k) for k in ("passes", "net_correct_facts", "extra_requests", "facts_per_8_extra")},
                     "critical_C": {"resolved": [(c["pool_id"], c["page"], c["field"]) for c in res["metrics"]["C"]["critical"]["resolved"]],
                                    "unresolved": len(res["metrics"]["C"]["critical"]["unresolved"])},
                     "concentration": {f: {"outcome": v["outcome"], "net_gain": v["net_gain"], "reasons": v["reasons"],
                                           "attribution_statement": v["attribution_statement"],
                                           "largest_shares": {g: (v["groupings"][g]["largest_gain_group"], v["groupings"][g]["largest_gain_share"])
                                                              for g in ("project", "contractor", "layout_key", "decision_type", "stratum")}}
                                       for f, v in res["concentration"]["fields"].items()},
                     "decision_controls": res["concentration"]["decision_controls"],
                     "default_selected": res["default_selected"]}
    return {"note": "SYNTHETIC lane results built from the frozen truth itself (correct values copied from it, wrong values invented); "
                    "no application reader, no model, no prediction; these exercise score_bcr_r32 and concentration_r32 on the real run-set "
                    "structure and are NOT results", "scenarios": out, "reference_set_statement": I.REFERENCE_SET_STATEMENT}


def main(stamp, binding, binding_sha):
    report = {"stamp": stamp, "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              "ledger_before": ledger(), "model_requests": 0, "provider_calls": 0}
    pre = subprocess.run([PY, str(R33 / "preflight_inputs.py")], capture_output=True, text=True)
    report["preflight_inputs"] = pre.stdout.strip().splitlines()[-1]
    assert report["preflight_inputs"] == "PACKET OK", pre.stdout[-2000:]
    x = I.load_all()
    truth = A.build_truth(x["reviewed2"], renders=x["renders"], source_manifest=x["source_manifest"], selection=x["selection"], verification=x["verification"])
    t_text = json.dumps(truth, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    report["truth_sha256"] = hashlib.sha256(t_text.encode("utf-8")).hexdigest()
    assert report["truth_sha256"] == I.sha256_file(DRY / "TRUTH-R32.json"), "the adapter is not deterministic"
    report["population"] = {f: len(v) for f, v in A.population(truth).items()}
    report["not_scorable"] = {k: v for k, v in A.not_scorable_summary(truth).items() if k != "rows_list"}
    prop = json.loads((PKG / "RUN-SET-PROPOSAL.json").read_text(encoding="utf-8"))
    again = RS.build_proposal(truth, inputs=prop["inputs"])
    assert json.dumps(again, sort_keys=True) == json.dumps(prop, sort_keys=True), "the selector is not deterministic"
    report["run_set"] = {"sha256": I.sha256_file(PKG / "RUN-SET-PROPOSAL.json"), "count": prop["count"], "by_reason": prop["by_reason"],
                         "shortfalls": prop["shortfalls"], "projection": {f: v["documents"] for f, v in prop["per_field_matched_projection"].items()}}
    # ---- deliverable 7: the 72 staged files registered without processing ---------------------------------------------
    ing = SI.ingest(SI.SANDBOX_BASE / f"{stamp}-all72", sorted(truth["documents"]), truth)
    write(ing, DRY / "INGEST-72.json")
    report["ingest_72"] = {k: ing[k] for k in ("ok", "documents", "projects", "registration", "state_check", "b_database_sha256", "model_requests", "processing_run")}
    # ---- the guard ------------------------------------------------------------------------------------------------------
    guard = {"authorization_file": str(DG.AUTH_PATH), "authorization_file_exists": DG.AUTH_PATH.exists(), "check_without_declaration": DG.check(None),
             "check_with_a_made_up_declaration_hash": DG.check("0" * 64)}
    write(guard, DRY / "GUARD-CHECK.json")
    report["guard"] = guard
    # ---- the runner, dry, over the proposal -----------------------------------------------------------------------------
    rout = DRY / "runner"
    if rout.exists():
        raise SystemExit("dry-run/runner exists: a dry run never reuses its folders")
    RN.main(["--mode", "dry", "--stamp", stamp, "--run-set", str(PKG / "RUN-SET-PROPOSAL.json"), "--binding", str(binding), "--binding-sha", binding_sha,
             "--out", str(rout), "--resume-drill"])
    rr = json.loads((rout / "RUN-REPORT.json").read_text(encoding="utf-8"))
    report["runner"] = {k: rr.get(k) for k in ("binding", "dispatch_guard", "population_gate", "run_set", "ingest", "b_database_sha256_final", "state_check_C",
                                                "state_check_R", "store", "resume_drill", "stop_controller", "lanes", "model_requests", "ledger_before",
                                                "ledger_after", "ledger_unchanged", "score_outcome_by_field", "comparison_state", "concentration_outcome_by_field")}
    # ---- the scorer and the concentration rule on synthetic results -----------------------------------------------------
    sc = scenarios(truth, {d["pool_id"] for d in prop["documents"]})
    report["scenarios_sha256"] = write(sc, DRY / "SCORER-SCENARIOS.json")
    report["scenario_outcomes"] = {k: {"fields": v["outcome_by_field"], "concentration": {f: c["outcome"] for f, c in v["concentration"].items()}}
                                   for k, v in sc["scenarios"].items()}
    report["ledger_after"] = ledger()
    report["ledger_unchanged"] = report["ledger_after"] == report["ledger_before"]
    report["model_requests"] = rr.get("model_requests", 0)
    report["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    report["reference_set_statement"] = I.REFERENCE_SET_STATEMENT
    write(report, DRY / "DRY-RUN-REPORT.json")
    assert report["ledger_unchanged"] and report["model_requests"] == 0
    print(json.dumps({k: report[k] for k in ("ledger_before", "ledger_after", "model_requests", "population", "run_set", "scenario_outcomes")}, indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
