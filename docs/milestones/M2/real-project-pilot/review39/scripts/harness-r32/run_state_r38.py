"""ORCH-08 / ORCH-08C (A-09 points 1, 2 and 7): the application-free part of the r38 lane control, importable by the
runner (which never imports the application): the event kinds and classes, the per-lane recorder of every event and
document status (COMPLETE / INCOMPLETE / DEFERRED), the unread pages of a document, the response classification, the
stop controller with the model-identity and contract-breach rules and the stop guard. run_control_r38 (the provider
chain) imports it; see that module for the chain.

ORCH-08C (Verification 39):
  R39-06  the document-status rule. Harness and resource refusals ('limit' class: lane allowance, parent ceiling, window,
          breaker, ledger, guard, identity, the application's per-project rolling limit; and the 'failure' class: timeout,
          provider failure, interruption) make the document INCOMPLETE. Application-internal per-document behaviour under
          the declared limits ('arm_policy' class: the reader's own per-document call cap, the per-document JobBudget, a
          reader exception) leaves the document COMPLETE with every page it did not read listed in `unread_pages` (page,
          kind, reason) and counted as unread in every denominator -- never silent. unread_pages_of_attempt() derives
          them from the evidence attempt the application stored.
  R39-04  a request with an undeclared task kind for its lane, or with no / a stale context, is a contract breach: the
          run is INVALID (CONTRACT-BREACH.json), every lane terminal, and such a request never counts toward any
          document's failure streak (classify -> 'contract_breach', not 'provider_failure').
  R39-16  a dispatched retry of a failed request is recorded ('retry_dispatched', class 'retry': visibility only)."""
from __future__ import annotations

import datetime
import json
import pathlib

import stop_rules


# event classes: 'limit'      an experiment / resource limit refused or stopped the work (the document is INCOMPLETE; a B / C
#                             document so affected makes the comparison INCOMPLETE);
#                'failure'    a provider failure / timeout / interruption (the document is INCOMPLETE; the comparison follows the
#                             stop rules);
#                'arm_policy' application-internal per-document behaviour under the declared limits (the reader's own cap, the
#                             per-document JobBudget, a reader exception): the document stays COMPLETE, its pages not read are
#                             listed in unread_pages and counted as unread in every denominator (ORCH-08C, R39-06);
#                'retry'      a failed request dispatched again on the application's own retry path (visibility only)
LIMIT_KINDS = ("lane_allowance", "parent_ceiling", "parent_input_tokens", "parent_output_tokens", "parent_elapsed", "project_window",
               "deferral_beyond_bound", "unattributed", "terminal_stop", "identity_invalid", "identity_mismatch", "breaker", "ledger", "guard",
               "lane_stopped", "application_project_limit", "not_started", "waiting", "undeclared_task_kind", "missing_context", "contract_breach_invalid")
FAILURE_KINDS = ("provider_timeout", "provider_failure", "interrupted_charged", "served_failure", "dispatched_unsaved", "prerequisite_failed")
POLICY_KINDS = ("application_document_limit", "application_reader_cap", "application_reader_exception")
RETRY_KINDS = ("retry_dispatched",)
BREACH_KINDS = ("undeclared_task_kind", "missing_context")
STATUSES = ("COMPLETE", "INCOMPLETE", "DEFERRED")
BREACH_MARKER = "CONTRACT-BREACH.json"


def kind_class(kind: str) -> str:
    if kind in POLICY_KINDS:
        return "arm_policy"
    if kind in FAILURE_KINDS:
        return "failure"
    if kind in RETRY_KINDS:
        return "retry"
    return "limit"                                   # unknown kinds count as limits (fail closed)


