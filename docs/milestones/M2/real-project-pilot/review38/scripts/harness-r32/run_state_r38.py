"""ORCH-08 (A-09 points 1, 2 and 7): the application-free part of the r38 lane control, importable by the runner (which
never imports the application): the event kinds and classes, the per-lane recorder of every event and document
status (COMPLETE / INCOMPLETE / DEFERRED), the response classification, the stop controller with the model-identity
rule and the stop guard. run_control_r38 (the provider chain) imports it; see that module for the chain."""
from __future__ import annotations

import datetime

import stop_rules


# event classes: 'limit'      an experiment limit refused or stopped the work (makes a B / C comparison INCOMPLETE);
#                'failure'    a provider failure / interruption (the page is INCOMPLETE; the comparison follows the stop rules);
#                'arm_policy' an application per-document job limit of the arm itself (the page is INCOMPLETE; part of the arm's result)
LIMIT_KINDS = ("lane_allowance", "parent_ceiling", "parent_input_tokens", "parent_output_tokens", "parent_elapsed", "project_window",
               "deferral_beyond_bound", "unattributed", "terminal_stop", "identity_invalid", "identity_mismatch", "breaker", "ledger", "guard",
               "lane_stopped", "application_project_limit", "not_started", "waiting")
FAILURE_KINDS = ("provider_timeout", "provider_failure", "interrupted_charged", "served_failure", "dispatched_unsaved", "prerequisite_failed")
POLICY_KINDS = ("application_document_limit",)
STATUSES = ("COMPLETE", "INCOMPLETE", "DEFERRED")


def kind_class(kind: str) -> str:
    if kind in POLICY_KINDS:
        return "arm_policy"
    if kind in FAILURE_KINDS:
        return "failure"
    return "limit"                                   # unknown kinds count as limits (fail closed)


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
        self.current = None

    def event(self, kind: str, *, pid=None, page=None, task=None, detail=None, retry_at=None, served=False):
        pid = pid if pid is not None else self.current
        e = {"lane": self.lane, "kind": kind, "pool_id": pid, "page": None if page is None else str(page), "task": task, "detail": detail,
             "retry_at_utc": _utc(retry_at), "retry_at": retry_at, "served": served, "at_utc": _now(), "class": kind_class(kind)}
        self.events.append(e)
        return e

    def set(self, pid, status, reason, *, retry_at=None, cls=None):
        assert status in STATUSES, status
        self.status[pid] = {"status": status, "reason": reason, "retry_at": retry_at, "retry_at_utc": _utc(retry_at), "class": cls}

    def documents(self) -> dict:
        """Every run-set document: its status, the events that touched it (by page) and its INCOMPLETE class."""
        out = {}
        for pid in self.order:
            evs = [e for e in self.events if e["pool_id"] == pid]
            st = dict(self.status.get(pid) or {"status": "INCOMPLETE", "reason": "never reached by the lane (recorded, not skipped)",
                                               "retry_at": None, "retry_at_utc": None})
            touched = [e for e in evs if e["kind"] != "project_window"]
            if st["status"] == "COMPLETE" and touched:
                st["status"], st["reason"] = "INCOMPLETE", "events while reading: " + ", ".join(sorted({e["kind"] for e in touched}))
            classes = sorted({e["class"] for e in touched})
            if st["status"] == "DEFERRED":
                classes = sorted(set(classes) | {"limit"})
            elif st["status"] == "INCOMPLETE" and not classes:
                classes = [st.get("class") or "limit"]
            pages = {}
            for e in evs:
                pages.setdefault(e["page"] or "*", []).append(e["kind"])
            out[pid] = st | {"classes": classes, "events": len(evs), "kinds": sorted({e["kind"] for e in evs}),
                             "pages": {k: sorted(set(v)) for k, v in pages.items()}}
        return out


def classify(resp) -> str:
    err = getattr(resp, "error", None)
    if getattr(resp, "ok", False):
        return "ok"
    if err == "dry_refused":
        return "dry_refused"
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
