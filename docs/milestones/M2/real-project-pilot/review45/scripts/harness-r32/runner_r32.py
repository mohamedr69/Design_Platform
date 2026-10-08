"""ORCH-05.1 / ORCH-05C / ORCH-08: the guarded runner of the r32 fresh validation, lanes B, C, R and P (plan v2 section
4). It never imports the application: each lane is a subprocess (lane_r32.py) in its own tree and sandbox.

  runner_r32.py run    --mode dry  --stamp S --run-set RS.json --binding BM.json --binding-sha SHA [--sandbox-base D]
                       [--out DIR] [--dry-fault L:N] [--dry-inject INJECT.json] [--dry-synthetic SPEC.json]
  runner_r32.py resume --mode dry  (the same arguments as the run)
  runner_r32.py run    --mode dry  --dry-baseline-facts SPEC.json --stamp S --run-set RS.json --binding BM.json --binding-sha SHA
                       [--sandbox-base D]   (R43-42, review45: lane B on frozen-r13, F009 / F020 / F030 only; drill_r45.py)
  runner_r32.py run    --mode live --declaration DECL.json --declaration-sha SHA --run-set RS.json --binding BM.json --binding-sha SHA
  runner_r32.py resume --mode live (the same arguments)
There is no --auth-path (RC-3): the authorization is pinned beside the declaration (dispatch_guard_r32).

ONE run folder per declaration (RC-4): <sandbox base>/<stamp> -- live: the declaration binds run.sandbox_base, run.stamp
and run.folder; dry: --sandbox-base / R38_SANDBOX_BASE / C:/t/r2x/r42-sandbox (ORCH-10). It holds RUN-STATE.json, the ONE durable
allowance (allowance_r32: parent budget, lane allowances, project window, charges, refusals, durable stops), the ONE
capture store, the identity records (CLI-VERSIONS.jsonl, IDENTITY-INVALID.json when a mismatch happened), the consumed
authorizations (live) and one sub-folder per invocation (inv-<n>/: fresh sandboxes B, C, R, P, the scoring sandbox,
PROVIDER-IDENTITY.json and the identity logs, and out/ with ALLOWANCE-AUDIT.json and RUN-REPORT.json).
  run     the FIRST invocation: refused when the run folder exists.
  resume  a later invocation of the SAME run. Every bound ANSWER is SERVED from the capture store (never re-sent); a
          reserved request without an answer is served 'interrupted_charged'; a request whose dispatches all FAILED is
          dispatched again as a retry with its ordinal (ORCH-08C, R39-16: charged); requests never made before are
          dispatched. No allowance, charge, refusal or terminal stop is ever reset. Refused after a terminal comparison
          (RESULT; INVALID -- a model identity mismatch or, ORCH-08C, a contract breach) and after a complete run; refused
          while a DEFERRED run's declared resume_policy time has not come (ORCH-08C, R39-08: 'full' = the structural
          retry_at_full, 'earliest' = the first freed slot; nothing is created); after the elapsed bound a deferred run is
          CLOSED INCOMPLETE (recorded in RUN-STATE.json, deferred documents listed) and nothing is dispatched.
Lane order (ORCH-08 gating, every gate recorded in the report): B; C only when no B document is DEFERRED; R and P only
when no C document is DEFERRED (R is served C's capture, P samples C's answered rows: both need C's complete capture);
a lane that cannot start records every one of its documents as DEFERRED ('waiting') -- never silently absent.
Preflight before anything is created (live): binding; the declaration contract (since ORCH-10 contract 5: parent budget,
lane allowances, project window, request bounds and compatible limits, pinned model identity; ORCH-08C: application_env,
lane_task_kinds, resume_policy, decision_coverage_gate; ORCH-10: interpreter, disk_precondition, isolation,
resume_authorization, global_provider); HEADs; population gate; run set; bounds recomputed; ledger scope; guard preview.
The ORDER of an invocation since ORCH-10 is given at the end of this docstring (the version check, the capture store and
the allowance all precede the consumption of the authorization).
Dry mode: no provider exists (run_control_r38.DryStub), no ledger path (a FAKE ledger only with --dry-inject's
dry_ledger, inside the run folder), PATH without any CLI, 0 model requests; the AI ledger must read the same before and
after. Dry-only drills: --dry-fault L:N (lane L dies after its N-th response, before saving it), --dry-inject (timeouts,
an identity mismatch, interruptions, unsaved responses, ledger usage; small caps / window / parent / application limits),
--dry-synthetic (the application readers on SYNTHETIC EP-990001 documents only). ORCH-08C dry drills: undeclared and
context-free requests, an evidence-reader exception, and a resume_policy in the --dry-inject file.

ORCH-10 (R42; Verification 41 R41-09, R41-10, R41-11; contract 5). The order of an invocation is now:
  1. every check, with NOTHING created, re-opened or consumed: the binding; (live) the declaration contract 5, the bound
     interpreter, the pinned CLI FILE's sha256 (read as bytes); the free space of the sandbox base's drive (>= the declared
     floor, 2 GiB; dry mode the same floor); the HEADs; the truth and population gate; the run set; (live) the bounds and
     the ledger scope; 'run' on an existing folder only through reentry_proof (below), 'resume' through the existing
     resume rules; then `claude --version` and its comparison with the pin and the run's first recorded line
     (check_version); then the guard preview;
  2. the run folder (invocation 1) / re-entry / re-opening, RUN-STATE.json, the WRITER lock, the output folder, the
     version and provider-identity record;
  3. the capture store bound to the run key, then the ONE allowance created atomically (built aside and renamed into place
     only once bound; a resume opens the existing one and never re-creates it);
  4. (live) ONLY THEN the authorization nonce is consumed (O_EXCL record), so a failure in steps 2-3 consumes no
     authorization and charges nothing;
  5. the lanes, the audit, the scoring.
A failure after the folder exists but before the allowance exists leaves a folder that 'run' may RE-ENTER: reentry_proof
requires, from the folder's own records, that no allowance was ever created (allowance.sqlite absent), no nonce was
consumed (no consumption record) and no request was charged (no capture-store request); it writes REENTRY-<n>.json, and
the re-entry is a new invocation number (nothing existing is reset or re-created; a partial allowance file from an
interrupted creation is kept aside, never used). With an allowance present 'run' is refused ('use resume'); a resume
re-checks the CLI file, the version line and the free disk before it consumes its nonce (R41-11). Every earlier refusal
stays: a second 'run' with an allowance, a resume without an allowance, WRITER.lock, an identity mismatch (INVALID)."""
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
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import allowance_r32 as AL  # noqa: E402
import dispatch_guard_r32 as DG  # noqa: E402
import inputs_r32 as I  # noqa: E402
import model_identity_r38 as MI  # noqa: E402
import preflight_r32 as PF  # noqa: E402
import run_state_r38 as RC  # noqa: E402  (the application-free half of the lane control: the runner never imports the application)
import sandbox_ingest_r32 as SI  # noqa: E402
import score_bcr_r32 as S  # noqa: E402
import state_check  # noqa: E402

