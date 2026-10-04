"""ORCH-05.1 (Review 33 C-5) and ORCH-05C (Review 34 RC-3, RC-4, RC-5): ONE lane of the r32 run, as a subprocess started
by runner_r32.py. Usage:
  lane_r32.py <B|C|R|P> <run config json abs>
B runs in the frozen baseline tree (cwd C:/t/iso/frozen-r12/backend), C, R and P in the candidate tree
(cwd C:/t/iso/cand-r29/backend); every application root is the lane's sandbox (C:/t/r2x/r34-sandbox/<stamp>/inv-<n>/<lane>).

Live mode (RC-3 / RC-5): a lane process -- whether the runner started it or someone started it directly -- executes the
SAME preflight as the runner (preflight_r32.live_preflight: binding manifest, the declaration contract, run set, HEADs,
truth and population gate, the declared ledger scope, and its run configuration against the declaration), verifies its
AI_EVIDENCE_* switches and provider environment against the declaration (and the application's settings), and passes the
SAME guard (dispatch_guard_r32.authorize, action 'verify': the pinned authorization consumed by THIS invocation) before
anything is built; a configuration with 'auth_path' or a dry fault is refused. The harness folder is the one this file is
in (a configuration cannot redirect it).

Provider chain (the only way a request can leave the process):
  stop guard (refuses once the lane is stopped) -> capture_store.StoreProvider (reserve before dispatch; lane-scoped;
  R served C's capture by content key) -> allowance_r32.AllowanceProvider (the declaration's ONE durable allowance: lane
  cap and the per-project UTC-day limit across all lanes; live: an unattributed request is refused)
  -> dry: dispatch_guard_r32.DryRefusingProvider ('dry_refused', no provider exists)
     live: dispatch_guard_r32.GuardedProvider (authorize() before EVERY request; the real provider, wrapped in the
           application's LedgerProvider on the declared scope, is built only after it)
In dry mode every live provider class of the application is also replaced by one that raises. A dry drill may inject a
crash ('dry_fault': the process exits right after its N-th dispatch was sent, leaving the row reserved and charged).

reader "application" (live, or dry over SYNTHETIC test documents only):
  B: the application's processing (document_processing.run) of the registered PENDING rows; the per-field tripwire runs
     after every document the application writes (document_sync.process and apply_form_reading are wrapped) and once
     more over every run-set row at the end; a critical acceptance on resolved truth makes B terminal (INVALID);
  C / R: the evidence stage, one run-set document at a time, with the lane's switches; tripwire after each document in C
     (R: reference findings only);  P: the seeded 15 % variation probe over C's answered dispatches.
reader "none" (dry over the real r32 cohort): NO application reader touches a cohort document -- that would create a
  prediction, which no authority allows. The lane loads its tree and sandbox under the same confinement asserts, then
  sends one synthetic probe request per run-set document through the whole provider chain (R re-sends C's probe, served
  from C's capture, plus one reference-only probe), and runs the tripwire machinery with an empty fact list.
Writes only into the lane's out folder, its sandbox and the run's allowance / capture store; never the AI ledger in dry
mode (no ledger path at all); in live mode only the application's LedgerProvider writes, to the declared scope."""
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
from app.ai.provider import AiRequest, AiResponse, TextPart  # noqa: E402

import capture_store as CS  # noqa: E402
import stop_rules  # noqa: E402

blocked = []
if MODE == "dry":
    def _forbidden(self, request):
        blocked.append(type(self).__name__)
        raise RuntimeError("dry run: a live provider request is forbidden")

    for cls in (prov.ClaudeProvider, prov.OpenAiProvider, prov.ClaudeCodeProvider):
        cls.complete = _forbidden
    inner = DG.DryRefusingProvider(AiResponse)
    fault = CFG.get("dry_fault") or {}
    if fault.get("lane") == LANE:
        class CrashAfterSend:
            """Dry drill: the process dies right after its N-th dispatch was sent (row reserved, charge recorded)."""
            def __init__(self, stub, n):
                self.stub, self.n, self.calls = stub, int(n), 0

            def complete(self, request):
                resp = self.stub.complete(request)
                self.calls += 1
                if self.calls >= self.n:
                    sys.stdout.flush()
                    os._exit(75)
                return resp

        inner = CrashAfterSend(inner, fault["after_dispatches"])
