"""ORCH-05.1 (Review 33 C-5, R33-06): the guarded live runner of the r32 fresh validation, lanes B, C, R and P (plan v2
section 4). It never imports the application: each lane is a subprocess (lane_r32.py) in its own tree and sandbox.

  runner_r32.py --mode dry|live --stamp S --run-set RUN-SET.json --binding BINDING-MANIFEST-R33.json --binding-sha SHA
                [--declaration DECL.json --declaration-sha SHA] [--resume-drill] [--out DIR]

Order (plan v2 section 4):
  0. preflight: the binding manifest hash and every file it binds (a difference refuses the run); in live mode the
     ORCH-07 declaration hash, and the declaration must bind this binding manifest and this run set; the dispatch guard
     (live: must authorize; dry: its refusal is recorded); candidate and baseline HEADs clean; the AI ledger counted
     read-only; the population gate on the reference set (DISPATCH_ELIGIBLE or stop); the run set (canonical ids, <= 30);
     one writer (an exclusive lock file);
  1. B: sandbox_ingest_r32 registers exactly the run set (no processing), then lane B (the application's processing,
     tripwire after every document); B's database file sha256 is recorded when B finishes;
  2. C-from-B: C's sandbox is a sqlite-backup copy of B; state_check.check_c_start must pass;
  3. C: lane C through the capture store, tripwire after every document;
  4. R: lane R on its own copy of B (state check), served C's capture by content key;
  5. P: the variation probe over C's answered dispatches;
  6. scoring offline: score_lane_r32 per lane, then score_bcr_r32.evaluate (per field) with the concentration rule.
Stop rules: stop_rules.StopController (unchanged copy) replays every lane's events in order; B INVALID means C never starts.
Dry mode over the r32 cohort: reader 'none' -- no application reader touches a cohort document (that would be a
prediction); every other stage runs for real (ingestion, state checks, capture store, allowance, guard, stop rules,
resume drill, scoring of the unprocessed rows as an exercise). The application readers' path is exercised in dry mode only
on SYNTHETIC documents (test_runner_r32.py). Dry mode: no provider exists (DryRefusingProvider), no ledger path, PATH
without any CLI, 0 model requests; the AI ledger must read the same before and after.
Resume contract: a run's capture store and durable allowance are never recreated or raised; every bound fingerprint is
served from the store; a reserved request without an answer is CHARGED and served 'interrupted_charged', never sent
again; lanes always run on new sandboxes (--resume-drill demonstrates it on a copy)."""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dispatch_guard_r32 as DG  # noqa: E402
import inputs_r32 as I  # noqa: E402
import labels_adapter_r32 as A  # noqa: E402
import sandbox_ingest_r32 as SI  # noqa: E402
import score_bcr_r32 as S  # noqa: E402
import state_check  # noqa: E402
import stop_rules  # noqa: E402

PY = SI.PY
SANDBOX_BASE = SI.SANDBOX_BASE
RUNS = pathlib.Path("C:/t/iso/work/r2x/r33/runs")
TREES = {"baseline": "C:/t/iso/frozen-r12/backend", "candidate": "C:/t/iso/cand-r29/backend"}
HEADS = {"C:/t/iso/frozen-r12": I.BASELINE_HEAD, "C:/t/iso/cand-r29": I.CANDIDATE_HEAD}
CAPS = {"B": 240, "C": 240, "R": 40, "P": 36}
# lane switches: DRAFT-DECLARATION.v2 (review31) arms; the ORCH-07 declaration binds the final values
LANE_SWITCHES = {
    "B": {"AI_EVIDENCE_VARIANT": "off"},
    "C": {"AI_EVIDENCE_VARIANT": "EV1", "AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_SUPPORT": "v2", "AI_EVIDENCE_SCHEDULING": "required_first",
          "AI_EVIDENCE_DEADLINE": "1", "AI_EVIDENCE_TARGETED": "1", "AI_EVIDENCE_IDGUARD": "1", "AI_EVIDENCE_ADJUDICATE": "1",
          "AI_EVIDENCE_DECISION_REGION": "1", "AI_EVIDENCE_ASSOC": "1"},
    "R": {"AI_EVIDENCE_VARIANT": "EV1", "AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_SUPPORT": "v2", "AI_EVIDENCE_SCHEDULING": "required_first",
          "AI_EVIDENCE_DEADLINE": "1", "AI_EVIDENCE_TARGETED": "1"},
}
C_MARKERS = SI.C_MARKERS
EVIDENCE_TASKS = ["discover_page", "discover_region", "locate_decision", "read_identity", "read_revision", "read_decision",
                  "read_field_context", "read_boq_row"]