def breach_marker(run_folder) -> dict | None:
    """The run's contract-breach record (an undeclared request path reached the gate), or None."""
    p = pathlib.Path(run_folder) / BREACH_MARKER
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def unread_pages_of_attempt(attempt: dict | None, in_scope_pages: int) -> list[dict]:
    """ORCH-08C (R39-06): the pages of one document that the application's evidence attempt did NOT read, from the attempt
    the application itself stored (`extracted.ai_evidence.attempts[-1]`: outcome, error, pages {n: {outcome, requests}})
    or the reader's coverage ({outcome, pages: [{page, outcome, requests}]}):
      * the attempt failed (the reader raised: evidence_stage records outcome 'failed' and no page) -> every in-scope page,
        kind application_reader_exception;
      * a page whose outcome is 'budget: calls per document' -> the reader's own per-document cap (MAX_CALLS_PER_DOCUMENT,
        checked between pages), kind application_reader_cap;
      * a page whose outcome is 'budget: <limit>' -> the per-document JobBudget (or a harness refusal that set the run's
        exhaustion: those pages also carry the harness event, class 'limit'), kind application_document_limit;
      * a page read in part because a request was refused by the budget (request outcome 'budget') -> listed with
        'partial': True, kind application_document_limit.
    Pages with outcome 'no_trigger' were never meant to be read (the reader's trigger rule) and are not listed."""
    if not attempt:
        return []
    pages = attempt.get("pages")
    if isinstance(pages, dict):
        items = [(str(k), v or {}) for k, v in pages.items()]
    else:
        items = [(str(e.get("page")), e) for e in (pages or [])]
    if str(attempt.get("outcome")) == "failed":
        return [{"page": str(n), "kind": "application_reader_exception", "partial": False,
                 "reason": f"the evidence reader raised: {str(attempt.get('error') or '')[:200]}"} for n in range(1, int(in_scope_pages) + 1)]
    out = []
    for page, e in items:
        outcome = str(e.get("outcome") or "")
        if outcome.startswith("budget"):
            why = outcome.split(":", 1)[1].strip() if ":" in outcome else outcome
            kind = "application_reader_cap" if why == "calls per document" else "application_document_limit"
            out.append({"page": page, "kind": kind, "partial": False, "reason": f"not read: {outcome}"})
        elif any(str(v) == "budget" for v in (e.get("requests") or {}).values()):
            refused = sorted(k for k, v in (e.get("requests") or {}).items() if str(v) == "budget")
            out.append({"page": page, "kind": "application_document_limit", "partial": True,
                        "reason": f"read in part: request(s) {', '.join(refused)} refused by the application's budget"})
    return sorted(out, key=lambda x: (int(x["page"]) if x["page"].isdigit() else 0, x["kind"]))


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _utc(ts):
    return None if ts is None else datetime.datetime.fromtimestamp(float(ts), datetime.timezone.utc).isoformat(timespec="seconds")