else:
    LED = PRE["values"]["ledger"]

    def _build_live():
        builders = {"claude-code": prov.ClaudeCodeProvider, "claude_code": prov.ClaudeCodeProvider, "subscription": prov.ClaudeCodeProvider,
                    "claude": prov.ClaudeProvider, "anthropic": prov.ClaudeProvider, "openai": prov.OpenAiProvider, "gpt": prov.OpenAiProvider}
        PF.verify_ledger_scope(LED)                                 # the scope exists with the declared limits (never created here)
        assert PF._norm(settings.ai_ledger_path) == PF._norm(LED["path"]) and settings.ai_ledger_scope == LED["scope"]
        real = builders[settings.ai_provider.lower()]()
        from app.ai import ledger as ai_ledger

        return ai_ledger.LedgerProvider(real, ai_ledger.Ledger(settings.ai_ledger_path, settings.ai_ledger_scope, ai_ledger.Limits(**LED["limits"])))

    inner = DG.GuardedProvider(_build_live, CFG["declaration_path"], CFG["declaration_sha256"], AiResponse, run_folder=CFG["run_folder"],
                               invocation=CFG["invocation"], token=OWNER_TOKEN)

alias = lambda tier: settings.ai_model_standard if tier == "standard" else settings.ai_model_small  # noqa: E731
current = {"ep": None}
EP_BY_SHA = {d["staged_sha256"]: d["ep"] for d in TRUTH["documents"].values() if d.get("staged_sha256")}


def ep_of():
    """The project of the request being charged: the lane's current document, else the request's source document (the
    probe re-sends C's payloads with their context) -- the project-day limit counts every lane."""
    if current["ep"] is not None:
        return current["ep"]
    return EP_BY_SHA.get(CS.get_context().get("sha256"))


if AL.bound_key(CFG["store"]) != CFG["run_key"]:
    raise SystemExit("refused: the capture store is not bound to this run (RC-4)")
allowance = AL.LaneAllowance(CFG["allowance"], CFG["caps"], CFG["project_day_limit"], run_key=CFG["run_key"], require_project=MODE == "live", create=False)
alw = AL.AllowanceProvider(allowance, LANE, inner, AiResponse, ep_of=ep_of)
store = CS.CaptureStore(CFG["store"])
ctl = stop_rules.StopController()
events = []
stats = {"stopped_by_guard": 0, "ok": 0}
TRIP = []
BY_KEY = {d["doc_key"]: d["pool_id"] for d in RUNSET}


class StopLane(BaseException):
    """Raised at the application's next check point once the lane is stopped (passes through its except Exception)."""


class StopGuard:
    name, ready, status = "stop-guard", True, "r34 per-lane stop guard"

    def __init__(self, inner_provider):
        self.inner = inner_provider

    def complete(self, request):
        if not ctl.can_dispatch(LANE):
            stats["stopped_by_guard"] += 1
            return AiResponse(data=None, model="guard", error="stopped", error_detail=f"lane {LANE} stopped: {ctl.lanes[LANE]['reason']}")
        resp = self.inner.complete(request)
        err = resp.error
        if resp.ok:
            kind = "ok"
        elif err == "dry_refused":
            kind = "dry_refused"                       # a dry-run artefact: never fed to the stop controller
        elif err in ("allowance_refused", "dispatch_refused"):
            kind = "budget_refusal"
        else:
            kind = "provider_failure"
        key = "ok" if kind == "ok" else (err if err in ("dry_refused", "allowance_refused", "dispatch_refused", "interrupted_charged") else "provider_failure")
        stats[key] = stats.get(key, 0) + 1
        events.append({"lane": LANE, "kind": kind, "task": getattr(request, "task", None), "error": err, "ep": current["ep"]})
        if kind != "dry_refused":
            ctl.observe(LANE, kind)
        return resp


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


