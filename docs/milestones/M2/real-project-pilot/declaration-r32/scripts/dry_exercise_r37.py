"""ORCH-07 (R37DECL-IMPL): the dry-mode exercise of the frozen declaration's switches with the refusing stub.

Usage: dry_exercise_r37.py <dry stamp>
  1. Test twin: the bound harness (PILOT/review36/scripts/harness-r32, each file checked against BINDING-MANIFEST-R36
     harness_r36_package) copied to C:/t/iso/work/r2x/r37/harness-r32-dry-twin with ONLY the literal string
     C:/t/r2x/r34-sandbox replaced by C:/t/r2x/r37-sandbox (this task may write sandboxes only there). The twin is not
     bound and is never a live harness; TWIN-RECORD.json lists every file's bound and twin sha256.
  2. runner_r32.main(['run', '--mode', 'dry', ...]) in-process from the twin, with runner_r32.DRY_LANE_SWITCHES set to the
     declaration's lane_switches (checked equal to the runner's own dry defaults) and the declaration's caps and day limit
     (checked equal to the dry values). Dry mode: no declaration is passed to the runner, no provider exists
     (DryRefusingProvider answers every request 'dry_refused'), the live provider classes are patched to raise, the lane
     PATH holds no CLI, no ledger path; reader 'none' (no application reader touches a cohort document).
  3. The AI ledger read-only before and after (483 / 17 / 0) and no scope; the outputs are copied into
     PILOT/declaration-r32/dry-run/exercise/ (TRUTH-R32.json by hash only) with DRY-EXERCISE.json as the summary."""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import shutil
import sys

sys.dont_write_bytecode = True
os.environ["GIT_OPTIONAL_LOCKS"] = "0"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ.pop("R34_OWNER_DISPATCH_TOKEN", None)
import r37common as C  # noqa: E402

TWIN = C.WORK / "harness-r32-dry-twin"
SUBST_FROM = b"C:/t/r2x/r34-sandbox"
SUBST_TO = b"C:/t/r2x/r37-sandbox"
OUT = C.PACKAGE / "dry-run" / "exercise"


def make_twin() -> dict:
    man = json.loads(C.BINDING.read_text(encoding="utf-8"))
    bound = man["files"]["harness_r36_package"]
    if TWIN.exists():
        raise SystemExit(f"refused: {TWIN} exists (a twin is never reused)")
    TWIN.mkdir(parents=True)
    files = {}
    for p in sorted(C.HARNESS_PACKAGE.iterdir()):
        if not p.is_file():
            continue
        b = p.read_bytes()
        want = bound.get(p.as_posix())
        if want is None or C.sha256_bytes(b) != want:
            raise C.PacketMismatch(f"PACKET MISMATCH: {p}")
        t = b.replace(SUBST_FROM, SUBST_TO)
        with open(TWIN / p.name, "xb") as fh:
            fh.write(t)
        files[p.name] = {"bound_sha256": want, "twin_sha256": C.sha256_bytes(t), "substitutions": b.count(SUBST_FROM)}
    return {"kind": "ORCH-07 dry-exercise twin record (not bound, never a live harness)", "source": C.HARNESS_PACKAGE.as_posix(), "twin": TWIN.as_posix(),
            "substitution": [SUBST_FROM.decode(), SUBST_TO.decode()], "files": files, "file_count": len(files),
            "files_with_substitutions": sorted(k for k, v in files.items() if v["substitutions"]),
            "substitutions_total": sum(v["substitutions"] for v in files.values())}