class LaneRecorder:
    def __init__(self, lane: str, run_set: list[dict]):
        self.lane = lane
        self.order = [d["pool_id"] for d in run_set]
        self.events: list[dict] = []
        self.status: dict[str, dict] = {}
        self.unread: dict[str, list[dict]] = {}
        self.current = None
        self.expected_sha = None             # ORCH-08C: the context (document sha256) the current request must carry

    def begin(self, pid, sha):
        """The lane starts reading document `pid` (bytes `sha`): requests must carry that context until end()."""
        self.current, self.expected_sha = pid, sha

    def end(self):
        """The lane finished a document: no request is attributed to it afterwards (a later request has no context)."""
        self.current, self.expected_sha = None, None

    def event(self, kind: str, *, pid=None, page=None, task=None, detail=None, retry_at=None, served=False, extra=None):
        pid = pid if pid is not None else self.current
        e = {"lane": self.lane, "kind": kind, "pool_id": pid, "page": None if page is None else str(page), "task": task, "detail": detail,
             "retry_at_utc": _utc(retry_at), "retry_at": retry_at, "served": served, "at_utc": _now(), "class": kind_class(kind)}
        if extra:
            e.update(extra)
        self.events.append(e)
        return e

    def set(self, pid, status, reason, *, retry_at=None, cls=None, retry_full=None):
        """retry_at: the earliest retry (the first freed slot); retry_full: {'planning': t, 'structural': t} -- when the
        project's remaining requests (planning estimate / structural maximum) fit within the window (ORCH-08C, R39-08)."""
        assert status in STATUSES, status
        self.status[pid] = {"status": status, "reason": reason, "retry_at": retry_at, "retry_at_utc": _utc(retry_at), "class": cls}
        if retry_full:
            self.status[pid] |= {"retry_at_full": dict(retry_full), "retry_at_full_utc": {k: _utc(v) for k, v in retry_full.items()}}

    def unread_pages(self, pid, pages: list[dict]):
        """ORCH-08C (R39-06): the pages of `pid` the application did not read under its own per-document behaviour; each is
        recorded as an event (class 'arm_policy', per page) and listed on the document."""
        for u in pages:
            self.event(u["kind"], pid=pid, page=u["page"], detail=u["reason"], extra={"partial": bool(u.get("partial"))})
            self.unread.setdefault(pid, []).append(dict(u))

    def documents(self) -> dict:
        """Every run-set document: its status, the events that touched it (by page), its INCOMPLETE class and its unread
        pages. 'arm_policy' and 'retry' events never turn a COMPLETE document INCOMPLETE (ORCH-08C rule); 'limit' and
        'failure' events do."""
        out = {}
        for pid in self.order:
            evs = [e for e in self.events if e["pool_id"] == pid]
            st = dict(self.status.get(pid) or {"status": "INCOMPLETE", "reason": "never reached by the lane (recorded, not skipped)",
                                               "retry_at": None, "retry_at_utc": None})
            touched = [e for e in evs if e["kind"] != "project_window"]
            blocking = [e for e in touched if e["class"] in ("limit", "failure")]
            if st["status"] == "COMPLETE" and blocking:
                st["status"], st["reason"] = "INCOMPLETE", "events while reading: " + ", ".join(sorted({e["kind"] for e in blocking}))
            classes = sorted({e["class"] for e in touched})
            if st["status"] == "DEFERRED":
                classes = sorted(set(classes) | {"limit"})
            elif st["status"] == "INCOMPLETE" and not ({"limit", "failure"} & set(classes)):
                classes = sorted(set(classes) | {st.get("class") or "limit"})
            pages = {}
            for e in evs:
                pages.setdefault(e["page"] or "*", []).append(e["kind"])
            unread = {}
            for u in self.unread.get(pid, []):
                unread.setdefault(u["page"], []).append({k: u[k] for k in ("kind", "reason", "partial") if k in u})
            if st["status"] == "COMPLETE" and unread:
                st["reason"] = f"{st['reason']}; {sum(1 for v in unread.values() if not all(x.get('partial') for x in v))} page(s) not read " \
                               "under the application's own per-document limits (listed in unread_pages, counted as unread)"
            out[pid] = st | {"classes": classes, "events": len(evs), "kinds": sorted({e["kind"] for e in evs}),
                             "pages": {k: sorted(set(v)) for k, v in pages.items()},
                             "unread_pages": unread,
                             "unread_page_count": sum(1 for v in unread.values() if not all(x.get("partial") for x in v)),
                             "partially_read_pages": sorted(p for p, v in unread.items() if all(x.get("partial") for x in v)),
                             "retries": sum(1 for e in evs if e["kind"] == "retry_dispatched")}
        return out


def classify(resp) -> str:
    err = getattr(resp, "error", None)
    if getattr(resp, "ok", False):
        return "ok"
    if err == "dry_refused":
        return "dry_refused"
    if err == "contract_breach":
        return "contract_breach"                     # never a provider failure: it never counts toward a failure streak
    if err in ("identity_mismatch", "identity_invalid"):
        return "identity_mismatch"
    if err in ("budget", "allowance_refused", "dispatch_refused"):
        return "budget_refusal"
    return "provider_failure"


