"""allowance_r32 (ORCH-08, A-09 points 1 and 3): the immutable parent budget with separately auditable lane allowances
(no borrowing), the project ROLLING window (a refusal is a deferral with its earliest retry time, never a charge),
charges that are never refunded (failed, timed-out, interrupted and dispatched-but-unsaved stay charged), durable refusal
and terminal-stop records that a resume never resets, the audit view and its reconciliation with a FAKE ledger scope.
Run: python -m pytest -q test_allowance_r32.py"""
import json
import sqlite3
import subprocess
import sys
import time

import pytest

import allowance_r32 as AL
import r32_test_helpers as H

KEY = "a" * 64
CAPS = {"B": 3, "C": 3, "R": 1, "P": 1}
WIN = {"limit": 3, "window_s": 100}
PARENT = {"total": 8, "input_tokens": 1000, "output_tokens": 500, "elapsed_s": 1000}


class Resp:
    def __init__(self, data=None, model="", error=None, error_detail=None, usage=None, **kw):
        self.data, self.error, self.error_detail, self.model, self.usage = data, error, error_detail, model, usage


def _a(tmp_path, caps=CAPS, win=WIN, parent=PARENT, **kw):
    return AL.LaneAllowance(tmp_path / "a.sqlite", caps, win, parent=parent, run_key=KEY, **kw)


def test_the_default_budget_is_the_plan_parent_and_lane_allowances():
    assert AL.CAPS == {"B": 240, "C": 240, "R": 40, "P": 36} and sum(AL.CAPS.values()) == AL.PARENT["total"] == 556
    assert AL.PROJECT_WINDOW == {"limit": 60, "window_s": 86400}


def test_lane_allowances_are_enforced_durable_and_never_borrowed(tmp_path):
    a = _a(tmp_path, win={"limit": 100, "window_s": 100})
    for _ in range(3):
        a.charge("C", "1")
    with pytest.raises(AL.AllowanceRefused, match="its own allowance 3 is used") as e:
        a.charge("C", "1")
    assert e.value.kind == "lane_allowance"
    a.charge("B", "1")                                  # B still has its own allowance: C never borrowed it, B never lends it
    b = _a(tmp_path, win={"limit": 100, "window_s": 100}, create=False)
    assert b.used("C") == 3 and b.used("B") == 1, "a new process sees the charges"
    with pytest.raises(AL.AllowanceRefused, match="its own allowance"):
        b.charge("C", "1")


def test_a_lane_cannot_borrow_even_when_the_parent_has_room(tmp_path):
    a = _a(tmp_path, win={"limit": 100, "window_s": 100})
    a.charge("R", "1")
    assert a.used() == 1 < PARENT["total"]
    with pytest.raises(AL.AllowanceRefused, match="lane R: its own allowance 1 is used"):
        a.charge("R", "1")


def test_the_parent_total_bounds_every_lane_and_the_lanes_must_fit_it(tmp_path):
    with pytest.raises(AL.AllowanceRefused, match="must fit the parent total"):
        AL.LaneAllowance(tmp_path / "x.sqlite", {"B": 5, "C": 5}, WIN, parent=PARENT, run_key=KEY)
    a = _a(tmp_path, caps={"B": 4, "C": 4}, win={"limit": 100, "window_s": 100}, parent=dict(PARENT, total=8))
    for lane in "BBBBCCCC":
        a.charge(lane, "1")
    with pytest.raises(AL.AllowanceRefused):
        a.charge("C", "1")


def test_parent_token_and_elapsed_bounds(tmp_path):
    a = _a(tmp_path, win={"limit": 100, "window_s": 100})
    cid = a.charge("C", "1")
    a.settle(cid, "ok", input_tokens=1000, output_tokens=10)
    with pytest.raises(AL.AllowanceRefused) as e:
        a.charge("B", "1")
    assert e.value.kind == "parent_input_tokens"
    b = AL.LaneAllowance(tmp_path / "e.sqlite", CAPS, WIN, parent=PARENT, run_key=KEY)
    with pytest.raises(AL.AllowanceRefused) as e2:
        b.charge("B", "1", now=b.bound_at + PARENT["elapsed_s"] + 1)
    assert e2.value.kind == "parent_elapsed"


def test_the_project_window_is_rolling_counts_every_lane_and_defers_with_the_earliest_retry(tmp_path):
    a = _a(tmp_path)
    t0 = a.bound_at + 1
    a.charge("B", "27331", now=t0)
    a.charge("C", "27331", now=t0 + 10)
    a.charge("C", "27331", now=t0 + 20)
    with pytest.raises(AL.WindowDeferred) as e:
        a.charge("R", "27331", now=t0 + 30)
    assert e.value.kind == "project_window" and e.value.retry_at == pytest.approx(t0 + 100), "the oldest charge leaves the window at t0 + 100"
    assert a.used() == 3, "a deferral is never a charge"
    a.charge("C", "3563", now=t0 + 30)                    # another project is unaffected
    with pytest.raises(AL.WindowDeferred):
        a.precheck("R", "27331", now=t0 + 99)
    a.precheck("R", "27331", now=t0 + 101)               # the window has freed one slot
    a.charge("R", "27331", now=t0 + 101)
    with pytest.raises(AL.WindowDeferred) as e2:
        a.charge("B", "27331", now=t0 + 102)
    assert e2.value.retry_at == pytest.approx(t0 + 110)