SANDBOX_BASE = PF.SANDBOX_BASE
# sandbox_ingest_r32 is carried UNCHANGED by hash from review33 (its constant names C:/t/r2x/r33-sandbox); the runner sets
# the module's base to the run's sandbox base before every ingestion (it is read when ingest() is called).
SI.SANDBOX_BASE = SANDBOX_BASE
PY = SI.PY
TREES = {"baseline": "C:/t/iso/frozen-r13/backend", "candidate": "C:/t/iso/cand-r30n/backend"}
CAPS = dict(PF.PLAN_CAPS)
PARENT = dict(AL.PARENT)
WINDOW = dict(AL.PROJECT_WINDOW)
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
DRY_PINS = {"provider": MI.PROVIDER, "small": MI.PINNED["small"], "standard": MI.PINNED["standard"], "cli_path": None, "cli_version": None}
DRY_CLI_VERSION = "dry mode: no CLI is run"
C_MARKERS = SI.C_MARKERS
EVIDENCE_TASKS = ["discover_page", "discover_region", "locate_decision", "read_identity", "read_revision", "read_decision",
                  "read_field_context", "read_boq_row"]
DRY_PATH = "C:/Windows/system32;C:/Windows"
INJECTION_KINDS = ("provider_timeout", "identity_mismatch", "interrupted", "unsaved", "usage",
                   "undeclared_request", "context_free_request", "reader_exception",    # ORCH-08C drills (dry only)
                   "global_provider_request")                                          # ORCH-10 drill (R40-04, dry only)
Refused = PF.Refused


def sha256(path) -> str:
    return I.sha256_file(path)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _utc(ts):
    return None if ts is None else datetime.datetime.fromtimestamp(float(ts), datetime.timezone.utc).isoformat(timespec="seconds")


