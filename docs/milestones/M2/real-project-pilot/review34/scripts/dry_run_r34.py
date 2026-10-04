"""ORCH-05C (after make_binding_r34.py): the dry run. NO model request, no provider, no prediction, no ledger scope, no
authorization file. Usage: dry_run_r34.py <stamp> <binding manifest> <binding sha256>
Writes PILOT/review34/dry-run/:
  INGEST-72.json            sandbox ingestion of all 72 staged files (registration only; the unchanged sandbox_ingest_r32 under
                            the r34 sandbox base) + state check
  runner/                   the TWO-INVOCATION DRILL of runner_r32 --mode dry over RUN-SET-PROPOSAL.json (reader 'none'):
                              inv-1  'run' with a dry fault: lane C dies right after its 5th dispatch was sent (row reserved,
                                     charge recorded) -- as a crash would leave it
                              ---    a second 'run' of the same stamp: refused
                              inv-2  'resume' (same stamp): nothing re-sent, the reserved request served once as
                                     interrupted_charged, the same allowance (no fresh caps), the run completes
                              ---    a further 'resume' and a further 'run': refused
                            RUN-STATE.json (copied from the run folder) and DRILL.json (the checks)
  GUARD-CHECK.json          the dispatch guard's refusals; no authorization file anywhere; no --auth-path
  SCORER-SCENARIOS.json     score_bcr_r32 + concentration_r32 v2 on Review 34's scenario structures over the real truth and run
                            set with SYNTHETIC lanes made from the truth (not predictions), and the EP-27331 gain-size sweep
  DRY-RUN-REPORT.json       everything above with the AI ledger counts before and after"""
import datetime
import hashlib
import json
import pathlib
import shutil
import sqlite3
import subprocess
import sys

R34 = pathlib.Path("C:/t/iso/work/r2x/r34")
sys.path.insert(0, str(R34 / "harness-r32"))
import allowance_r32 as AL  # noqa: E402
import concentration_r32 as K  # noqa: E402
import converter_r32 as CV  # noqa: E402
import dispatch_guard_r32 as DG  # noqa: E402
import inputs_r32 as I  # noqa: E402
import labels_adapter_r32 as A  # noqa: E402
import preflight_r32 as PF  # noqa: E402
import r34_scenarios as SC  # noqa: E402
import run_set_selector_r32 as RS  # noqa: E402
import runner_r32 as RN  # noqa: E402
import sandbox_ingest_r32 as SI  # noqa: E402
import score_bcr_r32 as S  # noqa: E402

PKG = I.PILOT / "review34"
DRY = PKG / "dry-run"
PY = SI.PY
FAULT_AFTER = 5


def ledger():
    c = PF.ledger_counts(I.AI_LEDGER)
    return c


def text(obj):
    return json.dumps(obj, sort_keys=True, indent=1, default=str, ensure_ascii=False) + "\n"