def test_a_deferral_beyond_the_elapsed_bound_is_permanent_and_visible(tmp_path):
    a = _a(tmp_path, win={"limit": 1, "window_s": 5000})
    t0 = a.bound_at + 1
    a.charge("C", "1", now=t0)
    with pytest.raises(AL.AllowanceRefused) as e:
        a.charge("C", "1", now=t0 + 1)
    assert e.value.kind == "deferral_beyond_bound" and not isinstance(e.value, AL.WindowDeferred) and e.value.retry_at > a.bound_end()


def test_charges_are_never_refunded_whatever_the_outcome(tmp_path):
    a = _a(tmp_path, caps={"B": 5, "C": 5}, win={"limit": 100, "window_s": 100}, parent=dict(PARENT, total=10))
    ids = [a.charge("C", "1", task=t) for t in ("answered", "failed", "timeout", "interrupted", "unsaved")]
    a.settle(ids[0], "ok", model="claude-sonnet-5", input_tokens=5, output_tokens=1)
    a.settle(ids[1], "invalid_response", model="claude-sonnet-5")
    a.settle(ids[2], "timeout", model="claude-sonnet-5")
    # ids[3] / ids[4]: the process died before the answer was saved -- they stay 'dispatched', charged
    audit = a.audit()
    assert audit["lanes"]["C"]["charged"] == 5 and audit["lanes"]["C"]["dispatched_never_settled"] == 2
    assert audit["lanes"]["C"]["by_outcome"] == {"ok": 1, "invalid_response": 1, "timeout": 1, "dispatched": 2}
    assert [c["outcome"] for c in audit["charges"]] == ["ok", "invalid_response", "timeout", "dispatched", "dispatched"]


def test_refusals_and_terminal_stops_are_durable_and_a_resume_never_resets_them(tmp_path):
    a = _a(tmp_path)
    a.record_refusal("C", "breaker", "ledger refused (breaker)", ep="1", invocation=1, doc="F037", page="2", task="read_decision")
    assert a.record_stop("C", "breaker", "budget refusal (breaker)", 1) and not a.record_stop("C", "lane_allowance", "x", 2), "the first stop wins"
    b = _a(tmp_path, create=False)                        # the second invocation
    with pytest.raises(AL.AllowanceRefused) as e:
        b.charge("C", "1")
    assert e.value.kind == "terminal_stop" and "breaker" in e.value.detail
    b.charge("B", "1")                                    # other lanes keep their own state
    assert b.stops()["C"]["kind"] == "breaker" and b.audit()["refusals"][0]["document"] == "F037"


def test_a_cap_window_or_parent_is_never_changed_and_never_fresh(tmp_path):
    _a(tmp_path)
    for kw, match in (({"caps": dict(CAPS, C=2)}, "bound to another run or other limits"), ({"win": {"limit": 4, "window_s": 100}}, "bound to another run"),
                      ({"parent": dict(PARENT, total=9)}, "bound to another run")):
        with pytest.raises(AL.AllowanceRefused, match=match):
            _a(tmp_path, **kw)
    with pytest.raises(AL.AllowanceRefused, match="bound to another run"):
        AL.LaneAllowance(tmp_path / "a.sqlite", CAPS, WIN, parent=PARENT, run_key="b" * 64)
    with pytest.raises(AL.AllowanceRefused, match="always bound to a run key"):
        AL.LaneAllowance(tmp_path / "x.sqlite", CAPS, WIN, parent=PARENT, run_key="")


def test_a_second_invocation_reopens_the_same_counts_and_never_gets_fresh_caps(tmp_path):
    first = _a(tmp_path, win={"limit": 100, "window_s": 100})
    first.charge("C", "1")
    first.charge("C", "1")
    second = _a(tmp_path, win={"limit": 100, "window_s": 100}, create=False)
    assert second.used("C") == 2 and second.caps_fixed() == CAPS and second.bound_at == first.bound_at
    second.charge("C", "1")
    with pytest.raises(AL.AllowanceRefused, match="allowance 3 is used"):
        second.charge("C", "1")


