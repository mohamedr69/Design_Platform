"""ORCH-09 (R40DECL-IMPL): the dry-mode exercise of the corrected declaration with the BOUND review39 harness, unchanged
(the sandbox base is a declared parameter: C:/t/r2x/r40-sandbox; no twin), the refusing stub and reader 'none'.

Usage: dry_exercise_r40.py new-tag            (prints a fresh tag)
       dry_exercise_r40.py loops <tag>        (phase 2 and 3 below; needs LOOP_FREE_MB free per invocation)
       dry_exercise_r40.py main <tag>         (phase 1 below; needs MIN_FREE_MB free)
       dry_exercise_r40.py main-split <tag>   (phase 1 as six per-project dry runs; for a nearly full drive C)
       dry_exercise_r40.py finish <tag>       (DRY-EXERCISE.json and the copies into the package, only if both phases succeeded)
  0. the declaration's values equal the runner's dry values (switches, lane allowances, parent, window, application_env,
     task kinds, the decision coverage gate, the default resume policy 'full'): dry mode therefore runs the declared arms
  1. MAIN: runner_r32.py run --mode dry over the 24-document run set (subprocess from PILOT/review39/scripts/harness-r32)
  2. DEFERRAL LOOPS under resume_policy 'full' over EP-27331's 6 documents with a small rolling window (dry drill values:
     10 per 20 s, the shape of the planning case -> 2 invocations; 6 per 20 s, the shape of the structural case -> 3):
     after every DEFERRED invocation an immediate resume (refused, nothing created), a resume between the earliest and the
     full time when they differ (refused), then a resume at resume_not_before; until the run finishes
  3. the CLI-version dead-end drill (cli_version_deadend_r40.py)
  The AI ledger is read (mode=ro) before and after every step: 483 / 17 / 0. 0 model requests (the stub answers every
  request 'dry_refused'; no provider is built; the lane PATH holds no CLI; no ledger path).
Writes the summaries and copies of the outputs into PILOT/declaration-r32-v2/dry-run/ (once each) and the run folders under
C:/t/r2x/r40-sandbox/r40d-*; work files under C:/t/iso/work/r2x/r40/dry/."""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
os.environ["GIT_OPTIONAL_LOCKS"] = "0"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ.pop("R34_OWNER_DISPATCH_TOKEN", None)
import build_declaration_r40 as BD  # noqa: E402
import r40common as C  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
OUT = C.PACKAGE / "dry-run"
WORKDRY = C.WORK / "dry"
ENV = {k: v for k, v in os.environ.items() if k != C.TOKEN_ENV and not k.startswith("R38_SANDBOX")} | {
    "PYTHONDONTWRITEBYTECODE": "1", "GIT_OPTIONAL_LOCKS": "0", "PYTHONIOENCODING": "utf-8"}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def staged_mb(run_set) -> int:
    """The MB the ingestion of this run set stages (its PDFs, copied from the frozen staging)."""
    ids = [d["pool_id"] for d in json.loads(pathlib.Path(run_set).read_text(encoding="utf-8"))["documents"]]
    return -(-sum(os.path.getsize(f"C:/t/r2x/r32-stage/files/{i}.pdf") for i in ids) // (1 << 20))


def runner(cmd, stamp, run_set, inject=None) -> dict:
    # free space needed: the staged PDFs of this run plus a 40 MB margin for everything else (and never less than 50 MB)
    need_space(f"{cmd} {stamp}", None if stamp.startswith("r40d-main") else max(50, staged_mb(run_set) + 40))
    argv = [C.PY, "-B", "runner_r32.py", cmd, "--mode", "dry", "--stamp", stamp, "--sandbox-base", C.SANDBOX_BASE.as_posix(), "--run-set", str(run_set),
            "--binding", C.BINDING.as_posix(), "--binding-sha", C.BINDING_SHA] + (["--dry-inject", str(inject)] if inject else [])
    t0 = time.time()
    r = subprocess.run(argv, cwd=str(C.HARNESS), env=ENV, capture_output=True, text=True, encoding="utf-8", timeout=3600)
    last = [ln for ln in (r.stderr or "").strip().splitlines() if ln.strip()]
    printed = None
    for ln in reversed((r.stdout or "").strip().splitlines()):
        if ln.startswith("{"):
            try:
                printed = json.loads(ln)
                break
            except ValueError:
                pass
    return {"command": cmd, "at_utc": now(), "seconds": round(time.time() - t0, 1), "returncode": r.returncode,
            "result": "finished" if r.returncode == 0 else ("refused" if last and "Refused" in last[-1] else "error"),
            "why": (last[-1] if last else None) if r.returncode else None, "printed": printed}


MIN_FREE_MB = 250                 # before the MAIN run (it stages 112 MB of PDFs); a loop invocation stages 33 MB: LOOP_FREE_MB
LOOP_FREE_MB = 80                 # a loop invocation or a per-project run stages at most 37 MB (trimmed after it)


def free_mb() -> int:
    return shutil.disk_usage("C:/").free // (1 << 20)


def need_space(what: str, minimum: int | None = None):
    """Refuse to start a dry run step when drive C has less than MIN_FREE_MB free (attempt 1 failed when the drive reached 0 bytes
    because other processes were writing): nothing half-written ever reaches the package."""
    f, need = free_mb(), (minimum or MIN_FREE_MB)
    if f < need:
        raise SystemExit(f"refused: only {f} MB free on C: before {what} (need {need}); nothing was written to the package")


TRIMMED = []


def trim(stamp):
    """After an invocation has FINISHED: remove the staged PDF copies of the dry run's finished invocations (<run folder>/inv-<n>/B/s,
    copies of the frozen staging made by sandbox_ingest; regenerable; never the live run folder). A resume never reads them."""
    for inv in sorted((C.SANDBOX_BASE / stamp).glob("inv-*")):
        for sub in (inv / "B" / "s",):
            if sub.is_dir():
                n = sum(f.stat().st_size for f in sub.rglob("*") if f.is_file())
                shutil.rmtree(chr(92) * 2 + "?" + chr(92) + str(sub).replace("/", chr(92)))
                TRIMMED.append({"path": sub.as_posix(), "bytes": n})


def state(stamp):
    p = C.SANDBOX_BASE / stamp / "RUN-STATE.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def lane_summary(out_dir: pathlib.Path) -> dict:
    lanes = {}
    for lane in ("B", "C", "R", "P"):
        f = out_dir / f"LANE-{lane}.json"
        if f.exists():
            m = json.loads(f.read_text(encoding="utf-8"))
            lanes[lane] = {"reader": m.get("reader"), "model_requests": m.get("model_requests"), "dry_stub_calls": m.get("dry_stub_calls"),
                           "allowance_used": m.get("allowance_used"), "live_provider_attempts_blocked": m.get("live_provider_attempts_blocked"),
                           "switches_verified": (m.get("environment_check") or {}).get("switches"), "task_kinds": m.get("task_kinds"),
                           "application_env_check": m.get("application_env_check"), "serves_by_mode": m.get("serves_by_mode"),
                           "deferred": m.get("deferred"), "statuses": {pid: d.get("status") for pid, d in (m.get("documents") or {}).items()}}
    return lanes


def checks_equal(BDmod=None) -> tuple[dict, str]:
    C.harness_import_path()
    import preflight_r32 as PF  # noqa: E402
    import runner_r32 as RN  # noqa: E402
    import score_bcr_r32 as S  # noqa: E402
    frozen, fsha = BD.frozen_bytes_checked()
    decl = json.loads(frozen.decode("utf-8"))
    checks = {"lane_switches_equal_runner_dry_defaults": RN.DRY_LANE_SWITCHES == decl["lane_switches"],
              "lane_allowances_equal_dry_caps": RN.CAPS == decl["budget"]["lane_allowances"],
              "parent_equal_dry_parent": RN.PARENT == decl["budget"]["parent"],
              "project_window_equal_dry_window": RN.WINDOW == decl["project_window"],
              "application_env_equal": PF.APPLICATION_ENV == decl["application_env"],
              "lane_task_kinds_equal": PF.task_kinds_for(RN.DRY_LANE_SWITCHES) == decl["lane_task_kinds"],
              "decision_coverage_gate_equal": S.DECISION_COVERAGE_GATE == decl["decision_coverage_gate"],
              "resume_policy_equal_dry_default": PF.DEFAULT_RESUME_POLICY == decl["resume_policy"]}
    if not all(checks.values()):
        raise SystemExit(f"refused: the dry values differ from the declaration: {checks}")
    return checks, fsha


def stage_dir(tag) -> pathlib.Path:
    d = WORKDRY / f"out-{tag}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def phase_main(tag) -> int:
    """The MAIN dry run over the 24-document run set (stages 112 MB of PDFs: it needs MIN_FREE_MB free)."""
    STAGE = stage_dir(tag)
    if (STAGE / "PHASE-MAIN.json").exists():
        raise SystemExit("refused: the main phase of this tag is done")
    checks, fsha = checks_equal()
    led0 = C.ledger_counts()
    stamp = f"r40d-main-{tag}"
    step = runner("run", stamp, C.RUN_SET)
    out_dir = C.SANDBOX_BASE / stamp / "inv-1" / "out"
    rep = json.loads((out_dir / "RUN-REPORT.json").read_text(encoding="utf-8"))
    lanes = lane_summary(out_dir)
    dest = STAGE / "exercise"
    dest.mkdir(parents=True, exist_ok=True)
    copied = {}
    for p in sorted(out_dir.iterdir()):
        if p.is_file() and p.name != "TRUTH-R32.json":
            shutil.copyfile(p, dest / p.name)
            copied[p.name] = C.sha256_file(dest / p.name)
    shutil.copyfile(C.SANDBOX_BASE / stamp / "RUN-STATE.json", dest / "RUN-STATE.json")
    copied["RUN-STATE.json"] = C.sha256_file(dest / "RUN-STATE.json")
    truth_sha = C.sha256_file(out_dir / "TRUTH-R32.json")
    trim(stamp)
    led1 = C.ledger_counts()
    res = {"stamp": stamp, "run_folder": (C.SANDBOX_BASE / stamp).as_posix(), "checks_before": checks, "declaration_sha256": fsha, "step": step,
           "truth_in_out_sha256": truth_sha, "truth_equals_bound_truth": truth_sha == C.TRUTH_SHA,
           "report": {k: rep.get(k) for k in ("mode", "status", "model_requests", "ledger_before", "ledger_after", "ledger_unchanged", "candidate_outcome",
                                              "comparison_state", "run_state", "score_outcome_by_field", "concentration_outcome_by_field", "allowance",
                                              "store", "ingest", "dispatch_guard", "population_gate", "heads", "lane_gates", "unread_pages",
                                              "scope_limitations", "diagnostics", "provider_identity")},
           "lanes": lanes, "model_requests_total": sum(int(v.get("model_requests") or 0) for v in lanes.values()),
           "copied_to": "dry-run/exercise/", "copied": copied, "trimmed": list(TRIMMED), "ai_ledger_before": led0, "ai_ledger_after": led1,
           "finished_utc": now()}
    (STAGE / "PHASE-MAIN.json").write_text(json.dumps(res, indent=1, sort_keys=True, default=str) + chr(10), encoding="utf-8", newline=chr(10))
    print(json.dumps({"phase": "main", "status": rep.get("status"), "model_requests": res["model_requests_total"], "ledger_unchanged": led0 == led1,
                      "candidate_outcome": rep.get("candidate_outcome"), "comparison_state": rep.get("comparison_state")}, default=str))
    return 0


def phase_main_split(tag) -> int:
    """The MAIN exercise as six dry runs, one per cohort project, covering all 24 run-set documents (each stages at most 37 MB,
    trimmed after its run): used because drive C stayed below MIN_FREE_MB for the single 112 MB run. Same declared switches,
    caps, parent and window (the dry defaults); each run scores its own documents."""
    STAGE = stage_dir(tag)
    if (STAGE / "PHASE-MAIN.json").exists():
        raise SystemExit("refused: the main phase of this tag is done")
    checks, fsha = checks_equal()
    import preflight_r32 as PF  # noqa: E402
    led0 = C.ledger_counts()
    T = PF.build_truth()
    docs = json.loads(C.RUN_SET.read_text(encoding="utf-8"))["documents"]
    eps = sorted({str(d["ep"]) for d in docs}, key=int)
    runs, all_copied = {}, {}
    for ep in eps:
        rs = WORKDRY / f"RUN-SET-EP{ep}.json"
        if not rs.exists():
            rs.write_text(json.dumps({"documents": [{"pool_id": d["pool_id"], "doc_key": T["documents"][d["pool_id"]]["doc_key"],
                                                     "ep": T["documents"][d["pool_id"]]["ep"]} for d in docs if str(d["ep"]) == ep]}, indent=1) + chr(10),
                          encoding="utf-8", newline=chr(10))
        stamp = f"r40d-m{ep}-{tag}"
        prior = state(stamp)
        if prior and prior["invocations"] and prior["invocations"][-1].get("status") == "finished":
            step = {"command": "run", "result": "finished", "reused": "finished earlier in this phase (the phase stopped at a later project for lack of space and was re-entered)"}
        else:
            step = runner("run", stamp, rs)
        out_dir = C.SANDBOX_BASE / stamp / "inv-1" / "out"
        rep = json.loads((out_dir / "RUN-REPORT.json").read_text(encoding="utf-8"))
        lanes = lane_summary(out_dir)
        dest = STAGE / "exercise" / f"EP-{ep}"
        dest.mkdir(parents=True, exist_ok=True)
        for p in sorted(out_dir.iterdir()):
            if p.is_file() and p.name != "TRUTH-R32.json":
                shutil.copyfile(p, dest / p.name)
                all_copied[f"EP-{ep}/{p.name}"] = C.sha256_file(dest / p.name)
        shutil.copyfile(C.SANDBOX_BASE / stamp / "RUN-STATE.json", dest / "RUN-STATE.json")
        all_copied[f"EP-{ep}/RUN-STATE.json"] = C.sha256_file(dest / "RUN-STATE.json")
        truth_sha = C.sha256_file(out_dir / "TRUTH-R32.json")
        trim(stamp)
        runs[f"EP-{ep}"] = {"stamp": stamp, "run_set": rs.as_posix(), "documents": [d["pool_id"] for d in docs if str(d["ep"]) == ep], "step": step,
                            "truth_equals_bound_truth": truth_sha == C.TRUTH_SHA,
                            "report": {k: rep.get(k) for k in ("status", "model_requests", "ledger_unchanged", "candidate_outcome", "comparison_state",
                                                               "run_state", "lane_gates", "unread_pages", "allowance", "store", "ingest", "population_gate",
                                                               "scope_limitations", "provider_identity")},
                            "lanes": lanes, "model_requests_total": sum(int(v.get("model_requests") or 0) for v in lanes.values())}
    led1 = C.ledger_counts()
    finished = all(r["step"]["result"] == "finished" and r["report"].get("status") == "finished" for r in runs.values())
    res = {"kind": "split: one dry run per project (all 24 run-set documents)", "checks_before": checks, "declaration_sha256": fsha, "runs": runs,
           "documents_covered": sum(len(r["documents"]) for r in runs.values()),
           "step": {"result": "finished" if finished else "not finished"}, "report": {"status": "finished" if finished else "not finished"},
           "model_requests_total": sum(r["model_requests_total"] for r in runs.values()),
           "copied_to": "dry-run/exercise/EP-<ep>/", "copied": all_copied, "trimmed": list(TRIMMED), "ai_ledger_before": led0, "ai_ledger_after": led1,
           "finished_utc": now()}
    (STAGE / "PHASE-MAIN.json").write_text(json.dumps(res, indent=1, sort_keys=True, default=str) + chr(10), encoding="utf-8", newline=chr(10))
    print(json.dumps({"phase": "main-split", "finished": finished, "documents_covered": res["documents_covered"], "model_requests": res["model_requests_total"],
                      "ledger_unchanged": led0 == led1, "runs": {k: (v["report"].get("status"), v["report"].get("comparison_state")) for k, v in runs.items()}},
                     default=str))
    return 0


def phase_loops(tag) -> int:
    """The EP-27331 deferral / resume loops under 'full' (33 MB staged per invocation, trimmed after each) and the CLI drill."""
    STAGE = stage_dir(tag)
    if (STAGE / "PHASE-LOOPS.json").exists():
        raise SystemExit("refused: the loops phase of this tag is done")
    checks, fsha = checks_equal()
    import preflight_r32 as PF  # noqa: E402
    led0 = C.ledger_counts()
    T = PF.build_truth()
    ep_docs = [d for d in json.loads(C.RUN_SET.read_text(encoding="utf-8"))["documents"] if str(d["ep"]) == "27331"]
    rs27 = WORKDRY / "RUN-SET-EP27331.json"
    if not rs27.exists():
        rs27.write_text(json.dumps({"documents": [{"pool_id": d["pool_id"], "doc_key": T["documents"][d["pool_id"]]["doc_key"], "ep": T["documents"][d["pool_id"]]["ep"]}
                                                  for d in ep_docs]}, indent=1) + chr(10), encoding="utf-8", newline=chr(10))
    loops = {}
    for name, limit in (("planning-shape-window-10", 10), ("structural-shape-window-6", 6)):
        inj = WORKDRY / f"INJECT-{name}.json"
        if not inj.exists():
            inj.write_text(json.dumps({"project_window": {"limit": limit, "window_s": 20}, "resume_policy": "full"}, indent=1) + chr(10),
                           encoding="utf-8", newline=chr(10))
        st = f"r40d-{'p' if limit == 10 else 's'}{limit}-{tag}"
        steps = [runner("run", st, rs27, inj)]
        trim(st)
        for _ in range(12):
            last = state(st)["invocations"][-1]
            if last.get("run_state") != "DEFERRED":
                break
            n_before = len(state(st)["invocations"])
            early = runner("resume", st, rs27, inj)
            steps.append(early | {"early": True, "invocations_before": n_before, "resume_not_before_utc": last.get("resume_not_before_utc"),
                                  "earliest_retry_utc": last.get("earliest_retry_utc"), "retry_at_full_utc": last.get("retry_at_full_utc"),
                                  "invocations_after": len(state(st)["invocations"])})
            if last.get("resume_not_before") and last.get("earliest_retry") and float(last["resume_not_before"]) > float(last["earliest_retry"]) + 2.0:
                time.sleep(max(0.0, float(last["earliest_retry"]) - time.time()) + 0.5)
                if time.time() < float(last["resume_not_before"]) - 1.0:
                    n_before = len(state(st)["invocations"])
                    between = runner("resume", st, rs27, inj)
                    steps.append(between | {"between_earliest_and_full": True, "invocations_before": n_before,
                                            "invocations_after": len(state(st)["invocations"])})
            time.sleep(max(0.0, float(last.get("resume_not_before") or last["earliest_retry"]) - time.time()) + 1.0)
            steps.append(runner("resume", st, rs27, inj))
            trim(st)
        s = state(st)
        invs = [i for i in s["invocations"] if i.get("kind") in ("fresh", "resume")]
        ldir = STAGE / f"deferral-loop-{name}"
        ldir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(C.SANDBOX_BASE / st / "RUN-STATE.json", ldir / "RUN-STATE.json")
        lcopied = {"RUN-STATE.json": C.sha256_file(ldir / "RUN-STATE.json")}
        per_inv = []
        for i in invs:
            od = C.SANDBOX_BASE / st / f"inv-{i['n']}" / "out"
            if (od / "RUN-REPORT.json").exists():
                shutil.copyfile(od / "RUN-REPORT.json", ldir / f"RUN-REPORT-inv-{i['n']}.json")
                lcopied[f"RUN-REPORT-inv-{i['n']}.json"] = C.sha256_file(ldir / f"RUN-REPORT-inv-{i['n']}.json")
                rr = json.loads((od / "RUN-REPORT.json").read_text(encoding="utf-8"))
                per_inv.append({"n": i["n"], "kind": i["kind"], "status": i["status"], "run_state": i.get("run_state"), "comparison_state": i.get("comparison_state"),
                                "deferred": i.get("deferred"), "resume_not_before_utc": i.get("resume_not_before_utc"),
                                "retry_at_earliest_utc": rr.get("retry_at_earliest_utc"), "retry_at_full_utc": rr.get("retry_at_full_utc"),
                                "lane_gates": rr.get("lane_gates"), "allowance_used": (rr.get("allowance") or {}).get("used"),
                                "model_requests": rr.get("model_requests"), "ledger_unchanged": rr.get("ledger_unchanged")})
        loops[name] = {"stamp": st, "run_folder": (C.SANDBOX_BASE / st).as_posix(), "run_set": rs27.as_posix(), "documents": [d["pool_id"] for d in ep_docs],
                       "inject": json.loads(inj.read_text(encoding="utf-8")), "steps": steps, "invocations": len(invs),
                       "early_resumes_refused": sum(1 for x in steps if x.get("early") and x["result"] == "refused"),
                       "between_resumes_refused": sum(1 for x in steps if x.get("between_earliest_and_full") and x["result"] == "refused"),
                       "refused_resumes_created_nothing": all(x["invocations_after"] == x["invocations_before"] for x in steps
                                                              if x.get("early") or x.get("between_earliest_and_full")),
                       "final_run_state": s["invocations"][-1].get("run_state"), "final_comparison_state": s["invocations"][-1].get("comparison_state"),
                       "per_invocation": per_inv, "copied_to": f"dry-run/deferral-loop-{name}/", "copied": lcopied}
    cst = f"r40d-cli-{tag}"
    cli_out = STAGE / "CLI-VERSION-DEADEND.json"
    need_space(f"the CLI drill {cst}", LOOP_FREE_MB)
    r = subprocess.run([C.PY, "-B", str(HERE / "cli_version_deadend_r40.py"), cst, str(cli_out)], cwd=str(HERE), env=ENV, capture_output=True, text=True,
                       encoding="utf-8", timeout=3600)
    led1 = C.ledger_counts()
    res = {"checks_before": checks, "declaration_sha256": fsha, "deferral_loops": loops, "trimmed": list(TRIMMED),
           "cli_version_deadend": {"returncode": r.returncode, "output": "dry-run/CLI-VERSION-DEADEND.json",
                                   "summary": json.loads(cli_out.read_text(encoding="utf-8"))["steps"] if cli_out.exists() else r.stderr[-1500:]},
           "ai_ledger_before": led0, "ai_ledger_after": led1, "finished_utc": now()}
    (STAGE / "PHASE-LOOPS.json").write_text(json.dumps(res, indent=1, sort_keys=True, default=str) + chr(10), encoding="utf-8", newline=chr(10))
    print(json.dumps({"phase": "loops", "loops": {k: (v["invocations"], v["early_resumes_refused"], v["between_resumes_refused"], v["final_run_state"])
                                                  for k, v in loops.items()}, "cli": [(s["command"], s["result"]) for s in res["cli_version_deadend"]["summary"]]
                      if isinstance(res["cli_version_deadend"]["summary"], list) else res["cli_version_deadend"]["summary"],
                      "ledger_unchanged": led0 == led1}, default=str))
    return 0


def finish(tag) -> int:
    """Assemble DRY-EXERCISE.json from both phases and copy the staged outputs into the package, only when everything succeeded."""
    if (OUT / "DRY-EXERCISE.json").exists():
        raise SystemExit("refused: DRY-EXERCISE.json is written once")
    STAGE = WORKDRY / f"out-{tag}"
    main_r = json.loads((STAGE / "PHASE-MAIN.json").read_text(encoding="utf-8"))
    loops_r = json.loads((STAGE / "PHASE-LOOPS.json").read_text(encoding="utf-8"))
    cli = json.loads((STAGE / "CLI-VERSION-DEADEND.json").read_text(encoding="utf-8"))
    leds = [main_r["ai_ledger_before"], main_r["ai_ledger_after"], loops_r["ai_ledger_before"], loops_r["ai_ledger_after"], C.ledger_counts()]
    res = {"name": "DRY-EXERCISE (ORCH-09) of declaration-r32-v2 with the bound review39 harness", "tag": tag, "declaration_sha256": main_r["declaration_sha256"],
           "harness": C.HARNESS.as_posix(), "sandbox_base": C.SANDBOX_BASE.as_posix(), "checks_before": main_r["checks_before"],
           "phases": {"loops_finished_utc": loops_r["finished_utc"], "main_finished_utc": main_r["finished_utc"],
                      "why_two_phases": ("drive C was nearly full (attempt 1 failed when it reached 0 bytes free, other processes writing): the EP-27331 loops "
                                         "(33 MB staged per invocation) and the main exercise were run as separate phases, each only when enough space was free; "
                                         "a single main run stages 112 MB and needs 250 MB free, so when the drive stayed below that the main exercise ran as "
                                         "six per-project dry runs covering the same 24 documents (main_kind)")},
           "main": {k: v for k, v in main_r.items() if k not in ("checks_before", "declaration_sha256", "ai_ledger_before", "ai_ledger_after")},
           "main_kind": main_r.get("kind", "single: one dry run over the 24-document run set"),
           "deferral_loops": loops_r["deferral_loops"], "cli_version_deadend": loops_r["cli_version_deadend"],
           "ai_ledger_snapshots": leds, "ai_ledger_unchanged_483_17_0": all(x == leds[0] for x in leds) and
           {k: leds[0][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,
           "model_requests_total": main_r["model_requests_total"] + sum(int(p.get("model_requests") or 0) for lp in loops_r["deferral_loops"].values()
                                                                         for p in lp["per_invocation"]),
           "live_run_folder_absent": not C.RUN_FOLDER.exists(),
           "staged_pdf_copies_trimmed": {"count": len(main_r["trimmed"]) + len(loops_r["trimmed"]),
                                         "bytes": sum(t["bytes"] for t in main_r["trimmed"] + loops_r["trimmed"]),
                                         "paths": [t["path"] for t in loops_r["trimmed"] + main_r["trimmed"]],
                                         "why": "drive C was nearly full: the staged PDF copies of finished dry invocations were removed after each invocation"},
           "finished_utc": now(),
           "statement": ("dry exercise only: reader 'none' on the real run set (no application reader touched a cohort document), every request ended at "
                         "the refusing stub ('dry_refused'), no provider was built, no ledger path, no scope; the loops use dry drill windows (10 or 6 per "
                         "20 s) to show the deferral / resume loop under 'full'; the scorer figures exercise the scorer and are not results; reference "
                         "set independently AI-reviewed (Claude agents), not human-signed")}
    ok = (main_r["step"]["result"] == "finished" and main_r["report"].get("status") == "finished" and res["ai_ledger_unchanged_483_17_0"]
          and res["model_requests_total"] == 0 and res["live_run_folder_absent"]
          and all(v["final_run_state"] == "FINISHED" and v["refused_resumes_created_nothing"] for v in loops_r["deferral_loops"].values())
          and [x["result"] for x in cli.get("steps", [])] == ["refused", "refused", "refused"] and cli.get("after_first_invocation", {}).get("allowance_exists") is False)
    res["ok"] = ok
    if not ok:
        (WORKDRY / f"DRY-EXERCISE-FAILED-{tag}.json").write_text(json.dumps(res, indent=1, sort_keys=True, default=str) + chr(10), encoding="utf-8",
                                                                 newline=chr(10))
        raise SystemExit(f"the dry exercise did not complete as expected; see DRY-EXERCISE-FAILED-{tag}.json; nothing was written to the package")
    for src in sorted(STAGE.rglob("*")):
        if src.is_file() and not src.name.startswith("PHASE-"):
            dst = OUT / src.relative_to(STAGE)
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                raise SystemExit(f"refused: {dst} exists")
            shutil.copyfile(src, dst)
    sha = C.write_json_once(OUT / "DRY-EXERCISE.json", res)
    print(json.dumps({"written": sha, "ok": ok, "main_status": main_r["report"].get("status"),
                      "loops": {k: v["invocations"] for k, v in loops_r["deferral_loops"].items()}, "model_requests_total": res["model_requests_total"]}))
    return 0


if __name__ == "__main__":
    cmd, tag = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else None)
    if cmd == "new-tag":
        print(uuid.uuid4().hex[:6])
        sys.exit(0)
    sys.exit({"main": phase_main, "main-split": phase_main_split, "loops": phase_loops, "finish": finish}[cmd](tag))
