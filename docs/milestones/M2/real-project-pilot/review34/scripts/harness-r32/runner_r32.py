"""ORCH-05.1 (Review 33 C-5, R33-06) and ORCH-05C (Review 34 RC-3, RC-4, RC-5): the guarded runner of the r32 fresh
validation, lanes B, C, R and P (plan v2 section 4). It never imports the application: each lane is a subprocess
(lane_r32.py) in its own tree and sandbox.

  runner_r32.py run    --mode dry  --stamp S --run-set RS.json --binding BM.json --binding-sha SHA [--out DIR] [--dry-fault L:N]
  runner_r32.py resume --mode dry  --stamp S --run-set RS.json --binding BM.json --binding-sha SHA [--out DIR]
  runner_r32.py run    --mode live --declaration DECL.json --declaration-sha SHA --run-set RS.json --binding BM.json --binding-sha SHA
  runner_r32.py resume --mode live --declaration DECL.json --declaration-sha SHA --run-set RS.json --binding BM.json --binding-sha SHA
There is no --auth-path (RC-3): the authorization is pinned beside the declaration (dispatch_guard_r32).

ONE run folder per declaration (RC-4): C:/t/r2x/r34-sandbox/<stamp> (live: the declaration binds run.stamp and
run.folder; dry: the stamp names a dry run). It holds RUN-STATE.json, the ONE durable allowance (lane caps 240/240/40/36
and the project-day counter, 60 per project per UTC day across all lanes) and the ONE capture store, both bound to the run
key (live: the declaration sha256; dry: sha256 of the dry stamp, binding and run set), the consumed authorizations (live)
and one sub-folder per invocation (inv-<n>/: fresh sandboxes B, C, R, P and the scoring sandbox).
  run     the FIRST invocation: refused when the run folder exists ("a second fresh invocation is refused; use resume").
  resume  a later invocation of the SAME run (same stamp, key, binding and run set): it re-opens the same allowance and
          capture store (never fresh caps; caps and the day limit are bound in the allowance file), runs every lane again
          on NEW sandboxes, serves every bound fingerprint from the capture store (never re-sent), serves a reserved
          request without an answer as 'interrupted_charged', and dispatches only requests never made before. It is
          refused after a terminal comparison (RESULT: the candidate failed the safety gate; INVALID) and after a complete
          run. In live mode every invocation consumes a NEW owner authorization (a fresh nonce) for the same declaration.
Order (plan v2 section 4) after the preflight (binding; live: the declaration contract, ledger scope and the guard;
HEADs; population gate; run set): B (sandbox_ingest_r32 registers exactly the run set, no processing; lane B with the
tripwire after every document; B's database sha256 recorded) -> C and R from copies of B (state_check) -> C -> R (served
C's capture by content key) -> P (the probe) -> offline scoring (score_lane_r32, then score_bcr_r32 with the candidate-level
outcome). Stop rules: stop_rules.StopController (unchanged copy) replays every lane's events; B INVALID means C never starts.
Dry mode over the r32 cohort: reader 'none' -- no application reader touches a cohort document (that would be a
prediction); every other stage runs for real. Dry mode: no provider exists (DryRefusingProvider), no ledger path, PATH
without any CLI, 0 model requests; the AI ledger must read the same before and after (DRY ONLY). Live mode: the ledger
may grow only inside the declared scope and within the caps (preflight_r32.ledger_live_check).
Lane switches (RC-5): live mode uses only the declaration's lane_switches and provider_env (missing -> refused); dry mode
uses DRY_LANE_SWITCHES, labelled as dry defaults; each lane verifies its environment against them."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import allowance_r32 as AL  # noqa: E402
import dispatch_guard_r32 as DG  # noqa: E402
import inputs_r32 as I  # noqa: E402
import preflight_r32 as PF  # noqa: E402
import sandbox_ingest_r32 as SI  # noqa: E402
import score_bcr_r32 as S  # noqa: E402
import state_check  # noqa: E402
import stop_rules  # noqa: E402

SANDBOX_BASE = PF.SANDBOX_BASE
# sandbox_ingest_r32 is carried UNCHANGED by hash from review33 (its constant names C:/t/r2x/r33-sandbox); every r34 sandbox
# lives under C:/t/r2x/r34-sandbox, so the module's base is set here at run time (it is read when ingest() is called).
SI.SANDBOX_BASE = SANDBOX_BASE
PY = SI.PY
TREES = {"baseline": "C:/t/iso/frozen-r12/backend", "candidate": "C:/t/iso/cand-r29/backend"}
CAPS = dict(PF.PLAN_CAPS)
RUN_STATE = "RUN-STATE.json"
# DRY DEFAULTS ONLY (RC-5): the DRAFT-DECLARATION.v2 (review31) arms. Never used in live mode, where the declaration's
# lane_switches are required.
DRY_LANE_SWITCHES = {
    "B": {"AI_EVIDENCE_VARIANT": "off"},
    "C": {"AI_EVIDENCE_VARIANT": "EV1", "AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_SUPPORT": "v2", "AI_EVIDENCE_SCHEDULING": "required_first",
          "AI_EVIDENCE_DEADLINE": "1", "AI_EVIDENCE_TARGETED": "1", "AI_EVIDENCE_IDGUARD": "1", "AI_EVIDENCE_ADJUDICATE": "1",
          "AI_EVIDENCE_DECISION_REGION": "1", "AI_EVIDENCE_ASSOC": "1"},
    "R": {"AI_EVIDENCE_VARIANT": "EV1", "AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_SUPPORT": "v2", "AI_EVIDENCE_SCHEDULING": "required_first",
          "AI_EVIDENCE_DEADLINE": "1", "AI_EVIDENCE_TARGETED": "1"},
    "P": {},
}
C_MARKERS = SI.C_MARKERS
EVIDENCE_TASKS = ["discover_page", "discover_region", "locate_decision", "read_identity", "read_revision", "read_decision",
                  "read_field_context", "read_boq_row"]
DRY_PATH = "C:/Windows/system32;C:/Windows"
Refused = PF.Refused


def sha256(path) -> str:
    return I.sha256_file(path)


def _text(obj) -> str:
    return json.dumps(obj, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n"


def _write(path, obj):
    pathlib.Path(path).write_text(_text(obj), encoding="utf-8", newline="\n")


def ledger_state(path=I.AI_LEDGER) -> dict:
    """The real AI ledger, read-only (mode=ro, uri=True): the dry-mode 'unchanged' evidence."""
    c = PF.ledger_counts(path)
    return {k: c[k] for k in ("entries", "scopes", "limit_amendments")}


def lane_env(mode, root, lane, cfg) -> dict:
    """The lane's environment: the sandbox; EXACTLY the configured AI_EVIDENCE_* switches of the lane (no fallback); in
    live mode the declaration's provider environment; in dry mode no ledger path and a PATH without any CLI."""
    switches = (cfg.get("lane_switches") or {}).get(lane)
    if switches is None:
        raise Refused(f"refused: no switches for lane {lane} in the run configuration (no silent default)")
    env = SI.sandbox_env(pathlib.Path(root), ai_enabled=True)
    for k in [k for k in env if k.startswith("AI_EVIDENCE_")]:
        del env[k]
    env.update(switches)
    if mode == "dry":
        env["PATH"] = DRY_PATH
        env["AI_LEDGER_PATH"] = ""
    else:
        pe = cfg.get("provider_env")
        if not pe:
            raise Refused("refused: live mode without the declaration's provider environment (no silent default)")
        env.update(pe)
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
                "reserved_without_answer": q("select count(*) n from requests where state = 'reserved'")[0]["n"],
                "rows": q("select count(*) n from requests")[0]["n"]}
    finally:
        con.close()


