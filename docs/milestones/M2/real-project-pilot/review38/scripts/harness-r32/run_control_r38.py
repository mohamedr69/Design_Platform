"""ORCH-08 (A-09 points 1, 2, 3 and 7): the r38 request chain of a lane and its VISIBLE records.

Chain (outermost first):
  StopGuardR38   the lane's stop controller: once the lane is stopped every request is refused ('stopped') and recorded
                 per document and page ('lane_stopped'); every response is classified (ok, provider failure, budget
                 refusal, identity mismatch); a lane that becomes terminal records a durable stop in the allowance
  GateStoreProvider (capture_store.StoreProvider, unchanged module, subclassed): a bound fingerprint already in the
                 store is SERVED (never re-sent; R is served C's capture by content key); a request that would be
                 dispatched passes the GATE first, before anything is reserved:
                   * the run is INVALID (IDENTITY-INVALID.json)        -> refused 'identity_invalid' (recorded)
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
No model is called by this module."""
from __future__ import annotations

import datetime
import json
import os
import random
import sqlite3
import sys

import allowance_r32 as AL
import capture_store as CS
import model_identity_r38 as MI
from run_state_r38 import (FAILURE_KINDS, LIMIT_KINDS, POLICY_KINDS, STATUSES, ControllerR38, LaneRecorder, StopGuardR38,  # noqa: F401
                           StopLane, classify, event_kind, kind_class)


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


class GateStoreProvider(CS.StoreProvider):
    def __init__(self, store, lane, inner, policy_fn, model_alias_fn, *, reference_from=None, allowance: AL.LaneAllowance, recorder: LaneRecorder,
                 ep_of, run_folder, invocation, response_cls, page_of=lambda: None):
        super().__init__(store, lane, inner, policy_fn, model_alias_fn, reference_from=reference_from)
        self.allowance, self.rec, self.ep_of, self.run_folder, self.invocation = allowance, recorder, ep_of, run_folder, invocation
        self.response_cls, self.page_of = response_cls, page_of
        self.served, self.gate_refused, self.deferred = 0, 0, 0

    def _serve(self, row, mode, policy, bkey, request):
        self.store.log_serve(self.lane, policy, bkey, row, mode)
        self.served += 1
        resp = CS._served(row, mode)
        kind = event_kind(resp)                 # None for an answer and for a dry-run artefact ('dry_refused')
        if kind:
            self.rec.event(kind, page=self.page_of(), task=getattr(request, "task", None), detail=f"served ({mode}): {resp.error}", served=True)
        return resp

    def complete(self, request):
        ctx, policy = CS.get_context(), self.policy_fn()
        ckey = CS.content_key(ctx, request, self.model_alias_fn(request.tier))
        task, page = getattr(request, "task", None), self.page_of()
        if self.reference_from:
            row = self.store.by_content(self.reference_from, ckey)
            if row is not None:
                return self._serve(row, "reference_from_capture", policy, CS.bound_key(self.lane, policy, ckey), request)
        bkey = CS.bound_key(self.lane, policy, ckey)
        existing = self.store.rows("select * from requests where bound_key = ?", (bkey,))
        if existing:
            return self._serve(existing[0], "same_bound_fingerprint", policy, bkey, request)
        ep = self.ep_of()
        if MI.invalid_marker(self.run_folder) is not None:
            self.gate_refused += 1
            self.allowance.record_refusal(self.lane, "identity_invalid", "the run is INVALID: no request is sent", ep=ep, invocation=self.invocation,
                                          doc=self.rec.current, page=page, task=task)
            self.rec.event("identity_invalid", page=page, task=task, detail="the run is INVALID (model identity mismatch)")
            return self.response_cls(data=None, model="identity", error="identity_invalid", error_detail="the run is INVALID (model identity mismatch)")
        try:
            self.allowance.precheck(self.lane, ep)
        except AL.WindowDeferred as w:
            self.deferred += 1
            self.allowance.record_refusal(self.lane, w.kind, w.detail, ep=ep, invocation=self.invocation, doc=self.rec.current, page=page, task=task,
                                          retry_at=w.retry_at)
            self.rec.event("project_window", page=page, task=task, detail=w.detail, retry_at=w.retry_at)
            raise AL.DeferDocument(w, self.lane) from None
        except AL.AllowanceRefused as a:
            self.gate_refused += 1
            self.allowance.record_refusal(self.lane, a.kind, a.detail, ep=ep, invocation=self.invocation, doc=self.rec.current, page=page, task=task,
                                          retry_at=a.retry_at)
            self.rec.event(a.kind, page=page, task=task, detail=a.detail, retry_at=a.retry_at)
            return self.response_cls(data=None, model="allowance", error="budget", error_detail=f"harness allowance refused ({a.kind}): {a.detail}")
        row, created = self.store.reserve(self.lane, policy, ckey, ctx, task)
        if not created:
            return self._serve(row, "same_bound_fingerprint", policy, bkey, request)
        self.store.keep_payload(ckey, CS.payload_of(ctx, request))
        self.dispatched += 1
        try:
            resp = self.inner.complete(request, doc=self.rec.current, bound_key=bkey)
        except AL.DeferDocument as d:
            _release(self.store.path, row["seq"], self.lane, f"deferred after the reservation: {d}")
            self.deferred += 1
            self.rec.event("project_window", page=page, task=task, detail=str(d), retry_at=d.refusal.retry_at)
            raise
        self.store.settle(row["seq"], resp)
        k = event_kind(resp)
        if k:
            self.rec.event(k, page=page, task=task, detail=str(getattr(resp, "error_detail", "") or "")[:300])
        return resp


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
    """capture_store.probe's sample (identical rows, seed and rule), each item through `chain`; per-item status."""
    rows = [r for r in store.rows("select * from requests where lane = ? and state = 'answered' order by seq", (lane_from,))]
    k = round(rate * len(rows))
    sample = sorted(random.Random(seed).sample(rows, k), key=lambda r: r["seq"]) if k else []
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
        recorder.current = f"probe:{r['seq']}"
        try:
            resp = chain.complete(request)
        except AL.DeferDocument as d:
            out.append(item | {"probe": "deferred", "status": "DEFERRED", "retry_at": d.refusal.retry_at, "retry_at_utc": _utc(d.refusal.retry_at)})
            continue
        status = "COMPLETE" if resp.ok or resp.error == "dry_refused" else "INCOMPLETE"
        out.append(item | {"probe": "answered" if resp.ok else resp.error, "status": status,
                           "agrees": resp.ok and json.dumps(resp.data, sort_keys=True) == json.dumps(json.loads(r["answer"]), sort_keys=True)})
    recorder.current = None
    states = [i["status"] for i in out]
    return {"sampled": k, "of": len(rows), "seed": seed, "rate": rate, "rows": out,
            "population_state": ("COMPLETE" if all(s == "COMPLETE" for s in states) else "DEFERRED" if "DEFERRED" in states else "INCOMPLETE"),
            "credit": "none: report-only diagnostic (A-09 point 6)"}
