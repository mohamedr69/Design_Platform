"""R43-40: the dry-mode exercise of the v4 declaration with the BOUND review43 harness (byte copies; S-BASE dry base).
ORCH-10 (R42PORT-IMPL): the dry-mode exercise of the v3 declaration with the BOUND review42 harness, unchanged (the
sandbox base is a declared parameter: C:/t/r2x/r42-sandbox; no twin), the refusing stub and reader 'none'.

Usage: dry_exercise_r42.py new-tag | single <tag> | split <tag> | loops <tag> | xproject <tag> | cli <tag> | finish <tag>
       (run with PYTHONPATH=<work>/guard; each phase writes its record into WORK/dry/out-<tag>/; 'finish' copies them into
       PILOT/declaration-r32-v3/dry-run/ only when every phase succeeded)
  0. the declaration's values equal the runner's dry values (switches, lane allowances, parent, window, application_env, task
     kinds, the decision coverage gate, the default resume policy 'full', the global provider, the disk floor)
  single   ONE dry run over the 24-document run set (R41-13: v2 could not run it; v3 does)
  split    the same 24 documents as six per-project dry runs (v2's evidence shape, for comparison)
  loops    the EP-27331 deferral loops under resume_policy 'full' (dry drill windows 10 per 20 s and 6 per 20 s: the shapes of
           the planning and the structural cases -> 2 and 3 invocations); every early resume refused, nothing created
  xproject the cross-project deferral drill on all 24 documents (window 10 per 20 s): C waits for every project's B, R and P
           for every project's C; an early resume refused; finished
  cli      the corrected CLI-version case: a version refusal at invocation 1 (injected in-process) creates NOTHING; the same
           'run' then finishes -- Verification 41's dead-end no longer exists
The AI ledger is read (mode=ro) before and after every phase: 484 / 18 / 0 (R43-40; v3: 483 / 17 / 0). 0 model requests. Staged PDF copies of every
finished dry invocation are removed after it (scripts/trim_sandbox_r42.py rule); run records are kept."""
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
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_declaration_r42 as BD  # noqa: E402
import r42common as C  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
OUT = C.PACKAGE / "dry-run"
WORKDRY = C.WORK / "dry"
ENV = {k: v for k, v in os.environ.items() if k != C.TOKEN_ENV and not k.startswith(("R38_SANDBOX", "AI_", "CLAUDE", "ANTHROPIC"))
       and k.upper() not in ("PWD", "OLDPWD")} | {"PYTHONDONTWRITEBYTECODE": "1", "GIT_OPTIONAL_LOCKS": "0", "PYTHONIOENCODING": "utf-8"}
TRIMMED = []


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def runner(cmd, stamp, run_set, inject=None) -> dict:
    argv = [C.PY, "-B", str(HERE / "runner_r43p.py"), cmd, "--mode", "dry", "--stamp", stamp, "--sandbox-base", C.DRY_BASE.as_posix(), "--run-set", str(run_set),
            "--binding", C.BINDING43.as_posix(), "--binding-sha", C.sha256_file(C.BINDING43)] + (["--dry-inject", str(inject)] if inject else [])   # R43-40
    t0 = time.time()
    r = subprocess.run(argv, cwd=str(C.HARNESS42), env=ENV, capture_output=True, text=True, encoding="utf-8", timeout=3600)
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


def trim(stamp):
    for inv in sorted((C.DRY_BASE / stamp).glob("inv-*")):
        sub = inv / "B" / "s"
        if sub.is_dir():
            n = sum(os.path.getsize(os.path.join(dp, f)) for dp, _d, fs in os.walk(C.long_path(sub)) for f in fs)
            shutil.rmtree(C.long_path(sub))
            TRIMMED.append({"path": sub.as_posix(), "bytes": n})


