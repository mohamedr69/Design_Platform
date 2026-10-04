"""Provider-failure boundary matrix (review 24, R24-01) through the ACTUAL runner (arm_ev.py v4.2) and the scripted
provider, in NEW isolated roots under C:/t/r2x/dry-runs/r24-boundary/<scenario>, built with the helper definitions of
lifecycle_probes.py (private synthetic A baseline, AGREEING synthetic labels -- no critical acceptance can fire -- and a
privately rebound declaration). No model request. Critical-stop boundaries are the existing lifecycle scenarios T1 / T5a /
T5b (rerun with v4.2 in the chain); they are reported separately and are not evidence for these.
  P1 provider stop, ordinary (persisted in-process)            -> resume: exit 4, zero sends, stop kept
  P2 provider stop, killed BEFORE the stop file (the finding)   -> resume: reconstructed from the journal, exit 4, zero sends
  P3 provider stop, killed AFTER the stop file                  -> resume: exit 4 on the file, zero sends
  P4 repeated resume of P2's recovered stop                     -> exit 4, zero sends; stop file, allowance charges, journal,
                                                                   manifest lists and io unchanged
  P5a two completed failures + one UNRESOLVED request (killed in flight) -> not terminal: resume continues and completes
  P5b failures with a success between them (F F ok F F ...)    -> no stop; a plain resume is ordinary (no reconstruction)
  P5c the breaker survives a restart: F F [unresolved] | resume, first resumed request F -> terminal in the resumed
      process, evidence spanning both processes; a further resume refuses
  P6a-d unusable persisted evidence after a P2-type stop: torn last record / journal deleted / journal bound to another
      run / a result without its attempt -> exit 5, zero sends, no stop fabricated, run record untouched
Writes boundary-evidence/BOUNDARY.json (+ per-scenario logs)."""
import hashlib
import json
import os
import pathlib
import sqlite3
import sys

HERE = pathlib.Path(__file__).resolve().parent
src = (HERE / "lifecycle_probes.py").read_text(encoding="utf-8")
g = {"__file__": str(HERE / "lifecycle_probes.py"), "__name__": "lifecycle_helpers"}
exec(compile(src[: src.index('R = {"lifecycle_contract"')], str(HERE / "lifecycle_probes.py"), "exec"), g)
g["ROOTS"] = pathlib.Path(os.environ.get("R24_BOUNDARY_ROOT", "C:/t/r2x/dry-runs/r25-boundary"))
make_root, run, snapshot, refusals = g["make_root"], g["run"], g["snapshot"], g["refusals"]
OUT = HERE.parent / "boundary-evidence"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() if pathlib.Path(p).exists() else None


def out(root):
    return root / "runs/L1/out"


def journal(root):
    f = out(root) / "PROVIDER-OUTCOMES.jsonl"
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()] if f.exists() else None


def jsummary(root):
    j = journal(root)
    if j is None:
        return None
    res = [r for r in j if r["type"] == "result"]
    att = {r["seq"] for r in j if r["type"] == "attempt"}
    return {"records": len(j), "results": [r["kind"] for r in res], "unresolved_seqs": sorted(att - {r["seq"] for r in res}), "pids": sorted({r["pid"] for r in j})}


def charges(root):
    con = sqlite3.connect(f"file:{(root / 'dry-allowance.sqlite').as_posix()}?mode=ro", uri=True)
    try:
        return {s[:8]: c for s, c in con.execute("select sha256, calls from allowance order by sha256")}
    finally:
        con.close()


def resumed_state(root):
    m = json.loads((out(root) / "RUN.json").read_text(encoding="utf-8"))
    return (m.get("resumes") or [{}])[-1]


def ledger_outcomes(root):
    con = sqlite3.connect(f"file:{(root / 'dry-ledger.sqlite').as_posix()}?mode=ro", uri=True)
    try:
        return [(s, o) for s, o in con.execute("select state, outcome from entries order by id")]
    finally:
        con.close()


R = {"lifecycle_contract": "runner-lifecycle-2026-10-01.v2", "scenarios": {}}
same = lambda a, b: a is not None and b is not None and all(a.get(k) == b.get(k) for k in ("kind", "reason", "evidence", "at_utc", "pid", "reconstructed"))