def event_kind(resp) -> str | None:
    """The visible event kind of a non-ok response (None for ok / dry_refused)."""
    err, detail = getattr(resp, "error", None), str(getattr(resp, "error_detail", "") or "")
    if getattr(resp, "ok", False) or err == "dry_refused":
        return None
    if err == "budget":
        if detail.startswith("ledger refused (breaker)"):
            return "breaker"
        if detail.startswith("ledger refused"):
            return "ledger"
        if detail.startswith("harness allowance refused ("):
            return detail.split("(", 1)[1].split(")", 1)[0]
        return "ledger"
    if err == "dispatch_refused":
        return "guard"
    if err == "contract_breach":
        return detail.split(":", 1)[0] if detail.split(":", 1)[0] in BREACH_KINDS + ("contract_breach_invalid",) else "contract_breach_invalid"
    if err in ("identity_mismatch", "identity_invalid"):
        return err
    if err == "timeout":
        return "provider_timeout"
    if err == "interrupted_charged":
        return "interrupted_charged"
    if err == "stopped":
        return "lane_stopped"
    return "provider_failure"


class ControllerR38(stop_rules.StopController):
    """stop_rules.StopController (unchanged) plus the identity rule: a model identity mismatch makes EVERY lane terminal and
    the comparison INVALID (A-09 point 2)."""

    def observe(self, lane: str, kind: str, *, resolved=None, detail=None) -> dict:
        if kind == "identity_mismatch":
            self.log.append({"lane": lane, "kind": kind, "resolved": None, "detail": detail})
            for name, st in self.lanes.items():
                if st["state"] == "running":
                    st["state"], st["reason"] = "terminal", f"model identity mismatch ({lane}): the run is INVALID"
            self.comparison = f"INVALID: model identity mismatch in lane {lane}"
            return self.state()
        if kind == "contract_breach":
            # ORCH-08C (R39-04): an undeclared request path reached the gate -- the run is INVALID; the request is never a
            # provider failure, so no document's failure streak counts it
            self.log.append({"lane": lane, "kind": kind, "resolved": None, "detail": detail})
            for name, st in self.lanes.items():
                if st["state"] == "running":
                    st["state"], st["reason"] = "terminal", f"contract breach ({lane}: {detail}): the run is INVALID"
            self.comparison = f"INVALID: contract breach in lane {lane} ({detail})"
            return self.state()
        before = self.lanes[lane]["state"]
        super().observe(lane, kind, resolved=resolved, detail=detail)
        if kind == "budget_refusal" and before == "running" and detail:
            self.lanes[lane]["reason"] = f"budget refusal ({detail}; never raised)"
        return self.state()


class StopLane(BaseException):
    """Raised at the application's next check point once the lane is stopped (passes through its except Exception)."""


class StopGuardR38:
    name, ready, status = "stop-guard", True, "r38 per-lane stop guard"

    def __init__(self, inner, ctl: ControllerR38, lane: str, recorder: LaneRecorder, response_cls, *, allowance=None, invocation=None,
                 page_of=lambda: None):
        self.inner, self.ctl, self.lane, self.rec, self.response_cls = inner, ctl, lane, recorder, response_cls
        self.allowance, self.invocation, self.page_of = allowance, invocation, page_of
        self.stats = {"stopped_by_guard": 0, "ok": 0}
        self.events = []

    def complete(self, request):
        if not self.ctl.can_dispatch(self.lane):
            self.stats["stopped_by_guard"] += 1
            self.rec.event("lane_stopped", page=self.page_of(), task=getattr(request, "task", None), detail=self.ctl.lanes[self.lane]["reason"])
            return self.response_cls(data=None, model="guard", error="stopped", error_detail=f"lane {self.lane} stopped: {self.ctl.lanes[self.lane]['reason']}")
        resp = self.inner.complete(request)
        kind = classify(resp)
        self.stats[kind] = self.stats.get(kind, 0) + 1
        self.events.append({"lane": self.lane, "kind": kind, "task": getattr(request, "task", None), "error": getattr(resp, "error", None),
                            "pool_id": self.rec.current})
        if kind != "dry_refused":
            before = self.ctl.lanes[self.lane]["state"]
            self.ctl.observe(self.lane, kind, detail=event_kind(resp))
            after = self.ctl.lanes[self.lane]["state"]
            if self.allowance is not None and before == "running" and after != "running":
                self.allowance.record_stop(self.lane, event_kind(resp) or kind, self.ctl.lanes[self.lane]["reason"], self.invocation)
        return resp