def state(stamp):
    p = C.DRY_BASE / stamp / "RUN-STATE.json"
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
                           "global_provider": {k: (m.get("global_provider") or {}).get(k) for k in ("lane_kind", "at_start", "at_end", "requests_refused")},
                           "isolation_ok": all((x or {}).get("ok") for x in (m.get("isolation_check") or {}).values()),
                           "serves_by_mode": m.get("serves_by_mode"), "deferred": m.get("deferred"),
                           "statuses": {pid: d.get("status") for pid, d in (m.get("documents") or {}).items()}}
    return lanes


def checks_equal() -> tuple[dict, str]:
    C.check_run_copy()                                              # R43-40
    sys.path.insert(0, str(C.HARNESS42))
    import preflight_r32 as PF  # noqa: E402
    import runner_r32 as RN  # noqa: E402
    import score_bcr_r32 as S  # noqa: E402
    frozen, fsha = BD.frozen_bytes_checked()
    decl = json.loads(frozen.decode("utf-8"))
    checks = {"lane_switches_equal_runner_dry_defaults": RN.DRY_LANE_SWITCHES == decl["lane_switches"],
              "lane_allowances_equal_dry_caps": RN.CAPS == decl["budget"]["lane_allowances"], "parent_equal_dry_parent": RN.PARENT == decl["budget"]["parent"],
              "project_window_equal_dry_window": RN.WINDOW == decl["project_window"], "application_env_equal": PF.APPLICATION_ENV == decl["application_env"],
              "lane_task_kinds_equal": PF.task_kinds_for(RN.DRY_LANE_SWITCHES) == decl["lane_task_kinds"],
              "decision_coverage_gate_equal": S.DECISION_COVERAGE_GATE == decl["decision_coverage_gate"],
              "resume_policy_equal_dry_default": PF.DEFAULT_RESUME_POLICY == decl["resume_policy"],
              "global_provider_equal": PF.GLOBAL_PROVIDER == decl["global_provider"],
              "disk_floor_equal_dry_floor": PF.dry_disk_precondition(C.SANDBOX_BASE) == decl["disk_precondition"]}
    if not all(checks.values()):
        raise SystemExit(f"refused: the dry values differ from the declaration: {checks}")
    return checks, fsha


def stage_dir(tag) -> pathlib.Path:
    d = WORKDRY / f"out-{tag}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def copy_out(out_dir, dest: pathlib.Path, stamp) -> dict:
    dest.mkdir(parents=True, exist_ok=True)
    copied = {}
    for p in sorted(out_dir.iterdir()):
        if p.is_file() and p.name != "TRUTH-R32.json":
            shutil.copyfile(p, dest / p.name)
            copied[p.name] = C.sha256_file(dest / p.name)
    shutil.copyfile(C.DRY_BASE / stamp / "RUN-STATE.json", dest / "RUN-STATE.json")
    copied["RUN-STATE.json"] = C.sha256_file(dest / "RUN-STATE.json")
    return copied


def report_of(stamp, n=1):
    return json.loads((C.DRY_BASE / stamp / f"inv-{n}" / "out" / "RUN-REPORT.json").read_text(encoding="utf-8"))


REPORT_KEYS = ("mode", "status", "model_requests", "ledger_before", "ledger_after", "ledger_unchanged", "candidate_outcome", "comparison_state", "run_state",
               "score_outcome_by_field", "concentration_outcome_by_field", "allowance", "store", "ingest", "dispatch_guard", "population_gate", "heads",
               "lane_gates", "unread_pages", "scope_limitations", "diagnostics", "provider_identity", "free_disk", "allowance_creation", "kind")