def allowance_state(cfg) -> dict:
    a = AL.LaneAllowance(cfg["allowance"], cfg["caps"], cfg["project_day_limit"], run_key=cfg["run_key"], create=False)
    return {"caps_fixed": a.caps_fixed(), "used": {lane: a.used(lane) for lane in ("B", "C", "R", "P")}, "used_total": a.used(),
            "project_day_limit": a.project_day_limit, "run_key": cfg["run_key"]}


def execute(cfg: dict, truth: dict, run_set: list, out: pathlib.Path, sbx: pathlib.Path, *, stage_files=SI.STAGE_FILES) -> dict:
    """Stages 1-6 for a prepared configuration (the preflight and the run folder are main's). Returns the run report part.
    The run's allowance and capture store are opened (created on the first invocation) and bound to cfg['run_key']."""
    report = {}
    truth_path = pathlib.Path(cfg["truth"])
    roots = {k: pathlib.Path(v) for k, v in cfg["sandbox"].items()}
    AL.LaneAllowance(cfg["allowance"], cfg["caps"], cfg["project_day_limit"], run_key=cfg["run_key"], require_project=cfg["mode"] == "live")
    AL.bind_store(cfg["store"], cfg["run_key"])
    cfg_path = out / "RUN-CONFIG.json"
    _write(cfg_path, cfg)
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
            _write(out / f"STATE-CHECK-{lane}.json", sc)
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
    report["allowance"] = allowance_state(cfg)
    # ---- 6. scoring (offline) ----------------------------------------------------------------------------------------
    n = {}
    own = lambda lane: sum(r["n"] for r in report["store"]["requests_by_lane_state"] if r["lane"] == lane)  # noqa: E731
    req = {"B": {"own_dispatched": own("B"), "inherited_from_b": 0}}
    for lane in ("C", "R"):
        req[lane] = {"own_dispatched": own(lane), "inherited_from_b": req["B"]["own_dispatched"]}
    rs_path = out / "RUN-SET-KEYS.json"
    _write(rs_path, run_set)
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
                               env={k: val for k, val in {**SI.sandbox_env(sbx / "score"), "PATH": DRY_PATH}.items() if k != DG.TOKEN_ENV},
                               stdout=fh, stderr=subprocess.STDOUT)
        if r.returncode:
            raise RuntimeError(f"scoring {lane} failed; see {log}")
        n[lane] = json.loads((out / f"lane-{lane}.r32.json").read_text(encoding="utf-8"))
    if "B" in n and "C" in n:
        res = S.evaluate(n["B"], n["C"], n.get("R"), truth, caps={"B": cfg["caps"]["B"], "C": cfg["caps"]["C"]}, extensions_used=0, stop_state=ctl.state(),
                         docs={d["pool_id"] for d in run_set})
        if cfg.get("reader") == "none":
            res["exercise_only"] = ("dry run: no application reader ran on any document (reader 'none'); every lane has 0 facts; "
                                    "the figures exercise the scorer and are not a result")
        (out / "SCORE-BCR-R32.json").write_text(_text(res), encoding="utf-8", newline="\n")
        report["candidate_outcome"] = res["outcome"]
        report["score_outcome_by_field"] = res["outcome_by_field"]
        report["comparison_state"] = res["comparison_state"]
        report["concentration_outcome_by_field"] = {f: v["outcome"] for f, v in res["concentration"]["fields"].items()}
    report["stop_controller"] = ctl.state()
    report["lanes"] = {k: {x: v.get(x) for x in ("reader", "seconds", "stats", "lane_stop_state", "model_requests", "allowance_used", "dry_stub_calls",
                                                 "live_provider_attempts_blocked", "policy_version", "stopped", "store_dispatched_to_inner",
                                                 "application_processing_run", "application_reader_run", "evidence_tasks", "environment_check",
                                                 "switch_source", "serves_by_mode")}
                       for k, v in lanes.items()}
    report["model_requests"] = sum(int(v.get("model_requests") or 0) for v in lanes.values())
    return report