def write(obj, path):
    t = text(obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(t)
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


SCRATCH = pathlib.Path("C:/Users/moham/AppData/Local/Temp/claude/C--Users-moham-Desktop-dev-dev/453468dd-6650-45fd-93b4-4712a8308d22/scratchpad/r34harness")
AUTH_KEYS = {"declaration_sha256", "owner_token_sha256", "nonce", "authorized_by"}


def authorization_files():
    """(1) any file named like an owner dispatch authorization under PILOT, the work folders, the r34 sandbox and the
    scratchpad; (2) any JSON object with the keys of an authorization under every folder this task writes to."""
    named = sorted(str(p) for r in (I.PILOT, pathlib.Path("C:/t/iso/work/r2x"), PF.SANDBOX_BASE, SCRATCH) if r.exists()
                   for p in r.rglob("*DISPATCH-AUTHORIZATION*"))
    like = []
    for r in (PKG, R34, PF.SANDBOX_BASE, SCRATCH):
        for p in (r.rglob("*.json") if r.exists() else []):
            try:
                if p.stat().st_size > 1_000_000:
                    continue
                obj = json.loads(p.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            if isinstance(obj, dict) and AUTH_KEYS <= set(obj):
                like.append(str(p))
    return sorted(set(named) | set(like))


def preexisting_named_authorization_files():
    """Files whose NAME contains AUTHORIZATION under PILOT that existed before this task (reported, not dispatch authorizations)."""
    return {str(p.relative_to(I.PILOT)): datetime.datetime.fromtimestamp(p.stat().st_mtime, datetime.timezone.utc).isoformat(timespec="seconds")
            for p in I.PILOT.rglob("*AUTHORIZATION*") if p.is_file() and "DISPATCH-AUTHORIZATION" not in p.name}


def guard_check(binding, binding_sha):
    pinned = DG.pinned_path(PKG / "DECLARATION.json")
    out = {"pinned_authorization_path_for_a_declaration_at_the_review34_root": pinned.as_posix(), "exists": pinned.exists(),
           "check_without_declaration": DG.check(None, None), "check_with_a_made_up_declaration_hash": DG.check(PKG / "DECLARATION.json", "0" * 64),
           "authorization_files_found": authorization_files(),
           "preexisting_files_with_authorization_in_the_name": preexisting_named_authorization_files(),
           "preexisting_note": "earlier packages' files (written before this task) whose name contains AUTHORIZATION; none is an owner dispatch authorization"}
    r = subprocess.run([PY, str(R34 / "harness-r32" / "runner_r32.py"), "run", "--mode", "live", "--run-set", str(PKG / "RUN-SET-PROPOSAL.json"),
                        "--binding", str(binding), "--binding-sha", binding_sha, "--auth-path", str(PKG / "x.json")],
                       capture_output=True, text=True, env={"PYTHONDONTWRITEBYTECODE": "1", "SYSTEMROOT": "C:/Windows", "PATH": "C:/Windows/system32"})
    out["runner_auth_path_argument"] = {"returncode": r.returncode, "stderr_tail": r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ""}

    class Resp:
        def __init__(self, data=None, model="", error=None, error_detail=None, **kw):
            self.error = error

    def must_not_build():
        raise AssertionError("built")

    g = DG.GuardedProvider(must_not_build, PKG / "DECLARATION.json", "0" * 64, Resp, run_folder=PF.SANDBOX_BASE / "no-run", invocation=1)
    out["guarded_provider"] = {"response": g.complete(object()).error, "built": g.inner is not None}
    out["ok"] = (not out["exists"] and not out["check_without_declaration"]["authorized"] and not out["check_with_a_made_up_declaration_hash"]["authorized"]
                 and out["authorization_files_found"] == [] and out["runner_auth_path_argument"]["returncode"] == 2
                 and "unrecognized arguments: --auth-path" in out["runner_auth_path_argument"]["stderr_tail"]
                 and out["guarded_provider"] == {"response": "dispatch_refused", "built": False})
    return out


def drill(stamp, binding, binding_sha):
    rs = PKG / "RUN-SET-PROPOSAL.json"
    base = ["--mode", "dry", "--stamp", stamp, "--run-set", str(rs), "--binding", str(binding), "--binding-sha", binding_sha]
    rout = DRY / "runner"
    if rout.exists():
        raise SystemExit("dry-run/runner exists: a dry run never reuses its folders")
    rout.mkdir(parents=True)
    folder = PF.run_folder_of(stamp)
    steps = []

    def step(name, argv, expect):
        t0 = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        try:
            rc = RN.main(argv)
            res = {"returncode": rc}
        except RN.Refused as exc:
            res = {"refused": str(exc)}
        except RuntimeError as exc:
            res = {"error": str(exc)}
        res |= {"step": name, "argv": argv, "started_utc": t0, "expected": expect}
        res["as_expected"] = (expect in res) if expect in ("refused", "error") else res.get("returncode") == 0
        steps.append(res)
        return res

    step("1 run (fresh) with a dry fault: lane C dies after its 5th dispatch was sent", ["run", *base, "--out", str(rout / "inv-1"), "--dry-fault", f"C:{FAULT_AFTER}"], "error")
    st1 = json.loads((folder / "RUN-STATE.json").read_text(encoding="utf-8"))
    con = sqlite3.connect(f"file:{(folder / 'capture.sqlite').as_posix()}?mode=ro", uri=True)
    after1 = {"rows_by_lane_state": [list(r) for r in con.execute("select lane, state, count(*) from requests group by lane, state order by lane, state")],
              "reserved_seq": [r[0] for r in con.execute("select seq from requests where state = 'reserved'")]}
    con.close()
    a1 = AL.LaneAllowance(folder / "allowance.sqlite", RN.CAPS, 60, run_key=st1["run_key"], create=False)
    after1["allowance_used"] = {lane: a1.used(lane) for lane in ("B", "C", "R", "P")}
    step("2 run (fresh) again, same stamp", ["run", *base, "--out", str(rout / "refused-run-2")], "refused")
    step("3 resume (same stamp)", ["resume", *base, "--out", str(rout / "inv-2")], "returncode")
    step("4 resume again", ["resume", *base, "--out", str(rout / "refused-resume-3")], "refused")
    step("5 run (fresh) again", ["run", *base, "--out", str(rout / "refused-run-4")], "refused")
    shutil.copyfile(folder / "RUN-STATE.json", rout / "RUN-STATE.json")
    rep2 = json.loads((rout / "inv-2" / "RUN-REPORT.json").read_text(encoding="utf-8"))
    con = sqlite3.connect(f"file:{(folder / 'capture.sqlite').as_posix()}?mode=ro", uri=True)
    reserved_after = [r[0] for r in con.execute("select seq from requests where state = 'reserved'")]
    rows_total = con.execute("select count(*) from requests").fetchone()[0]
    dup = con.execute("select count(*) from (select bound_key from requests group by bound_key having count(*) > 1)").fetchone()[0]
    con.close()
    l2 = rep2["lanes"]
    n_docs = rep2["run_set"]["documents"]
    stub_total = {"inv-1 (B complete, C crashed)": {"B": n_docs, "C": FAULT_AFTER}, "inv-2": {k: v.get("dry_stub_calls") for k, v in l2.items()}}
    checks = {
        "inv1_interrupted": [i["status"] for i in st1["invocations"]] == ["interrupted"],
        "inv1_one_reserved_row_in_C": len(after1["reserved_seq"]) == 1,
        "second_fresh_run_refused": "refused" in steps[1] and "second fresh invocation" in steps[1]["refused"],
        "resume_completed": steps[2].get("returncode") == 0 and rep2["status"] == "finished" and rep2["kind"] == "resume" and rep2["invocation"] == 2,
        "resume_B_sent_nothing": l2["B"]["dry_stub_calls"] == 0 and l2["B"]["serves_by_mode"] == {"same_bound_fingerprint": n_docs},
        "resume_C_sent_only_new_requests": l2["C"]["dry_stub_calls"] == n_docs - FAULT_AFTER and l2["C"]["serves_by_mode"] == {"same_bound_fingerprint": FAULT_AFTER},
        "reserved_served_once_as_interrupted_charged": l2["C"]["stats"].get("interrupted_charged") == 1,
        "reserved_row_never_resent": reserved_after == after1["reserved_seq"],
        "no_duplicate_bound_key": dup == 0,
        "no_fresh_caps": rep2["allowance"]["caps_fixed"] == RN.CAPS,
        "charges_equal_first_dispatches": rep2["allowance"]["used"]["C"] == n_docs and rep2["allowance"]["used"]["B"] == n_docs
        and rep2["allowance"]["used_total"] == rows_total,
        "further_resume_refused": "refused" in steps[3] and "complete" in steps[3]["refused"],
        "further_run_refused": "refused" in steps[4] and "second fresh invocation" in steps[4]["refused"],
        "ledger_unchanged_each_invocation": rep2["ledger_unchanged"] and json.loads((rout / "inv-1" / "RUN-REPORT.json").read_text(encoding="utf-8"))["ledger_unchanged"],
        "model_requests_0": rep2["model_requests"] == 0,
    }
    out = {"stamp": stamp, "run_folder": folder.as_posix(), "fault": {"lane": "C", "after_dispatches": FAULT_AFTER}, "steps": steps,
           "after_invocation_1": after1, "after_invocation_2": {"reserved_seq": reserved_after, "rows": rows_total, "allowance": rep2["allowance"],
                                                                 "store": rep2["store"], "lanes": {k: {x: v.get(x) for x in ("dry_stub_calls", "serves_by_mode", "stats", "allowance_used")} for k, v in l2.items()}},
           "dry_stub_calls": stub_total, "checks": checks, "passes": all(checks.values()) and all(s["as_expected"] for s in steps),
           "note": "dry stub calls are not provider or model requests: no provider exists in dry mode (DryRefusingProvider)"}
    write(out, rout / "DRILL.json")
    return out, rep2


def scenarios():
    T, run = SC.load()
    out = {}
    for name, (B, C, R, stop, note) in SC.build(T, run).items():
        res = S.evaluate(B, C, R, T, caps={"B": 240, "C": 240}, extensions_used=0, stop_state=stop, docs=set(run))
        out[name] = {"note": note} | SC.summarise(res)
    _, has, by_proj = SC.groups(T, run)
    sweep = {}
    for k in range(1, len(by_proj["EP-27331"]) + 1):
        g = {(p, "decision") for p in by_proj["EP-27331"][:k]}
        res = S.evaluate(SC.lane(T, run, "B", miss=g, own=100), SC.lane(T, run, "C", own=20, inherited=100), None, T, caps={"B": 240, "C": 240},
                         extensions_used=0, docs=set(run))
        c = res["concentration"]["fields"]["decision"]
        sweep[str(k)] = {"documents": by_proj["EP-27331"][:k], "net_gain": c["net_gain"], "concentration": c["outcome"], "candidate": res["outcome"],
                         "request_gate_passes": res["request_gate"]["passes"], "paired_ci95": res["paired"]["decision"]["paired_difference"]["ci95"]}
    return {"note": "SYNTHETIC lane results built from the frozen truth itself (correct values copied from it, wrong values invented); no "
                    "application reader, no model, no prediction; Review 34's scenario structures (section 6) on the corrected scorer; "
                    "these exercise score_bcr_r32 and concentration_r32 v2 and are NOT results",
            "rule_version": K.RULE_VERSION, "run_set": run, "scenarios": out,
            "ep27331_decision_gain_sweep": sweep, "reference_set_statement": I.REFERENCE_SET_STATEMENT}


def main(stamp, binding, binding_sha):
    report = {"stamp": stamp, "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              "ledger_before": ledger(), "model_requests": 0, "provider_calls": 0}
    pre = subprocess.run([PY, str(R34 / "preflight_inputs.py")], capture_output=True, text=True)
    report["preflight_inputs"] = pre.stdout.strip().splitlines()[-1]
    assert report["preflight_inputs"] == "PACKET OK", pre.stdout[-2000:]
    x = I.load_all()
    truth = A.build_truth(x["reviewed2"], renders=x["renders"], source_manifest=x["source_manifest"], selection=x["selection"], verification=x["verification"])
    report["truth_sha256"] = hashlib.sha256(PF.truth_text(truth).encode("utf-8")).hexdigest()
    assert report["truth_sha256"] == I.sha256_file(DRY / "TRUTH-R32.json") == "4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064"
    report["population"] = {f: len(v) for f, v in A.population(truth).items()}
    prop = json.loads((PKG / "RUN-SET-PROPOSAL.json").read_text(encoding="utf-8"))
    assert json.dumps(RS.build_proposal(truth, inputs=prop["inputs"]), sort_keys=True) == json.dumps(prop, sort_keys=True), "the selector is not deterministic"
    ev = CV.convert(truth)
    assert hashlib.sha256(text(ev).encode("utf-8")).hexdigest() == I.sha256_file(PKG / "LABELS-R32-EVAL-INPUT.json"), "the converter output differs"
    report["carried_reproduced"] = {"TRUTH-R32.json": True, "RUN-SET-PROPOSAL.json": True, "LABELS-R32-EVAL-INPUT.json": True}
    report["run_set"] = {"sha256": I.sha256_file(PKG / "RUN-SET-PROPOSAL.json"), "count": prop["count"], "by_reason": prop["by_reason"],
                         "shortfalls": prop["shortfalls"], "projection": {f: v["documents"] for f, v in prop["per_field_matched_projection"].items()}}
    ing = SI.ingest(PF.SANDBOX_BASE / f"{stamp}-all72", sorted(truth["documents"]), truth)
    write(ing, DRY / "INGEST-72.json")
    report["ingest_72"] = {k: ing[k] for k in ("ok", "root", "documents", "projects", "registration", "state_check", "b_database_sha256", "model_requests", "processing_run")}
    guard = guard_check(binding, binding_sha)
    write(guard, DRY / "GUARD-CHECK.json")
    report["guard"] = guard
    d, rep2 = drill(stamp, binding, binding_sha)
    report["drill"] = {"passes": d["passes"], "checks": d["checks"], "steps": [{k: s.get(k) for k in ("step", "returncode", "refused", "error", "as_expected")} for s in d["steps"]]}
    report["runner_invocation_2"] = {k: rep2.get(k) for k in ("binding", "dispatch_guard", "population_gate", "run_set", "ingest", "b_database_sha256_final", "state_check_C",
                                                              "state_check_R", "store", "allowance", "stop_controller", "lanes", "model_requests", "ledger_before",
                                                              "ledger_after", "ledger_unchanged", "candidate_outcome", "score_outcome_by_field", "comparison_state",
                                                              "concentration_outcome_by_field", "run_key", "run_folder", "kind", "invocation")}
    sc = scenarios()
    report["scenarios_sha256"] = write(sc, DRY / "SCORER-SCENARIOS.json")
    report["scenario_outcomes"] = {k: {"candidate": v["outcome"], "fields": v["outcome_by_field"], "concentration": {f: c["outcome"] for f, c in v["concentration"].items()}}
                                   for k, v in sc["scenarios"].items()}
    report["ep27331_decision_gain_sweep"] = {k: (v["net_gain"], v["concentration"], v["candidate"]) for k, v in sc["ep27331_decision_gain_sweep"].items()}
    report["authorization_files_found"] = authorization_files()
    report["ledger_after"] = ledger()
    report["ledger_unchanged"] = report["ledger_after"] == report["ledger_before"]
    report["model_requests"] = rep2.get("model_requests", 0)
    report["dry_stub_calls_note"] = "every request of the dry run ended at DryRefusingProvider ('dry_refused'); no provider exists in dry mode"
    report["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    report["reference_set_statement"] = I.REFERENCE_SET_STATEMENT
    write(report, DRY / "DRY-RUN-REPORT.json")
    assert report["ledger_unchanged"] and report["model_requests"] == 0 and d["passes"] and guard["ok"] and report["authorization_files_found"] == []
    print(json.dumps({k: report[k] for k in ("ledger_before", "ledger_after", "model_requests", "population", "run_set", "drill", "scenario_outcomes",
                                             "ep27331_decision_gain_sweep")}, indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