def test_a_lane_never_creates_the_allowance_and_live_refuses_an_unattributed_request(tmp_path):
    with pytest.raises(AL.AllowanceRefused, match="never creates"):
        AL.LaneAllowance(tmp_path / "missing.sqlite", CAPS, WIN, parent=PARENT, run_key=KEY, create=False)
    a = _a(tmp_path, require_project=True)
    with pytest.raises(AL.AllowanceRefused, match="cannot be attributed to a project"):
        a.charge("P", None)
    assert a.used() == 0


def test_the_allowance_provider_charges_first_refuses_visibly_and_defers_without_a_charge(tmp_path):
    a = _a(tmp_path, caps={"C": 2, "B": 1}, win={"limit": 1, "window_s": 100}, parent=dict(PARENT, total=3))
    calls, refusals = [], []

    class Inner:
        def complete(self, request):
            calls.append(request)
            return Resp(data={}, model="claude-sonnet-5")

    p = AL.AllowanceProvider(a, "C", Inner(), Resp, ep_of=lambda: "1", invocation=1, ledger_entry_of=lambda: 17,
                             on_refusal=lambda exc, req: refusals.append(exc.kind))
    assert p.complete("r1").error is None and calls == ["r1"]
    assert a.audit()["charges"][0]["ledger_entry"] == 17 and a.audit()["charges"][0]["model"] == "claude-sonnet-5"
    with pytest.raises(AL.DeferDocument) as d:              # the project window (1) is full: deferred, nothing charged
        p.complete("r2")
    assert d.value.refusal.retry_at is not None and calls == ["r1"] and a.used() == 1
    q = AL.AllowanceProvider(a, "C", Inner(), Resp, ep_of=lambda: "2", invocation=1, on_refusal=lambda exc, req: refusals.append(exc.kind))
    assert q.complete("r3").error is None and calls == ["r1", "r3"]
    s = AL.AllowanceProvider(a, "C", Inner(), Resp, ep_of=lambda: "3", invocation=1, on_refusal=lambda exc, req: refusals.append(exc.kind))
    r = s.complete("r4")                                     # C's own allowance (2) is used: refused, never dispatched
    assert r.error == "budget" and "lane_allowance" in r.error_detail and calls == ["r1", "r3"] and refusals == ["lane_allowance"]
    assert [x["kind"] for x in a.audit()["refusals"]] == ["lane_allowance"]


def test_the_capture_store_file_is_bound_to_the_same_run_key(tmp_path):
    p = tmp_path / "capture.sqlite"
    assert AL.bind_store(p, KEY) == {"created": True}
    assert AL.bind_store(p, KEY) == {"created": False} and AL.bound_key(p) == KEY
    with pytest.raises(AL.AllowanceRefused, match="bound to another run"):
        AL.bind_store(p, "c" * 64)


def test_the_audit_view_reconciles_with_the_single_ledger_scope(tmp_path):
    a = _a(tmp_path, win={"limit": 100, "window_s": 100}, parent=dict(PARENT, total=8))
    led = H.fake_ledger(tmp_path / "ledger.sqlite", {"s": ({"requests": 8}, None, 0)})
    con = sqlite3.connect(str(led))
    e1 = con.execute("insert into entries (scope, state) values ('s', 'settled')").lastrowid
    e2 = con.execute("insert into entries (scope, state, outcome) values ('s', 'refused', 'breaker')").lastrowid
    con.commit()
    con.close()
    c1, c2, c3 = a.charge("B", "1"), a.charge("C", "1"), a.charge("C", "1")
    a.settle(c1, "ok", ledger_entry=e1)
    a.settle(c2, "budget", ledger_entry=e2)
    a.settle(c3, "dispatch_refused")
    rec = a.audit(led, "s")["reconciliation"]
    assert rec["consistent"] and rec["ledger_dispatch_entries"] == 1 and rec["ledger_refused_entries"] == 1
    assert rec["charges_with_ledger_entry"] == 2 and rec["charges_without_ledger_entry"] == 1 and rec["ledger_entries_without_charge_record"] == []
    bad = H.fake_ledger(tmp_path / "ledger2.sqlite", {"s": ({"requests": 9}, None, 3)})
    rec2 = a.audit(bad, "s")["reconciliation"]
    assert not rec2["consistent"] and any("differs from the parent total" in x for x in rec2["problems"])


def test_the_audit_cli_is_read_only(tmp_path):
    a = _a(tmp_path, win={"limit": 100, "window_s": 100})
    a.charge("C", "1", doc="F037", page="1", task="discover_page")
    before = (tmp_path / "a.sqlite").read_bytes()
    out = tmp_path / "ALLOWANCE-AUDIT.json"
    r = subprocess.run([sys.executable, AL.__file__, "audit", str(tmp_path / "a.sqlite"), str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    x = json.loads(out.read_text(encoding="utf-8"))
    assert x["charges"][0]["document"] == "F037" and x["lanes"]["C"]["charged"] == 1 and x["parent"] == PARENT
    assert (tmp_path / "a.sqlite").read_bytes() == before
    time.sleep(0)
