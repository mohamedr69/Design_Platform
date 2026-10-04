"""run_control_r38 / run_state_r38 (ORCH-08, A-09 points 1, 2, 3 and 7): the gate in front of the capture store (serve, or
refuse / defer before anything is reserved), the release of a reservation that was never dispatched, the durable stop,
the per-document recorder (nothing skipped silently), the identity rule of the stop controller, the dry stub's injections
and the probe's sample. Runs from C:/t/iso/cand-r29/backend (the capture store imports app.ai.provider; read-only use).
No provider and no model: every inner provider is a refusing / scripted fake. Run: python -m pytest -q test_run_control_r38.py"""
import json
import sqlite3

import pytest

import allowance_r32 as AL
import capture_store as CS
import model_identity_r38 as MI
import run_control_r38 as RC
from app.ai.provider import AiRequest, AiResponse, TextPart, Usage

KEY = "k" * 64
RUN_SET = [{"pool_id": "F001"}, {"pool_id": "F002"}, {"pool_id": "F003"}]
DECLARED = {"provider": "dry-refusing", "small": "claude-sonnet-5", "standard": "claude-opus-5"}


def req(text="x", task="discover_page"):
    return AiRequest(task=task, system="s", parts=[TextPart("t", text)], schema={"type": "object"}, max_output_tokens=10)


class Scripted:
    name = "dry-refusing"

    def __init__(self, *responses):
        self.responses, self.calls = list(responses), 0

    def complete(self, request):
        self.calls += 1
        return self.responses.pop(0) if self.responses else AiResponse(data=None, model="dry", error="dry_refused")


def chain(tmp_path, lane="C", inner=None, caps=None, win=None, ep="27331", reference_from=None, store=None, allowance=None, recorder=None):
    allowance = allowance or AL.LaneAllowance(tmp_path / "allowance.sqlite", caps or {"B": 5, "C": 5, "R": 5, "P": 5}, win or {"limit": 10, "window_s": 100},
                                              parent={"total": 20, "input_tokens": 10 ** 9, "output_tokens": 10 ** 9, "elapsed_s": 10 ** 6}, run_key=KEY)
    store = store or CS.CaptureStore(tmp_path / "capture.sqlite")
    rec = recorder or RC.LaneRecorder(lane, RUN_SET)
    inner = inner or Scripted()
    ident = MI.IdentityGuard(inner, AiResponse, declared=DECLARED, run_folder=tmp_path, invocation=1, lane=lane, log_path=tmp_path / f"id-{lane}.jsonl",
                             ctx_fn=CS.get_context, provider_name_fn=lambda: "dry-refusing")
    alw = AL.AllowanceProvider(allowance, lane, ident, AiResponse, ep_of=lambda: ep, context_of=CS.get_context, invocation=1)
    gate = RC.GateStoreProvider(store, lane, alw, lambda: "pol", lambda tier: "claude-sonnet-5", reference_from=reference_from, allowance=allowance,
                                recorder=rec, ep_of=lambda: ep, run_folder=tmp_path, invocation=1, response_cls=AiResponse, page_of=lambda: CS.get_context().get("page"))
    ctl = RC.ControllerR38()
    guard = RC.StopGuardR38(gate, ctl, lane, rec, AiResponse, allowance=allowance, invocation=1, page_of=lambda: CS.get_context().get("page"))
    return guard, gate, allowance, store, rec, ctl, inner


def _rows(store):
    return store.rows("select lane, state, outcome from requests order by seq")


def test_a_bound_fingerprint_is_served_never_resent(tmp_path):
    CS.set_context(sha256="a" * 64, page=1, profile="p", variant="EV1")
    g, gate, a, store, rec, ctl, inner = chain(tmp_path, inner=Scripted(AiResponse(data={"v": 1}, model="claude-sonnet-5")))
    rec.current = "F001"
    assert g.complete(req()).data == {"v": 1} and g.complete(req()).data == {"v": 1}
    assert inner.calls == 1 and gate.served == 1 and a.used("C") == 1 and len(_rows(store)) == 1


def test_r_is_served_c_capture_by_content_key(tmp_path):
    CS.set_context(sha256="a" * 64, page=1, profile="p", variant="EV1")
    gc, _, a, store, _, _, _ = chain(tmp_path, inner=Scripted(AiResponse(data={"v": 2}, model="claude-sonnet-5")))
    gc.complete(req())
    gr, gate_r, _, _, _, _, inner_r = chain(tmp_path, lane="R", reference_from="C", store=store, allowance=a)
    assert gr.complete(req()).data == {"v": 2} and inner_r.calls == 0 and a.used("R") == 0