def phase_single(tag) -> int:
    ST = stage_dir(tag)
    checks, fsha = checks_equal()
    led0 = C.ledger_counts()
    stamp = f"r43d-single-{tag}"
    step = runner("run", stamp, C.RUN_SET)
    out_dir = C.DRY_BASE / stamp / "inv-1" / "out"
    rep = report_of(stamp)
    lanes = lane_summary(out_dir)
    copied = copy_out(out_dir, ST / "exercise-single", stamp)
    truth_sha = C.sha256_file(out_dir / "TRUTH-R32.json")
    trim(stamp)
    res = {"kind": "single: ONE dry run over the 24-document run set", "stamp": stamp, "checks_before": checks, "declaration_sha256": fsha, "step": step,
           "truth_equals_bound_truth": truth_sha == C.TRUTH_SHA, "report": {k: rep.get(k) for k in REPORT_KEYS}, "lanes": lanes,
           "documents": rep["run_set"]["documents"], "model_requests_total": sum(int(v.get("model_requests") or 0) for v in lanes.values()),
           "copied_to": "dry-run/exercise-single/", "copied": copied, "ai_ledger_before": led0, "ai_ledger_after": C.ledger_counts(), "finished_utc": now()}
    res["ok"] = step["result"] == "finished" and rep.get("status") == "finished" and rep.get("run_state") == "FINISHED" and res["model_requests_total"] == 0 \
        and led0 == res["ai_ledger_after"] and res["documents"] == 24
    C.write_json(ST / "PHASE-SINGLE.json", res)
    print(json.dumps({"phase": "single", "ok": res["ok"], "run_state": rep.get("run_state"), "documents": res["documents"]}))
    return 0 if res["ok"] else 1


def phase_split(tag) -> int:
    ST = stage_dir(tag)
    checks, fsha = checks_equal()
    sys.path.insert(0, str(C.HARNESS42))
    import preflight_r32 as PF  # noqa: E402
    led0 = C.ledger_counts()
    T = PF.build_truth()
    docs = json.loads(C.RUN_SET.read_text(encoding="utf-8"))["documents"]
    runs = {}
    for ep in sorted({str(d["ep"]) for d in docs}, key=int):
        rs = WORKDRY / f"RUN-SET-EP{ep}.json"
        if not rs.exists():
            C.write_json(rs, {"documents": [{"pool_id": d["pool_id"], "doc_key": T["documents"][d["pool_id"]]["doc_key"], "ep": T["documents"][d["pool_id"]]["ep"]}
                                            for d in docs if str(d["ep"]) == ep]})
        stamp = f"r43d-m{ep}-{tag}"
        step = runner("run", stamp, rs)
        out_dir = C.DRY_BASE / stamp / "inv-1" / "out"
        rep = report_of(stamp)
        copy_out(out_dir, ST / "exercise-split" / f"EP-{ep}", stamp)
        trim(stamp)
        runs[f"EP-{ep}"] = {"stamp": stamp, "documents": [d["pool_id"] for d in docs if str(d["ep"]) == ep], "step": step,
                            "report": {k: rep.get(k) for k in ("status", "model_requests", "ledger_unchanged", "candidate_outcome", "comparison_state", "run_state")},
                            "lanes": lane_summary(out_dir)}
    res = {"kind": "split: one dry run per project (all 24 run-set documents)", "checks_before": checks, "declaration_sha256": fsha, "runs": runs,
           "documents_covered": sum(len(r["documents"]) for r in runs.values()), "ai_ledger_before": led0, "ai_ledger_after": C.ledger_counts(),
           "model_requests_total": sum(int(l.get("model_requests") or 0) for r in runs.values() for l in r["lanes"].values()), "finished_utc": now()}
    res["ok"] = all(r["report"]["run_state"] == "FINISHED" for r in runs.values()) and res["documents_covered"] == 24 and led0 == res["ai_ledger_after"] \
        and res["model_requests_total"] == 0
    C.write_json(ST / "PHASE-SPLIT.json", res)
    print(json.dumps({"phase": "split", "ok": res["ok"], "runs": {k: v["report"]["run_state"] for k, v in runs.items()}}))
    return 0 if res["ok"] else 1


