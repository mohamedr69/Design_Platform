"""One-off patch of the r39 development copy of lane_r32.py (exact string replacements; refuses if any anchor is missing
or not unique). Writes only C:/t/iso/work/r2x/r39/harness-r32/lane_r32.py."""
import pathlib
import sys

P = pathlib.Path("C:/t/iso/work/r2x/r39/harness-r32/lane_r32.py")
s = P.read_text(encoding="utf-8")

REPL = [
    # docstring
    ("""Writes only into the lane's out folder, its sandbox, the run folder's identity log and the run's allowance / capture store
(and, dry only, the fake ledger); never the AI ledger in dry mode.\"\"\"""",
     """ORCH-08C (Verification 39):
  R39-04  before anything is built, every lane (live AND dry, every invocation and resume) verifies the declared
          application_env (DRAWINGS_AI_REVIEW_ENABLED=false) in its environment and in the application's settings, and
          that the application's drawings-AI review reports itself switched off; the gate refuses any request whose task
          kind is not declared for the lane or that carries no / a stale document context (the lane opens a document
          scope per document and clears the context after it): a contract breach, the run INVALID.
  R39-06  after each document of C / R the pages the application did not read under its own per-document limits (the
          reader's cap, the JobBudget, a reader exception) are taken from the attempt the application stored and recorded
          per page; the document stays COMPLETE with unread_pages. B's form read refused by the application's own
          per-document budget is recorded the same way.
  R39-16  a repeat of a failed request is dispatched again (the gate), recorded as a retry with its ordinal.
Writes only into the lane's out folder, its sandbox, the run folder's identity log, contract-breach record and the run's
allowance / capture store (and, dry only, the fake ledger); never the AI ledger in dry mode.\"\"\""""),
    # application env verification
    ("""except PF.Refused as exc:
    raise SystemExit(f"{exc} [lane {LANE} environment]")
GUARD = None""",
     """except PF.Refused as exc:
    raise SystemExit(f"{exc} [lane {LANE} environment]")
try:                                                                # ORCH-08C (R39-04): the declared application environment
    APP_ENV_CHECK = PF.verify_application_env(LANE, CFG.get("application_env"), os.environ, settings)
except PF.Refused as exc:
    raise SystemExit(f"{exc} [lane {LANE} application environment]")
from app.services import drawing_ai_review as _dar  # noqa: E402   (the module exists in both trees; enabled() reads settings first)

_dar_on, _dar_why = _dar.enabled()
if _dar_on:
    raise SystemExit(f"refused: lane {LANE}: the application's drawings-AI review reports itself enabled ({_dar_why}) [lane {LANE} application environment]")
APP_ENV_CHECK["drawings_ai_review_enabled"] = {"enabled": False, "why": _dar_why}
GUARD = None"""),
    # task kinds and the document scope
    ("""order = [] if LANE == "P" else list(RUNSET) + ([{"pool_id": "_reference_only"}] if (LANE == "R" and READER == "none") else [])
recorder = RC.LaneRecorder(LANE, order)
""",
     """order = [] if LANE == "P" else list(RUNSET) + ([{"pool_id": "_reference_only"}] if (LANE == "R" and READER == "none") else [])
recorder = RC.LaneRecorder(LANE, order)
TASK_KINDS = set((CFG.get("lane_task_kinds") or {}).get(LANE) or [])         # ORCH-08C (R39-04): the declared task kinds of this lane
if MODE == "dry" and READER == "none":
    TASK_KINDS.add(PF.DRY_PROBE_TASK)                                         # dry exercise only: its synthetic probe request
if not TASK_KINDS:
    raise SystemExit(f"refused: lane {LANE} has no declared task kinds (lane_task_kinds)")
SHA_BY_PID = {d["pool_id"]: TRUTH["documents"][d["pool_id"]]["staged_sha256"] for d in RUNSET if d["pool_id"] in TRUTH["documents"]}


class doc_scope:
    \"\"\"ORCH-08C: the lane reads ONE document: requests must carry its context; on exit the previous state is restored, so
    after the outermost scope the context is CLEARED (a later request has no context and is refused at the gate).\"\"\"

    def __init__(self, pid, sha, **ctx):
        self.pid, self.sha, self.ctx = pid, sha, ctx

    def __enter__(self):
        self.saved = (recorder.current, recorder.expected_sha, CS.get_context())
        recorder.begin(self.pid, self.sha)
        CS.set_context(sha256=self.sha, **self.ctx)
        return self

    def __exit__(self, *exc):
        recorder.current, recorder.expected_sha = self.saved[0], self.saved[1]
        CS.set_context(**self.saved[2])
        return False
"""),
    # gate parameters
    ("""    return RC.GateStoreProvider(store, LANE, alw, policy_fn, alias, reference_from=reference_from, allowance=allowance, recorder=recorder, ep_of=ep_of,
                                run_folder=RUN_FOLDER, invocation=INVOCATION, response_cls=AiResponse, page_of=page_of)""",
     """    return RC.GateStoreProvider(store, LANE, alw, policy_fn, alias, reference_from=reference_from, allowance=allowance, recorder=recorder, ep_of=ep_of,
                                run_folder=RUN_FOLDER, invocation=INVOCATION, response_cls=AiResponse, page_of=page_of, task_kinds=TASK_KINDS,
                                expected_sha_of=lambda: recorder.expected_sha)"""),
    # allowance with project totals
    ("""allowance = AL.LaneAllowance(CFG["allowance"], CFG["caps"], CFG["project_window"], parent=CFG["parent"], run_key=CFG["run_key"],
                             require_project=MODE == "live", create=False)""",
     """allowance = AL.LaneAllowance(CFG["allowance"], CFG["caps"], CFG["project_window"], parent=CFG["parent"], run_key=CFG["run_key"],
                             require_project=MODE == "live", create=False, project_totals=CFG.get("project_totals"))"""),
    # dry injections of undeclared / context-free requests (helpers before exercise)
    ("""def _limit_kind(detail: str) -> str:""",
     """def inject_requests(chain, after: int, *, sha=None, pid=None):
    \"\"\"Dry drill only (ORCH-08C visibility): send the injected undeclared / context-free requests that name this point
    (`after` = the number of documents the lane has finished; 0 = the end of B's processing). An undeclared task kind is
    sent with the current document's context; a context-free request carries a DECLARED task kind and no context.\"\"\"
    for i in INJECT:
        if i.get("lane") != LANE or after not in (i.get("calls") or []):
            continue
        if i["kind"] == "undeclared_request":
            task = i.get("task") or "drawings_reply_match"
            with doc_scope(pid, sha, page=None, profile="drill", variant="drill"):
                chain.complete(AiRequest(task=task, system="r39 drill: an undeclared request path", parts=[TextPart("t", f"undeclared:{after}")],
                                         schema={"type": "object"}, max_output_tokens=16))
        elif i["kind"] == "context_free_request":
            CS.set_context()
            saved = (recorder.current, recorder.expected_sha)
            recorder.current, recorder.expected_sha = None, None
            chain.complete(AiRequest(task=i.get("task") or sorted(TASK_KINDS)[0], system="r39 drill: a request without a document context",
                                     parts=[TextPart("t", f"no-context:{after}")], schema={"type": "object"}, max_output_tokens=16))
            recorder.current, recorder.expected_sha = saved


def _limit_kind(detail: str) -> str:"""),
    # exercise: document scopes, retry_full, injections
    ("""    for d in RUNSET:
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
    return per_doc""",
     """    for n, d in enumerate(RUNSET, 1):
        pid = d["pool_id"]
        current["ep"] = d["ep"]
        sha = SHA_BY_PID.get(pid)
        if not ctl.can_dispatch(LANE):
            recorder.event("not_started", pid=pid, detail=f"lane {LANE} stopped before this document: {ctl.lanes[LANE]['reason']}")
            recorder.set(pid, "INCOMPLETE", f"lane stopped before this document ({ctl.lanes[LANE]['reason']})")
            per_doc[pid] = {"probe": "not_started"}
            continue
        try:
            with doc_scope(pid, sha, page=1, profile="r33-dry", variant=policy_note):
                resp = chain.complete(probe_request(pid, "C" if LANE in ("C", "R") else LANE))
        except AL.DeferDocument as dd:
            recorder.set(pid, "DEFERRED", f"project window: {dd.refusal.detail}", retry_at=dd.refusal.retry_at, retry_full=dd.refusal.retry_at_full)
            per_doc[pid] = {"probe": "deferred", "retry_at": dd.refusal.retry_at}
            continue
        per_doc[pid] = {"probe": resp.error or "answered"}
        recorder.set(pid, "COMPLETE", "probe sent through the full chain (reader 'none': no document read)")
        inject_requests(chain, n, sha=sha, pid=pid)
    if LANE == "R":                                     # a request C never made: dispatched once in lane R (reference-only)
        current["ep"] = RUNSET[0]["ep"] if RUNSET else None
        ref_sha = SHA_BY_PID.get(RUNSET[0]["pool_id"]) if RUNSET else None   # attributed to the first run-set document's context
        try:
            with doc_scope("_reference_only", ref_sha, page=1, profile="r33-dry", variant=policy_note):
                resp = chain.complete(probe_request("reference-only", "R"))
            per_doc["_reference_only"] = {"probe": resp.error or "answered"}
            recorder.set("_reference_only", "COMPLETE", "reference-only probe")
        except AL.DeferDocument as dd:
            per_doc["_reference_only"] = {"probe": "deferred"}
            recorder.set("_reference_only", "DEFERRED", f"project window: {dd.refusal.detail}", retry_at=dd.refusal.retry_at,
                         retry_full=dd.refusal.retry_at_full)
    recorder.end()
    return per_doc"""),
    # B: form-read wrapper with a document scope; application budget -> unread pages
    ("""        CS.set_context(sha256=document_sha, page=None, profile="b-accepted-path", variant="off")
        recorder.current = PID_BY_SHA.get(document_sha, recorder.current)
        before = self.exhausted
        out = _orig_run_call(self, document_sha=document_sha, parts=parts)
        if self.exhausted and not before:
            kind, pid = _limit_kind(str(self.exhausted)), PID_BY_SHA.get(document_sha)
            recorder.event(kind, pid=pid, detail=f"application budget: {self.exhausted}")
            allowance.record_refusal(LANE, kind, f"application budget: {self.exhausted}", ep=current["ep"], invocation=INVOCATION, doc=pid,
                                     task="read_submittal_form")
        return out""",
     """        before = self.exhausted
        with doc_scope(PID_BY_SHA.get(document_sha), document_sha, page=None, profile="b-accepted-path", variant="off"):
            out = _orig_run_call(self, document_sha=document_sha, parts=parts)
        if self.exhausted and not before:
            kind, pid = _limit_kind(str(self.exhausted)), PID_BY_SHA.get(document_sha)
            if kind == "application_document_limit":   # ORCH-08C (R39-06): application-internal -> unread pages, the document COMPLETE
                recorder.unread_pages(pid, [{"page": "*", "kind": kind, "partial": False,
                                             "reason": f"the form read was refused by the application's own budget ({self.exhausted})"}])
            else:
                recorder.event(kind, pid=pid, detail=f"application budget: {self.exhausted}")
            allowance.record_refusal(LANE, kind, f"application budget: {self.exhausted}", ep=current["ep"], invocation=INVOCATION, doc=pid,
                                     task=PF.FORM_TASK)
        return out"""),
    ("""        def process(db, project, row, path, root, **kw):
            current["ep"] = project.ep_number
            recorder.current = BY_KEY.get(f"EP-{project.ep_number}/{row.relative_path}".replace("\\\\", "/"))
            CS.set_context(sha256=row.sha256, page=None, profile="b-accepted-path", variant="off")
            out = _process(db, project, row, path, root, **kw)
            db.flush()
            _after(row, project)
            return out

        def read_form_or_raise(db, run, path, sha256, **kw):
            recorder.current = PID_BY_SHA.get(sha256, recorder.current)
            CS.set_context(sha256=sha256, page=None, profile="b-accepted-path", variant="off")
            return _read_form(db, run, path, sha256, **kw)""",
     """        def process(db, project, row, path, root, **kw):
            current["ep"] = project.ep_number
            pid = BY_KEY.get(f"EP-{project.ep_number}/{row.relative_path}".replace("\\\\", "/"))
            with doc_scope(pid, row.sha256, page=None, profile="b-accepted-path", variant="off"):
                out = _process(db, project, row, path, root, **kw)
                db.flush()
            _after(row, project)
            return out

        def read_form_or_raise(db, run, path, sha256, **kw):
            with doc_scope(PID_BY_SHA.get(sha256), sha256, page=None, profile="b-accepted-path", variant="off"):
                return _read_form(db, run, path, sha256, **kw)"""),
    # B: project loop -> deferral with retry_full; injected requests after processing
    ("""                try:
                    per_project[key] = document_processing.run(db, project, ctx=Ctx(), provider=chain)
                except RC.StopLane as exc:""",
     """                try:
                    per_project[key] = document_processing.run(db, project, ctx=Ctx(), provider=chain)
                    inject_requests(chain, 0)
                except RC.StopLane as exc:"""),
    ("""            if ep in deferred:
                recorder.set(pid, "DEFERRED", f"project window: {deferred[ep].detail}", retry_at=deferred[ep].retry_at)
            elif (per_project.get(ep) or {}).get("not_started") or (stopped and (row or {}).get("state") != "fresh"):""",
     """            if ep in deferred:
                recorder.set(pid, "DEFERRED", f"project window: {deferred[ep].detail}", retry_at=deferred[ep].retry_at,
                             retry_full=deferred[ep].retry_at_full)
            elif (per_project.get(ep) or {}).get("not_started") or (stopped and (row or {}).get("state") != "fresh"):"""),
    ("""            elif row["state"] != "fresh":
                recorder.event("prerequisite_failed", pid=pid, detail=f"B row state {row['state']}: {row.get('error')}")
                recorder.set(pid, "INCOMPLETE", f"B row state {row['state']}", cls="failure")""",
     """            elif row["state"] != "fresh" and recorder.unread.get(pid) and not any(
                    e["pool_id"] == pid and e["class"] in ("limit", "failure") for e in recorder.events):
                recorder.set(pid, "COMPLETE", f"processed by the application (B); B row state {row['state']}: its form read was refused by the "
                                              "application's own per-document budget (unread pages listed)")
            elif row["state"] != "fresh":
                recorder.event("prerequisite_failed", pid=pid, detail=f"B row state {row['state']}: {row.get('error')}")
                recorder.set(pid, "INCOMPLETE", f"B row state {row['state']}", cls="failure")"""),
    # C / R: reader exception injection, document scope, unread pages
    ("""        er.EvidenceRun.call = _call
        submittal_reader.available = lambda project, provider=None: None""",
     """        er.EvidenceRun.call = _call
        _orig_read_document = er.read_document
        _raise_at = sorted({n for i in INJECT if i.get("lane") == LANE and i.get("kind") == "reader_exception" for n in (i.get("calls") or [])})
        doc_no = {"n": 0}

        def _read_document(*a, **k):
            \"\"\"Dry drill only (ORCH-08C): the injected reader exception on the n-th document read.\"\"\"
            if doc_no["n"] in _raise_at:
                raise RuntimeError("r39 drill: injected evidence-reader exception (dry only)")
            return _orig_read_document(*a, **k)
        if _raise_at:
            if MODE == "live":
                raise SystemExit("refused: injections are dry-mode drills only")
            er.read_document = _read_document
        submittal_reader.available = lambda project, provider=None: None"""),
    ("""                    current["ep"] = d["ep"]
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
            recorder.current = None""",
     """                    current["ep"] = d["ep"]
                    doc_no["n"] += 1
                    n_before = len(((row.extracted or {}).get("ai_evidence") or {}).get("attempts") or [])
                    try:
                        with doc_scope(pid, row.sha256, page=None, profile="evidence", variant="EV1"):
                            per_doc[pid] = er.evidence_stage(db, project, [(row, pathlib.Path(row.path))], provider=chain, variant="EV1")
                            db.commit()
                    except AL.DeferDocument as dd:
                        db.rollback()
                        recorder.set(pid, "DEFERRED", f"project window: {dd.refusal.detail}", retry_at=dd.refusal.retry_at,
                                     retry_full=dd.refusal.retry_at_full)
                        per_doc[pid] = {"deferred": dd.refusal.detail, "retry_at": dd.refusal.retry_at}
                        continue
                    db.refresh(row)
                    attempts = ((row.extracted or {}).get("ai_evidence") or {}).get("attempts") or []
                    attempt = attempts[-1] if len(attempts) > n_before else None
                    in_scope = int(TRUTH["documents"][pid].get("in_scope_pages") or 0)
                    unread = RC.unread_pages_of_attempt(attempt, in_scope)       # ORCH-08C (R39-06): never silent
                    recorder.unread_pages(pid, unread)
                    for u in unread:
                        allowance.record_refusal(LANE, u["kind"], u["reason"], ep=current["ep"], invocation=INVOCATION, doc=pid, page=u["page"])
                    per_doc[pid] = (per_doc[pid] or {}) | {"unread_pages": unread, "attempt_outcome": (attempt or {}).get("outcome")}
                    facts = TW.facts_from_row(EV, row_dict(row, project.ep_number), ai_context, d["doc_key"])
                    observe_trip(pid, TW.tripwire(TRUTH, pid, facts, row.sha256), "after_document" if LANE == "C" else "reference")
                    recorder.set(pid, "COMPLETE", "read by the application's evidence stage")
                    with doc_scope(pid, row.sha256, page=None, profile="evidence", variant="EV1"):
                        inject_requests(chain, doc_no["n"], sha=row.sha256, pid=pid)
            recorder.end()"""),
    # manifest: the new checks and counters
    ("""             "identity": {"checked": IDENT.checked, "mismatches": IDENT.mismatches, "refused": IDENT.refused,""",
     """             "application_env_check": APP_ENV_CHECK, "task_kinds": sorted(TASK_KINDS),
             "retries": {"dispatched": G.retried, "events": [e for e in recorder.events if e["kind"] == "retry_dispatched"]},
             "contract_breaches": G.breaches, "contract_breach": RC.breach_marker(RUN_FOLDER),
             "unread_pages": {pid: v["unread_pages"] for pid, v in docs.items() if v.get("unread_pages")},
             "identity": {"checked": IDENT.checked, "mismatches": IDENT.mismatches, "refused": IDENT.refused,"""),
]


def main():
    global s
    for old, new in REPL:
        n = s.count(old)
        if n != 1:
            print(f"ANCHOR NOT UNIQUE ({n}): {old[:160]!r}")
            return 1
        s = s.replace(old, new)
    P.write_text(s, encoding="utf-8", newline="\n")
    print("patched", len(REPL))
    return 0


if __name__ == "__main__":
    sys.exit(main())