def test_a_lane_allowance_refusal_reserves_nothing_is_recorded_and_stops_the_lane_durably(tmp_path):
    CS.set_context(sha256="a" * 64, page=3, profile="p", variant="EV1")
    g, gate, a, store, rec, ctl, inner = chain(tmp_path, caps={"B": 5, "C": 1, "R": 5, "P": 5})
    rec.current = "F001"
    g.complete(req("one"))
    rec.current = "F002"
    r = g.complete(req("two"))
    assert r.error == "budget" and "lane_allowance" in r.error_detail and inner.calls == 1 and len(_rows(store)) == 1
    assert ctl.lanes["C"]["state"] == "budget_stopped" and a.stops()["C"]["kind"] == "lane_allowance"
    assert [e["kind"] for e in rec.events] == ["lane_allowance"] and rec.events[0]["pool_id"] == "F002" and rec.events[0]["page"] == "3"
    rec.current = "F003"
    assert g.complete(req("three")).error == "stopped" and rec.events[-1]["kind"] == "lane_stopped", "every later request is visible"
    docs = rec.documents()
    assert docs["F002"]["status"] == "INCOMPLETE" and docs["F003"]["status"] == "INCOMPLETE" and docs["F001"]["status"] == "INCOMPLETE"
    assert docs["F002"]["classes"] == ["limit"] and docs["F002"]["pages"] == {"3": ["lane_allowance"]}


def test_a_full_project_window_defers_before_anything_is_reserved_and_the_retry_dispatches_once(tmp_path):
    CS.set_context(sha256="a" * 64, page=1, profile="p", variant="EV1")
    g, gate, a, store, rec, ctl, inner = chain(tmp_path, win={"limit": 1, "window_s": 100})
    rec.current = "F001"
    g.complete(req("one"))
    rec.current = "F002"
    with pytest.raises(AL.DeferDocument) as d:
        g.complete(req("two"))
    assert d.value.refusal.retry_at is not None and len(_rows(store)) == 1 and a.used() == 1, "not reserved, not charged"
    assert ctl.lanes["C"]["state"] == "running", "a deferral is not a stop"
    assert a.audit()["refusals"][0]["kind"] == "project_window" and rec.events[0]["retry_at"] == d.value.refusal.retry_at
    con = sqlite3.connect(str(tmp_path / "allowance.sqlite"))
    con.execute("update charges set at = at - 200")                   # the window frees (the charge is older than the window)
    con.commit()
    con.close()
    assert g.complete(req("two")).error == "dry_refused" and inner.calls == 2 and a.used() == 2
    assert g.complete(req("two")).error == "dry_refused" and inner.calls == 2, "dispatched once; then served"


def test_a_deferral_raised_after_the_reservation_releases_the_row_visibly(tmp_path, monkeypatch):
    CS.set_context(sha256="a" * 64, page=1, profile="p", variant="EV1")
    g, gate, a, store, rec, ctl, inner = chain(tmp_path)
    monkeypatch.setattr(a, "charge", lambda *x, **k: (_ for _ in ()).throw(AL.WindowDeferred("project_window", "race", retry_at=1.0)))
    rec.current = "F001"
    with pytest.raises(AL.DeferDocument):
        g.complete(req())
    assert _rows(store) == [] and inner.calls == 0
    con = sqlite3.connect(str(tmp_path / "capture.sqlite"))
    assert con.execute("select count(*) from releases").fetchone()[0] == 1
    con.close()


def test_an_identity_mismatch_makes_every_lane_terminal_and_the_run_invalid(tmp_path):
    CS.set_context(sha256="a" * 64, page=1, profile="p", variant="EV1")
    g, gate, a, store, rec, ctl, inner = chain(tmp_path, inner=Scripted(AiResponse(data={"x": 1}, usage=Usage(5, 1), model="claude-sonnet-5-1")))
    rec.current = "F001"
    r = g.complete(req())
    assert r.error == "identity_mismatch" and r.data is None
    assert ctl.comparison.startswith("INVALID: model identity mismatch") and all(s["state"] == "terminal" for s in ctl.lanes.values())
    assert MI.invalid_marker(tmp_path)["returned_model"] == "claude-sonnet-5-1"
    assert a.audit()["charges"][0]["outcome"] == "identity_mismatch", "the mismatched request stays charged"
    g2, gate2, *_ = chain(tmp_path, lane="R", store=store, allowance=a)
    assert g2.complete(req("other")).error == "identity_invalid" and gate2.gate_refused == 1, "refused at the gate, nothing reserved"