def deferral_loop(ST, name, stamp, rs, inj) -> dict:
    steps = [runner("run", stamp, rs, inj)]
    trim(stamp)
    for _ in range(12):
        last = state(stamp)["invocations"][-1]
        if last.get("run_state") != "DEFERRED":
            break
        n_before = len(state(stamp)["invocations"])
        early = runner("resume", stamp, rs, inj)
        steps.append(early | {"early": True, "invocations_before": n_before, "resume_not_before_utc": last.get("resume_not_before_utc"),
                              "earliest_retry_utc": last.get("earliest_retry_utc"), "retry_at_full_utc": last.get("retry_at_full_utc"),
                              "invocations_after": len(state(stamp)["invocations"])})
        if last.get("resume_not_before") and last.get("earliest_retry") and float(last["resume_not_before"]) > float(last["earliest_retry"]) + 2.0:
            time.sleep(max(0.0, float(last["earliest_retry"]) - time.time()) + 0.5)
            if time.time() < float(last["resume_not_before"]) - 1.0:
                n_before = len(state(stamp)["invocations"])
                between = runner("resume", stamp, rs, inj)
                steps.append(between | {"between_earliest_and_full": True, "invocations_before": n_before,
                                        "invocations_after": len(state(stamp)["invocations"])})
        time.sleep(max(0.0, float(last.get("resume_not_before") or last["earliest_retry"]) - time.time()) + 1.0)
        steps.append(runner("resume", stamp, rs, inj))
        trim(stamp)
    s = state(stamp)
    invs = [i for i in s["invocations"] if i.get("kind") in ("fresh", "resume")]
    ldir = ST / name
    ldir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(C.DRY_BASE / stamp / "RUN-STATE.json", ldir / "RUN-STATE.json")
    per_inv = []
    for i in invs:
        od = C.DRY_BASE / stamp / f"inv-{i['n']}" / "out"
        if (od / "RUN-REPORT.json").exists():
            shutil.copyfile(od / "RUN-REPORT.json", ldir / f"RUN-REPORT-inv-{i['n']}.json")
            rr = json.loads((od / "RUN-REPORT.json").read_text(encoding="utf-8"))
            per_inv.append({"n": i["n"], "kind": i["kind"], "status": i["status"], "run_state": i.get("run_state"), "comparison_state": i.get("comparison_state"),
                            "deferred": i.get("deferred"), "resume_not_before_utc": i.get("resume_not_before_utc"),
                            "retry_at_earliest_utc": rr.get("retry_at_earliest_utc"), "retry_at_full_utc": rr.get("retry_at_full_utc"),
                            "lane_gates": rr.get("lane_gates"), "allowance_used": (rr.get("allowance") or {}).get("used"),
                            "model_requests": rr.get("model_requests"), "ledger_unchanged": rr.get("ledger_unchanged")})
    return {"stamp": stamp, "run_set": str(rs), "inject": json.loads(pathlib.Path(inj).read_text(encoding="utf-8")), "steps": steps, "invocations": len(invs),
            "early_resumes_refused": sum(1 for x in steps if x.get("early") and x["result"] == "refused"),
            "between_resumes_refused": sum(1 for x in steps if x.get("between_earliest_and_full") and x["result"] == "refused"),
            "refused_resumes_created_nothing": all(x["invocations_after"] == x["invocations_before"] for x in steps if x.get("early") or x.get("between_earliest_and_full")),
            "final_run_state": s["invocations"][-1].get("run_state"), "per_invocation": per_inv, "copied_to": f"dry-run/{name}/"}