def _text(obj) -> str:
    return json.dumps(obj, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n"


def _write(path, obj):
    pathlib.Path(path).write_text(_text(obj), encoding="utf-8", newline="\n")


def ledger_state(path=I.AI_LEDGER) -> dict:
    """The real AI ledger, read-only (mode=ro, uri=True): the dry-mode 'unchanged' evidence."""
    c = PF.ledger_counts(path)
    return {k: c[k] for k in ("entries", "scopes", "limit_amendments")}


def lane_env(mode, root, lane, cfg) -> dict:
    """The lane's environment: the sandbox; EXACTLY the configured AI_EVIDENCE_* switches of the lane (no fallback); the
    declared application environment (ORCH-08C: DRAWINGS_AI_REVIEW_ENABLED=false; live: the declaration's, dry: the
    harness allowlist; the lane verifies it again); in live mode the declaration's provider environment; in dry mode no
    ledger path and a PATH without any CLI."""
    switches = (cfg.get("lane_switches") or {}).get(lane)
    if switches is None:
        raise Refused(f"refused: no switches for lane {lane} in the run configuration (no silent default)")
    app_env = cfg.get("application_env")
    if app_env is None:
        raise Refused("refused: no application environment in the run configuration (no silent default)")
    PF.validate_application_env(app_env)
    env = SI.sandbox_env(pathlib.Path(root), ai_enabled=True)
    for k in [k for k in env if k.startswith("AI_EVIDENCE_")]:
        del env[k]
    env.update(switches)
    env.update(app_env)
    if mode == "dry":
        env["PATH"] = DRY_PATH
        env["AI_LEDGER_PATH"] = ""
        env.update(cfg.get("dry_application_limits") or {})     # dry drill only: lower application limits to show they are visible
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
        has_releases = bool(q("select count(*) n from sqlite_master where name = 'releases'")[0]["n"])
        has_retries = bool(q("select count(*) n from sqlite_master where name = 'retries'")[0]["n"])
        return {"requests_by_lane_state": q("select lane, state, outcome, count(*) n from requests group by lane, state, outcome order by lane, state"),
                "serves_by_lane_mode": q("select lane, served_lane, mode, count(*) n from serves group by lane, served_lane, mode"),
                "duplicate_bound_keys": q("select bound_key, count(*) n from requests group by bound_key having n > 1"),
                "r_rows_served_to_c": q("select count(*) n from serves where lane = 'C' and served_lane != 'C'")[0]["n"],
                "b_or_c_served_from_p": q("select count(*) n from serves where lane in ('B', 'C') and served_lane = 'P'")[0]["n"],
                "reference_serves": q("select count(*) n from serves where lane = 'R' and mode = 'reference_from_capture'")[0]["n"],
                "reserved_without_answer": q("select count(*) n from requests where state = 'reserved'")[0]["n"],
                "releases": q("select lane, reason, count(*) n from releases group by lane, reason") if has_releases else [],
                "retries": q("select lane, ordinal, previous_outcome, count(*) n from retries group by lane, ordinal, previous_outcome")
                if has_retries else [],
                "rows": q("select count(*) n from requests")[0]["n"]}
    finally:
        con.close()


def open_allowance(cfg, *, create=False) -> AL.LaneAllowance:
    return AL.LaneAllowance(cfg["allowance"], cfg["caps"], cfg["project_window"], parent=cfg["parent"], run_key=cfg["run_key"],
                            require_project=cfg["mode"] == "live", create=create, project_totals=cfg.get("project_totals"))


def project_totals_of(bounds: dict | None) -> dict | None:
    """{project: {'planning': all-lane planning estimate, 'structural': all-lane structural maximum}} from
    PROJECT-REQUEST-BOUNDS content (ORCH-08C, R39-08: the basis of a deferral's retry_at_full)."""
    if not bounds:
        return None
    return {p: {"planning": v["planning"]["all_lanes"], "structural": v["structural_maximum"]["all_lanes"]} for p, v in bounds["projects"].items()}


def resume_times(documents: dict, earliest) -> dict:
    """The run-level retry times of a DEFERRED invocation (ORCH-08C, R39-08): 'earliest' = the first freed slot over the
    deferred documents; 'full' = the LATEST structural-basis retry_at_full over them (the time at which every deferred
    project's remaining structural maximum fits the window, or its window is empty), else the earliest; the planning
    basis is reported beside it."""
    fulls = {"planning": [], "structural": []}
    for docs in (documents or {}).values():
        for v in (docs or {}).values():
            if v.get("status") == "DEFERRED" and v.get("retry_at_full"):
                for b in fulls:
                    if v["retry_at_full"].get(b) is not None:
                        fulls[b].append(float(v["retry_at_full"][b]))
    full = {b: (max(t) if t else earliest) for b, t in fulls.items()}
    return {"earliest": earliest, "full": full["structural"], "full_planning": full["planning"], "full_structural": full["structural"]}


def run_invalid(run_folder) -> str | None:
    """Why the run is INVALID (a model identity mismatch, A-09 point 2; a contract breach, ORCH-08C R39-04), or None."""
    m = MI.invalid_marker(run_folder)
    if m is not None:
        return f"model identity mismatch ({m.get('lane')})"
    b = RC.breach_marker(run_folder)
    if b is not None:
        return f"contract breach ({b.get('lane')}: {b.get('kind')}, task {b.get('task')!r})"
    return None


def allowance_state(cfg) -> dict:
    a = open_allowance(cfg)
    return {"caps_fixed": a.caps_fixed(), "used": {lane: a.used(lane) for lane in ("B", "C", "R", "P")}, "used_total": a.used(),
            "parent": a.parent, "project_window": a.window, "elapsed_bound_ends_utc": _utc(a.bound_end()), "stops": a.stops(), "run_key": cfg["run_key"]}


def _waiting(run_set, lane, blocker, retry_at):
    """A lane that cannot start: every document DEFERRED ('waiting' for the blocking lane), with the blocker's retry time."""
    return {d["pool_id"]: {"status": "DEFERRED", "reason": f"waiting: lane {lane} starts only when no {blocker} document is DEFERRED",
                           "retry_at": retry_at, "retry_at_utc": _utc(retry_at), "classes": ["limit"], "events": 0, "kinds": ["waiting"],
                           "pages": {"*": ["waiting"]}} for d in run_set}


def _not_started(run_set, lane, why):
    """A lane that will not start in this run (a terminal comparison or a stopped lane): every document INCOMPLETE, with why."""
    return {d["pool_id"]: {"status": "INCOMPLETE", "reason": f"lane {lane} not started: {why}", "retry_at": None, "retry_at_utc": None,
                           "classes": ["limit"], "events": 0, "kinds": ["not_started"], "pages": {"*": ["not_started"]}} for d in run_set}


def _deferred(docs: dict) -> dict:
    return {pid: v["retry_at"] for pid, v in (docs or {}).items() if v.get("status") == "DEFERRED"}


def execute(cfg: dict, truth: dict, run_set: list, out: pathlib.Path, sbx: pathlib.Path, *, stage_files=SI.STAGE_FILES) -> dict:
    """Stages 1-6 for a prepared configuration (the preflight and the run folder are main's). Returns the run report part.
    The run's allowance and capture store are opened (created on the first invocation) and bound to cfg['run_key']."""
    report = {}
    truth_path = pathlib.Path(cfg["truth"])
    roots = {k: pathlib.Path(v) for k, v in cfg["sandbox"].items()}
    allowance = open_allowance(cfg)                    # ORCH-10: created atomically by main() before any authorization was consumed
    if AL.bound_key(cfg["store"]) != cfg["run_key"]:
        raise Refused("refused: the capture store is not bound to this run")
    cfg_path = out / "RUN-CONFIG.json"
    _write(cfg_path, cfg)
    mode = cfg["mode"]
    ctl = RC.ControllerR38()
    lanes, documents, gates = {}, {}, {}

    def replay(m):
        for e in m["events"]:
            if e["kind"] != "dry_refused":
                ctl.observe(e["lane"], e["kind"], detail=e.get("error"))
        for t in m["tripwire"]:
            for c in t["resolved"]:
                ctl.observe(m["lane"], "critical", resolved=True, detail=f"{c['pool_id']} p{c['page']} {c['field']}")
            if m["lane"] in ("B", "C"):
                for c in t["unresolved"]:
                    ctl.observe(m["lane"], "critical", resolved=False, detail=f"{c['pool_id']} p{c['page']} {c['field']}")

    SI.SANDBOX_BASE = pathlib.Path(cfg["sandbox_base"])
    ing = SI.ingest(roots["B"], [d["pool_id"] for d in run_set], truth, stage_files=stage_files)
    report["ingest"] = {k: ing[k] for k in ("ok", "documents", "projects", "registration", "state_check", "b_database_sha256")}
    if not ing["ok"]:
        raise Refused("refused: the B sandbox ingestion check failed")
    lanes["B"] = run_lane("B", cfg_path, out, lane_env(mode, roots["B"], "B", cfg), TREES["baseline"])
    replay(lanes["B"])
    documents["B"] = lanes["B"]["documents"]
    b_db = roots["B"] / "db" / "default.db"
    report["b_database_sha256_final"] = state_check.file_sha256(b_db)
    report["after_B"] = ctl.state()
    b_def = _deferred(documents["B"])
    invalid = run_invalid(cfg["run_folder"]) is not None
    if b_def:
        first = min(b_def.values())
        for lane in ("C", "R", "P"):
            documents[lane] = _waiting(run_set, lane, "B", first)
        gates = {lane: f"not started: {len(b_def)} B document(s) DEFERRED (earliest retry {_utc(first)})" for lane in ("C", "R", "P")}
    elif ctl.can_dispatch("C") and not invalid:
        for lane in ("C", "R"):
            copy_b(roots["B"], roots[lane])
            sc = state_check.check_c_start(b_db, report["b_database_sha256_final"], roots[lane] / "db" / "default.db", C_MARKERS, EVIDENCE_TASKS)
            _write(out / f"STATE-CHECK-{lane}.json", sc)
            report[f"state_check_{lane}"] = sc
            if not sc["ok"]:
                raise Refused(f"refused: {lane} does not start from the intended B state: {sc['problems']}")
            if lane == "C":
                lanes["C"] = run_lane("C", cfg_path, out, lane_env(mode, roots["C"], "C", cfg), TREES["candidate"])
                replay(lanes["C"])
                documents["C"] = lanes["C"]["documents"]
                c_def = _deferred(documents["C"])
                if c_def or run_invalid(cfg["run_folder"]) is not None:
                    break
            elif ctl.lanes["R"]["state"] == "running":
                lanes["R"] = run_lane("R", cfg_path, out, lane_env(mode, roots["R"], "R", cfg), TREES["candidate"])
                replay(lanes["R"])
                documents["R"] = lanes["R"]["documents"]
            else:
                gates["R"] = f"not started: lane R is {ctl.lanes['R']['state']} ({ctl.lanes['R']['reason']})"
                documents["R"] = _not_started(run_set, "R", f"lane R is {ctl.lanes['R']['state']}")
        c_def = _deferred(documents.get("C"))
        if c_def:
            first = min(c_def.values())
            for lane in ("R", "P"):
                documents[lane] = _waiting(run_set, lane, "C", first) if lane == "R" else {}
                gates[lane] = f"not started: {len(c_def)} C document(s) DEFERRED (earliest retry {_utc(first)})"
        elif run_invalid(cfg["run_folder"]) is not None:
            why = f"the run is INVALID ({run_invalid(cfg['run_folder'])})"
            gates |= {lane: f"not started: {why}" for lane in ("R", "P") if lane not in lanes}
            if "R" not in lanes:
                documents["R"] = _not_started(run_set, "R", why)
        else:
            lanes["P"] = run_lane("P", cfg_path, out, {**lane_env(mode, sbx / "P", "P", cfg), "DATABASE_URL": f"sqlite:///{(sbx / 'P' / 'no-db.sqlite').as_posix()}"},
                                  TREES["candidate"])
            replay(lanes["P"])
    else:
        report["C_not_started"] = ctl.comparison if not invalid else f"INVALID: {run_invalid(cfg['run_folder'])}"
        gates = {lane: f"not started: {report['C_not_started']}" for lane in ("C", "R", "P")}
        for lane in ("C", "R"):
            documents[lane] = _not_started(run_set, lane, report["C_not_started"])
    report["lane_gates"] = gates
    report["store"] = store_counts(cfg["store"])
    report["allowance"] = allowance_state(cfg)
    audit = allowance.audit(*((cfg["ledger"]["path"], cfg["ledger"]["scope"]) if mode == "live" else
                              ((cfg["dry_ledger"]["path"], cfg["dry_ledger"]["scope"]) if cfg.get("dry_ledger") else (None, None))))
    _write(out / "ALLOWANCE-AUDIT.json", audit)
    report["allowance_audit"] = {"path": (out / "ALLOWANCE-AUDIT.json").as_posix(), "total_charged": audit["total_charged"],
                                 "refusals": len(audit["refusals"]), "stops": audit["stops"], "reconciliation": audit["reconciliation"]}
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
                                str(rq), str(out / f"lane-{lane}.r32.json"), str(out / f"LANE-{lane}.json")], cwd=TREES["candidate"],
                               env={k: val for k, val in {**SI.sandbox_env(sbx / "score"), "PATH": DRY_PATH}.items() if k != DG.TOKEN_ENV},
                               stdout=fh, stderr=subprocess.STDOUT)
        if r.returncode:
            raise RuntimeError(f"scoring {lane} failed; see {log}")
        n[lane] = json.loads((out / f"lane-{lane}.r32.json").read_text(encoding="utf-8"))
    report["documents"] = documents
    report["run_set_keys"] = run_set
    deferred = {lane: _deferred(docs) for lane, docs in documents.items() if _deferred(docs)}
    retries = [t for d in deferred.values() for t in d.values() if t is not None]
    report["deferred"] = {lane: {pid: _utc(t) for pid, t in d.items()} for lane, d in deferred.items()}
    report["earliest_retry_utc"] = _utc(min(retries)) if retries else None
    report["earliest_retry"] = min(retries) if retries else None
    if retries:
        rt = resume_times(documents, min(retries))
        report["retry_at_earliest"], report["retry_at_earliest_utc"] = rt["earliest"], _utc(rt["earliest"])
        report["retry_at_full"] = {"structural": rt["full_structural"], "planning": rt["full_planning"]}
        report["retry_at_full_utc"] = {k: _utc(v) for k, v in report["retry_at_full"].items()}
        report["resume_policy"] = cfg["resume_policy"]
        report["resume_not_before"] = rt["full"] if cfg["resume_policy"] == "full" else rt["earliest"]
        if report["resume_not_before"] > allowance.bound_end():
            report["resume_not_before"] = rt["earliest"]
            report["resume_policy_note"] = "the full-policy time is after the elapsed bound: the resume falls back to the earliest retry"
        report["resume_not_before_utc"] = _utc(report["resume_not_before"])
    report["unread_pages"] = {lane: {pid: {"unread_pages": d.get("unread_pages"), "unread_page_count": d.get("unread_page_count"),
                                           "status": d.get("status")} for pid, d in (docs or {}).items() if d.get("unread_pages")}
                              for lane, docs in documents.items()}
    report["elapsed_bound_ends_utc"] = _utc(allowance.bound_end())
    if "B" in n and "C" in n:
        res = S.evaluate(n["B"], n["C"], n.get("R"), truth, caps={"B": cfg["caps"]["B"], "C": cfg["caps"]["C"]}, extensions_used=0, stop_state=ctl.state(),
                         docs={d["pool_id"] for d in run_set}, P=(lanes.get("P") or {}).get("probe"), r_gate=gates.get("R"),
                         gate_definition=cfg["decision_coverage_gate"])
        if cfg.get("reader") == "none":
            res["exercise_only"] = ("dry run: no application reader ran on any document (reader 'none'); every lane has 0 facts; "
                                    "the figures exercise the scorer and are not a result")
        (out / "SCORE-BCR-R32.json").write_text(_text(res), encoding="utf-8", newline="\n")
        report["candidate_outcome"] = res["outcome"]
        report["score_outcome_by_field"] = res["outcome_by_field"]
        report["comparison_state"] = res["comparison_state"]
        report["concentration_outcome_by_field"] = {f: v["outcome"] for f, v in res["concentration"]["fields"].items()}
        report["scope_limitations"] = res["scope_limitations"]
        report["diagnostics"] = {k: {x: v.get(x) for x in ("state", "credit")} for k, v in res["diagnostics"].items()}
    else:
        state = ctl.comparison if ctl.comparison.startswith(("INVALID", "RESULT")) else \
            (f"DEFERRED: B documents deferred by the project window; C not started (earliest retry {report['earliest_retry_utc']})" if deferred.get("B")
             else "INCOMPLETE: C did not run")
        report["comparison_state"] = state
        report["candidate_outcome"] = "INVALID" if state.startswith("INVALID") else "INCOMPLETE"
        report["scope_limitations"] = S.SCOPE_LIMITATIONS
    if run_invalid(cfg["run_folder"]) is not None:
        report["comparison_state"], report["candidate_outcome"] = f"INVALID: {run_invalid(cfg['run_folder'])}", "INVALID"
        report["identity_invalid"] = MI.invalid_marker(cfg["run_folder"])
        report["contract_breach"] = RC.breach_marker(cfg["run_folder"])
    report["run_state"] = ("INVALID" if report["candidate_outcome"] == "INVALID" else "RESULT" if str(report["comparison_state"]).startswith("RESULT")
                           else "DEFERRED" if deferred else "FINISHED")
    report["stop_controller"] = ctl.state()
    report["lanes"] = {k: {x: v.get(x) for x in ("reader", "seconds", "stats", "lane_stop_state", "model_requests", "allowance_used", "dry_stub_calls",
                                                 "live_provider_attempts_blocked", "policy_version", "stopped", "store_dispatched_to_inner",
                                                 "application_processing_run", "application_reader_run", "evidence_tasks", "environment_check",
                                                 "switch_source", "serves_by_mode", "gate", "deferred", "identity", "cli_version", "limit_events")}
                       for k, v in lanes.items()}
    report["probe"] = (lanes.get("P") or {}).get("probe")
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


