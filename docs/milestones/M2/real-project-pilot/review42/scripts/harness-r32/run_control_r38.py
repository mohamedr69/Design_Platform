"""ORCH-08 / ORCH-08C (A-09 points 1, 2, 3 and 7; Verification 39 R39-04, R39-16): the r38 request chain of a lane and
its VISIBLE records.

Chain (outermost first):
  StopGuardR38   the lane's stop controller: once the lane is stopped every request is refused ('stopped') and recorded
                 per document and page ('lane_stopped'); every response is classified (ok, provider failure, budget
                 refusal, identity mismatch, contract breach); a lane that becomes terminal records a durable stop
  GateStoreProvider (capture_store.StoreProvider, unchanged module, subclassed): FIRST the declaration check (ORCH-08C):
                 the request's task kind must be declared for the lane and it must carry the context of the document
                 the lane is reading, else a contract breach (refused, recorded, the run INVALID, never charged); then
                 a bound ANSWER already in the store is SERVED (never re-sent; R is served C's capture by content key);
                 a reserved row without an outcome is served 'interrupted_charged'; a fingerprint whose dispatches all
                 FAILED is dispatched again as a retry with its ordinal (ORCH-08C, R39-16); a request that would be
                 dispatched passes the GATE first, before anything is reserved:
                   * the run is INVALID (IDENTITY-INVALID.json or CONTRACT-BREACH.json) -> refused (recorded)
                   * allowance precheck: a durable terminal stop of the lane, the lane's own allowance, the parent
                     total, token and elapsed bounds                    -> refused 'budget' (recorded, permanent, durable stop)
                   * the project's rolling window is full               -> DeferDocument (recorded with the earliest retry
                     time; not charged, nothing reserved: the document is DEFERRED and a resume dispatches it later)
                 then the row is reserved, the allowance charged (AllowanceProvider) and the request dispatched
  AllowanceProvider -> IdentityGuard (model_identity_r38) -> live: dispatch_guard_r32.GuardedProvider (LedgerProvider
                 inside) | dry: DryStub (refuses every request; dry-only injections for the visibility drill)
LaneRecorder (run_state_r38, the application-free half that the runner imports too): every event (refusal, deferral,
failure, served failure, application limit, stop) per document and page, and the document statuses COMPLETE /
INCOMPLETE (event classes 'limit' -- an experiment limit; 'failure' -- a provider failure or interruption; 'arm_policy' --
an application per-document job limit, part of the arm's own policy) / DEFERRED (with its retry time). Every run-set
document of the lane gets a status: nothing is skipped silently.
probe_r38: lane P, the seeded 15 % variation probe -- the SAME sample as capture_store.probe (same rows, seed and rule),
each item through the chain; a deferred item is DEFERRED, a refused one INCOMPLETE.
DryStub: dry mode only; it never answers with a usable value (its one injected 'identity_mismatch' response carries an
empty object that the IdentityGuard, always directly above it, turns into the failure 'identity_mismatch').
No model is called by this module.

ORCH-10 (R42; Verification 40 R40-04, owner decision A-11: option 2, "a fail-closed boundary"): RefusingGlobalProvider
is installed by lane_r32 as the application's GLOBAL provider (app.ai.provider.set_provider) in lanes C, R and P, right
after the provider module is imported and before any application code runs (lane B keeps the harness chain as its global
provider, unchanged). Any application path that calls get_provider().complete(...) in C, R or P reaches it and is
refused: the response is 'dispatch_refused' (it never reaches the CLI, a ledger or the chain, and is never charged), the
request is recorded as the contract breach 'global_provider_request' (CONTRACT-BREACH.json: the run INVALID under the
contract's undeclared-request rule; the lane's recorder, the allowance's refusals and the lane's events), and the lane's
stop controller makes every lane terminal."""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import random
import sqlite3
import sys

