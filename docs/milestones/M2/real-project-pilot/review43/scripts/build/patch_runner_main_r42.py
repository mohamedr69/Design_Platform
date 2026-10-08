"""ORCH-10 (R42PORT-IMPL): replace runner_r32.main (lines from 'def main(argv=None) -> int:' up to, not including,
'def _dry_totals') in the WORK harness copy with the reordered, re-entrant main of section 2.3, and switch execute() to
an allowance and capture store that already exist. Exact-match edits only; refuses when an anchor is not found once."""
import pathlib
import sys

P = pathlib.Path("C:/t/iso/work/r2x/r42/harness-r32/runner_r32.py")
src = P.read_text(encoding="utf-8")


def once(old, new):
    global src
    n = src.count(old)
    if n != 1:
        raise SystemExit(f"anchor found {n} times: {old[:80]!r}")
    src = src.replace(old, new)


start = src.index("def main(argv=None) -> int:\n")
end = src.index("def _dry_totals(")
NEW_MAIN = r'''def reentry_proof(run_folder: pathlib.Path, run_key: str) -> dict:
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
    if live and (args.dry_fault or args.dry_inject or args.dry_synthetic or args.sandbox_base):
        raise Refused("refused: --dry-fault / --dry-inject / --dry-synthetic / --sandbox-base are dry-mode drills only")
    if not live and (args.declaration or args.declaration_sha):
        raise Refused("refused: dry mode takes no declaration (a declaration is the live contract)")
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
    # ---- the CLI version of this invocation, BEFORE anything is created or re-opened (R41-09 cases A and T; R41-11) ---
    try:
        version = MI.cli_version(pins["cli_path"]) if live else DRY_CLI_VERSION
        version_check = MI.check_version(run_folder if run_folder.exists() else None, pins, version)
    except MI.IdentityRefused as exc:
        raise Refused(f"{exc} (nothing was created and no authorization was consumed)") from exc
    guard = DG.check(args.declaration, args.declaration_sha, run_folder=run_folder, invocation=n, action="preview", stamp=stamp, kind=kind) if live else \
        {"authorized": False, "reason": "dry mode: no declaration, no provider; the dry stub refuses every request"}
    if live and not guard["authorized"]:
        raise Refused(guard["reason"])
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


'''
src = src[:start] + NEW_MAIN + src[end:]
# execute(): the allowance and the capture store exist (created / bound by main before any authorization is consumed)
once("""    allowance = open_allowance(cfg, create=True)
    AL.bind_store(cfg["store"], cfg["run_key"])
""", """    allowance = open_allowance(cfg)                    # ORCH-10: created atomically by main() before any authorization was consumed
    if AL.bound_key(cfg["store"]) != cfg["run_key"]:
        raise Refused("refused: the capture store is not bound to this run")
""")
once('''INJECTION_KINDS = ("provider_timeout", "identity_mismatch", "interrupted", "unsaved", "usage",
                   "undeclared_request", "context_free_request", "reader_exception")   # the last three: ORCH-08C drills (dry only)''',
     '''INJECTION_KINDS = ("provider_timeout", "identity_mismatch", "interrupted", "unsaved", "usage",
                   "undeclared_request", "context_free_request", "reader_exception",    # ORCH-08C drills (dry only)
                   "global_provider_request")                                          # ORCH-10 drill (R40-04, dry only)''')
P.write_text(src, encoding="utf-8", newline="\n")
print("patched", P, len(src))