# P1 -------------------------------------------------------------------------------------------------------------------------
root, decl, dg = make_root("p1-provider-ordinary", set())
r0 = run(root, decl, dg, [], env={"PILOT_DRY_FAIL_FROM": "1"}, name="initial")
s0 = snapshot(root)
r1 = run(root, decl, dg, ["--resume"], name="resume")
s1 = snapshot(root)
R["scenarios"]["P1_provider_stop_ordinary"] = {"initial": {"run": r0, "status": s0["status"], "sends": s0["sends_total_recorded"], "stop_file": s0["stop_file"], "journal": jsummary(root)},
    "resume": {"run": r1, "status": s1["status"], "sends": s1["sends_total_recorded"]},
    "checks": {"stop_persisted_in_process": r0["exit"] == 0 and s0["status"] == "stopped" and s0["stop_file"]["kind"] == "provider_failures" and s0["stop_file"]["reconstructed"] is False,
               "resume_zero_sends_stop_kept": r1["exit"] == 4 and s1["sends_total_recorded"] == s0["sends_total_recorded"] and same(s1["stop_file"], s0["stop_file"]) and s1["status"] == "stopped"}}

# P2 / P4 ----------------------------------------------------------------------------------------------------------------------
root, decl, dg = make_root("p2-provider-kill-before-file", set())
r0 = run(root, decl, dg, [], env={"PILOT_DRY_FAIL_FROM": "1", "PILOT_DRY_KILL_AT_STOP": "before_file"}, name="initial-killed-before-file")
s0 = snapshot(root)
j0 = jsummary(root)
r1 = run(root, decl, dg, ["--resume"], name="resume-1")
s1 = snapshot(root)
state1 = {"stop": (out(root) / "TERMINAL-STOP.json").read_bytes(), "charges": charges(root), "journal": sha(out(root) / "PROVIDER-OUTCOMES.jsonl"), "io": sha(out(root) / "io.jsonl")}
r2 = run(root, decl, dg, ["--resume"], name="resume-2")
s2 = snapshot(root)
R["scenarios"]["P2_provider_stop_killed_before_file"] = {
    "initial": {"run": r0, "status": s0["status"], "sends": s0["sends_total_recorded"], "stop_file": s0["stop_file"], "manifest_stop": s0["stopped"], "journal": j0},
    "resume": {"run": r1, "status": s1["status"], "stopped": s1["stopped"], "sends": s1["sends_total_recorded"], "stop_file": s1["stop_file"], "not_attempted": s1["not_attempted"]},
    "ledger_outcomes_independent": ledger_outcomes(root),
    "checks": {"decided_not_persisted": r0["exit"] == 98 and s0["stop_file"] is None and s0["stopped"] is None and j0["results"] == ["failure"] * 3 and s0["sends_total_recorded"] == 3,
               "reconstructed_and_refused": r1["exit"] == 4 and s1["sends_total_recorded"] == 3 and s1["status"] == "stopped" and s1["stopped"] == "stop: three consecutive provider failures"
               and s1["stop_file"]["kind"] == "provider_failures" and s1["stop_file"]["reconstructed"] is True and [e["outcome"] for e in s1["stop_file"]["evidence"]] == ["transport"] * 3,
               "evidence_is_the_journalled_failures": [e["seq"] for e in s1["stop_file"]["evidence"]] == [r["seq"] for r in journal(root) if r["type"] == "result" and r["kind"] == "failure"],
               "ledger_corroborates": [o for st, o in ledger_outcomes(root) if st == "settled"] == ["transport"] * 3}}
R["scenarios"]["P4_repeated_resume_of_recovered_provider_stop"] = {
    "run": r2, "status": s2["status"], "sends": s2["sends_total_recorded"],
    "checks": {"zero_sends": r2["exit"] == 4 and s2["sends_total_recorded"] == 3,
               "stop_evidence_charges_journal_unchanged": (out(root) / "TERMINAL-STOP.json").read_bytes() == state1["stop"] and charges(root) == state1["charges"]
               and sha(out(root) / "PROVIDER-OUTCOMES.jsonl") == state1["journal"] and sha(out(root) / "io.jsonl") == state1["io"],
               "first_reason_kept": s2["stopped"] == s1["stopped"] and same(s2["stop_file"], s1["stop_file"]) and s2["projects"] == s1["projects"] and s2["not_attempted"] == s1["not_attempted"],
               "two_refusals": len([x for x in refusals(root) if x.get("resume") and "terminal stop preserved" in x["refused"]]) == 2}}

