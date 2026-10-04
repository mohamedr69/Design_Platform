"""Recorded harness v4.2 edits (review 24, R24-01), applied to a copy of review23's frozen v4.1:
  arm_ev.py (runner `arm-ev-2026-10-01.v4.2`, lifecycle contract `runner-lifecycle-2026-10-01.v2`)
    * the provider-outcome journal (provider_journal.py): header at run creation (before any dispatch), `attempt` before a
      call may leave, `result` right after it returns and BEFORE the failure-streak decision;
    * --resume, after the existing stop-file / manifest / legacy-reason checks and BEFORE the critical reconstruction, the
      startup write and any dispatch: the journal is validated; a durable trailing streak of >= 3 completed provider
      failures reconstructs the provider-failure terminal stop (reason unchanged, `reconstructed: true`, the three failures
      as evidence) and refuses with zero requests (exit 4); an INDETERMINATE journal -- or no journal although this run
      recorded requests / charges -- refuses with zero requests (exit 5), writes no stop, leaves the run record untouched
      and records the refusal; otherwise the durable streak and its failures are carried into the process (a restart does
      not reset the breaker) and the journal continues its seq;
    * nothing else changes: the critical-stop paths, deferral, interruption recovery, completed-document skips, cache
      accounting, the 12 / document allowance, the arm scope and the rolling project limit.
  dry_provider2.py: PILOT_DRY_FAIL_AT="i,j,..." -- scripted failures at those dispatched-request indices of the process
    (a success between failures), dry only."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def patch(fn, subs):
    p = HERE / fn
    s = p.read_text(encoding="utf-8")
    for o, n in subs:
        assert s.count(o) == 1, (fn, o[:90], s.count(o))
        s = s.replace(o, n)
    p.write_text(s, encoding="utf-8")


patch("arm_ev.py", [
    ('RUNNER_VERSION = "arm-ev-2026-10-01.v4.1"\nLIFECYCLE_CONTRACT = "runner-lifecycle-2026-10-01.v1"       # see LIFECYCLE-CONTRACT.md: terminal stops survive --resume\n',
     'RUNNER_VERSION = "arm-ev-2026-10-01.v4.2"\nLIFECYCLE_CONTRACT = "runner-lifecycle-2026-10-01.v2"       # see LIFECYCLE-CONTRACT.md: terminal stops survive --resume (v2: provider stops recovered from the journal)\n'),
    ('import coverage_v4 as cv  # noqa: E402\n', 'import coverage_v4 as cv  # noqa: E402\nimport provider_journal as pj  # noqa: E402\n'),
    # --- the journal object, bound to this run -------------------------------------------------------------------------
    ('STOP_FILE = OUT / "TERMINAL-STOP.json"\n',
     'STOP_FILE = OUT / "TERMINAL-STOP.json"\n'
     'JOURNAL_BINDING = {"declaration_sha256": args.declaration_sha, "arm": args.arm, "tag": args.tag, "a_tag": args.a_tag, "allowance_scope": ALLOW_SCOPE,\n'
     '                   "allowance_profile": ALLOW_PROFILE, "policy": arm["identities"]["EVIDENCE_POLICY_VERSION"]}\n'
     'JOURNAL = pj.Journal(OUT / "PROVIDER-OUTCOMES.jsonl", JOURNAL_BINDING)\n'),
    # --- attempt before the call may leave; result before the streak decision ---------------------------------------------
    ('    before, n_log, hits = self.calls, len(self.log), self.cache_hits\n    out = _original_call(self, **kw)\n    new = self.log[n_log:]\n',
     '    before, n_log, hits = self.calls, len(self.log), self.cache_hits\n'
     '    jseq = None if self.exhausted else JOURNAL.attempt(pid=os.getpid(), sha256=kw.get("sha256"), task=kw.get("task"), page=kw.get("page"), tier=kw.get("tier", "small"))\n'
     '    out = _original_call(self, **kw)\n    new = self.log[n_log:]\n'
     '    if jseq is not None:\n'
     '        JOURNAL.result(jseq, pid=os.getpid(), entry=new[-1] if new else None)     # durable BEFORE the streak decision below\n'),
    # --- resume: provider-journal recovery before the critical reconstruction, the startup write and any dispatch ---------
    ('    if saved_stop is None:\n        # OFFLINE reconstruction from the saved evidence (no dispatch): the same tripwire over every project whose\n',
     '    if saved_stop is None:\n'
     '        jinfo = pj.load(JOURNAL.path, JOURNAL_BINDING, planned_sha256=set(planned_by_sha))\n'
     '        if jinfo["state"] == "absent" and run_recorded_requests():\n'
     '            jinfo = {"state": "indeterminate", "why": "no provider-outcome journal although this run recorded requests or charges"}\n'
     '        if jinfo["state"] == "indeterminate":\n'
     '            refuse_indeterminate(jinfo)\n'
     '        manifest["resumes"][-1]["provider_journal"] = {k: jinfo.get(k) for k in ("state", "streak", "unresolved", "last_seq", "result_counts", "processes")}\n'
     '        if jinfo["state"] == "ok" and jinfo["streak"] >= 3:\n'
     '            # the provider-failure stop had been REACHED (its failures are durable) but not persisted: reconstruct it offline\n'
     '            saved_stop = persist_terminal_stop("provider_failures", "stop: three consecutive provider failures", jinfo["trailing_failures"][-3:], reconstructed=True)\n'
     '        elif jinfo["state"] == "ok":\n'
     '            state["consecutive_failures"], state["recent_failures"] = jinfo["streak"], jinfo["trailing_failures"]   # a restart does not reset the breaker\n'
     '            JOURNAL.continue_from(jinfo)\n'
     '    if saved_stop is None:\n        # OFFLINE reconstruction from the saved evidence (no dispatch): the same tripwire over every project whose\n'),
    # --- new run: the journal header exists before any dispatch --------------------------------------------------------------
    ('manifest["deferred"] = []\nprogress("runner_start", resume=args.resume, reread=args.reread, clock=xtrack.now())\n',
     'if not args.resume:\n    JOURNAL.create(lifecycle=LIFECYCLE_CONTRACT, pid=os.getpid())   # before any request can leave\n'
     'manifest["deferred"] = []\nprogress("runner_start", resume=args.resume, reread=args.reread, clock=xtrack.now())\n'),
    # --- helpers: evidence that this run already did work; the fail-closed refusal ---------------------------------------------
    ('started = time.perf_counter()\nif args.resume:\n',
     'def run_recorded_requests() -> bool:\n'
     '    """Read-only: did this sandbox already record a request, a charge or a document start?"""\n'
     '    if (OUT / "io.jsonl").exists() and (OUT / "io.jsonl").stat().st_size > 0:\n'
     '        return True\n'
     '    if (OUT / "progress.jsonl").exists() and any(json.loads(l).get("event") == "document_start" for l in (OUT / "progress.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()):\n'
     '        return True\n'
     '    con = sqlite3.connect(f"file:{pathlib.Path(ALLOW_PATH).as_posix()}?mode=ro", uri=True)\n'
     '    try:\n'
     '        n = con.execute("select coalesce(sum(calls), 0) from allowance where scope = ? and profile = ? and sha256 in (%s)" % ",".join("?" * len(planned_by_sha)),\n'
     '                        (ALLOW_SCOPE, ALLOW_PROFILE, *planned_by_sha)).fetchone()[0]\n'
     '    finally:\n'
     '        con.close()\n'
     '    return n > 0\n\n\n'
     'def refuse_indeterminate(info: dict) -> None:\n'
     '    """Fail closed: the persisted provider evidence cannot establish that continuing is allowed. Nothing is dispatched,\n'
     '    no stop is fabricated and the run record is left as it was; the refusal is recorded beside the runs."""\n'
     '    (RUNS / "refusals").mkdir(parents=True, exist_ok=True)\n'
     '    with open(RUNS / "refusals" / "REFUSALS.jsonl", "a", encoding="utf-8") as f:\n'
     '        f.write(json.dumps({"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "tag": args.tag, "arm": args.arm, "resume": True,\n'
     '                            "refused": f"indeterminate provider state: {info.get(\'why\')}", "requests_sent": 0}) + "\\n")\n'
     '    progress("runner_refused_indeterminate", why=info.get("why"))\n'
     '    print(f"REFUSED (indeterminate provider state): {info.get(\'why\')} -- zero requests sent; the run record is left untouched")\n'
     '    sys.exit(5)\n\n\n'
     'started = time.perf_counter()\nif args.resume:\n'),
])
patch("dry_provider2.py", [
    ('  PILOT_DRY_FAIL_COUNT=k    ... k of them (default: every later request) -- the consecutive-failure stop probes',
     '  PILOT_DRY_FAIL_COUNT=k    ... k of them (default: every later request) -- the consecutive-failure stop probes\n'
     '  PILOT_DRY_FAIL_AT=i,j,..  scripted failures at exactly those dispatched-request indices of this process (a success between)'),
    ('        self.fail_count = int(os.environ.get("PILOT_DRY_FAIL_COUNT") or 0)\n',
     '        self.fail_count = int(os.environ.get("PILOT_DRY_FAIL_COUNT") or 0)\n'
     '        self.fail_at = {int(x) for x in (os.environ.get("PILOT_DRY_FAIL_AT") or "").split(",") if x.strip()}\n'),
    ('        if self.fail_from and self.calls >= self.fail_from and (not self.fail_count or self.calls < self.fail_from + self.fail_count):\n',
     '        if self.calls in self.fail_at or self.fail_from and self.calls >= self.fail_from and (not self.fail_count or self.calls < self.fail_from + self.fail_count):\n'),
])
for fn in ("runner_probes.py", "lifecycle_probes.py"):
    patch(fn, [('"PILOT_DRY_FAIL_FROM", "PILOT_DRY_FAIL_COUNT", "PILOT_DRY_KILL_AT_STOP"):', '"PILOT_DRY_FAIL_FROM", "PILOT_DRY_FAIL_COUNT", "PILOT_DRY_FAIL_AT", "PILOT_DRY_KILL_AT_STOP"):')])
patch("runner_probes.py", [('PROBES = pathlib.Path(os.environ.get("R22_PROBES_ROOT", "C:/t/r2x/dry-runs/r23-probes"))', 'PROBES = pathlib.Path(os.environ.get("R22_PROBES_ROOT", "C:/t/r2x/dry-runs/r24-probes"))')])
patch("lifecycle_probes.py", [('ROOTS = pathlib.Path(os.environ.get("R23_LIFECYCLE_ROOT", "C:/t/r2x/dry-runs/r23-lifecycle"))', 'ROOTS = pathlib.Path(os.environ.get("R23_LIFECYCLE_ROOT", "C:/t/r2x/dry-runs/r24-lifecycle"))')])
print("patched provider recovery")