def phase_loops(tag) -> int:
    ST = stage_dir(tag)
    checks, fsha = checks_equal()
    sys.path.insert(0, str(C.HARNESS42))
    import preflight_r32 as PF  # noqa: E402
    led0 = C.ledger_counts()
    T = PF.build_truth()
    ep_docs = [d for d in json.loads(C.RUN_SET.read_text(encoding="utf-8"))["documents"] if str(d["ep"]) == "27331"]
    rs27 = WORKDRY / "RUN-SET-EP27331.json"
    if not rs27.exists():
        C.write_json(rs27, {"documents": [{"pool_id": d["pool_id"], "doc_key": T["documents"][d["pool_id"]]["doc_key"], "ep": T["documents"][d["pool_id"]]["ep"]}
                                          for d in ep_docs]})
    loops = {}
    for name, limit in (("deferral-loop-planning-shape-window-10", 10), ("deferral-loop-structural-shape-window-6", 6)):
        inj = WORKDRY / f"INJECT-{name}.json"
        if not inj.exists():
            C.write_json(inj, {"project_window": {"limit": limit, "window_s": 20}, "resume_policy": "full"})
        loops[name] = deferral_loop(ST, name, f"r43d-{'p' if limit == 10 else 's'}{limit}-{tag}", rs27, inj)
    res = {"checks_before": checks, "declaration_sha256": fsha, "deferral_loops": loops, "ai_ledger_before": led0, "ai_ledger_after": C.ledger_counts(),
           "finished_utc": now()}
    res["ok"] = all(v["final_run_state"] == "FINISHED" and v["refused_resumes_created_nothing"] and v["early_resumes_refused"] >= 1 for v in loops.values()) \
        and [v["invocations"] for v in loops.values()] == [2, 3] and led0 == res["ai_ledger_after"]
    C.write_json(ST / "PHASE-LOOPS.json", res)
    print(json.dumps({"phase": "loops", "ok": res["ok"], "invocations": {k: v["invocations"] for k, v in loops.items()}}))
    return 0 if res["ok"] else 1


def phase_xproject(tag) -> int:
    ST = stage_dir(tag)
    checks, fsha = checks_equal()
    led0 = C.ledger_counts()
    inj = WORKDRY / "INJECT-xproject-window-10.json"
    if not inj.exists():
        C.write_json(inj, {"project_window": {"limit": 10, "window_s": 20}, "resume_policy": "full"})
    lp = deferral_loop(ST, "cross-project-drill-window-10", f"r43d-xp-{tag}", C.RUN_SET, inj)
    first = json.loads((ST / "cross-project-drill-window-10" / "RUN-REPORT-inv-1.json").read_text(encoding="utf-8"))
    res = {"kind": "cross-project deferral drill on all 24 documents (window 10 per 20 s, resume_policy full)", "checks_before": checks,
           "declaration_sha256": fsha, "loop": lp, "first_invocation": {"deferred": first.get("deferred"), "lane_gates": first.get("lane_gates")},
           "ai_ledger_before": led0, "ai_ledger_after": C.ledger_counts(), "finished_utc": now()}
    res["ok"] = lp["final_run_state"] == "FINISHED" and lp["refused_resumes_created_nothing"] and lp["invocations"] >= 2 and led0 == res["ai_ledger_after"]
    C.write_json(ST / "PHASE-XPROJECT.json", res)
    print(json.dumps({"phase": "xproject", "ok": res["ok"], "invocations": lp["invocations"], "early_refused": lp["early_resumes_refused"]}))
    return 0 if res["ok"] else 1


def phase_cli(tag) -> int:
    ST = stage_dir(tag)
    out = ST / "CLI-VERSION-NOT-A-DEADEND.json"
    r = subprocess.run([C.PY, "-B", str(HERE / "cli_version_drill_r42.py"), f"r43d-cli-{tag}", str(out)], cwd=str(HERE), env=ENV, capture_output=True,
                       text=True, encoding="utf-8", timeout=3600)
    res = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"error": r.stderr[-2000:]}
    trim(f"r43d-cli-{tag}")
    ok = r.returncode == 0 and res.get("ok") is True
    print(json.dumps({"phase": "cli", "ok": ok, "steps": [(s["command"], s["result"]) for s in res.get("steps", [])]}))
    return 0 if ok else 1