def resumable(last: dict, *, now: float | None = None, bound_end: float | None = None) -> tuple[bool, str]:
    st, comp, rs = last.get("status"), str(last.get("comparison_state") or ""), last.get("run_state")
    now = time.time() if now is None else now
    if st == "closed":
        return False, f"refused: the run was closed ({comp})"
    if st == "finished" and (comp.startswith("RESULT") or comp.startswith("INVALID") or rs in ("INVALID", "RESULT")):
        return False, f"refused: the comparison is terminal ({comp}); a terminal comparison is never resumed"
    if bound_end is not None and now > bound_end:
        return False, f"refused: the elapsed bound ended at {_utc(bound_end)}"
    if st in ("started", "interrupted", "refused"):
        return True, f"the last invocation is {st} (it never finished)"
    if st == "finished" and rs == "DEFERRED":
        retry = last.get("resume_not_before", last.get("earliest_retry"))
        policy = last.get("resume_policy") or "earliest"
        if retry is not None and now < float(retry):
            return False, (f"refused: the resume policy '{policy}' allows a resume at {_utc(retry)} (earliest retry {_utc(last.get('earliest_retry'))}, "
                           f"full {(last.get('retry_at_full_utc') or {}).get('structural')}); nothing was created")
        return True, f"the last invocation DEFERRED documents and the resume policy '{policy}' time has come"
    if st == "finished" and comp.startswith("INCOMPLETE"):
        return True, "the last invocation finished INCOMPLETE"
    if st == "finished":
        return False, "refused: the run is complete; there is nothing to resume"
    return False, f"refused: the last invocation has status {st!r}"