def main(stamp: str) -> int:
    started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    C.check_frozen()
    decl_path = C.PACKAGE / C.DECLARATION_NAME
    sha = C.sha256_file(decl_path)
    if sha != (C.PACKAGE / "DECLARATION.sha256").read_text(encoding="utf-8").split()[0]:
        raise C.PacketMismatch("PACKET MISMATCH: the declaration")
    decl = json.loads(decl_path.read_text(encoding="utf-8"))
    if OUT.exists():
        raise SystemExit(f"refused: {OUT} exists")
    twin = make_twin()
    C.write_json_once(C.PACKAGE / "dry-run" / "TWIN-RECORD.json", twin)
    sys.path.insert(0, str(TWIN))
    import preflight_r32 as PF  # noqa: E402
    import runner_r32 as RN  # noqa: E402
    import sandbox_ingest_r32 as SI  # noqa: E402

    assert PF.SANDBOX_BASE.as_posix() == C.DRY_SANDBOX_BASE.as_posix() and RN.SANDBOX_BASE.as_posix() == C.DRY_SANDBOX_BASE.as_posix()
    assert SI.SANDBOX_BASE.as_posix() == C.DRY_SANDBOX_BASE.as_posix(), SI.SANDBOX_BASE
    switches = decl["lane_switches"]
    checks = {"declaration_switches_equal_runner_dry_defaults": RN.DRY_LANE_SWITCHES == switches,
              "declaration_caps_equal_dry_caps": RN.CAPS == decl["caps"],
              "declaration_day_limit_equal_dry_day_limit": PF.PLAN_PROJECT_DAY_LIMIT == decl["project_day_limit"]}
    if not all(checks.values()):
        raise SystemExit(f"refused: the dry values differ from the declaration: {checks}")
    RN.DRY_LANE_SWITCHES = {k: dict(v) for k, v in switches.items()}
    PF.DRY_LANE_SWITCHES_LABEL = ("ORCH-07 dry exercise: the frozen declaration's lane_switches (sha256 " + sha +
                                  "), equal to the DRAFT-DECLARATION.v2 arms; dry mode only")
    run_folder = C.DRY_SANDBOX_BASE / stamp
    led_before = {k: v for k, v in C.ledger_state().items() if k != "scope_names"}
    binding_sha = C.FROZEN["binding_manifest_r36"][1]
    argv = ["run", "--mode", "dry", "--stamp", stamp, "--run-set", C.RUN_SET.as_posix(), "--binding", C.BINDING.as_posix(), "--binding-sha", binding_sha]
    rc = RN.main(argv)
    led_after = {k: v for k, v in C.ledger_state().items() if k != "scope_names"}
    out = run_folder / "inv-1" / "out"
    OUT.mkdir(parents=True)
    copied = {}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name != "TRUTH-R32.json":
            shutil.copyfile(p, OUT / p.name)
            copied[p.name] = C.sha256_file(OUT / p.name)
    shutil.copyfile(run_folder / "RUN-STATE.json", OUT / "RUN-STATE.json")
    copied["RUN-STATE.json"] = C.sha256_file(OUT / "RUN-STATE.json")
    truth_sha = C.sha256_file(out / "TRUTH-R32.json")
    report = json.loads((out / "RUN-REPORT.json").read_text(encoding="utf-8"))
    lanes = {}
    for lane in ("B", "C", "R", "P"):
        f = out / f"LANE-{lane}.json"
        if f.exists():
            m = json.loads(f.read_text(encoding="utf-8"))
            lanes[lane] = {"reader": m.get("reader"), "model_requests": m.get("model_requests"), "dry_stub_calls": m.get("dry_stub_calls"),
                           "live_provider_attempts_blocked": m.get("live_provider_attempts_blocked"), "stats": m.get("stats"),
                           "allowance_used": m.get("allowance_used"), "switches_verified": (m.get("environment_check") or {}).get("switches"),
                           "switches_equal_declaration": (m.get("environment_check") or {}).get("switches") == switches[lane],
                           "switch_source": m.get("switch_source"), "serves_by_mode": m.get("serves_by_mode"),
                           "application_processing_run": m.get("application_processing_run"), "application_reader_run": m.get("application_reader_run")}
    summary = {"name": "DRY-EXERCISE (ORCH-07)", "started_utc": started, "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
               "declaration_sha256": sha, "stamp": stamp, "run_folder": run_folder.as_posix(), "returncode": rc, "argv": argv,
               "twin_record": "dry-run/TWIN-RECORD.json", "checks_before": checks,
               "ai_ledger_before": led_before, "ai_ledger_after": led_after,
               "ai_ledger_unchanged_483_17_0": led_before == led_after and {k: led_after[k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,
               "runner_report": {k: report.get(k) for k in ("mode", "status", "model_requests", "ledger_before", "ledger_after", "ledger_unchanged", "candidate_outcome",
                                                            "comparison_state", "score_outcome_by_field", "concentration_outcome_by_field", "allowance", "store",
                                                            "ingest", "dispatch_guard", "population_gate", "heads")},
               "lanes": lanes, "model_requests_total": sum(int(v.get("model_requests") or 0) for v in lanes.values()),
               "truth_in_out_sha256": truth_sha, "truth_equals_bound_truth": truth_sha == C.sha256_file(C.PILOT / "review34/dry-run/TRUTH-R32.json"),
               "copied": copied,
               "statement": ("dry exercise only: reader 'none' (no application reader touched a cohort document), every request ended at the refusing "
                             "stub ('dry_refused'), no provider was built, no ledger path, no scope; the scorer figures exercise the scorer and are "
                             "not results; reference set independently AI-reviewed (Claude agents), not human-signed")}
    C.write_json_once(C.PACKAGE / "dry-run" / "DRY-EXERCISE.json", summary)
    print(json.dumps({k: summary[k] for k in ("returncode", "ai_ledger_unchanged_483_17_0", "model_requests_total", "checks_before", "truth_equals_bound_truth")}
                     | {"lanes": {k: {x: v[x] for x in ("model_requests", "dry_stub_calls", "allowance_used", "switches_equal_declaration", "live_provider_attempts_blocked")}
                                  for k, v in lanes.items()},
                        "status": report.get("status"), "candidate_outcome": report.get("candidate_outcome"), "comparison_state": report.get("comparison_state")},
                     indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