def finish(tag) -> int:
    if (OUT / "DRY-EXERCISE.json").exists():
        raise SystemExit("refused: DRY-EXERCISE.json is written once")
    ST = WORKDRY / f"out-{tag}"
    ph = {n: json.loads((ST / f"PHASE-{n.upper()}.json").read_text(encoding="utf-8")) for n in ("single", "split", "loops", "xproject")}
    cli = json.loads((ST / "CLI-VERSION-NOT-A-DEADEND.json").read_text(encoding="utf-8"))
    leds = [x for p in ph.values() for x in (p["ai_ledger_before"], p["ai_ledger_after"])] + [C.ledger_counts()]
    res = {"name": "DRY-EXERCISE (R43-40) of declaration-r32-v4 with the bound review43 harness (byte copies)", "tag": tag,
           "declaration_sha256": ph["single"]["declaration_sha256"], "harness": C.HARNESS43.as_posix(), "imported_from": C.HARNESS42.as_posix(),
           "sandbox_base": C.DRY_BASE.as_posix(), "substitution": "S-BASE (r43p_base.py): the dry base inside the work folder",
           "checks_before": ph["single"]["checks_before"],
           "single": {k: v for k, v in ph["single"].items() if k not in ("checks_before",)},
           "split": {k: v for k, v in ph["split"].items() if k not in ("checks_before",)},
           "deferral_loops": ph["loops"]["deferral_loops"], "cross_project_drill": {k: v for k, v in ph["xproject"].items() if k not in ("checks_before",)},
           "cli_version_case": cli, "ai_ledger_snapshots": leds,
           "ai_ledger_unchanged_484_18_0": all(x == leds[0] for x in leds) and {k: leds[0][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,
           "model_requests_total": ph["single"]["model_requests_total"] + ph["split"]["model_requests_total"]
           + sum(int(p.get("model_requests") or 0) for lp in ph["loops"]["deferral_loops"].values() for p in lp["per_invocation"])
           + sum(int(p.get("model_requests") or 0) for p in ph["xproject"]["loop"]["per_invocation"]),
           "live_run_folder_absent": not C.RUN_FOLDER.exists(),
           "staged_pdf_copies_trimmed": "after every finished dry invocation (WORK out/TRIMMED.jsonl and each phase's trim list)",
           "finished_utc": now(),
           "statement": ("dry exercise only: reader 'none' on the real run set (no application reader touched a cohort document: the bound harness runs a "
                         "reader in dry mode on synthetic documents only, so no lane-B fact of a cohort document exists here), every request ended at "
                         "the refusing stub ('dry_refused'), no provider was built, no ledger path, no scope; the loops and the cross-project drill use "
                         "dry drill windows (10 or 6 per 20 s) to show the deferral / resume loop under 'full'; the scorer figures exercise the scorer and "
                         "are not results; reference set independently AI-reviewed (Claude agents), not human-signed")}
    res["ok"] = all(p["ok"] for p in ph.values()) and cli.get("ok") is True and res["ai_ledger_unchanged_484_18_0"] and res["model_requests_total"] == 0 \
        and res["live_run_folder_absent"]
    if not res["ok"]:
        C.write_json(WORKDRY / f"DRY-EXERCISE-FAILED-{tag}.json", res)
        raise SystemExit(f"the dry exercise did not complete as expected; see DRY-EXERCISE-FAILED-{tag}.json; nothing was written to the package")
    for src in sorted(ST.rglob("*")):
        if src.is_file() and not src.name.startswith("PHASE-"):
            dst = OUT / src.relative_to(ST)
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                raise SystemExit(f"refused: {dst} exists")
            shutil.copyfile(src, dst)
    sha = C.write_json_once(OUT / "DRY-EXERCISE.json", res)
    print(json.dumps({"written": sha, "ok": res["ok"], "model_requests_total": res["model_requests_total"]}))
    return 0


if __name__ == "__main__":
    cmd, tag = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else None)
    if cmd == "new-tag":
        print(uuid.uuid4().hex[:6])
        sys.exit(0)
    rc = {"single": phase_single, "split": phase_split, "loops": phase_loops, "xproject": phase_xproject, "cli": phase_cli, "finish": finish}[cmd](tag)
    if TRIMMED:
        with open(C.WORK / "out" / "TRIMMED.jsonl", "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"at_utc": now(), "phase": cmd, "tag": tag, "removed": TRIMMED}) + "\n")
    sys.exit(rc)