def _state_write(path: pathlib.Path, state: dict, *, exclusive=False):
    text = _text(state).encode("utf-8")
    if exclusive:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, text)
        os.close(fd)
        return
    tmp = path.with_suffix(".json.tmp")
    tmp.write_bytes(text)
    os.replace(tmp, path)


def resumable(last: dict) -> tuple[bool, str]:
    st, comp = last.get("status"), str(last.get("comparison_state") or "")
    if st in ("started", "interrupted", "refused"):
        return True, f"the last invocation is {st} (it never finished)"
    if st == "finished" and comp.startswith("INCOMPLETE"):
        return True, "the last invocation finished INCOMPLETE"
    if st == "finished" and (comp.startswith("RESULT") or comp.startswith("INVALID")):
        return False, f"refused: the comparison is terminal ({comp}); a terminal comparison is never resumed"
    if st == "finished":
        return False, "refused: the run is complete; there is nothing to resume"
    return False, f"refused: the last invocation has status {st!r}"


def parse(argv=None):
    a = argparse.ArgumentParser(prog="runner_r32.py", description="r32 guarded runner (ORCH-05C); there is no --auth-path")
    a.add_argument("command", choices=("run", "resume"))
    a.add_argument("--mode", choices=("dry", "live"), required=True)
    a.add_argument("--run-set", required=True)
    a.add_argument("--binding", required=True)
    a.add_argument("--binding-sha", required=True)
    a.add_argument("--declaration")
    a.add_argument("--declaration-sha")
    a.add_argument("--stamp", help="dry: the dry run's stamp; live: optional, must equal the declaration's run.stamp")
    a.add_argument("--out", help="this invocation's output folder (new); default <run folder>/inv-<n>/out")
    a.add_argument("--dry-fault", help="dry drill only: LANE:N -- the lane process dies right after its N-th dispatch was sent "
                                       "(the row stays reserved and charged), as a crash would leave it")
    return a.parse_args(argv)