def parse(argv=None):
    a = argparse.ArgumentParser(prog="runner_r32.py", description="r32 guarded runner (ORCH-08); there is no --auth-path")
    a.add_argument("command", choices=("run", "resume"))
    a.add_argument("--mode", choices=("dry", "live"), required=True)
    a.add_argument("--run-set", required=True)
    a.add_argument("--binding", required=True)
    a.add_argument("--binding-sha", required=True)
    a.add_argument("--declaration")
    a.add_argument("--declaration-sha")
    a.add_argument("--stamp", help="dry: the dry run's stamp; live: optional, must equal the declaration's run.stamp")
    a.add_argument("--sandbox-base", help="dry only: the sandbox base (C:/t/r2x/r<NN>-sandbox); live uses the declaration's")
    a.add_argument("--out", help="this invocation's output folder (new); default <run folder>/inv-<n>/out")
    a.add_argument("--dry-fault", help="dry drill only: LANE:N -- the lane process dies right after its N-th response came back, "
                                       "before it was saved (the row stays reserved and charged)")
    a.add_argument("--dry-inject", help="dry drill only: a JSON file {injections: [...], caps?, project_window?, parent?, dry_ledger?, application_limits?}")
    a.add_argument("--dry-synthetic", help="dry drill only: a JSON spec of SYNTHETIC EP-990001 documents (application readers on them only)")
    a.add_argument("--dry-baseline-facts", help="dry drill only (R43-42): the baseline-facts drill SPEC -- lane B, frozen-r13, F009 / F020 / F030 "
                                                "by id and sha256, AI off, the refusing global provider; no allowance, store or ledger (drill_r45.py)")
    return a.parse_args(argv)


DRY_APPLICATION_LIMIT_KEYS = ("AI_MAX_CALLS_PER_PROJECT_PER_DAY", "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY", "AI_MAX_CALLS_PER_DOCUMENT")


def _dry_inject(path) -> dict:
    x = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    for i in x.get("injections") or []:
        if i.get("kind") not in INJECTION_KINDS or i.get("lane") not in ("B", "C", "R", "P") or not isinstance(i.get("calls"), list):
            raise Refused(f"refused: a dry injection is {{kind in {INJECTION_KINDS}, lane, calls: [n, ...]}} ({i})")
    bad = [k for k in (x.get("application_limits") or {}) if k not in DRY_APPLICATION_LIMIT_KEYS]
    if bad:
        raise Refused(f"refused: a dry drill may lower only {DRY_APPLICATION_LIMIT_KEYS} ({bad})")
    if x.get("resume_policy") not in (None,) + PF.RESUME_POLICIES:
        raise Refused(f"refused: a dry drill's resume_policy is one of {PF.RESUME_POLICIES} ({x.get('resume_policy')!r})")
    return x


def reentry_proof(run_folder: pathlib.Path, run_key: str) -> dict:
    """ORCH-10 (R41-09 closure): may 'run' re-enter an EXISTING run folder? Only when the folder's own records prove that
    no allowance was ever created (allowance.sqlite absent), no authorization nonce was consumed (no consumption record)
    and no request was charged (no allowance, so no charge; the capture store, if bound, is bound to THIS run key and holds
    no request). Anything else is refused ('use resume'). Read-only: nothing is created, moved or removed here."""
    proof = {"run_folder": run_folder.as_posix(), "checked_utc": _now()}
    if (run_folder / "allowance.sqlite").exists():
        raise Refused(f"refused: a second fresh invocation of this run is refused ({run_folder.as_posix()} holds the run's allowance); use 'resume'")
    proof["allowance_created"] = False
    consumed = sorted(p.name for p in (run_folder / DG.CONSUMED_DIR).glob("consumed-*.json")) if (run_folder / DG.CONSUMED_DIR).is_dir() else []
    if consumed:
        raise Refused(f"refused: an authorization nonce was consumed in this run folder ({consumed}); use 'resume'")
    proof["nonces_consumed"] = 0
    cap = run_folder / "capture.sqlite"
    if cap.exists():
        k = AL.bound_key(cap)
        if k not in (None, run_key):
            raise Refused("refused: the capture store in this run folder is bound to another run")
        con = sqlite3.connect(f"file:{cap.as_posix()}?mode=ro", uri=True)
        try:
            has = con.execute("select count(*) from sqlite_master where name = 'requests'").fetchone()[0]
            rows = con.execute("select count(*) from requests").fetchone()[0] if has else 0
        finally:
            con.close()
        if rows:
            raise Refused(f"refused: the capture store holds {rows} request(s); use 'resume'")
        proof["capture_store"] = {"exists": True, "bound_key": k, "requests": rows}
    else:
        proof["capture_store"] = {"exists": False}
    proof["requests_charged"] = 0
    proof["partial_allowance"] = (run_folder / "allowance.sqlite.new").exists()
    proof["rule"] = ("no allowance was ever created, no nonce consumed, no request charged: 'run' re-enters this folder as a new invocation "
                     "number; nothing existing is reset or re-created")
    return proof


