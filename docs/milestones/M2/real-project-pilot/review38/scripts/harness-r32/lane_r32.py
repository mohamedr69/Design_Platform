"""ORCH-05.1 / ORCH-05C / ORCH-08: ONE lane of the r32 run, as a subprocess started by runner_r32.py. Usage:
  lane_r32.py <B|C|R|P> <run config json abs>
B runs in the frozen baseline tree (cwd C:/t/iso/frozen-r12/backend), C, R and P in the candidate tree
(cwd C:/t/iso/cand-r29/backend); every application root is the lane's sandbox (<sandbox base>/<stamp>/inv-<n>/<lane>).

Live mode (RC-3 / RC-5, carried): a lane process -- whether the runner started it or someone started it directly --
executes the SAME preflight as the runner (preflight_r32.live_preflight, now including the request bounds and the
model identity), verifies its AI_EVIDENCE_* switches and provider environment against the declaration (and the
application's settings), and passes the SAME guard (dispatch_guard_r32.authorize, action 'verify') before anything is
built; a configuration with 'auth_path' or any dry injection is refused.

Provider chain (ORCH-08; run_control_r38): StopGuardR38 -> GateStoreProvider (serve a bound fingerprint, or pass the
gate: run INVALID / durable terminal stop / lane allowance / parent budget / project rolling window -> refused or
DEFERRED, recorded) -> allowance_r32.AllowanceProvider (charge before dispatch, settle with outcome and ledger entry) ->
model_identity_r38.IdentityGuard (every response's model and provider against the declaration) ->
  dry:  run_control_r38.DryStub ('dry_refused'; dry-only injections), optionally inside the APPLICATION's LedgerProvider
        on a FAKE ledger file in the run folder (dry_ledger: never the AI ledger)
  live: dispatch_guard_r32.GuardedProvider (authorize() before EVERY request; the real provider, wrapped in the
        application's LedgerProvider on the declared scope, is built only after it; its adapter name must be the declared
        provider)
Visibility (A-09 points 1 and 7): every run-set document of the lane gets a status (COMPLETE / INCOMPLETE / DEFERRED)
with the events that touched it per page (run_control_r38.LaneRecorder); a project-window refusal DEFERS the document
(DeferDocument passes through the application, which catches Exception only; the document's database work is rolled
back; nothing is skipped silently); the application's own budget stops are observed (EvidenceRun.call / the baseline's
submittal _Run.call) and recorded per document and page (application_project_limit / application_document_limit).
reader "application" (live, or dry over SYNTHETIC test documents only) and reader "none" (dry over the real r32 cohort:
no application reader touches a cohort document) as in review34.
Writes only into the lane's out folder, its sandbox, the run folder's identity log and the run's allowance / capture store
(and, dry only, the fake ledger); never the AI ledger in dry mode."""
import json
import os
import pathlib
import subprocess
import sys
import time

LANE, CONFIG_PATH = sys.argv[1], pathlib.Path(sys.argv[2])
CFG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = pathlib.Path(CFG["out_dir"])
MODE, READER = CFG["mode"], CFG.get("reader", "application")
assert MODE in ("dry", "live") and LANE in ("B", "C", "R", "P") and READER in ("application", "none")
if pathlib.Path(CFG.get("harness_dir") or "").resolve() != HERE:
    raise SystemExit(f"refused: the configuration names another harness folder ({CFG.get('harness_dir')}); the lane runs only its own")

import allowance_r32 as AL  # noqa: E402
import dispatch_guard_r32 as DG  # noqa: E402
import model_identity_r38 as MI  # noqa: E402
import preflight_r32 as PF  # noqa: E402

PRE = None
if MODE == "live":
    if READER != "application":
        raise SystemExit("refused: a live lane runs the application reader")
    try:
        PRE = PF.live_preflight(CFG, lane=LANE)                     # RC-3 / RC-5: the runner's preflight, again, in the lane
    except PF.Refused as exc:
        raise SystemExit(f"{exc} [lane {LANE} live preflight]")
elif CFG.get("auth_path") is not None:
    raise SystemExit("refused: an authorization path cannot be configured (RC-3)")