def test_the_recorder_never_drops_a_document():
    rec = RC.LaneRecorder("C", RUN_SET)
    rec.set("F001", "COMPLETE", "read")
    rec.set("F002", "DEFERRED", "window", retry_at=123.0)
    docs = rec.documents()
    assert set(docs) == {"F001", "F002", "F003"} and docs["F003"]["status"] == "INCOMPLETE" and "never reached" in docs["F003"]["reason"]
    assert docs["F002"]["classes"] == ["limit"] and docs["F002"]["retry_at_utc"]
    rec.current = "F001"
    rec.event("application_document_limit", page=2, detail="calls_per_document")
    d = rec.documents()["F001"]
    assert d["status"] == "INCOMPLETE" and d["classes"] == ["arm_policy"] and d["pages"] == {"2": ["application_document_limit"]}


def test_event_kinds_and_classes():
    assert RC.kind_class("provider_timeout") == "failure" and RC.kind_class("breaker") == "limit" and RC.kind_class("unknown-kind") == "limit"
    assert RC.event_kind(AiResponse(data=None, error="budget", error_detail="ledger refused (breaker): x")) == "breaker"
    assert RC.event_kind(AiResponse(data=None, error="budget", error_detail="ledger refused (requests): x")) == "ledger"
    assert RC.event_kind(AiResponse(data=None, error="budget", error_detail="harness allowance refused (parent_ceiling): x")) == "parent_ceiling"
    assert RC.event_kind(AiResponse(data=None, error="dry_refused")) is None and RC.event_kind(AiResponse(data={})) is None
    assert RC.classify(AiResponse(data=None, error="identity_invalid")) == "identity_mismatch"


def test_the_dry_stub_refuses_and_injects_only_what_it_is_told(monkeypatch):
    s = RC.DryStub(AiResponse, Usage, "C", [{"kind": "provider_timeout", "lane": "C", "calls": [2]}, {"kind": "identity_mismatch", "lane": "R", "calls": [1]},
                                            {"kind": "usage", "lane": "C", "calls": [3], "input_tokens": 7}], declared_model="claude-sonnet-5")
    assert s.complete(req()).error == "dry_refused"
    t = s.complete(req())
    assert t.error == "timeout" and t.model == "claude-sonnet-5"
    u = s.complete(req())
    assert u.error == "dry_refused" and u.usage.input_tokens == 7
    assert not any(s.complete(req()).ok for _ in range(3)), "the stub never answers"


def test_the_probe_samples_exactly_what_capture_store_probe_samples(tmp_path):
    store = CS.CaptureStore(tmp_path / "capture.sqlite")
    for i in range(20):
        CS.set_context(sha256=f"{i:064d}", page=1, profile="p", variant="EV1")
        row, _ = store.reserve("C", "pol", f"ck{i}", CS.get_context(), "discover_page")
        store.keep_payload(f"ck{i}", CS.payload_of(CS.get_context(), req(f"t{i}")))
        store.settle(row["seq"], AiResponse(data={"i": i}, model="claude-sonnet-5"))
    a = AL.LaneAllowance(tmp_path / "allowance.sqlite", {"B": 5, "C": 5, "R": 5, "P": 1}, {"limit": 100, "window_s": 100},
                         parent={"total": 16, "input_tokens": 10 ** 9, "output_tokens": 10 ** 9, "elapsed_s": 10 ** 6}, run_key=KEY)
    rec = RC.LaneRecorder("P", [])
    g, *_ = chain(tmp_path, lane="P", store=store, allowance=a, recorder=rec)
    out = RC.probe_r38(store, g, "probe:pol", lambda tier: "claude-sonnet-5", rec)
    import random
    rows = store.rows("select * from requests where lane = 'C' and state = 'answered' order by seq")
    want = sorted(random.Random("m2-r30-variation-2026-10-02").sample(rows, round(0.15 * len(rows))), key=lambda r: r["seq"])
    assert [r["seq"] for r in out["rows"]] == [r["seq"] for r in want] and out["sampled"] == 3
    assert [r["status"] for r in out["rows"]] == ["COMPLETE", "INCOMPLETE", "INCOMPLETE"], "P's own allowance (1): the rest is refused, visibly"
    assert out["population_state"] == "INCOMPLETE" and out["credit"].startswith("none")
    assert json.dumps(out)