# P3 -------------------------------------------------------------------------------------------------------------------------
root, decl, dg = make_root("p3-provider-kill-after-file", set())
r0 = run(root, decl, dg, [], env={"PILOT_DRY_FAIL_FROM": "1", "PILOT_DRY_KILL_AT_STOP": "after_file"}, name="initial-killed-after-file")
s0 = snapshot(root)
r1 = run(root, decl, dg, ["--resume"], name="resume")
s1 = snapshot(root)
R["scenarios"]["P3_provider_stop_killed_after_file"] = {"initial": {"run": r0, "stop_file": s0["stop_file"], "manifest_stop": s0["stopped"]}, "resume": {"run": r1, "status": s1["status"], "sends": s1["sends_total_recorded"]},
    "checks": {"file_written_manifest_not": r0["exit"] == 98 and s0["stop_file"] is not None and s0["stopped"] is None,
               "refused_on_file": r1["exit"] == 4 and s1["sends_total_recorded"] == 3 and same(s1["stop_file"], s0["stop_file"]) and s1["status"] == "stopped" and s1["stop_file"]["reconstructed"] is False}}

# P5a ------------------------------------------------------------------------------------------------------------------------
root, decl, dg = make_root("p5a-two-failures-one-unresolved", set())
r0 = run(root, decl, dg, [], env={"PILOT_DRY_FAIL_FROM": "1", "PILOT_DRY_FAIL_COUNT": "2", "PILOT_DRY_KILL_AFTER": "3"}, name="initial-killed-in-flight")
j0 = jsummary(root)
c0 = charges(root)
r1 = run(root, decl, dg, ["--resume"], name="resume")
s1 = snapshot(root)
rs = resumed_state(root)
R["scenarios"]["P5a_two_failures_and_an_unresolved_request"] = {"initial": {"run": r0, "journal": j0, "charges": c0}, "resume": {"run": r1, "status": s1["status"], "stopped": s1["stopped"], "requests": s1["requests_this_invocation"],
    "provider_journal": rs.get("provider_journal"), "stop_file": s1["stop_file"], "charges": charges(root)},
    "checks": {"state_before_resume": r0["exit"] == 97 and j0["results"] == ["failure", "failure"] and len(j0["unresolved_seqs"]) == 1,
               "not_terminal_resume_completes": r1["exit"] == 0 and s1["status"] == "completed" and s1["stopped"] is None and s1["stop_file"] is None and sum(s1["requests_this_invocation"].values()) > 0,
               "streak_carried_as_two_unresolved_not_counted": rs.get("provider_journal", {}).get("streak") == 2 and len(rs.get("provider_journal", {}).get("unresolved") or []) == 1,
               "in_flight_request_stays_charged": all(charges(root)[k] >= v for k, v in c0.items())}}

# P5b ------------------------------------------------------------------------------------------------------------------------
root, decl, dg = make_root("p5b-success-between-failures", set())
r0 = run(root, decl, dg, [], env={"PILOT_DRY_FAIL_AT": "1,2,4,5"}, name="initial")
s0 = snapshot(root)
j0 = jsummary(root)
r1 = run(root, decl, dg, ["--resume"], name="resume")
s1 = snapshot(root)
rs = resumed_state(root)
R["scenarios"]["P5b_success_between_failures"] = {"initial": {"run": r0, "status": s0["status"], "journal": j0}, "resume": {"run": r1, "status": s1["status"], "provider_journal": rs.get("provider_journal"), "requests": s1["requests_this_invocation"]},
    "checks": {"no_stop_with_ok_between": r0["exit"] == 0 and s0["status"] == "completed" and s0["stop_file"] is None and j0["results"][:6] == ["failure", "failure", "ok", "failure", "failure", "ok"],
               "no_false_reconstruction_on_resume": r1["exit"] == 0 and s1["status"] == "completed" and s1["stop_file"] is None and rs.get("provider_journal", {}).get("streak") == 0
               and sum(s1["requests_this_invocation"].values()) == 0}}