TRUTH = json.loads(pathlib.Path(CFG["truth"]).read_text(encoding="utf-8"))
RUNSET = CFG["run_set"]
if MODE == "dry" and READER == "application":
    cohort = [d["pool_id"] for d in RUNSET if not d["pool_id"].startswith("SYN")]
    assert not cohort, f"dry mode never runs a reader on a cohort document: {cohort[:5]}"
TREE = pathlib.Path(os.getcwd())
EXPECT_TREE = CFG["trees"]["baseline" if LANE == "B" else "candidate"]
assert TREE.as_posix().lower() == EXPECT_TREE.lower(), (TREE, EXPECT_TREE)
sys.path.insert(0, str(TREE))
ROOT = pathlib.Path(CFG["sandbox"][LANE]) if LANE != "P" else None
if ROOT is not None:
    assert os.environ["DATABASE_URL"] == f"sqlite:///{(ROOT / 'db' / 'default.db').as_posix()}", os.environ["DATABASE_URL"]
if MODE == "dry":
    assert not os.environ.get("AI_LEDGER_PATH"), "dry mode: no ledger"

from app.core.config import get_settings  # noqa: E402

settings = get_settings()
assert not settings.data_root
if ROOT is not None:
    assert settings.database_url == os.environ["DATABASE_URL"]
    for name in ("cache_root", "library_root", "uploads_root"):
        assert str(getattr(settings, name) or "").replace("\\", "/").startswith(ROOT.as_posix()), (name, getattr(settings, name))
if MODE == "dry":
    assert not settings.ai_ledger_path
try:                                                                # RC-5: switches and provider environment
    ENV_CHECK = PF.verify_lane_environment(LANE, (CFG.get("lane_switches") or {}).get(LANE), CFG.get("provider_env") if MODE == "live" else None,
                                           os.environ, settings, mode=MODE)
except PF.Refused as exc:
    raise SystemExit(f"{exc} [lane {LANE} environment]")
GUARD = None
OWNER_TOKEN = os.environ.pop(DG.TOKEN_ENV, None)                    # kept in memory only: no child process inherits it
if MODE == "live":
    try:                                                            # RC-3: the same guard, before anything is built
        GUARD = DG.authorize(CFG["declaration_path"], CFG["declaration_sha256"], run_folder=CFG["run_folder"], invocation=CFG["invocation"],
                             action="verify", token=OWNER_TOKEN)
    except DG.DispatchRefused as exc:
        raise SystemExit(f"{exc} [lane {LANE} guard]")

from app.ai import provider as prov  # noqa: E402
from app.ai.provider import AiRequest, AiResponse, TextPart, Usage  # noqa: E402

import capture_store as CS  # noqa: E402
import run_control_r38 as RC  # noqa: E402  (imports capture_store: after the tree is on the path)

RUN_FOLDER = pathlib.Path(CFG["run_folder"])
INVOCATION = int(CFG["invocation"])
PINS = CFG["model_identity"]
INJECT = [i for i in CFG.get("dry_inject") or [] if INVOCATION in (i.get("invocations") or [1])]   # dry drills: this invocation's
if MODE == "live" and (INJECT or CFG.get("dry_ledger") or CFG.get("dry_application_limits")):
    raise SystemExit("refused: injections and fake ledgers are dry-mode drills only")
alias = lambda tier: settings.ai_model_standard if tier == "standard" else settings.ai_model_small  # noqa: E731
current = {"ep": None}
EP_BY_SHA = {d["staged_sha256"]: d["ep"] for d in TRUTH["documents"].values() if d.get("staged_sha256")}
PID_BY_SHA = {TRUTH["documents"][d["pool_id"]]["staged_sha256"]: d["pool_id"] for d in RUNSET if d["pool_id"] in TRUTH["documents"]}
BY_KEY = {d["doc_key"]: d["pool_id"] for d in RUNSET}
order = [] if LANE == "P" else list(RUNSET) + ([{"pool_id": "_reference_only"}] if (LANE == "R" and READER == "none") else [])
recorder = RC.LaneRecorder(LANE, order)