def _state_of_reentry(run_folder: pathlib.Path, state_path: pathlib.Path, ident: dict) -> tuple[dict, dict]:
    """The run state of a re-entered folder: the existing RUN-STATE.json when it is readable and names this run; when it is
    missing or unreadable (the first attempt failed while writing it) a new one is started and the unreadable file is kept
    beside it (renamed, never deleted)."""
    note = {}
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except ValueError:
            aside = state_path.with_name(f"RUN-STATE.unreadable-{int(time.time())}.json")
            os.replace(state_path, aside)
            note["unreadable_state_kept_as"] = aside.name
            state = None
        if state is not None:
            diff = [k for k, w in ident.items() if state.get(k) != w]
            if diff:
                raise Refused(f"refused: the existing run folder belongs to another run (RUN-STATE.json differs in {diff})")
            return state, note
    note["state_started_by_reentry"] = True
    return dict(ident, schema="r38-run-state-1", run_folder=run_folder.as_posix(), invocations=[],
                rule="one run folder, allowance and capture store per run key; 'run' once (re-entered only while no allowance exists), then only 'resume'"), note


def create_allowance_atomic(cfg: dict, run_folder: pathlib.Path) -> dict:
    """ORCH-10: the run's ONE allowance, created complete or not at all -- built as allowance.sqlite.new and renamed into
    place (os.replace) only after its binding (run key, caps, window, parent) is committed. A partial file left by an
    interrupted creation was never an allowance: it is kept aside (renamed), never used. An existing allowance.sqlite is
    never re-created (refused)."""
    final, tmp = run_folder / "allowance.sqlite", run_folder / "allowance.sqlite.new"
    if final.exists():
        raise Refused("refused: the run's allowance exists; it is never re-created")
    rec = {}
    if tmp.exists():
        aside = run_folder / f"allowance.partial-{int(time.time())}.sqlite"
        os.replace(tmp, aside)
        rec["partial_kept_as"] = aside.name
    AL.LaneAllowance(tmp.as_posix(), cfg["caps"], cfg["project_window"], parent=cfg["parent"], run_key=cfg["run_key"],
                     require_project=cfg["mode"] == "live", create=True, project_totals=cfg.get("project_totals"))
    os.replace(tmp, final)
    return rec | {"created": True, "path": final.as_posix()}