DRY_PATH = "C:/Windows/system32;C:/Windows"


class Refused(RuntimeError):
    pass


def sha256(path) -> str:
    return I.sha256_file(path)


def ledger_state() -> dict:
    con = sqlite3.connect(f"file:{I.AI_LEDGER}?mode=ro", uri=True)
    try:
        return {"entries": con.execute("select count(*) from entries").fetchone()[0], "scopes": con.execute("select count(*) from scopes").fetchone()[0],
                "limit_amendments": con.execute("select count(*) from limit_amendments").fetchone()[0]}
    finally:
        con.close()


def verify_binding(path, expected_sha) -> dict:
    got = sha256(path)
    if not expected_sha or got != expected_sha:
        raise Refused(f"refused: binding manifest {got} != {expected_sha}")
    man = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    bad = [p for files in (man.get("files") or {}).values() for p, want in files.items()
           if not pathlib.Path(p).exists() or sha256(p) != want]
    if bad:
        raise Refused(f"refused: {len(bad)} bound file(s) differ: {bad[:5]}")
    return {"binding_manifest": str(path), "sha256": got, "files_verified": sum(len(v) for v in (man.get("files") or {}).values())}


def heads() -> dict:
    out = {}
    for repo, want in HEADS.items():
        head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
        if head != want or dirty:
            raise Refused(f"refused: {repo} HEAD {head} clean={not dirty}")
        out[repo] = head
    return out


def lane_env(mode, root, lane, cfg=None) -> dict:
    """The lane's environment: the sandbox, the lane switches (the declaration's in live mode, else LANE_SWITCHES), and in
    live mode the declaration's provider environment; in dry mode no ledger path and a PATH without any CLI."""
    switches = ((cfg or {}).get("lane_switches") or LANE_SWITCHES).get(lane, {})
    env = SI.sandbox_env(pathlib.Path(root), ai_enabled=True, extra=switches)
    if mode == "dry":
        env["PATH"] = DRY_PATH
        env["AI_LEDGER_PATH"] = ""
    else:
        env.update((cfg or {}).get("provider_env") or {})
    return env


def run_lane(lane, cfg_path, out, env, tree, tag=None):
    log = pathlib.Path(out) / f"lane-{tag or lane}.log"
    with open(log, "w", encoding="utf-8") as fh:
        r = subprocess.run([PY, str(HERE / "lane_r32.py"), lane, str(cfg_path)], cwd=tree, env=env, stdout=fh, stderr=subprocess.STDOUT)
    if r.returncode:
        raise RuntimeError(f"lane {lane} failed ({r.returncode}); see {log}")
    return json.loads((pathlib.Path(out) / f"LANE-{lane}.json").read_text(encoding="utf-8"))


def copy_b(b_root: pathlib.Path, root: pathlib.Path):
    if root.exists():
        raise Refused(f"refused: {root} exists (a lane never reuses a sandbox)")
    for d in ("db", "out"):
        (root / d).mkdir(parents=True)
    SI.c_copy(b_root / "db" / "default.db", root / "db" / "default.db")
    for d in ("cache", "lib", "up"):
        shutil.copytree(b_root / d, root / d)