import allowance_r32 as AL
import capture_store as CS
import model_identity_r38 as MI
from run_state_r38 import (BREACH_MARKER, FAILURE_KINDS, LIMIT_KINDS, POLICY_KINDS, STATUSES, ControllerR38, LaneRecorder,  # noqa: F401
                           StopGuardR38, StopLane, breach_marker, classify, event_kind, kind_class, unread_pages_of_attempt)


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _utc(ts):
    return None if ts is None else datetime.datetime.fromtimestamp(float(ts), datetime.timezone.utc).isoformat(timespec="seconds")


def _release(store_path, seq, lane, reason):
    """A reserved row whose request was never dispatched (the allowance deferred it after the reservation): removed, and
    the removal recorded (table releases), so the request can be dispatched once later."""
    con = sqlite3.connect(str(store_path), timeout=60, isolation_level=None)
    try:
        con.execute("create table if not exists releases (id integer primary key autoincrement, seq integer, bound_key text, lane text, reason text, at text)")
        row = con.execute("select bound_key, state from requests where seq = ?", (seq,)).fetchone()
        if row and row[1] == "reserved":
            con.execute("insert into releases (seq, bound_key, lane, reason, at) values (?, ?, ?, ?, ?)", (seq, row[0], lane, reason, _now()))
            con.execute("delete from requests where seq = ? and state = 'reserved'", (seq,))
    finally:
        con.close()


RETRIES_DDL = ("create table if not exists retries (seq integer primary key, base_bound_key text, ordinal integer, retry_key text unique, "
               "previous_seq integer, previous_outcome text, lane text, invocation integer, at text)")


def retry_key(base_bound_key: str, ordinal: int) -> str:
    """The bound key of the ordinal-th dispatch of a failed fingerprint (ordinal >= 2; the first dispatch keeps the base key)."""
    return CS._h({"retry_of": base_bound_key, "ordinal": int(ordinal)})


def is_bound(row) -> bool:
    """ORCH-08C (R39-16): what the store serves on a repeat of the same bound fingerprint -- an ANSWER; in dry mode the
    stub's 'dry_refused' artefact stands for an answer (no answer exists in dry mode); a reserved row without an outcome
    (an interrupted dispatch) is served 'interrupted_charged' and never re-sent (the provider may have received it). A
    stored FAILURE is never served: the repeat is dispatched again on the application's own retry path."""
    return row["state"] == "answered" or (row["state"] == "failed" and row["outcome"] == "dry_refused")