def ep_of():
    """The project of the request being charged: the lane's current document, else the request's source document (the
    probe re-sends C's payloads with their context) -- the project window counts every lane."""
    if current["ep"] is not None:
        return current["ep"]
    return EP_BY_SHA.get(CS.get_context().get("sha256"))


def page_of():
    return CS.get_context().get("page")


LEDGER_LAST = {}
blocked = []


def _record_ledger_entries(led, ai_ledger):
    """Every reservation's ledger entry id (or the id of the refusal it recorded) is kept for the allowance's audit view."""
    original = led.reserve

    def reserve(*a, **k):
        try:
            eid = original(*a, **k)
            LEDGER_LAST["entry"] = eid
            return eid
        except ai_ledger.LedgerRefused:
            import sqlite3
            con = sqlite3.connect(f"file:{pathlib.Path(led.path).as_posix()}?mode=ro", uri=True)
            try:
                LEDGER_LAST["entry"] = con.execute("select max(id) from entries where scope = ? and state = 'refused'", (led.scope,)).fetchone()[0]
            finally:
                con.close()
            raise
    led.reserve = reserve


if MODE == "dry":
    def _forbidden(self, request):
        blocked.append(type(self).__name__)
        raise RuntimeError("dry run: a live provider request is forbidden")

    for cls in (prov.ClaudeProvider, prov.OpenAiProvider, prov.ClaudeCodeProvider):
        cls.complete = _forbidden
    STUB = RC.DryStub(AiResponse, Usage, LANE, INJECT, declared_model=PINS["small"])
    base_inner = STUB
    if CFG.get("dry_ledger"):
        from app.ai import ledger as ai_ledger
        dl = CFG["dry_ledger"]
        lp = pathlib.Path(dl["path"]).resolve()
        assert lp.as_posix().lower().startswith(RUN_FOLDER.resolve().as_posix().lower() + "/"), "a fake ledger lives in the dry run folder"
        assert lp.as_posix().lower() != pathlib.Path("C:/t/r2x/ledger/r2x-ledger.sqlite").resolve().as_posix().lower(), "never the AI ledger"
        DLED = ai_ledger.Ledger(str(lp), dl["scope"], ai_ledger.Limits(**dl["limits"]))
        _record_ledger_entries(DLED, ai_ledger)
        base_inner = ai_ledger.LedgerProvider(STUB, DLED)
    declared = {"provider": STUB.name, "small": PINS["small"], "standard": PINS["standard"]}
    provider_name_fn = lambda: STUB.name  # noqa: E731
else:
    LED = PRE["values"]["ledger"]

    def _build_live():
        builders = {"claude-code": prov.ClaudeCodeProvider, "claude_code": prov.ClaudeCodeProvider, "subscription": prov.ClaudeCodeProvider,
                    "claude": prov.ClaudeProvider, "anthropic": prov.ClaudeProvider, "openai": prov.OpenAiProvider, "gpt": prov.OpenAiProvider}
        PF.verify_ledger_scope(LED)                                 # the scope exists with the declared limits (never created here)
        assert PF._norm(settings.ai_ledger_path) == PF._norm(LED["path"]) and settings.ai_ledger_scope == LED["scope"]
        real = builders[settings.ai_provider.lower()]()
        if getattr(real, "name", None) != PINS["provider"]:
            raise RuntimeError(f"refused: the built provider is {getattr(real, 'name', None)!r}, the declaration binds {PINS['provider']!r}")
        from app.ai import ledger as ai_ledger
        led = ai_ledger.Ledger(settings.ai_ledger_path, settings.ai_ledger_scope, ai_ledger.Limits(**LED["limits"]))
        _record_ledger_entries(led, ai_ledger)
        return ai_ledger.LedgerProvider(real, led)

    GUARDED = DG.GuardedProvider(_build_live, CFG["declaration_path"], CFG["declaration_sha256"], AiResponse, run_folder=CFG["run_folder"],
                                 invocation=CFG["invocation"], token=OWNER_TOKEN)
    base_inner = GUARDED
    declared = {"provider": PINS["provider"], "small": PINS["small"], "standard": PINS["standard"]}
    provider_name_fn = lambda: getattr(getattr(GUARDED.inner, "inner", None), "name", None)  # noqa: E731