# P5c ------------------------------------------------------------------------------------------------------------------------
root, decl, dg = make_root("p5c-breaker-survives-restart", set())
r0 = run(root, decl, dg, [], env={"PILOT_DRY_FAIL_AT": "1,2", "PILOT_DRY_KILL_AFTER": "3"}, name="initial-killed-in-flight")
j0 = jsummary(root)
r1 = run(root, decl, dg, ["--resume"], env={"PILOT_DRY_FAIL_AT": "1"}, name="resume-first-request-fails")
s1 = snapshot(root)
j1 = jsummary(root)
r2 = run(root, decl, dg, ["--resume"], name="resume-again")
s2 = snapshot(root)
R["scenarios"]["P5c_breaker_not_reset_by_restart"] = {"initial": {"run": r0, "journal": j0}, "resume": {"run": r1, "status": s1["status"], "stop_file": s1["stop_file"], "journal": j1}, "resume_again": {"run": r2, "status": s2["status"], "sends": s2["sends_total_recorded"]},
    "checks": {"two_failures_then_in_flight": r0["exit"] == 97 and j0["results"] == ["failure", "failure"] and len(j0["unresolved_seqs"]) == 1,
               "terminal_after_first_resumed_failure": s1["status"] == "stopped" and s1["stop_file"]["kind"] == "provider_failures" and s1["stop_file"]["reconstructed"] is False
               and len({e["pid"] for e in s1["stop_file"]["evidence"]}) == 2 and j1["results"] == ["failure", "failure", "failure"],
               "further_resume_refused": r2["exit"] == 4 and s2["sends_total_recorded"] == s1["sends_total_recorded"] and same(s2["stop_file"], s1["stop_file"])}}

# P6a-d ------------------------------------------------------------------------------------------------------------------------


def unusable(name, damage):
    root, decl, dg = make_root(name, set())
    r0 = run(root, decl, dg, [], env={"PILOT_DRY_FAIL_FROM": "1", "PILOT_DRY_KILL_AT_STOP": "before_file"}, name="initial-killed-before-file")
    jf = out(root) / "PROVIDER-OUTCOMES.jsonl"
    what = damage(jf)
    before = {"run_json": sha(out(root) / "RUN.json"), "io": sha(out(root) / "io.jsonl"), "charges": charges(root), "journal": sha(jf)}
    r1 = run(root, decl, dg, ["--resume"], name="resume")
    after = {"run_json": sha(out(root) / "RUN.json"), "io": sha(out(root) / "io.jsonl"), "charges": charges(root), "journal": sha(jf)}
    ref = [x for x in refusals(root) if x.get("resume")]
    return {"damage": what, "initial": r0, "resume": r1, "refusals": ref,
            "checks": {"refused_exit_5": r1["exit"] == 5 and bool(r1["printed"]) and r1["printed"].startswith("REFUSED (indeterminate"),
                       "zero_sends_nothing_changed": before == after, "no_stop_fabricated": not (out(root) / "TERMINAL-STOP.json").exists(),
                       "refusal_recorded_zero_requests": len(ref) == 1 and ref[0]["requests_sent"] == 0}}


def torn(jf):
    b = jf.read_bytes()
    jf.write_bytes(b[: len(b) - 20])
    return "the last record truncated by 20 bytes (torn write)"


def deleted(jf):
    jf.unlink()
    return "the journal deleted (requests and charges exist)"


def rebound(jf):
    lines = jf.read_text(encoding="utf-8").splitlines()
    h = json.loads(lines[0])
    h["binding"]["tag"] = "another-tag"
    lines[0] = json.dumps(h, sort_keys=True)
    jf.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "the header bound to another tag"


def orphan(jf):
    lines = jf.read_text(encoding="utf-8").splitlines()
    idx = next(i for i, l in enumerate(lines) if json.loads(l)["type"] == "attempt" and json.loads(l)["seq"] == 2)
    del lines[idx]
    jf.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "the attempt record of seq 2 removed (a result without its attempt)"


for key, name, fn in (("P6a_torn_record", "p6a-torn", torn), ("P6b_journal_missing", "p6b-missing", deleted), ("P6c_other_binding", "p6c-rebound", rebound), ("P6d_result_without_attempt", "p6d-orphan", orphan)):
    R["scenarios"][key] = unusable(name, fn)

OUT.mkdir(exist_ok=True)
(OUT / "BOUNDARY.json").write_text(json.dumps(R, indent=1, default=str) + "\n", encoding="utf-8")
for n, s in R["scenarios"].items():
    print(n, s["checks"])