def main(argv=None) -> int:
    args = parse(argv)
    live = args.mode == "live"
    if live and (args.dry_fault or args.dry_inject or args.dry_synthetic or args.sandbox_base or args.dry_baseline_facts):
        raise Refused("refused: --dry-fault / --dry-inject / --dry-synthetic / --dry-baseline-facts / --sandbox-base are dry-mode drills only")
    if not live and (args.declaration or args.declaration_sha):
        raise Refused("refused: dry mode takes no declaration (a declaration is the live contract)")
    if args.dry_baseline_facts:                                          # R43-42 (review45): an additional, explicitly named dry drill
        import drill_r45 as DR
        return DR.run(args, sys.modules[__name__])
    started = _now()
    # ---- 0. preflight: NOTHING is created, re-opened or consumed before every check has passed (ORCH-10, R41-09) ------
    binding = PF.verify_binding(args.binding, args.binding_sha)
    rs_sha = sha256(args.run_set)
    inject = _dry_inject(args.dry_inject) if args.dry_inject else {}
    synthetic = json.loads(pathlib.Path(args.dry_synthetic).read_text(encoding="utf-8")) if args.dry_synthetic else None
    # the dry run key binds the drill's configuration (the inject file and the synthetic spec); --dry-fault is a crash of
    # ONE invocation and is not part of it (a resume is given without it)
    drill_key = hashlib.sha256(json.dumps([inject, synthetic], sort_keys=True).encode()).hexdigest() if (inject or synthetic) else ""
    if args.dry_fault:
        lane_f, _, nf = args.dry_fault.partition(":")
        inject = {**inject, "injections": list(inject.get("injections") or []) + [{"kind": "unsaved", "lane": lane_f, "calls": [int(nf)],
                                                                                   "invocations": "current"}]}
    if live:
        decl, v = PF.load_declaration(args.declaration, args.declaration_sha, binding_sha=binding["sha256"], run_set_sha=rs_sha)
        if args.stamp and args.stamp != v["stamp"]:
            raise Refused(f"refused: the stamp is the declaration's ({v['stamp']}), not {args.stamp}")
        stamp, run_folder, run_key, base = v["stamp"], pathlib.Path(v["run_folder"]), args.declaration_sha, v["sandbox_base"]
        caps, parent, window = v["caps"], v["parent"], v["project_window"]
        switches, provider_env, pins = v["lane_switches"], v["provider_env"], v["model_identity"]
        interpreter = PF.verify_interpreter(v["interpreter"])            # ORCH-10: the bound interpreter
        cli_file = PF.verify_cli(pins)                                   # ORCH-10: the pinned CLI file's sha256 (read as bytes)
        disk = v["disk_precondition"]
    else:
        if not args.stamp:
            raise Refused("refused: dry mode needs --stamp")
        base = PF.sandbox_base(args.sandbox_base).as_posix()
        stamp, run_folder = args.stamp, PF.run_folder_of(args.stamp, base)
        run_key = hashlib.sha256(f"r34-dry-run|{stamp}|{binding['sha256']}|{rs_sha}{'|' + drill_key if drill_key else ''}".encode("utf-8")).hexdigest()
        caps, parent, window = dict(inject.get("caps") or CAPS), dict(inject.get("parent") or PARENT), dict(inject.get("project_window") or WINDOW)
        switches, provider_env, pins, v = DRY_LANE_SWITCHES, None, dict(DRY_PINS), None
        interpreter, cli_file, disk = None, None, PF.dry_disk_precondition(base)
    free_disk = PF.verify_free_disk(disk)                                # ORCH-10 (R41-10, C1): before any folder or nonce
    hd = PF.heads()
    if synthetic is None:
        truth = PF.build_truth()
        gate = PF.population(truth)
        run_set = PF.load_run_set(args.run_set, truth)
    else:
        truth, gate, run_set = None, {"action": "DRY SYNTHETIC EXERCISE (no population gate: synthetic EP-990001 documents only)"}, None
    if live:
        report_bounds = PF.verify_bounds(v, run_set, truth)
    scope = PF.verify_ledger_scope(v["ledger"]) if live else None
    state_path = run_folder / RUN_STATE
    ident = {"run_key": run_key, "mode": args.mode, "stamp": stamp, "binding_sha256": binding["sha256"], "run_set_sha256": rs_sha,
             "caps": caps, "parent": parent, "project_window": window}
    reentry = None
    if args.command == "run":
        if run_folder.exists():
            reentry = reentry_proof(run_folder, run_key)                 # ORCH-10: re-enter only a folder with no allowance
            state, reentry["state"] = _state_of_reentry(run_folder, state_path, ident)
            n, kind = len(state["invocations"]) + 1, "reentry"
        else:
            n, state, kind = 1, None, "fresh"
    else:
        if not state_path.is_file():
            raise Refused(f"refused: nothing to resume ({state_path.as_posix()} does not exist)")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        diff = [k for k, w in ident.items() if state.get(k) != w]
        if diff:
            raise Refused(f"refused: resume must be the same run (same stamp, key, binding, run set, caps, parent budget and window); differs in {diff}")
        for f in ("allowance.sqlite", "capture.sqlite"):
            if not (run_folder / f).is_file():
                raise Refused(f"refused: the run's {f} is missing; a resume never re-creates it"
                              + ("; no allowance was ever created, so 'run' re-enters this folder" if f == "allowance.sqlite" else ""))
        if AL.bound_key(run_folder / "capture.sqlite") != run_key:
            raise Refused("refused: the capture store is bound to another run")
        if MI.invalid_marker(run_folder) is not None:
            raise Refused("refused: the run is INVALID (model identity mismatch recorded in IDENTITY-INVALID.json); it is never resumed")
        if RC.breach_marker(run_folder) is not None:
            raise Refused("refused: the run is INVALID (contract breach recorded in CONTRACT-BREACH.json: an undeclared request path); it is never resumed")
        bound_end = AL.LaneAllowance(run_folder / "allowance.sqlite", caps, window, parent=parent, run_key=run_key, create=False).bound_end()
        last = state["invocations"][-1]
        ok, why = resumable(last, bound_end=bound_end)
        if not ok:
            if "elapsed bound" in why and last.get("status") != "closed":
                _close(run_folder, state, state_path, last, why)
            raise Refused(why)
        n, kind = len(state["invocations"]) + 1, "resume"
    guard = DG.check(args.declaration, args.declaration_sha, run_folder=run_folder, invocation=n, action="preview", stamp=stamp, kind=kind) if live else \
        {"authorized": False, "reason": "dry mode: no declaration, no provider; the dry stub refuses every request"}
    if live and not guard["authorized"]:
        raise Refused(guard["reason"])
    # ---- the CLI version of this invocation, after the guard preview and BEFORE anything is created or re-opened (R41-09 cases A and T; R41-11): the only process this step starts ---
    try:
        version = MI.cli_version(pins["cli_path"]) if live else DRY_CLI_VERSION
        version_check = MI.check_version(run_folder if run_folder.exists() else None, pins, version)
    except MI.IdentityRefused as exc:
        raise Refused(f"{exc} (nothing was created and no authorization was consumed)") from exc
    # ---- the run folder: created by the first invocation (or re-entered while it holds no allowance), re-opened by a resume
    if kind == "fresh":
        run_folder.mkdir(parents=True)
    if kind in ("fresh", "reentry") and not state_path.is_file():
        state = dict(state or ident, schema="r38-run-state-1", run_folder=run_folder.as_posix(), sandbox_base=base,
                     declaration_sha256=args.declaration_sha if live else None, created_utc=started, invocations=list((state or {}).get("invocations") or []),
                     rule="one run folder, allowance and capture store per run key; 'run' once (re-entered only while no allowance exists), then only 'resume'")
        state.update(ident)
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
              "run_folder": run_folder.as_posix(), "sandbox_base": base, "run_key": run_key, "declaration_sha256": args.declaration_sha if live else None,
              "binding": binding, "heads": hd, "population_gate": gate, "dispatch_guard": guard, "ledger_scope": scope, "model_requests": 0,
              "interpreter": interpreter, "cli_file": cli_file, "cli_version_check": version_check, "free_disk": free_disk,
              "ledger_rule": "dry: the AI ledger must read the same before and after; live: growth only inside the declared scope, within the parent total"}
    if reentry is not None:
        report["reentry"] = reentry
    report["ledger_before"] = ledger_state() if not live else None
    snap_before = PF.ledger_snapshot(v["ledger"]["path"]) if live else None
    inv = {"n": n, "kind": kind, "started_utc": started, "status": "started", "out": out.as_posix()}
    status = "interrupted"
    try:
        if reentry is not None:
            _write(run_folder / f"REENTRY-{n}.json", reentry)
        if out.exists():
            raise Refused(f"refused: {out} exists (an invocation never reuses its output folder)")
        out.mkdir(parents=True)
        # ---- the CLI version and the provider identity of this invocation (A-09 point 2), recorded ---------------------
        try:
            report["provider_identity"] = MI.record_invocation(run_folder, n, pins, version, mode=args.mode)
        except MI.IdentityRefused as exc:
            raise Refused(str(exc)) from exc
        state["invocations"].append(inv)
        _state_write(state_path, state)
        # ---- ORCH-10: the capture store, then the allowance, bound to the run key BEFORE any authorization is consumed --
        cap_bind = AL.bind_store((run_folder / "capture.sqlite").as_posix(), run_key)
        alw_cfg = {"caps": caps, "project_window": window, "parent": parent, "run_key": run_key, "mode": args.mode,
                   "project_totals": project_totals_of(v["bounds"]) if live else None}
        if kind == "resume":
            open_allowance(alw_cfg | {"allowance": (run_folder / "allowance.sqlite").as_posix()})       # exists; bound to this run
            report["allowance_creation"] = {"created": False, "rule": "a resume never re-creates the allowance"}
        else:
            report["allowance_creation"] = create_allowance_atomic(alw_cfg, run_folder)
        report["capture_binding"] = cap_bind
        if live:
            report["request_bounds"] = report_bounds
            auth = DG.authorize(args.declaration, args.declaration_sha, run_folder=run_folder, invocation=n, action="consume", stamp=stamp, kind=kind)
            report["authorization"] = auth
            inv["authorization_sha256"] = auth["authorization_sha256"]
            inv["nonce_index"] = auth.get("nonce_index")
        sbx = run_folder / f"inv-{n}"
        stage_files = SI.STAGE_FILES
        if synthetic is not None:
            truth = _synthetic_truth(run_folder, synthetic)
            run_set = [{"pool_id": p, "doc_key": d["doc_key"], "ep": d["ep"]} for p, d in truth["documents"].items()]
            stage_files = run_folder / "syn-files"
        truth_path = out / "TRUTH-R32.json"
        truth_path.write_text(PF.truth_text(truth), encoding="utf-8", newline="\n")
        report["truth_sha256"] = sha256(truth_path)
        report["run_set"] = {"path": str(args.run_set), "sha256": rs_sha, "documents": len(run_set), "synthetic": synthetic is not None}
        cfg = {"mode": args.mode, "reader": "application" if (live or synthetic is not None) else "none", "harness_dir": str(HERE), "out_dir": str(out),
               "truth": str(truth_path), "run_set": run_set, "run_set_path": str(args.run_set), "run_folder": run_folder.as_posix(), "run_key": run_key,
               "sandbox_base": base, "stamp": stamp, "invocation": n, "store": (run_folder / "capture.sqlite").as_posix(),
               "allowance": (run_folder / "allowance.sqlite").as_posix(), "caps": caps, "parent": parent, "project_window": window,
               "trees": TREES, "sandbox": {k: str(sbx / k) for k in ("B", "C", "R")}, "binding": str(args.binding), "binding_sha256": binding["sha256"],
               "declaration_path": args.declaration if live else None, "declaration_sha256": args.declaration_sha if live else None,
               "lane_switches": switches, "provider_env": provider_env, "model_identity": pins, "cli_version": version,
               "switch_source": "the declaration's lane_switches" if live else PF.DRY_LANE_SWITCHES_LABEL,
               "policies": {"B": "B:accepted-path:evidence-off"},
               "application_env": v["application_env"] if live else dict(PF.APPLICATION_ENV),
               "lane_task_kinds": v["lane_task_kinds"] if live else PF.task_kinds_for(switches),
               "resume_policy": v["resume_policy"] if live else inject.get("resume_policy", PF.DEFAULT_RESUME_POLICY),
               "decision_coverage_gate": v["decision_coverage_gate"] if live else S.DECISION_COVERAGE_GATE,
               "project_totals": project_totals_of(v["bounds"]) if live else _dry_totals(run_set, truth, switches, window, parent, caps)}
        if live:
            cfg["ledger"] = v["ledger"]
        if inject.get("injections"):
            # an injection applies to the invocations it names (default: the first); --dry-fault to the invocation it is given to
            cfg["dry_inject"] = [dict(i, invocations=[n]) if i.get("invocations") == "current" else dict(i, invocations=i.get("invocations") or [1])
                                 for i in inject["injections"]]
        if inject.get("dry_ledger"):
            cfg["dry_ledger"] = {**inject["dry_ledger"], "path": (run_folder / "FAKE-LEDGER.sqlite").as_posix()}
        if inject.get("application_limits"):
            cfg["dry_application_limits"] = {k: str(v) for k, v in inject["application_limits"].items()}
        report |= execute(cfg, truth, run_set, out, sbx, stage_files=stage_files)
        status = "finished"
    except Refused as exc:
        status = "refused"
        report["refused"] = str(exc)
        raise
    except BaseException as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        try:
            if live:
                report["ledger_live_check"] = PF.ledger_live_check(snap_before, PF.ledger_snapshot(v["ledger"]["path"]), v["ledger"], parent["total"])
            else:
                report["ledger_after"] = ledger_state()
                report["ledger_unchanged"] = report["ledger_after"] == report["ledger_before"]
            report["finished_utc"] = _now()
            report["status"] = status
            inv.update({"status": status, "finished_utc": report["finished_utc"], "comparison_state": report.get("comparison_state"),
                        "outcome": report.get("candidate_outcome"), "run_state": report.get("run_state"),
                        "earliest_retry": report.get("earliest_retry"), "earliest_retry_utc": report.get("earliest_retry_utc"),
                        "retry_at_full": report.get("retry_at_full"), "retry_at_full_utc": report.get("retry_at_full_utc"),
                        "resume_policy": report.get("resume_policy"), "resume_not_before": report.get("resume_not_before"),
                        "resume_not_before_utc": report.get("resume_not_before_utc"),
                        "deferred": report.get("deferred"), "cli_version": (report.get("provider_identity") or {}).get("cli_version"),
                        "allowance_existed_at_end": (run_folder / "allowance.sqlite").exists(),
                        "authorization_consumed": "authorization" in report})
            if inv not in state["invocations"]:
                state["invocations"].append(inv)
            _state_write(state_path, state)
            dest = out if out.exists() else run_folder / f"inv-{n}"
            dest.mkdir(parents=True, exist_ok=True)
            _write(dest / "RUN-REPORT.json", report)
        finally:
            try:
                lock.unlink()
            except OSError:
                pass
    if not live and not report["ledger_unchanged"]:
        raise RuntimeError("the AI ledger changed (dry mode)")
    if live and not report["ledger_live_check"]["ok"]:
        raise RuntimeError(f"the AI ledger changed outside the declared scope or the parent total: {report['ledger_live_check']['problems']}")
    print(json.dumps({k: report.get(k) for k in ("mode", "command", "invocation", "kind", "status", "model_requests", "ledger_before", "ledger_after",
                                                 "candidate_outcome", "score_outcome_by_field", "comparison_state", "run_state", "earliest_retry_utc")},
                     default=str))
    return 0