IDENT = MI.IdentityGuard(base_inner, AiResponse, declared=declared, run_folder=RUN_FOLDER, invocation=INVOCATION, lane=LANE,
                         log_path=RUN_FOLDER / f"inv-{INVOCATION}" / f"IDENTITY-LOG-{LANE}.jsonl", ctx_fn=CS.get_context, provider_name_fn=provider_name_fn)
MID = RC.CrashAfterResponse(IDENT, LANE, INJECT) if MODE == "dry" else IDENT
if AL.bound_key(CFG["store"]) != CFG["run_key"]:
    raise SystemExit("refused: the capture store is not bound to this run (RC-4)")
allowance = AL.LaneAllowance(CFG["allowance"], CFG["caps"], CFG["project_window"], parent=CFG["parent"], run_key=CFG["run_key"],
                             require_project=MODE == "live", create=False)
alw = AL.AllowanceProvider(allowance, LANE, MID, AiResponse, ep_of=ep_of, context_of=CS.get_context, invocation=INVOCATION,
                           ledger_entry_of=lambda: LEDGER_LAST.pop("entry", None))
store = CS.CaptureStore(CFG["store"])
ctl = RC.ControllerR38()
TRIP = []


def gate(policy_fn, reference_from=None):
    return RC.GateStoreProvider(store, LANE, alw, policy_fn, alias, reference_from=reference_from, allowance=allowance, recorder=recorder, ep_of=ep_of,
                                run_folder=RUN_FOLDER, invocation=INVOCATION, response_cls=AiResponse, page_of=page_of)


def stop_guard(inner):
    return RC.StopGuardR38(inner, ctl, LANE, recorder, AiResponse, allowance=allowance, invocation=INVOCATION, page_of=page_of)


def row_dict(r, ep):
    return {"id": r.id, "ep": ep, "role": r.role, "state": r.state, "error": r.error, "sha256": r.sha256,
            "mirror": {"reference": r.reference, "revision": r.revision, "status": r.status, "system_code": r.system_code},
            "extracted": r.extracted}


def observe_trip(pool_id, res, when, lane=LANE):
    TRIP.append({"pool_id": pool_id, "when": when, "resolved": res["resolved"], "unresolved": res["unresolved"]})
    for c in res["resolved"]:
        ctl.observe(lane, "critical", resolved=True, detail=f"{c['pool_id']} p{c['page']} {c['field']}")
    if lane in ("B", "C"):
        for c in res["unresolved"]:
            ctl.observe(lane, "critical", resolved=False, detail=f"{c['pool_id']} p{c['page']} {c['field']}")