def write_breach(run_folder, record: dict) -> dict:
    """The run's contract-breach record: the first breach is kept (O_EXCL); every breach is appended to the log."""
    folder = pathlib.Path(run_folder)
    with open(folder / "CONTRACT-BREACH-LOG.jsonl", "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(record, sort_keys=True, default=str) + "\n")
    try:
        fd = os.open(str(folder / BREACH_MARKER), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, (json.dumps(record, sort_keys=True, indent=1, default=str) + "\n").encode("utf-8"))
        os.close(fd)
    except FileExistsError:
        pass
    return record


class GateStoreProvider(CS.StoreProvider):
    """ORCH-08C additions (Verification 39):
      R39-04  every request carries a task kind DECLARED for the lane (`task_kinds`) and the context of the document the
              lane is reading (`expected_sha_of`: the lane clears the context after each document). A request with an
              undeclared task kind, or with no / a stale context, is refused at the gate BEFORE anything is served or
              reserved, recorded (lane, task kind, the context it carried and the context expected) in the lane rows,
              the allowance's refusals and CONTRACT-BREACH.json, and makes the run INVALID; it is never charged and never
              counts toward any document's failure streak.
      R39-16  the store serves only bound answers (is_bound); a fingerprint whose dispatches all FAILED is dispatched
              again -- charged, never refunded -- as a retry with its ordinal (table 'retries'; retry_key), identically
              for B and C; R is served C's capture by content key (contract 3, unchanged): C's answer when C holds one,
              otherwise C's latest state exactly as C saw it (R never re-sends a request C already sent)."""

    def __init__(self, store, lane, inner, policy_fn, model_alias_fn, *, reference_from=None, allowance: AL.LaneAllowance, recorder: LaneRecorder,
                 ep_of, run_folder, invocation, response_cls, task_kinds, expected_sha_of=None, page_of=lambda: None):
        super().__init__(store, lane, inner, policy_fn, model_alias_fn, reference_from=reference_from)
        self.allowance, self.rec, self.ep_of, self.run_folder, self.invocation = allowance, recorder, ep_of, run_folder, invocation
        self.response_cls, self.page_of = response_cls, page_of
        if task_kinds is None or not len(task_kinds):
            raise ValueError("a gate is always given the lane's declared task kinds")
        self.task_kinds, self.expected_sha_of = frozenset(task_kinds), expected_sha_of
        self.served, self.gate_refused, self.deferred, self.retried, self.breaches = 0, 0, 0, 0, 0
        con = sqlite3.connect(self.store.path, timeout=60, isolation_level=None)
        try:
            con.execute(RETRIES_DDL)
        finally:
            con.close()

    def _serve(self, row, mode, policy, bkey, request):
        self.store.log_serve(self.lane, policy, bkey, row, mode)
        self.served += 1
        resp = CS._served(row, mode)
        kind = event_kind(resp)                 # None for an answer and for a dry-run artefact ('dry_refused')
        if kind:
            self.rec.event(kind, page=self.page_of(), task=getattr(request, "task", None), detail=f"served ({mode}): {resp.error}", served=True)
        return resp

    def _breach(self, kind, detail, request, ctx, page, task):
        self.gate_refused += 1
        self.breaches += 1
        expected = self.expected_sha_of() if self.expected_sha_of else None
        record = {"kind": kind, "lane": self.lane, "invocation": self.invocation, "task": task, "declared_task_kinds": sorted(self.task_kinds),
                  "context": {k: ctx.get(k) for k in ("sha256", "page", "profile", "variant")}, "expected_sha256": expected,
                  "document": self.rec.current, "detail": detail, "at_utc": _now(),
                  "rule": "an undeclared request path is a contract breach: the run is INVALID; the request was not charged"}
        write_breach(self.run_folder, record)
        try:
            ep = self.ep_of()
        except Exception:  # noqa: BLE001 -- attribution is best effort for the record; the refusal stands
            ep = None
        self.allowance.record_refusal(self.lane, kind, detail, ep=ep, invocation=self.invocation, doc=self.rec.current, page=page, task=task)
        self.rec.event(kind, page=page, task=task, detail=detail, extra={"context": record["context"], "expected_sha256": expected})
        return self.response_cls(data=None, model="gate", error="contract_breach", error_detail=f"{kind}: {detail}")

    def _declared(self, request, ctx, page, task):
        """None when the request is declared for this lane and carries the current document's context; else the breach."""
        if task not in self.task_kinds:
            return self._breach("undeclared_task_kind", f"lane {self.lane}: task kind {task!r} is not declared for this lane "
                                                        f"(declared {sorted(self.task_kinds)}); context {ctx.get('sha256')!r}", request, ctx, page, task)
        sha = ctx.get("sha256")
        if not sha:
            return self._breach("missing_context", f"lane {self.lane}: task {task!r} arrived with no document context (the lane clears "
                                                   "the context after each document)", request, ctx, page, task)
        if self.expected_sha_of is not None:
            want = self.expected_sha_of()
            if want is None or sha != want:
                return self._breach("missing_context", f"lane {self.lane}: task {task!r} carries a stale context {sha!r}; the lane's "
                                                       f"current document is {want!r}", request, ctx, page, task)
        return None

    def _chain(self, bkey) -> list[dict]:
        """Every dispatch of one bound fingerprint, in order: the base row (ordinal 1), then its retries."""
        base = self.store.rows("select * from requests where bound_key = ?", (bkey,))
        if not base:
            return []
        more = self.store.rows("select r.*, t.ordinal as retry_ordinal from requests r join retries t on t.seq = r.seq "
                               "where t.base_bound_key = ? order by t.ordinal", (bkey,))
        return [base[0] | {"retry_ordinal": 1}] + more

    def _reference_row(self, ckey):
        rows = self.store.rows("select * from requests where lane = ? and content_key = ? order by seq", (self.reference_from, ckey))
        if not rows:
            return None
        return next((r for r in rows if r["state"] == "answered"), None) or next((r for r in rows if is_bound(r)), None) or rows[-1]

    def _reserve_retry(self, bkey, ordinal, previous, ctx, ckey, policy, task):
        """Reserve the ordinal-th dispatch of a failed fingerprint atomically (refused when the chain changed meanwhile)."""
        rk = retry_key(bkey, ordinal)
        con = sqlite3.connect(self.store.path, timeout=60, isolation_level=None)
        con.row_factory = sqlite3.Row
        try:
            con.execute("begin immediate")
            if con.execute("select count(*) from retries where base_bound_key = ? and ordinal >= ?", (bkey, ordinal)).fetchone()[0]:
                con.execute("rollback")
                return None
            con.execute("insert into requests (bound_key, content_key, lane, policy, task, page, doc, state, dispatched_at) values (?,?,?,?,?,?,?,?,?)",
                        (rk, ckey, self.lane, policy, task, ctx.get("page"), ctx.get("sha256"), "reserved", _now()))
            row = dict(con.execute("select * from requests where bound_key = ?", (rk,)).fetchone())
            con.execute("insert into retries (seq, base_bound_key, ordinal, retry_key, previous_seq, previous_outcome, lane, invocation, at) "
                        "values (?,?,?,?,?,?,?,?,?)", (row["seq"], bkey, ordinal, rk, previous["seq"], previous["outcome"], self.lane, self.invocation, _now()))
            con.execute("commit")
            return row
        finally:
            con.close()

    def complete(self, request):
        ctx, policy = CS.get_context(), self.policy_fn()
        task, page = getattr(request, "task", None), self.page_of()
        breach = self._declared(request, ctx, page, task)
        if breach is not None:
            return breach
        ckey = CS.content_key(ctx, request, self.model_alias_fn(request.tier))
        if self.reference_from:
            row = self._reference_row(ckey)
            if row is not None:
                return self._serve(row, "reference_from_capture", policy, CS.bound_key(self.lane, policy, ckey), request)
        bkey = CS.bound_key(self.lane, policy, ckey)
        chain = self._chain(bkey)
        ordinal, previous = 1, None
        if chain:
            bound = next((r for r in chain if r["state"] == "answered"), None) or next((r for r in chain if is_bound(r)), None)
            if bound is not None:
                return self._serve(bound, "same_bound_fingerprint", policy, bkey, request)
            if chain[-1]["state"] == "reserved":
                return self._serve(chain[-1], "same_bound_fingerprint", policy, bkey, request)      # interrupted: never re-sent
            ordinal, previous = len(chain) + 1, chain[-1]                                           # failed: the application's retry
        ep = self.ep_of()
        for marker, kind, why in ((MI.invalid_marker(self.run_folder), "identity_invalid", "the run is INVALID (model identity mismatch)"),
                                  (breach_marker(self.run_folder), "contract_breach_invalid", "the run is INVALID (contract breach)")):
            if marker is not None:
                self.gate_refused += 1
                self.allowance.record_refusal(self.lane, kind, f"{why}: no request is sent", ep=ep, invocation=self.invocation,
                                              doc=self.rec.current, page=page, task=task)
                self.rec.event(kind, page=page, task=task, detail=why)
                if kind == "identity_invalid":
                    return self.response_cls(data=None, model="identity", error="identity_invalid", error_detail=why)
                return self.response_cls(data=None, model="gate", error="contract_breach", error_detail=f"contract_breach_invalid: {why}")
        try:
            self.allowance.precheck(self.lane, ep)
        except AL.WindowDeferred as w:
            self.deferred += 1
            self.allowance.record_refusal(self.lane, w.kind, w.detail, ep=ep, invocation=self.invocation, doc=self.rec.current, page=page, task=task,
                                          retry_at=w.retry_at)
            self.rec.event("project_window", page=page, task=task, detail=w.detail, retry_at=w.retry_at,
                           extra={"retry_at_full": w.retry_at_full, "retry_at_full_utc": {k: _utc(v) for k, v in (w.retry_at_full or {}).items()}})
            raise AL.DeferDocument(w, self.lane) from None
        except AL.AllowanceRefused as a:
            self.gate_refused += 1
            self.allowance.record_refusal(self.lane, a.kind, a.detail, ep=ep, invocation=self.invocation, doc=self.rec.current, page=page, task=task,
                                          retry_at=a.retry_at)
            self.rec.event(a.kind, page=page, task=task, detail=a.detail, retry_at=a.retry_at)
            return self.response_cls(data=None, model="allowance", error="budget", error_detail=f"harness allowance refused ({a.kind}): {a.detail}")
        if ordinal == 1:
            row, created = self.store.reserve(self.lane, policy, ckey, ctx, task)
            if not created:
                return self.complete(request)                                   # reserved meanwhile: decide again from the store
            row_key, note = bkey, ""
        else:
            row = self._reserve_retry(bkey, ordinal, previous, ctx, ckey, policy, task)
            if row is None:
                return self.complete(request)
            row_key, note = row["bound_key"], f"retry {ordinal} of {bkey} (previous seq {previous['seq']}: {previous['outcome']})"
            self.retried += 1
            self.rec.event("retry_dispatched", page=page, task=task, detail=f"retry {ordinal}: the previous dispatch (seq {previous['seq']}) "
                                                                            f"failed ({previous['outcome']}); dispatched again, charged",
                           extra={"retry_ordinal": ordinal, "previous_seq": previous["seq"], "previous_outcome": previous["outcome"]})
        self.store.keep_payload(ckey, CS.payload_of(ctx, request))
        self.dispatched += 1
        try:
            resp = self.inner.complete(request, doc=self.rec.current, bound_key=row_key, note=note)
        except AL.DeferDocument as d:
            _release(self.store.path, row["seq"], self.lane, f"deferred after the reservation: {d}")
            con = sqlite3.connect(self.store.path, timeout=60, isolation_level=None)
            try:
                con.execute("delete from retries where seq = ?", (row["seq"],))
            finally:
                con.close()
            self.deferred += 1
            self.rec.event("project_window", page=page, task=task, detail=str(d), retry_at=d.refusal.retry_at)
            raise
        self.store.settle(row["seq"], resp)
        k = event_kind(resp)
        if k:
            self.rec.event(k, page=page, task=task, detail=str(getattr(resp, "error_detail", "") or "")[:300])
        return resp


GLOBAL_BREACH_KIND = "global_provider_request"


class RefusingGlobalProvider:
    """ORCH-10 (R40-04, option 2): the application's GLOBAL provider in lanes C, R and P -- fail-closed. complete() never
    dispatches: it records the contract breach 'global_provider_request' (CONTRACT-BREACH.json, the lane recorder, the
    allowance's refusals, the stop controller, its own event list that the lane hands to the runner) and returns
    'dispatch_refused'. ready is True on purpose: an application path that asks the global provider whether AI is available
    is told yes, so a path that would then send a request reaches this refusal (recorded) instead of skipping silently."""
    name, ready, status = "r42-refusing-global", True, "r42 fail-closed global provider (lanes C, R, P): every request is refused and recorded"

    def __init__(self, response_cls, *, lane: str, run_folder, invocation: int):
        self.response_cls, self.lane, self.run_folder, self.invocation = response_cls, lane, pathlib.Path(run_folder), int(invocation)
        self.recorder = self.allowance = self.ctl = None
        self.ep_of = lambda: None
        self.page_of = lambda: None
        self.calls = 0
        self.events: list[dict] = []
        self.records: list[dict] = []

    def attach(self, *, recorder=None, allowance=None, ctl=None, ep_of=None, page_of=None):
        """The lane's recorder, allowance and stop controller, once they exist (the provider is installed before them)."""
        self.recorder, self.allowance, self.ctl = recorder, allowance, ctl
        self.ep_of, self.page_of = ep_of or self.ep_of, page_of or self.page_of
        return self

    def complete(self, request, **_kw):
        self.calls += 1
        ctx = CS.get_context()
        task = getattr(request, "task", None)
        try:
            page = self.page_of()
        except Exception:  # noqa: BLE001 -- attribution is best effort; the refusal stands
            page = None
        doc = getattr(self.recorder, "current", None)
        detail = (f"lane {self.lane}: task {task!r} reached the application's global provider (get_provider()), outside the harness chain; "
                  "refused fail-closed (never dispatched, never charged)")
        record = {"kind": GLOBAL_BREACH_KIND, "lane": self.lane, "invocation": self.invocation, "task": task,
                  "context": {k: ctx.get(k) for k in ("sha256", "page", "profile", "variant")}, "document": doc, "detail": detail,
                  "at_utc": _now(), "rule": "R40-04 option 2: a request outside the harness chain is an undeclared request path: the run is INVALID"}
        self.records.append(record)
        write_breach(self.run_folder, record)
        if self.allowance is not None:
            try:
                ep = self.ep_of()
            except Exception:  # noqa: BLE001
                ep = None
            self.allowance.record_refusal(self.lane, GLOBAL_BREACH_KIND, detail, ep=ep, invocation=self.invocation, doc=doc, page=page, task=task)
        if self.recorder is not None:
            self.recorder.event(GLOBAL_BREACH_KIND, page=page, task=task, detail=detail, extra={"context": record["context"]})
        if self.ctl is not None:
            self.ctl.observe(self.lane, "contract_breach", detail=GLOBAL_BREACH_KIND)
        self.events.append({"lane": self.lane, "kind": "contract_breach", "task": task, "error": GLOBAL_BREACH_KIND, "pool_id": doc})
        return self.response_cls(data=None, model="refusing-global", error="dispatch_refused", error_detail=f"{GLOBAL_BREACH_KIND}: {detail}")


class DryStub:
    """Dry mode: no provider exists. Every request is refused 'dry_refused' (never an answer), except the dry-only
    injections of the visibility drill (cfg['dry_inject'], refused in live mode):
      provider_timeout    -> the failure 'timeout' (the declared model echoed, as the adapter does on a timeout)
      identity_mismatch   -> a response that names another model (its data is an empty object and is never used: the
                             identity guard turns it into the failure 'identity_mismatch')
      interrupted         -> the process dies inside the call (the row stays reserved, the charge 'dispatched')
      usage               -> the refusal 'dry_refused' reporting the given usage (lets a FAKE ledger open its breaker)
    Injections are matched on (lane, n-th call of this stub)."""
    name, ready, status = "dry-refusing", True, "r38 dry run: refuses every request; no provider is built"

    def __init__(self, response_cls, usage_cls, lane: str, injections=None, declared_model: str = "dry"):
        self.response_cls, self.usage_cls, self.lane = response_cls, usage_cls, lane
        self.inj = [i for i in (injections or []) if i.get("lane") == lane and i.get("kind") in ("provider_timeout", "identity_mismatch", "interrupted", "usage")]
        self.declared_model, self.calls = declared_model, 0

    def complete(self, request):
        self.calls += 1
        hit = next((i for i in self.inj if self.calls in (i.get("calls") or [])), None)
        kind = hit["kind"] if hit else None
        if kind == "interrupted":
            sys.stdout.flush()
            os._exit(75)
        if kind == "provider_timeout":
            return self.response_cls(data=None, model=self.declared_model, error="timeout", error_detail="injected dry timeout (no provider)")
        if kind == "identity_mismatch":
            return self.response_cls(data={}, usage=self.usage_cls(10, 2), model=hit.get("model", "claude-sonnet-5-injected-mismatch"))
        usage = self.usage_cls(int(hit.get("input_tokens", 0)), int(hit.get("output_tokens", 0))) if kind == "usage" else self.usage_cls(0, 0)
        return self.response_cls(data=None, usage=usage, model="dry", error="dry_refused", error_detail="dry run: no provider, no model request")


class CrashAfterResponse:
    """Dry drill 'unsaved' (dispatched-but-unsaved): the response came back (identity logged, ledger settled) and the
    process dies before the capture store or the allowance saved it."""

    def __init__(self, inner, lane, injections=None):
        self.inner = inner
        self.calls = 0
        self.at = sorted({n for i in (injections or []) if i.get("lane") == lane and i.get("kind") == "unsaved" for n in (i.get("calls") or [])})

    def complete(self, request):
        resp = self.inner.complete(request)
        self.calls += 1
        if self.calls in self.at:
            sys.stdout.flush()
            os._exit(76)
        return resp


def probe_r38(store: CS.CaptureStore, chain, policy: str, model_alias_fn, recorder: LaneRecorder, *, rate=0.15,
              seed="m2-r30-variation-2026-10-02", lane_from="C", ep_by_sha=None) -> dict:
    """capture_store.probe's sample (identical rows, seed and rule), each item through `chain`; per-item status.
    ORCH-08C: the sample is drawn ONCE, at P's first run, and kept in the capture store (table probe_sample); a later
    invocation probes the same rows, so C's retries in a later invocation (R39-16: a failed C request is dispatched
    again and may then be answered) can never change P's declared population. Each item carries its own document context
    (recorder.expected_sha), and the context is cleared after each item."""
    con = sqlite3.connect(store.path, timeout=60, isolation_level=None)
    try:
        con.execute("create table if not exists probe_sample (lane_from text, seq integer, of_rows integer, picked_at text, primary key (lane_from, seq))")
        frozen = [r[0] for r in con.execute("select seq from probe_sample where lane_from = ? order by seq", (lane_from,))]
        of_rows = con.execute("select max(of_rows) from probe_sample where lane_from = ?", (lane_from,)).fetchone()[0]
        if not frozen and of_rows is None:
            rows = [r for r in store.rows("select * from requests where lane = ? and state = 'answered' order by seq", (lane_from,))]
            k = round(rate * len(rows))
            sample = sorted(random.Random(seed).sample(rows, k), key=lambda r: r["seq"]) if k else []
            con.execute("begin immediate")
            for r in sample:
                con.execute("insert into probe_sample (lane_from, seq, of_rows, picked_at) values (?, ?, ?, ?)", (lane_from, r["seq"], len(rows), _now()))
            if not sample:
                con.execute("insert into probe_sample (lane_from, seq, of_rows, picked_at) values (?, ?, ?, ?)", (lane_from, -1, len(rows), _now()))
            con.execute("commit")
            of_rows, frozen_from = len(rows), "drawn now (first run of P)"
        else:
            sample = [store.rows("select * from requests where seq = ?", (s,))[0] for s in frozen if s >= 0]
            k, frozen_from = len(sample), "the sample frozen at P's first run"
    finally:
        con.close()
    out = []
    for r in sample:
        payload = store.payload(r["content_key"])
        item = {"seq": r["seq"], "task": r["task"], "doc_sha256": r["doc"], "page": r["page"]}
        if payload is None:
            recorder.event("not_started", pid=f"probe:{r['seq']}", detail="no payload")
            out.append(item | {"probe": "no payload", "status": "INCOMPLETE"})
            continue
        ctx, request = CS.request_of(payload)
        CS.set_context(**ctx)
        recorder.current, recorder.expected_sha = f"probe:{r['seq']}", ctx.get("sha256")
        try:
            resp = chain.complete(request)
        except AL.DeferDocument as d:
            out.append(item | {"probe": "deferred", "status": "DEFERRED", "retry_at": d.refusal.retry_at, "retry_at_utc": _utc(d.refusal.retry_at)})
            continue
        finally:
            CS.set_context()
            recorder.expected_sha = None
        status = "COMPLETE" if resp.ok or resp.error == "dry_refused" else "INCOMPLETE"
        out.append(item | {"probe": "answered" if resp.ok else resp.error, "status": status,
                           "agrees": resp.ok and json.dumps(resp.data, sort_keys=True) == json.dumps(json.loads(r["answer"]), sort_keys=True)})
    recorder.current = None
    states = [i["status"] for i in out]
    return {"sampled": k, "of": of_rows, "seed": seed, "rate": rate, "rows": out, "sample_source": frozen_from,
            "population_state": ("COMPLETE" if all(s == "COMPLETE" for s in states) else "DEFERRED" if "DEFERRED" in states else "INCOMPLETE"),
            "credit": "none: report-only diagnostic (A-09 point 6)"}