def _dry_totals(run_set, truth, switches, window, parent, caps) -> dict | None:
    """Dry mode: the project totals for retry_at_full, from the same bounds model over the dry run set (real or synthetic)."""
    import project_bounds_r32 as PB
    try:
        b = PB.compute(run_set, truth, switches, window_limit=window["limit"], window_s=window["window_s"], elapsed_s=parent["elapsed_s"], caps=caps)
    except Exception:  # noqa: BLE001 -- dry only: no totals means retry_at_full falls back to the earliest retry
        return None
    return project_totals_of(b)


def _synthetic_truth(run_folder: pathlib.Path, spec: dict) -> dict:
    """Dry drill: the SYNTHETIC EP-990001 documents and their truth (synthetic_r32.build), generated once by the first
    invocation into <run folder>/syn-files and SYNTHETIC-TRUTH.json; a resume loads the same truth (the staged files'
    sha256 are checked again by the ingestion: PACKET MISMATCH on any difference)."""
    import synthetic_r32 as SY
    tp = run_folder / "SYNTHETIC-TRUTH.json"
    if not tp.exists():
        t = SY.build(run_folder / "syn-files", spec["documents"])
        tp.write_text(PF.truth_text(t), encoding="utf-8", newline="\n")
    t = json.loads(tp.read_text(encoding="utf-8"))
    if any(not d["pool_id"].startswith("SYN") or d["ep"] != SY.EP for d in t["documents"].values()):
        raise Refused("refused: a synthetic drill holds only SYN* documents of EP-990001")
    return t


def _close(run_folder: pathlib.Path, state: dict, state_path: pathlib.Path, last: dict, why: str):
    """The elapsed bound passed: the run is CLOSED, INCOMPLETE; its deferred documents are listed as INCOMPLETE."""
    rec = {"n": len(state["invocations"]) + 1, "kind": "close", "status": "closed", "finished_utc": _now(),
           "comparison_state": "INCOMPLETE: the deferral could not complete within the elapsed bound",
           "run_state": "INCOMPLETE", "deferred_now_incomplete": last.get("deferred"), "why": why}
    state["invocations"].append(rec)
    _state_write(state_path, state)


if __name__ == "__main__":
    sys.exit(main())