def dump_rows(path):
    import sqlite3

    con = sqlite3.connect(f"file:{(ROOT / 'db' / 'default.db').as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    out = {}
    for r in con.execute("select d.id, p.ep_number, d.relative_path, d.role, d.state, d.error, d.sha256, d.reference, d.revision, d.status, "
                         "d.system_code, d.extracted from project_documents d join projects p on p.id = d.project_id"):
        out[f"EP-{r['ep_number']}/{r['relative_path']}".replace("\\", "/")] = {
            "id": r["id"], "ep": r["ep_number"], "role": r["role"], "state": r["state"], "error": r["error"], "sha256": r["sha256"],
            "mirror": {"reference": r["reference"], "revision": r["revision"], "status": r["status"], "system_code": r["system_code"]},
            "extracted": json.loads(r["extracted"]) if r["extracted"] else None}
    con.close()
    path.write_text(json.dumps(out, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return out


def probe_request(pool_id, tag):
    """A synthetic request (no document content, no image): it exercises the chain and never reaches a provider in dry mode."""
    return AiRequest(task="r33_dry_probe", system="r33 dry-run probe (no document content)", parts=[TextPart("probe", f"{tag}:{pool_id}")],
                     schema={"type": "object"}, max_output_tokens=16)


def _limit_kind(detail: str) -> str:
    return "application_project_limit" if "calls_per_project_per_day" in detail else "application_document_limit"


def exercise(chain, policy_note):
    """reader 'none': one synthetic probe per run-set document through the full chain; every document gets a status."""
    import tripwire_r32 as TW  # noqa: F401  (imports cleanly in this tree; B uses the subprocess path below)
    per_doc = {}
    for d in RUNSET:
        pid = d["pool_id"]
        recorder.current, current["ep"] = pid, d["ep"]
        if not ctl.can_dispatch(LANE):
            recorder.event("not_started", detail=f"lane {LANE} stopped before this document: {ctl.lanes[LANE]['reason']}")
            recorder.set(pid, "INCOMPLETE", f"lane stopped before this document ({ctl.lanes[LANE]['reason']})")
            per_doc[pid] = {"probe": "not_started"}
            continue
        sha = TRUTH["documents"][pid]["staged_sha256"] if pid in TRUTH["documents"] else None
        CS.set_context(sha256=sha, page=1, profile="r33-dry", variant=policy_note)
        try:
            resp = chain.complete(probe_request(pid, "C" if LANE in ("C", "R") else LANE))
        except AL.DeferDocument as dd:
            recorder.set(pid, "DEFERRED", f"project window: {dd.refusal.detail}", retry_at=dd.refusal.retry_at)
            per_doc[pid] = {"probe": "deferred", "retry_at": dd.refusal.retry_at}
            continue
        per_doc[pid] = {"probe": resp.error or "answered"}
        recorder.set(pid, "COMPLETE", "probe sent through the full chain (reader 'none': no document read)")
    if LANE == "R":                                     # a request C never made: dispatched once in lane R (reference-only)
        recorder.current, current["ep"] = "_reference_only", RUNSET[0]["ep"] if RUNSET else None
        CS.set_context(sha256=None, page=1, profile="r33-dry", variant=policy_note)
        try:
            resp = chain.complete(probe_request("reference-only", "R"))
            per_doc["_reference_only"] = {"probe": resp.error or "answered"}
            recorder.set("_reference_only", "COMPLETE", "reference-only probe")
        except AL.DeferDocument as dd:
            per_doc["_reference_only"] = {"probe": "deferred"}
            recorder.set("_reference_only", "DEFERRED", f"project window: {dd.refusal.detail}", retry_at=dd.refusal.retry_at)
    recorder.current = None
    return per_doc


def serves_by_mode():
    import sqlite3

    con = sqlite3.connect(f"file:{pathlib.Path(CFG['store']).as_posix()}?mode=ro", uri=True)
    try:
        return dict(con.execute("select mode, count(*) from serves where lane = ? group by mode", (LANE,)).fetchall())
    finally:
        con.close()


SERVES_BEFORE = serves_by_mode()
t0 = time.perf_counter()
manifest = {"lane": LANE, "mode": MODE, "reader": READER, "tree": str(TREE), "sandbox": str(ROOT) if ROOT else None, "invocation": INVOCATION,
            "run_key": CFG["run_key"], "switch_source": CFG.get("switch_source"), "environment_check": ENV_CHECK,
            "cli_version": CFG.get("cli_version"), "declared_identity": declared,
            "authorization": {k: GUARD[k] for k in ("authorization_sha256", "nonce_sha256", "consumption_record", "invocation")} if GUARD else None}
stopped = None

if LANE == "B":
    from app.database import SessionLocal  # noqa: E402
    from app.models import Project  # noqa: E402
    from app.services import document_processing, document_sync  # noqa: E402
    from app.ai import submittal_reader  # noqa: E402

    G = gate(lambda: CFG["policies"]["B"])
    chain = stop_guard(G)
    prov.set_provider(chain)
    _orig_run_call = submittal_reader._Run.call

    def _run_call(self, *, document_sha, parts):
        """Every form read of B (the processing read AND the reconcile check's repeat) is attributed to ITS document: the
        context names the document's own sha256 (so a repeat is the same bound fingerprint -- served, never re-sent under
        another document's context) and the recorder names its pool id. The baseline's own budget stops (its JobBudget)
        are observed and recorded per document -- never silent."""
        CS.set_context(sha256=document_sha, page=None, profile="b-accepted-path", variant="off")
        recorder.current = PID_BY_SHA.get(document_sha, recorder.current)
        before = self.exhausted
        out = _orig_run_call(self, document_sha=document_sha, parts=parts)
        if self.exhausted and not before:
            kind, pid = _limit_kind(str(self.exhausted)), PID_BY_SHA.get(document_sha)
            recorder.event(kind, pid=pid, detail=f"application budget: {self.exhausted}")
            allowance.record_refusal(LANE, kind, f"application budget: {self.exhausted}", ep=current["ep"], invocation=INVOCATION, doc=pid,
                                     task="read_submittal_form")
        return out
    submittal_reader._Run.call = _run_call

    def b_tripwire(rows_by_pid, when):
        """The candidate's pure evaluator emission functions cannot be imported in the baseline tree: a subprocess."""
        tmp_in, tmp_out = OUT / f"_trip-in-{LANE}.json", OUT / f"_trip-out-{LANE}.json"
        tmp_in.write_text(json.dumps(rows_by_pid, default=str, ensure_ascii=False), encoding="utf-8", newline="\n")
        r = subprocess.run([sys.executable, str(HERE / "tripwire_r32.py"), CFG["truth"], str(tmp_in), str(tmp_out)], cwd=str(HERE),
                           env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "AI_ENABLED": "false"}, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(f"tripwire failed: {r.stderr[-2000:]}")
        res = json.loads(tmp_out.read_text(encoding="utf-8"))
        for pid, x in res.items():
            observe_trip(pid, x, when)
        return res

    if READER == "none":
        manifest["per_document"] = exercise(chain, "off")
        b_tripwire({d["pool_id"]: {"extracted": None} for d in RUNSET}, "exercise_no_facts")
        rows = dump_rows(OUT / "rows-B.json")
        manifest |= {"policy": CFG["policies"]["B"], "rows": len(rows), "application_processing_run": False}
    else:
        _process, _apply, _read_form = document_sync.process, document_sync.apply_form_reading, document_sync.read_form_or_raise

        def _after(row, project):
            pid = BY_KEY.get(f"EP-{project.ep_number}/{row.relative_path}".replace("\\", "/"))
            if pid is not None:
                b_tripwire({pid: row_dict(row, project.ep_number)}, "after_document")

        def process(db, project, row, path, root, **kw):
            current["ep"] = project.ep_number
            recorder.current = BY_KEY.get(f"EP-{project.ep_number}/{row.relative_path}".replace("\\", "/"))
            CS.set_context(sha256=row.sha256, page=None, profile="b-accepted-path", variant="off")
            out = _process(db, project, row, path, root, **kw)
            db.flush()
            _after(row, project)
            return out

        def read_form_or_raise(db, run, path, sha256, **kw):
            recorder.current = PID_BY_SHA.get(sha256, recorder.current)
            CS.set_context(sha256=sha256, page=None, profile="b-accepted-path", variant="off")
            return _read_form(db, run, path, sha256, **kw)

        def apply_form_reading(db, project, row, path, root, reading, **kw):
            out = _apply(db, project, row, path, root, reading, **kw)
            db.flush()
            _after(row, project)
            return out

        document_sync.process, document_sync.apply_form_reading, document_sync.read_form_or_raise = process, apply_form_reading, read_form_or_raise

        class Ctx:
            def progress(self, *a, **k):
                pass

            def check(self):
                if ctl.lanes[LANE]["state"] != "running":
                    raise RC.StopLane(ctl.lanes[LANE]["reason"])

        per_project, deferred = {}, {}
        with SessionLocal() as db:
            for project in db.query(Project).order_by(Project.id).all():
                current["ep"] = project.ep_number
                key = str(project.ep_number)
                if stopped:
                    per_project[key] = {"not_started": f"lane B stopped before this project: {stopped}"}
                    continue
                try:
                    per_project[key] = document_processing.run(db, project, ctx=Ctx(), provider=chain)
                except RC.StopLane as exc:
                    stopped = str(exc)
                    db.rollback()
                except AL.DeferDocument as dd:
                    db.rollback()
                    deferred[key] = dd.refusal
                    per_project[key] = {"deferred": dd.refusal.detail, "retry_at": dd.refusal.retry_at}
                db.commit()
        rows = dump_rows(OUT / "rows-B.json")
        for d in RUNSET:
            pid, ep, row = d["pool_id"], str(d["ep"]), rows.get(d["doc_key"])
            if ep in deferred:
                recorder.set(pid, "DEFERRED", f"project window: {deferred[ep].detail}", retry_at=deferred[ep].retry_at)
            elif (per_project.get(ep) or {}).get("not_started") or (stopped and (row or {}).get("state") != "fresh"):
                recorder.event("not_started", pid=pid, detail=f"lane B stopped: {stopped}")
                recorder.set(pid, "INCOMPLETE", f"lane B stopped before this document was read ({stopped})")
            elif row is None:
                recorder.event("prerequisite_failed", pid=pid, detail="not registered in the B sandbox")
                recorder.set(pid, "INCOMPLETE", "not registered", cls="failure")
            elif row["state"] != "fresh":
                recorder.event("prerequisite_failed", pid=pid, detail=f"B row state {row['state']}: {row.get('error')}")
                recorder.set(pid, "INCOMPLETE", f"B row state {row['state']}", cls="failure")
            else:
                recorder.set(pid, "COMPLETE", "processed by the application (B)")
        b_tripwire({BY_KEY[k]: v for k, v in rows.items() if k in BY_KEY}, "final")
        manifest |= {"per_project": per_project, "policy": CFG["policies"]["B"], "rows": len(rows), "application_processing_run": True,
                     "deferred_projects": {ep: {"retry_at": r.retry_at, "detail": r.detail} for ep, r in deferred.items()}}
else:
    from app.ai import evidence_reader as er  # noqa: E402
    import tripwire_r32 as TW  # noqa: E402

    EV = TW.load_evaluator()
    if LANE == "P":
        cpol = json.loads((OUT / "LANE-C.json").read_text(encoding="utf-8"))["policy_version"]
        G = gate(lambda: "probe:" + cpol)
        chain = stop_guard(G)
        result = RC.probe_r38(store, chain, "probe:" + cpol, alias, recorder, rate=0.15, seed="m2-r30-variation-2026-10-02")
        manifest |= {"probe": result, "policy_version": "probe:" + cpol, "store_dispatched_to_inner": G.dispatched}
    else:
        from app.ai import submittal_reader  # noqa: E402
        from app.database import SessionLocal  # noqa: E402
        from app.models import Project, ProjectDocument  # noqa: E402

        CS.install_context(er)
        _orig_call = er.EvidenceRun.call

        def _call(self, **kw):
            """The application's own budget stops (its per-document JobBudget), observed and recorded per page -- never silent."""
            before = self.exhausted
            out = _orig_call(self, **kw)
            ex = str(self.exhausted or "")
            if self.exhausted and not before and not ex.startswith(("harness allowance refused", "ledger refused")):
                kind = _limit_kind(ex)
                recorder.event(kind, page=kw.get("page"), task=kw.get("task"), detail=f"application budget: {ex}")
                allowance.record_refusal(LANE, kind, f"application budget: {ex}", ep=current["ep"], invocation=INVOCATION, doc=recorder.current,
                                         page=kw.get("page"), task=kw.get("task"))
            return out
        er.EvidenceRun.call = _call
        submittal_reader.available = lambda project, provider=None: None
        G = gate(lambda: er.EVIDENCE_POLICY_VERSION, reference_from="C" if LANE == "R" else None)
        chain = stop_guard(G)
        ai_context = {"variant": "EV1", "profile": "default", "policies": [er.EVIDENCE_POLICY_VERSION]}
        per_doc = {}
        if READER == "none":
            per_doc = exercise(chain, "EV1")
            for d in RUNSET:
                res = TW.tripwire(TRUTH, d["pool_id"], [])
                observe_trip(d["pool_id"], res, "exercise_no_facts")
        else:
            with SessionLocal() as db:
                projects = {p.ep_number: p for p in db.query(Project).all()}
                for d in RUNSET:
                    pid = d["pool_id"]
                    recorder.current = pid
                    if ctl.lanes[LANE]["state"] != "running":
                        stopped = ctl.lanes[LANE]["reason"]
                        recorder.event("not_started", detail=f"lane {LANE} stopped before this document: {stopped}")
                        recorder.set(pid, "INCOMPLETE", f"lane stopped before this document ({stopped})")
                        per_doc[pid] = {"not_started": stopped}
                        continue
                    project = projects.get(d["ep"]) or projects.get(int(d["ep"]) if str(d["ep"]).isdigit() else d["ep"])
                    row = None
                    if project is not None:
                        row = next((r for r in db.query(ProjectDocument).filter(ProjectDocument.project_id == project.id)
                                    if f"EP-{project.ep_number}/{r.relative_path}".replace("\\", "/") == d["doc_key"]), None)
                    if row is None or row.state != "fresh" or not (row.path or "").lower().endswith(".pdf"):
                        why = "no fresh PDF row in the B state" if row is not None else "not registered"
                        recorder.event("prerequisite_failed", detail=f"{why} (state {getattr(row, 'state', None)})")
                        recorder.set(pid, "INCOMPLETE", why, cls="failure")
                        per_doc[pid] = {"skipped": why, "state": getattr(row, "state", None)}
                        continue
                    current["ep"] = d["ep"]
                    try:
                        per_doc[pid] = er.evidence_stage(db, project, [(row, pathlib.Path(row.path))], provider=chain, variant="EV1")
                        db.commit()
                    except AL.DeferDocument as dd:
                        db.rollback()
                        recorder.set(pid, "DEFERRED", f"project window: {dd.refusal.detail}", retry_at=dd.refusal.retry_at)
                        per_doc[pid] = {"deferred": dd.refusal.detail, "retry_at": dd.refusal.retry_at}
                        continue
                    db.refresh(row)
                    facts = TW.facts_from_row(EV, row_dict(row, project.ep_number), ai_context, d["doc_key"])
                    observe_trip(pid, TW.tripwire(TRUTH, pid, facts, row.sha256), "after_document" if LANE == "C" else "reference")
                    recorder.set(pid, "COMPLETE", "read by the application's evidence stage")
            recorder.current = None
        dump_rows(OUT / f"rows-{LANE}.json")
        manifest |= {"policy_version": er.EVIDENCE_POLICY_VERSION, "reader_version": er.READER_VERSION, "per_document": per_doc,
                     "env_switches": {k: v for k, v in os.environ.items() if k.startswith("AI_EVIDENCE_")},
                     "evidence_tasks": sorted(er.PROMPTS), "store_dispatched_to_inner": G.dispatched,
                     "application_reader_run": READER == "application"}
after = serves_by_mode()
docs = recorder.documents()
manifest |= {"seconds": round(time.perf_counter() - t0, 1), "events": chain.events, "stats": chain.stats, "tripwire": TRIP, "stop_state": ctl.state(), "lane_stop_state": ctl.state()["lanes"][LANE], "stopped": stopped,
             "live_provider_attempts_blocked": blocked, "allowance_used": allowance.used(LANE), "allowance_refused": alw.refused,
             "allowance_charged_this_invocation": alw.charged, "gate": {"served": G.served, "refused": G.gate_refused, "deferred": G.deferred},
             "serves_by_mode": {k: after.get(k, 0) - SERVES_BEFORE.get(k, 0) for k in after},
             "documents": docs, "limit_events": recorder.events,
             "deferred": {pid: v["retry_at"] for pid, v in docs.items() if v["status"] == "DEFERRED"},
             "identity": {"checked": IDENT.checked, "mismatches": IDENT.mismatches, "refused": IDENT.refused,
                          "log": (RUN_FOLDER / f"inv-{INVOCATION}" / f"IDENTITY-LOG-{LANE}.jsonl").as_posix()},
             "dry_stub_calls": (STUB.calls if MODE == "dry" else None),
             "guard": {"refused": getattr(base_inner, "refused", None), "dispatched": getattr(base_inner, "dispatched", 0)} if MODE == "live" else None,
             "model_requests": 0 if MODE == "dry" else getattr(base_inner, "dispatched", 0)}
assert not blocked, "a live provider was reached"
(OUT / f"LANE-{LANE}.json").write_text(json.dumps(manifest, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: manifest.get(k) for k in ("lane", "mode", "reader", "seconds", "stats", "lane_stop_state", "model_requests", "allowance_used", "deferred")},
                 default=str))
