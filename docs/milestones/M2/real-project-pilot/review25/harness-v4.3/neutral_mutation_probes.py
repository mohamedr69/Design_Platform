"""R25-01 mutation probes through the ACTUAL runner (arm_ev.py, unchanged since v4.2) with the v4.3 journal validator and
the scripted provider, in NEW isolated roots under C:/t/r2x/dry-runs/r25-neutral/<scenario> (helpers of
lifecycle_probes.py: private synthetic A baseline, AGREEING synthetic labels, privately rebound declaration). No model call.
  M0 control: three scripted transport failures, killed before the stop file, journal left as written
     -> loads ok with streak 3; resume reconstructs the provider stop, exit 4, zero sends (the accepted R24-01 path)
  M1..M3 (the reviewer's mutations): the same run, then ONLY the third result's kind changed to budget / cache_hit / none,
     outcome=transport and everything else kept -> indeterminate, exit 5, zero sends, no stop file, run record / allowance
     charges / journal / io unchanged, one refusal recorded with the kind / outcome reason
Writes neutral-evidence/NEUTRAL.json (+ per-scenario logs; the journals before / after mutation are copied)."""
import hashlib
import json
import os
import pathlib
import sqlite3

import provider_journal as pj

HERE = pathlib.Path(__file__).resolve().parent
src = (HERE / "lifecycle_probes.py").read_text(encoding="utf-8")
g = {"__file__": str(HERE / "lifecycle_probes.py"), "__name__": "lifecycle_helpers"}
exec(compile(src[: src.index('R = {"lifecycle_contract"')], str(HERE / "lifecycle_probes.py"), "exec"), g)
g["ROOTS"] = pathlib.Path(os.environ.get("R25_NEUTRAL_ROOT", "C:/t/r2x/dry-runs/r25-neutral"))
make_root, run, snapshot, refusals = g["make_root"], g["run"], g["snapshot"], g["refusals"]
OUT = HERE.parent / "neutral-evidence"
OUT.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() if pathlib.Path(p).exists() else None


def charges(root):
    con = sqlite3.connect(f"file:{(root / 'dry-allowance.sqlite').as_posix()}?mode=ro", uri=True)
    try:
        return {s[:8]: c for s, c in con.execute("select sha256, calls from allowance order by sha256")}
    finally:
        con.close()


def state(root):
    o = root / "runs/L1/out"
    return {"run_json": sha(o / "RUN.json"), "journal": sha(o / "PROVIDER-OUTCOMES.jsonl"), "io": sha(o / "io.jsonl"), "progress_lines": len((o / "progress.jsonl").read_text(encoding="utf-8").splitlines()),
            "charges": charges(root), "stop_file": (o / "TERMINAL-STOP.json").exists()}


def load(jf):
    recs = [json.loads(l) for l in jf.read_text(encoding="utf-8").splitlines()]
    return pj.load(jf, recs[0]["binding"], planned_sha256={x["sha256"] for x in recs if x["type"] == "attempt"})


R = {"validator": pj.VALIDATOR_REVISION, "journal": pj.JOURNAL_VERSION, "scenarios": {}}
for kind in (None, "budget", "cache_hit", "none"):
    name = "m0-unmutated-control" if kind is None else f"m-{kind}"
    root, decl, dg = make_root(name, set())
    first = run(root, decl, dg, [], env={"PILOT_DRY_FAIL_FROM": "1", "PILOT_DRY_KILL_AT_STOP": "before_file"}, name="failure-kill")
    s0 = snapshot(root)
    jf = root / "runs/L1/out/PROVIDER-OUTCOMES.jsonl"
    original = jf.read_bytes()
    recs = [json.loads(l) for l in original.decode("utf-8").splitlines()]
    original_load = load(jf)
    alteration = None
    if kind is not None:
        old = dict(recs[-1])
        assert old["type"] == "result" and old["kind"] == "failure" and old["outcome"] == "transport"
        recs[-1]["kind"] = kind
        jf.write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in recs), encoding="utf-8")
        alteration = {"from": old, "to": recs[-1]}
    (OUT / f"{name}-JOURNAL-BEFORE.jsonl").write_bytes(original)
    (OUT / f"{name}-JOURNAL-RESUMED-FROM.jsonl").write_bytes(jf.read_bytes())
    pre_load = load(jf)
    before = state(root)
    resumed = run(root, decl, dg, ["--resume"], name="resume")
    after = state(root)
    s1 = snapshot(root)
    ref = [x for x in refusals(root) if x.get("resume")]
    entry = {"initial": {"run": first, "sends": s0["sends_total_recorded"], "stop_file": s0["stop_file"] is not None},
             "original_load": {k: original_load.get(k) for k in ("state", "streak", "why")}, "alteration": alteration,
             "load_before_resume": {k: pre_load.get(k) for k in ("state", "streak", "why")},
             "resume": {"run": resumed, "status_after": s1["status"], "new_sends": s1["sends_total_recorded"] - s0["sends_total_recorded"], "refusals": ref},
             "state_before_resume": before, "state_after_resume": after}
    if kind is None:
        entry["checks"] = {"three_failures_killed_before_file": first["exit"] == 98 and s0["sends_total_recorded"] == 3 and s0["stop_file"] is None,
                           "original_journal_streak_3": original_load["state"] == "ok" and original_load["streak"] == 3,
                           "reconstructed_stop_zero_sends": resumed["exit"] == 4 and entry["resume"]["new_sends"] == 0 and s1["status"] == "stopped" and s1["stop_file"]["reconstructed"] is True}
    else:
        entry["checks"] = {"three_failures_killed_before_file": first["exit"] == 98 and s0["sends_total_recorded"] == 3 and s0["stop_file"] is None,
                           "original_journal_streak_3": original_load["state"] == "ok" and original_load["streak"] == 3,
                           "only_the_kind_changed": {k: v for k, v in alteration["from"].items() if k != "kind"} == {k: v for k, v in alteration["to"].items() if k != "kind"},
                           "mutated_journal_indeterminate": pre_load["state"] == "indeterminate" and "kind and outcome disagree" in pre_load["why"] and repr(kind) in pre_load["why"],
                           "refused_exit_5_zero_sends": resumed["exit"] == 5 and entry["resume"]["new_sends"] == 0 and (resumed["printed"] or "").startswith("REFUSED (indeterminate"),
                           "no_stop_fabricated": not after["stop_file"],
                           "run_record_charges_journal_io_unchanged": {k: before[k] for k in ("run_json", "journal", "io", "charges")} == {k: after[k] for k in ("run_json", "journal", "io", "charges")},
                           "refusal_recorded_with_reason": len(ref) == 1 and ref[0]["requests_sent"] == 0 and "kind and outcome disagree" in ref[0]["refused"]}
    R["scenarios"][name] = entry
    print(name, entry["checks"], flush=True)
(OUT / "NEUTRAL.json").write_text(json.dumps(R, indent=1, default=str) + "\n", encoding="utf-8")
