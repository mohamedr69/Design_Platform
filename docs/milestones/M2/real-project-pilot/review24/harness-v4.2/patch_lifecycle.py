"""Recorded harness v4.1 edits (review 23, R23-01): the runner lifecycle contract `runner-lifecycle-2026-10-01.v1`.
  arm_ev.py
    * a TERMINAL stop (critical acceptance on a resolved label; three consecutive provider failures) is persisted the
      moment it is decided -- out/TERMINAL-STOP.json, written atomically BEFORE any manifest update and never overwritten
      (the first stop, its reason and its triggering evidence are kept);
    * --resume loads and validates the persisted state BEFORE the startup manifest write and before any call can leave:
      a terminal stop (file, or the manifest's terminal_stop / stopped reason of a v4 run, or one reconstructed OFFLINE
      from the saved evidence by the same tripwire) makes the resume return the preserved stopped result with ZERO
      provider requests (exit code 4, refusal recorded, lists preserved, status stays `stopped`);
    * a stopped run never becomes `completed`: the stop file is checked again when the final status is written;
    * remaining projects after any terminal stop are recorded as not_attempted (the critical-only prefix test is gone);
    * dry-only kill points around the persistence boundary: PILOT_DRY_KILL_AT_STOP=before_file | after_file.
    Daily deferral, process interruption (open attempt -> interrupted), completed-document skips, cache accounting, the
    12 / document allowance, the arm scope and the rolling project limit are untouched.
  dry_provider2.py: PILOT_DRY_FAIL_FROM=n [PILOT_DRY_FAIL_COUNT=k]: scripted provider failures (error="transport") from
    the n-th dispatched request, k of them (default: every later request) -- the consecutive-failure stop probe.
  runner_probes.py: outputs under review23/, probe roots under C:/t/r2x/dry-runs/r23-probes (the runner scenarios rerun
    with the v4.1 runner as positive controls)."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def patch(fn, subs):
    p = HERE / fn
    s = p.read_text(encoding="utf-8")
    for o, n in subs:
        assert s.count(o) == 1, (fn, o[:80], s.count(o))
        s = s.replace(o, n)
    p.write_text(s, encoding="utf-8")


patch("arm_ev.py", [
    ('HARNESS_CONTRACT = "harness-contract-2026-09-30.v4"\nRUNNER_VERSION = "arm-ev-2026-09-30.v4"\n',
     'HARNESS_CONTRACT = "harness-contract-2026-09-30.v4"\nRUNNER_VERSION = "arm-ev-2026-10-01.v4.1"\n'
     'LIFECYCLE_CONTRACT = "runner-lifecycle-2026-10-01.v1"       # see LIFECYCLE-CONTRACT.md: terminal stops survive --resume\n'
     'TERMINAL_PREFIXES = {"stop: critical": "critical_acceptance", "stop: three consecutive provider failures": "provider_failures"}\n'),
    # --- the stop file, written the moment a terminal stop is decided ------------------------------------------------
    ('def progress(event: str, **kw) -> None:',
     'STOP_FILE = OUT / "TERMINAL-STOP.json"\n\n\n'
     'def load_terminal_stop():\n'
     '    return json.loads(STOP_FILE.read_text(encoding="utf-8")) if STOP_FILE.exists() else None\n\n\n'
     'def persist_terminal_stop(kind: str, reason: str, evidence, *, reconstructed: bool = False) -> dict:\n'
     '    """Persist a TERMINAL stop atomically, before anything else is written; the first stop is never overwritten."""\n'
     '    existing = load_terminal_stop()\n'
     '    if existing:\n'
     '        return existing\n'
     '    if dry.DRY and os.environ.get("PILOT_DRY_KILL_AT_STOP") == "before_file":\n'
     '        os._exit(98)                          # the stop was decided, nothing persisted yet (recovery must reconstruct it)\n'
     '    rec = {"lifecycle": LIFECYCLE_CONTRACT, "terminal": True, "kind": kind, "reason": reason, "evidence": evidence, "reconstructed": reconstructed,\n'
     '           "at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "pid": os.getpid(), "clock": xtrack.now(),\n'
     '           "tag": args.tag, "arm": args.arm, "declaration_sha256": args.declaration_sha, "allowance_key": {"scope": ALLOW_SCOPE, "profile": ALLOW_PROFILE}}\n'
     '    tmp = OUT / "TERMINAL-STOP.json.tmp"\n'
     '    with open(tmp, "w", encoding="utf-8") as f:\n'
     '        json.dump(rec, f, indent=1, default=str)\n'
     '        f.flush()\n'
     '        os.fsync(f.fileno())\n'
     '    os.replace(tmp, STOP_FILE)\n'
     '    if dry.DRY and os.environ.get("PILOT_DRY_KILL_AT_STOP") == "after_file":\n'
     '        os._exit(98)                          # the stop file exists, the manifest does not know yet\n'
     '    return rec\n\n\n'
     'def progress(event: str, **kw) -> None:'),
    # --- the consecutive-failure stop is terminal and persisted at once ------------------------------------------------
    ('            if state["consecutive_failures"] >= 3 and not state["stopped"]:\n                state["stopped"] = "stop: three consecutive provider failures"\n',
     '            if state["consecutive_failures"] >= 3 and not state["stopped"]:\n                state["stopped"] = "stop: three consecutive provider failures"\n'
     '                state["terminal_stop"] = persist_terminal_stop("provider_failures", state["stopped"], [{k: e.get(k) for k in ("task", "page", "outcome", "error_detail", "model")} for e in self.log[-3:]])\n'
     '                manifest["terminal_stop"] = state["terminal_stop"]\n'),
    ('state = {"consecutive_failures": 0, "stopped": None, "xtrack_refusals": 0,',
     'state = {"consecutive_failures": 0, "stopped": None, "terminal_stop": None, "xtrack_refusals": 0,'),
    # --- resume: load and validate persisted state BEFORE the startup write and before any dispatch ---------------------
    ('    manifest.setdefault("resumes", []).append({"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "pid": os.getpid(), "clock": xtrack.now(), "reread": args.reread})\n'
     '    manifest["deferred_before_resume"] = manifest.get("deferred", [])\n',
     '    manifest.setdefault("resumes", []).append({"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "pid": os.getpid(), "clock": xtrack.now(), "reread": args.reread})\n'
     '    manifest["deferred_before_resume"] = manifest.get("deferred", [])\n'
     '    # ---- lifecycle: a terminal stop is loaded, validated and enforced before anything is written or dispatched ----\n'
     '    saved_stop = load_terminal_stop()\n'
     '    if saved_stop is None and manifest.get("terminal_stop"):\n'
     '        saved_stop = manifest["terminal_stop"]                                  # the manifest knew the stop; the file was lost\n'
     '    if saved_stop is None:\n'
     '        reason = (manifest.get("runner_state") or {}).get("stopped")\n'
     '        kind = next((k for pfx, k in TERMINAL_PREFIXES.items() if str(reason or "").startswith(pfx)), None)\n'
     '        if kind:                                                                # a v4 run record: the reason alone is terminal\n'
     '            saved_stop = persist_terminal_stop(kind, reason, [t for t in manifest.get("tripwire", []) if t.get("critical_on_resolved")], reconstructed=True)\n'
     '    if saved_stop is None:\n'
     '        # OFFLINE reconstruction from the saved evidence (no dispatch): the same tripwire over every project whose\n'
     '        # documents this arm already read (bound by the scoring contract), before any call can leave\n'
     '        read_eps = {rd["ep"] for rd in dump_rows().values() if rd.get("sha256") in planned_by_sha and completed(rd)}\n'
     '        if read_eps:\n'
     '            crit0, binding0 = tripwire(read_eps)\n'
     '            if crit0:\n'
     '                saved_stop = persist_terminal_stop("critical_acceptance", f"stop: critical acceptance on a resolved label (reconstructed on resume from the saved evidence of EP-{\', EP-\'.join(sorted(read_eps))})", crit0, reconstructed=True)\n'
     '    if saved_stop is not None:\n'
     '        assert saved_stop.get("declaration_sha256") in (None, args.declaration_sha) and saved_stop.get("arm") in (None, args.arm), "the saved stop belongs to another binding"\n'
     '        state["stopped"], state["terminal_stop"] = saved_stop["reason"], saved_stop\n'
     '        manifest["terminal_stop"] = saved_stop\n'
     '        manifest["status"] = "stopped"\n'
     '        manifest["deferred"] = manifest.get("deferred_before_resume", [])\n'
     '        manifest["resumes"][-1].update({"refused": "terminal stop preserved (plain --resume is not approval to clear it)", "requests_sent": 0, "terminal_kind": saved_stop["kind"]})\n'
     '        progress("runner_refused_terminal_stop", kind=saved_stop["kind"], reason=saved_stop["reason"], reconstructed=saved_stop.get("reconstructed"))\n'
     '        write_manifest(final=True)\n'
     '        (RUNS / "refusals").mkdir(parents=True, exist_ok=True)\n'
     '        with open(RUNS / "refusals" / "REFUSALS.jsonl", "a", encoding="utf-8") as f:\n'
     '            f.write(json.dumps({"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "tag": args.tag, "arm": args.arm, "resume": True,\n'
     '                                "refused": f"terminal stop preserved: {saved_stop[\'reason\']}", "requests_sent": 0}) + "\\n")\n'
     '        print(f"STOPPED (terminal, preserved): {saved_stop[\'reason\']} -- zero requests sent; a separate explicit decision and binding are required to reopen this arm")\n'
     '        sys.exit(4)\n'),
    # --- every terminal stop (not only the critical one) leaves the remaining projects not attempted ---------------------
    ('        if state["stopped"] and state["stopped"].startswith("stop: critical"):\n',
     '        if state["terminal_stop"] or (state["stopped"] and any(state["stopped"].startswith(p) for p in TERMINAL_PREFIXES)):\n'),
    # --- the critical stop is persisted the moment it is decided, before the manifest update -----------------------------
    ('        if crit and not state["stopped"]:\n            state["stopped"] = f"stop: critical acceptance on a resolved label after EP-{project.ep_number}"\n',
     '        if crit and not state["stopped"]:\n            state["stopped"] = f"stop: critical acceptance on a resolved label after EP-{project.ep_number}"\n'
     '            state["terminal_stop"] = persist_terminal_stop("critical_acceptance", state["stopped"], crit)\n'
     '            manifest["terminal_stop"] = state["terminal_stop"]\n'),
    # --- a stopped run never becomes completed -----------------------------------------------------------------------------
    ('                 "status": "deferred" if manifest["deferred"] else ("stopped" if state["stopped"] else "completed")})',
     '                 "status": "stopped" if (state["stopped"] or load_terminal_stop()) else ("deferred" if manifest["deferred"] else "completed"), "lifecycle": LIFECYCLE_CONTRACT})'),
])
patch("dry_provider2.py", [
    ('  PILOT_DRY_LATENCY_S=x     sleep x s per request (deadline probes)',
     '  PILOT_DRY_LATENCY_S=x     sleep x s per request (deadline probes)\n'
     '  PILOT_DRY_FAIL_FROM=n     scripted provider FAILURES (error="transport") from the n-th dispatched request on;\n'
     '  PILOT_DRY_FAIL_COUNT=k    ... k of them (default: every later request) -- the consecutive-failure stop probes'),
    ('        self.latency = float(os.environ.get("PILOT_DRY_LATENCY_S") or 0)\n',
     '        self.latency = float(os.environ.get("PILOT_DRY_LATENCY_S") or 0)\n'
     '        self.fail_from = int(os.environ.get("PILOT_DRY_FAIL_FROM") or 0)\n'
     '        self.fail_count = int(os.environ.get("PILOT_DRY_FAIL_COUNT") or 0)\n'),
    ('        if self.latency:\n            time.sleep(self.latency)\n',
     '        if self.latency:\n            time.sleep(self.latency)\n'
     '        if self.fail_from and self.calls >= self.fail_from and (not self.fail_count or self.calls < self.fail_from + self.fail_count):\n'
     '            return AiResponse(data=None, usage=Usage(input_tokens=10, output_tokens=0), model="dry", latency_ms=1, error="transport", error_detail="scripted provider failure")\n'),
])
patch("runner_probes.py", [
    ('PROBES = pathlib.Path(os.environ.get("R22_PROBES_ROOT", "C:/t/r2x/dry-runs/r22-probes"))', 'PROBES = pathlib.Path(os.environ.get("R22_PROBES_ROOT", "C:/t/r2x/dry-runs/r23-probes"))'),
    ('    if k.startswith("AI_EVIDENCE_") or k in ("XTRACK_FAKE_NOW", "PILOT_DRY_KILL_AFTER", "PILOT_DRY_LATENCY_S", "PILOT_DRY_NEW_TAG_OVERRIDE"):',
     '    if k.startswith("AI_EVIDENCE_") or k in ("XTRACK_FAKE_NOW", "PILOT_DRY_KILL_AFTER", "PILOT_DRY_LATENCY_S", "PILOT_DRY_NEW_TAG_OVERRIDE", "PILOT_DRY_FAIL_FROM", "PILOT_DRY_FAIL_COUNT", "PILOT_DRY_KILL_AT_STOP"):'),
])
patch("test_runner_v4.py", [
    ('        p = subprocess.run([sys.executable, str(HERE / "runner_probes.py")], cwd=str(HERE), capture_output=True, text=True, timeout=3000)',
     '        p = subprocess.run([sys.executable, str(HERE / "runner_probes.py")], cwd=str(HERE), capture_output=True, text=True, timeout=3000, env={**os.environ, "PILOT_DRY": "1", "PILOT_DRY_MODE": "coherent"})'),
])
print("patched lifecycle")