def store_counts(store) -> dict:
    con = sqlite3.connect(f"file:{pathlib.Path(store).as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    q = lambda sql, *a: [dict(r) for r in con.execute(sql, a)]  # noqa: E731
    try:
        return {"requests_by_lane_state": q("select lane, state, outcome, count(*) n from requests group by lane, state, outcome order by lane, state"),
                "serves_by_lane_mode": q("select lane, served_lane, mode, count(*) n from serves group by lane, served_lane, mode"),
                "duplicate_bound_keys": q("select bound_key, count(*) n from requests group by bound_key having n > 1"),
                "r_rows_served_to_c": q("select count(*) n from serves where lane = 'C' and served_lane != 'C'")[0]["n"],
                "b_or_c_served_from_p": q("select count(*) n from serves where lane in ('B', 'C') and served_lane = 'P'")[0]["n"],
                "reference_serves": q("select count(*) n from serves where lane = 'R' and mode = 'reference_from_capture'")[0]["n"],
                "rows": q("select count(*) n from requests")[0]["n"]}
    finally:
        con.close()


def execute(cfg: dict, truth: dict, run_set: list, out: pathlib.Path, sbx: pathlib.Path, *, stage_files=SI.STAGE_FILES,
            resume_drill_flag=False) -> dict:
    """Stages 1-6 for a prepared configuration (the preflight is main's). Returns the run report part."""
    report = {}
    truth_path = pathlib.Path(cfg["truth"])
    roots = {k: pathlib.Path(v) for k, v in cfg["sandbox"].items()}
    cfg_path = out / "RUN-CONFIG.json"
    cfg_path.write_text(json.dumps(cfg, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    mode = cfg["mode"]
    ctl = stop_rules.StopController()
    lanes = {}

    def replay(m):
        for e in m["events"]:
            if e["kind"] != "dry_refused":
                ctl.observe(e["lane"], e["kind"])
        for t in m["tripwire"]:
            for c in t["resolved"]:
                ctl.observe(m["lane"], "critical", resolved=True, detail=f"{c['pool_id']} p{c['page']} {c['field']}")
            if m["lane"] in ("B", "C"):
                for c in t["unresolved"]:
                    ctl.observe(m["lane"], "critical", resolved=False, detail=f"{c['pool_id']} p{c['page']} {c['field']}")

    ing = SI.ingest(roots["B"], [d["pool_id"] for d in run_set], truth, stage_files=stage_files)
    report["ingest"] = {k: ing[k] for k in ("ok", "documents", "projects", "registration", "state_check", "b_database_sha256")}
    if not ing["ok"]:
        raise Refused("refused: the B sandbox ingestion check failed")
    lanes["B"] = run_lane("B", cfg_path, out, lane_env(mode, roots["B"], "B", cfg), TREES["baseline"])
    replay(lanes["B"])
    b_db = roots["B"] / "db" / "default.db"
    report["b_database_sha256_final"] = state_check.file_sha256(b_db)
    report["after_B"] = ctl.state()
    if ctl.can_dispatch("C"):
        for lane in ("C", "R"):
            copy_b(roots["B"], roots[lane])
            sc = state_check.check_c_start(b_db, report["b_database_sha256_final"], roots[lane] / "db" / "default.db", C_MARKERS, EVIDENCE_TASKS)
            (out / f"STATE-CHECK-{lane}.json").write_text(json.dumps(sc, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
            report[f"state_check_{lane}"] = sc
            if not sc["ok"]:
                raise Refused(f"refused: {lane} does not start from the intended B state: {sc['problems']}")
            if lane == "C" or ctl.lanes["R"]["state"] == "running":
                lanes[lane] = run_lane(lane, cfg_path, out, lane_env(mode, roots[lane], lane, cfg), TREES["candidate"])
                replay(lanes[lane])
        lanes["P"] = run_lane("P", cfg_path, out, {**lane_env(mode, sbx / "P", "P", cfg), "DATABASE_URL": f"sqlite:///{(sbx / 'P' / 'no-db.sqlite').as_posix()}"},
                              TREES["candidate"])
    else:
        report["C_not_started"] = ctl.comparison
    report["store"] = store_counts(cfg["store"])
    if resume_drill_flag and mode == "dry" and "C" in lanes:
        report["resume_drill"] = resume_drill(cfg, out, sbx, roots, b_db, report["b_database_sha256_final"])
    # ---- 6. scoring (offline) ----------------------------------------------------------------------------------------
    n = {}
    own = lambda lane: sum(r["n"] for r in report["store"]["requests_by_lane_state"] if r["lane"] == lane)  # noqa: E731
    req = {"B": {"own_dispatched": own("B"), "inherited_from_b": 0}}
    for lane in ("C", "R"):
        req[lane] = {"own_dispatched": own(lane), "inherited_from_b": req["B"]["own_dispatched"]}
    rs_path = out / "RUN-SET-KEYS.json"
    rs_path.write_text(json.dumps(run_set, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    for lane in ("B", "C", "R"):
        if lane not in lanes:
            continue
        policy = "none" if lane == "B" else lanes[lane]["policy_version"]
        rq = out / f"requests-{lane}.json"
        rq.write_text(json.dumps({"requests": req[lane], "tokens": "dry run: no tokens" if mode == "dry" else "provider-reported usage in the capture store"}) + "\n",
                      encoding="utf-8", newline="\n")
        log = out / f"score-{lane}.log"
        with open(log, "w", encoding="utf-8") as fh:
            r = subprocess.run([PY, str(HERE / "score_lane_r32.py"), lane, str(out / f"rows-{lane}.json"), policy, str(truth_path), str(rs_path),
                                str(rq), str(out / f"lane-{lane}.r32.json")], cwd=TREES["candidate"],
                               env={**SI.sandbox_env(sbx / "score"), "PATH": DRY_PATH}, stdout=fh, stderr=subprocess.STDOUT)
        if r.returncode:
            raise RuntimeError(f"scoring {lane} failed; see {log}")
        n[lane] = json.loads((out / f"lane-{lane}.r32.json").read_text(encoding="utf-8"))
    if "B" in n and "C" in n:
        res = S.evaluate(n["B"], n["C"], n.get("R"), truth, caps={"B": CAPS["B"], "C": CAPS["C"]}, extensions_used=0, stop_state=ctl.state(),
                         docs={d["pool_id"] for d in run_set})
        if cfg.get("reader") == "none":
            res["exercise_only"] = ("dry run: no application reader ran on any document (reader 'none'); every lane has 0 facts; "
                                    "the figures exercise the scorer and are not a result")
        (out / "SCORE-BCR-R32.json").write_text(json.dumps(res, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        report["score_outcome_by_field"] = res["outcome_by_field"]
        report["comparison_state"] = res["comparison_state"]
        report["concentration_outcome_by_field"] = {f: v["outcome"] for f, v in res["concentration"]["fields"].items()}
    report["stop_controller"] = ctl.state()
    report["lanes"] = {k: {x: v.get(x) for x in ("reader", "seconds", "stats", "lane_stop_state", "model_requests", "allowance_used", "dry_stub_calls",
                                                 "live_provider_attempts_blocked", "policy_version", "stopped", "store_dispatched_to_inner",
                                                 "application_processing_run", "application_reader_run", "evidence_tasks")}
                       for k, v in lanes.items()}
    report["model_requests"] = sum(int(v.get("model_requests") or 0) for v in lanes.values())
    return report


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--mode", choices=("dry", "live"), required=True)
    a.add_argument("--stamp", required=True)
    a.add_argument("--run-set", required=True)
    a.add_argument("--binding", required=True)
    a.add_argument("--binding-sha", required=True)
    a.add_argument("--declaration")
    a.add_argument("--declaration-sha")
    a.add_argument("--auth-path", default=str(DG.AUTH_PATH))
    a.add_argument("--out")
    a.add_argument("--resume-drill", action="store_true", help="dry only: after C, re-run C on a copy of the capture with one request reset to RESERVED")
    args = a.parse_args(argv)
    out = pathlib.Path(args.out) if args.out else RUNS / args.stamp
    sbx = SANDBOX_BASE / args.stamp
    if out.exists() or sbx.exists():
        raise Refused("refused: a run never reuses its folders")
    out.mkdir(parents=True)
    sbx.mkdir(parents=True)
    lock = sbx / "WRITER.lock"
    fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    report = {"stamp": args.stamp, "mode": args.mode, "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              "ledger_before": ledger_state(), "model_requests": 0}
    try:
        report["binding"] = verify_binding(args.binding, args.binding_sha)
        decl_sha = None
        if args.mode == "live":
            if not args.declaration or not args.declaration_sha or sha256(args.declaration) != args.declaration_sha:
                raise Refused("refused: live mode needs the ORCH-07 declaration and its exact sha256")
            decl = json.loads(pathlib.Path(args.declaration).read_text(encoding="utf-8"))
            if decl.get("binding_manifest_sha256") != report["binding"]["sha256"] or decl.get("run_set_sha256") != sha256(args.run_set):
                raise Refused("refused: the declaration does not bind this binding manifest and this run set")
            decl_sha = args.declaration_sha
        report["declaration_sha256"] = decl_sha
        live_cfg = {"lane_switches": decl.get("lane_switches"), "provider_env": decl.get("provider_env")} if args.mode == "live" else {}
        report["dispatch_guard"] = DG.check(decl_sha, auth_path=args.auth_path)
        if args.mode == "live" and not report["dispatch_guard"]["authorized"]:
            raise Refused(report["dispatch_guard"]["reason"])
        report["heads"] = heads()
        x = I.load_all()
        truth = A.build_truth(x["reviewed2"], renders=x["renders"], source_manifest=x["source_manifest"], selection=x["selection"], verification=x["verification"])
        truth_path = out / "TRUTH-R32.json"
        truth_path.write_text(json.dumps(truth, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        report["truth_sha256"] = sha256(truth_path)
        gate = S.population_gate(truth, 0)
        report["population_gate"] = gate
        if gate["action"] != "DISPATCH_ELIGIBLE":
            raise Refused(f"stop: population gate {gate['action']} (no dispatch)")
        rs = json.loads(pathlib.Path(args.run_set).read_text(encoding="utf-8"))
        run_set = [{"pool_id": d["pool_id"], "doc_key": d["doc_key"], "ep": d["ep"]} for d in rs["documents"]]
        if len(run_set) > 30 or any(truth["documents"][d["pool_id"]]["is_alias"] for d in run_set) or \
                any(truth["documents"][d["pool_id"]]["doc_key"] != d["doc_key"] for d in run_set):
            raise Refused("refused: the run set is not canonical, not keyed by the reference set, or holds more than 30 documents")
        report["run_set"] = {"path": args.run_set, "sha256": sha256(args.run_set), "documents": len(run_set)}
        cfg = {"mode": args.mode, "reader": "none" if args.mode == "dry" else "application", "harness_dir": str(HERE), "out_dir": str(out),
               "truth": str(truth_path), "run_set": run_set, "store": str(sbx / "capture.sqlite"), "allowance": str(sbx / "allowance.sqlite"),
               "caps": CAPS, "trees": TREES, "sandbox": {k: str(sbx / k) for k in ("B", "C", "R")}, "declaration_sha256": decl_sha,
               "auth_path": args.auth_path, "policies": {"B": "B:accepted-path:evidence-off"}, **live_cfg}
        report |= execute(cfg, truth, run_set, out, sbx, resume_drill_flag=args.resume_drill)
    finally:
        report["ledger_after"] = ledger_state()
        report["ledger_unchanged"] = report["ledger_after"] == report["ledger_before"]
        report["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        (out / "RUN-REPORT.json").write_text(json.dumps(report, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        try:
            lock.unlink()
        except OSError:
            pass
    if not report["ledger_unchanged"]:
        raise RuntimeError("the AI ledger changed")
    print(json.dumps({k: report.get(k) for k in ("mode", "model_requests", "ledger_before", "ledger_after", "score_outcome_by_field", "comparison_state")}, default=str))
    return 0


def resume_drill(cfg, out, sbx, roots, b_db, b_sha) -> dict:
    """C again, on a fresh copy of B, against a COPY of the capture store and allowance with one C request reset to
    RESERVED (the process died after sending it): expected 0 new dispatches, the reserved row served once as
    'interrupted_charged', no row added, no charge refunded or added."""
    store2, allow2 = sbx / "capture-resume.sqlite", sbx / "allowance-resume.sqlite"
    shutil.copyfile(cfg["store"], store2)
    shutil.copyfile(cfg["allowance"], allow2)
    con = sqlite3.connect(str(store2))
    victim = con.execute("select seq, task from requests where lane = 'C' order by seq limit 1").fetchone()
    if victim is None:
        con.close()
        return {"skipped": "lane C made no request"}
    con.execute("update requests set state = 'reserved', answer = null, outcome = null, settled_at = null where seq = ?", (victim[0],))
    con.commit()
    before = con.execute("select count(*) from requests").fetchone()[0]
    con.close()
    c2 = sqlite3.connect(str(allow2))
    charges_before = c2.execute("select count(*) from charges").fetchone()[0]
    c2.close()
    root = sbx / "C-resume"
    copy_b(roots["B"], root)
    sc = state_check.check_c_start(b_db, b_sha, root / "db" / "default.db", C_MARKERS, EVIDENCE_TASKS)
    out2 = pathlib.Path(out) / "resume"
    out2.mkdir()
    cfg2 = dict(cfg, store=str(store2), allowance=str(allow2), out_dir=str(out2), sandbox=dict(cfg["sandbox"], C=str(root)))
    p2 = out2 / "RUN-CONFIG.json"
    p2.write_text(json.dumps(cfg2, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    lane = run_lane("C", p2, out2, lane_env("dry", root, "C", cfg), TREES["candidate"], tag="C-resume")
    con = sqlite3.connect(f"file:{store2.as_posix()}?mode=ro", uri=True)
    after = con.execute("select count(*) from requests").fetchone()[0]
    vstate = con.execute("select state from requests where seq = ?", (victim[0],)).fetchone()[0]
    serves = dict(con.execute("select mode, count(*) from serves where lane = 'C' group by mode").fetchall())
    con.close()
    c2 = sqlite3.connect(str(allow2))
    charges_after = c2.execute("select count(*) from charges").fetchone()[0]
    c2.close()
    interrupted = sum(1 for e in lane["events"] if e.get("error") == "interrupted_charged")
    return {"state_check": sc["ok"], "reset_to_reserved": {"seq": victim[0], "task": victim[1]}, "rows_before": before, "rows_after": after,
            "victim_state_after": vstate, "serves": serves, "interrupted_served": interrupted, "dry_stub_calls": lane.get("dry_stub_calls"),
            "allowance_charges_before": charges_before, "allowance_charges_after": charges_after,
            "passes": before == after and vstate == "reserved" and (lane.get("dry_stub_calls") or 0) == 0 and charges_after == charges_before
            and interrupted == 1}


if __name__ == "__main__":
    sys.exit(main())