def main(argv=None) -> int:
    args = parse(argv)
    live = args.mode == "live"
    if live and args.dry_fault:
        raise Refused("refused: --dry-fault is a dry-mode drill only")
    if not live and (args.declaration or args.declaration_sha):
        raise Refused("refused: dry mode takes no declaration (a declaration is the live contract)")
    started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    # ---- 0. preflight: nothing is created before every check has passed ----------------------------------------------
    binding = PF.verify_binding(args.binding, args.binding_sha)
    rs_sha = sha256(args.run_set)
    if live:
        decl, v = PF.load_declaration(args.declaration, args.declaration_sha, binding_sha=binding["sha256"], run_set_sha=rs_sha)
        if args.stamp and args.stamp != v["stamp"]:
            raise Refused(f"refused: the stamp is the declaration's ({v['stamp']}), not {args.stamp}")
        stamp, run_folder, run_key = v["stamp"], pathlib.Path(v["run_folder"]), args.declaration_sha
        caps, day_limit, switches, provider_env = v["caps"], v["project_day_limit"], v["lane_switches"], v["provider_env"]
    else:
        if not args.stamp:
            raise Refused("refused: dry mode needs --stamp")
        stamp, run_folder = args.stamp, PF.run_folder_of(args.stamp)
        run_key = hashlib.sha256(f"r34-dry-run|{stamp}|{binding['sha256']}|{rs_sha}".encode("utf-8")).hexdigest()
        caps, day_limit, switches, provider_env, v = dict(CAPS), PF.PLAN_PROJECT_DAY_LIMIT, DRY_LANE_SWITCHES, None, None
    hd = PF.heads()
    truth = PF.build_truth()
    gate = PF.population(truth)
    run_set = PF.load_run_set(args.run_set, truth)
    scope = PF.verify_ledger_scope(v["ledger"]) if live else None
    state_path = run_folder / RUN_STATE
    if args.command == "run":
        if run_folder.exists():
            raise Refused(f"refused: a second fresh invocation of this run is refused ({run_folder.as_posix()} exists); use 'resume'")
        n, state, kind = 1, None, "fresh"
    else:
        if not state_path.is_file():
            raise Refused(f"refused: nothing to resume ({state_path.as_posix()} does not exist)")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        want = {"run_key": run_key, "mode": args.mode, "stamp": stamp, "binding_sha256": binding["sha256"], "run_set_sha256": rs_sha,
                "caps": caps, "project_day_limit": day_limit}
        diff = [k for k, w in want.items() if state.get(k) != w]
        if diff:
            raise Refused(f"refused: resume must be the same run (same stamp, key, binding, run set, caps and day limit); differs in {diff}")
        for f in ("allowance.sqlite", "capture.sqlite"):
            if not (run_folder / f).is_file():
                raise Refused(f"refused: the run's {f} is missing; a resume never re-creates it")
        if AL.bound_key(run_folder / "capture.sqlite") != run_key:
            raise Refused("refused: the capture store is bound to another run")
        ok, why = resumable(state["invocations"][-1])
        if not ok:
            raise Refused(why)
        n, kind = len(state["invocations"]) + 1, "resume"
    guard = DG.check(args.declaration, args.declaration_sha, run_folder=run_folder, invocation=n, action="preview", stamp=stamp, kind=kind) if live else \
        {"authorized": False, "reason": "dry mode: no declaration, no provider; the dry stub refuses every request"}
    if live and not guard["authorized"]:
        raise Refused(guard["reason"])
    # ---- the run folder: created by the first invocation, re-opened by a resume -----------------------------------------
    if args.command == "run":
        run_folder.mkdir(parents=True)
        state = {"schema": "r34-run-state-1", "run_key": run_key, "mode": args.mode, "stamp": stamp, "run_folder": run_folder.as_posix(),
                 "declaration_sha256": args.declaration_sha if live else None, "binding_sha256": binding["sha256"], "run_set_sha256": rs_sha,
                 "caps": caps, "project_day_limit": day_limit, "created_utc": started, "invocations": [],
                 "rule": "one run folder, allowance and capture store per run key; 'run' once, then only 'resume'"}
        _state_write(state_path, state, exclusive=True)
    lock = run_folder / "WRITER.lock"
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise Refused("refused: another writer holds this run (WRITER.lock); after a crash the operator removes it once no runner is alive") from exc
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    out = pathlib.Path(args.out) if args.out else run_folder / f"inv-{n}" / "out"
    report = {"stamp": stamp, "mode": args.mode, "command": args.command, "invocation": n, "kind": kind, "started_utc": started,
              "run_folder": run_folder.as_posix(), "run_key": run_key, "declaration_sha256": args.declaration_sha if live else None,
              "binding": binding, "heads": hd, "population_gate": gate, "dispatch_guard": guard, "ledger_scope": scope, "model_requests": 0,
              "ledger_rule": "dry: the AI ledger must read the same before and after; live: growth only inside the declared scope, within the caps"}
    report["ledger_before"] = ledger_state() if not live else None
    snap_before = PF.ledger_snapshot(v["ledger"]["path"]) if live else None
    inv = {"n": n, "kind": kind, "started_utc": started, "status": "started", "out": out.as_posix()}
    status = "interrupted"
    try:
        if out.exists():
            raise Refused(f"refused: {out} exists (an invocation never reuses its output folder)")
        out.mkdir(parents=True)
        if live:
            auth = DG.authorize(args.declaration, args.declaration_sha, run_folder=run_folder, invocation=n, action="consume", stamp=stamp, kind=kind)
            report["authorization"] = auth
            inv["authorization_sha256"] = auth["authorization_sha256"]
        state["invocations"].append(inv)
        _state_write(state_path, state)
        truth_path = out / "TRUTH-R32.json"
        truth_path.write_text(PF.truth_text(truth), encoding="utf-8", newline="\n")
        report["truth_sha256"] = sha256(truth_path)
        report["run_set"] = {"path": str(args.run_set), "sha256": rs_sha, "documents": len(run_set)}
        sbx = run_folder / f"inv-{n}"
        cfg = {"mode": args.mode, "reader": "none" if not live else "application", "harness_dir": str(HERE), "out_dir": str(out),
               "truth": str(truth_path), "run_set": run_set, "run_set_path": str(args.run_set), "run_folder": run_folder.as_posix(), "run_key": run_key,
               "stamp": stamp, "invocation": n, "store": (run_folder / "capture.sqlite").as_posix(), "allowance": (run_folder / "allowance.sqlite").as_posix(),
               "caps": caps, "project_day_limit": day_limit, "trees": TREES, "sandbox": {k: str(sbx / k) for k in ("B", "C", "R")},
               "binding": str(args.binding), "binding_sha256": binding["sha256"], "declaration_path": args.declaration if live else None,
               "declaration_sha256": args.declaration_sha if live else None, "lane_switches": switches, "provider_env": provider_env,
               "switch_source": "the declaration's lane_switches" if live else PF.DRY_LANE_SWITCHES_LABEL,
               "policies": {"B": "B:accepted-path:evidence-off"}}
        if args.dry_fault:
            lane_f, _, nf = args.dry_fault.partition(":")
            cfg["dry_fault"] = {"lane": lane_f, "after_dispatches": int(nf)}
        report |= execute(cfg, truth, run_set, out, sbx)
        status = "finished"
    except Refused as exc:
        status = "refused"
        report["refused"] = str(exc)
        raise
    except BaseException as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if live:
            report["ledger_live_check"] = PF.ledger_live_check(snap_before, PF.ledger_snapshot(v["ledger"]["path"]), v["ledger"], caps)
        else:
            report["ledger_after"] = ledger_state()
            report["ledger_unchanged"] = report["ledger_after"] == report["ledger_before"]
        report["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        report["status"] = status
        inv.update({"status": status, "finished_utc": report["finished_utc"], "comparison_state": report.get("comparison_state"),
                    "outcome": report.get("candidate_outcome")})
        if inv not in state["invocations"]:
            state["invocations"].append(inv)
        _state_write(state_path, state)
        dest = out if out.exists() else run_folder / f"inv-{n}"
        dest.mkdir(parents=True, exist_ok=True)
        _write(dest / "RUN-REPORT.json", report)
        try:
            lock.unlink()
        except OSError:
            pass
    if not live and not report["ledger_unchanged"]:
        raise RuntimeError("the AI ledger changed (dry mode)")
    if live and not report["ledger_live_check"]["ok"]:
        raise RuntimeError(f"the AI ledger changed outside the declared scope or caps: {report['ledger_live_check']['problems']}")
    print(json.dumps({k: report.get(k) for k in ("mode", "command", "invocation", "status", "model_requests", "ledger_before", "ledger_after",
                                                 "candidate_outcome", "score_outcome_by_field", "comparison_state")}, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