def exercise(chain, policy_note):
    """reader 'none': one synthetic probe per run-set document through the full chain; tripwire with no facts."""
    import tripwire_r32 as TW  # noqa: F401  (imports cleanly in this tree; B uses the subprocess path below)
    per_doc = {}
    for d in RUNSET:
        current["ep"] = d["ep"]
        sha = TRUTH["documents"][d["pool_id"]]["staged_sha256"] if d["pool_id"] in TRUTH["documents"] else None
        CS.set_context(sha256=sha, page=1, profile="r33-dry", variant=policy_note)
        resp = chain.complete(probe_request(d["pool_id"], "C" if LANE in ("C", "R") else LANE))
        per_doc[d["pool_id"]] = {"probe": resp.error or "answered"}
    if LANE == "R":                                     # a request C never made: dispatched once in lane R (reference-only)
        CS.set_context(sha256=None, page=1, profile="r33-dry", variant=policy_note)
        per_doc["_reference_only"] = {"probe": chain.complete(probe_request("reference-only", "R")).error or "answered"}
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
manifest = {"lane": LANE, "mode": MODE, "reader": READER, "tree": str(TREE), "sandbox": str(ROOT) if ROOT else None, "invocation": CFG.get("invocation"),
            "run_key": CFG["run_key"], "switch_source": CFG.get("switch_source"), "environment_check": ENV_CHECK,
            "authorization": {k: GUARD[k] for k in ("authorization_sha256", "nonce_sha256", "consumption_record", "invocation")} if GUARD else None}

if LANE == "B":
    from app.database import SessionLocal  # noqa: E402
    from app.models import Project  # noqa: E402
    from app.services import document_processing, document_sync  # noqa: E402

    chain = StopGuard(CS.StoreProvider(store, "B", alw, lambda: CFG["policies"]["B"], alias))
    prov.set_provider(chain)

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
            CS.set_context(sha256=row.sha256, page=None, profile="b-accepted-path", variant="off")
            out = _process(db, project, row, path, root, **kw)
            db.flush()
            _after(row, project)
            return out

        def read_form_or_raise(db, run, path, sha256, **kw):
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
                    raise StopLane(ctl.lanes[LANE]["reason"])

        per_project, stopped = {}, None
        with SessionLocal() as db:
            for project in db.query(Project).order_by(Project.id).all():
                if stopped:
                    break
                current["ep"] = project.ep_number
                try:
                    per_project[project.ep_number] = document_processing.run(db, project, ctx=Ctx(), provider=chain)
                except StopLane as exc:
                    stopped = str(exc)
                    db.rollback()
                db.commit()
        rows = dump_rows(OUT / "rows-B.json")
        b_tripwire({BY_KEY[k]: v for k, v in rows.items() if k in BY_KEY}, "final")
        manifest |= {"per_project": per_project, "stopped": stopped, "policy": CFG["policies"]["B"], "rows": len(rows),
                     "application_processing_run": True}
else:
    from app.ai import evidence_reader as er  # noqa: E402
    import tripwire_r32 as TW  # noqa: E402

    EV = TW.load_evaluator()
    if LANE == "P":
        cpol = json.loads((OUT / "LANE-C.json").read_text(encoding="utf-8"))["policy_version"]
        result = CS.probe(store, StopGuard(alw), "probe:" + cpol, alias, rate=0.15, seed="m2-r30-variation-2026-10-02")
        manifest |= {"probe": result, "policy_version": "probe:" + cpol}
    else:
        from app.ai import submittal_reader  # noqa: E402
        from app.database import SessionLocal  # noqa: E402
        from app.models import Project, ProjectDocument  # noqa: E402

        CS.install_context(er)
        submittal_reader.available = lambda project, provider=None: None
        sp = CS.StoreProvider(store, LANE, alw, lambda: er.EVIDENCE_POLICY_VERSION, alias, reference_from="C" if LANE == "R" else None)
        chain = StopGuard(sp)
        ai_context = {"variant": "EV1", "profile": "default", "policies": [er.EVIDENCE_POLICY_VERSION]}
        per_doc, stopped = {}, None
        if READER == "none":
            per_doc = exercise(chain, "EV1")
            for d in RUNSET:
                res = TW.tripwire(TRUTH, d["pool_id"], [])
                observe_trip(d["pool_id"], res, "exercise_no_facts")
        else:
            with SessionLocal() as db:
                projects = {p.ep_number: p for p in db.query(Project).all()}
                for d in RUNSET:
                    if ctl.lanes[LANE]["state"] != "running":
                        stopped = ctl.lanes[LANE]["reason"]
                        break
                    project = projects.get(d["ep"])
                    row = None
                    if project is not None:
                        row = next((r for r in db.query(ProjectDocument).filter(ProjectDocument.project_id == project.id)
                                    if f"EP-{project.ep_number}/{r.relative_path}".replace("\\", "/") == d["doc_key"]), None)
                    if row is None or row.state != "fresh" or not (row.path or "").lower().endswith(".pdf"):
                        per_doc[d["pool_id"]] = {"skipped": "no fresh PDF row in the B state" if row is not None else "not registered",
                                                 "state": getattr(row, "state", None)}
                        continue
                    current["ep"] = d["ep"]
                    per_doc[d["pool_id"]] = er.evidence_stage(db, project, [(row, pathlib.Path(row.path))], provider=chain, variant="EV1")
                    db.commit()
                    db.refresh(row)
                    facts = TW.facts_from_row(EV, row_dict(row, project.ep_number), ai_context, d["doc_key"])
                    observe_trip(d["pool_id"], TW.tripwire(TRUTH, d["pool_id"], facts), "after_document" if LANE == "C" else "reference")
        dump_rows(OUT / f"rows-{LANE}.json")
        manifest |= {"policy_version": er.EVIDENCE_POLICY_VERSION, "reader_version": er.READER_VERSION, "per_document": per_doc,
                     "stopped": stopped, "env_switches": {k: v for k, v in os.environ.items() if k.startswith("AI_EVIDENCE_")},
                     "evidence_tasks": sorted(er.PROMPTS), "store_dispatched_to_inner": sp.dispatched,
                     "application_reader_run": READER == "application"}
after = serves_by_mode()
manifest |= {"seconds": round(time.perf_counter() - t0, 1), "events": events, "stats": stats, "tripwire": TRIP,
             "stop_state": ctl.state(), "lane_stop_state": ctl.state()["lanes"][LANE], "live_provider_attempts_blocked": blocked,
             "allowance_used": allowance.used(LANE), "allowance_refused": alw.refused, "allowance_charged_this_invocation": alw.charged,
             "serves_by_mode": {k: after.get(k, 0) - SERVES_BEFORE.get(k, 0) for k in after},
             "dry_stub_calls": (getattr(inner, "calls", None) if MODE == "dry" else None),
             "guard": {"refused": getattr(inner, "refused", None), "dispatched": getattr(inner, "dispatched", 0)} if MODE == "live" else None,
             "model_requests": 0 if MODE == "dry" else getattr(inner, "dispatched", 0)}
assert not blocked, "a live provider was reached"
(OUT / f"LANE-{LANE}.json").write_text(json.dumps(manifest, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: manifest.get(k) for k in ("lane", "mode", "reader", "seconds", "stats", "lane_stop_state", "model_requests", "allowance_used")}, default=str))
