"""One-off patch of the r39 development copy of test_run_control_r38.py (exact replacements; refuses on a missing anchor)."""
import pathlib
import sys

P = pathlib.Path("C:/t/iso/work/r2x/r39/harness-r32/test_run_control_r38.py")
s = P.read_text(encoding="utf-8")

NEW = '''

# ---- ORCH-08C (Verification 39) ---------------------------------------------------------------------------------------------
SHA = "a" * 64


def test_an_undeclared_task_kind_is_refused_before_anything_recorded_and_makes_the_run_invalid(tmp_path):
    CS.set_context(sha256=SHA, page=1, profile="p", variant="EV1")
    g, gate, a, store, rec, ctl, inner = chain(tmp_path, expected_sha_of=lambda: SHA)
    rec.current = "F001"
    r = g.complete(req(task="drawings_reply_match"))
    assert r.error == "contract_breach" and r.error_detail.startswith("undeclared_task_kind") and inner.calls == 0
    assert _rows(store) == [] and a.used() == 0, "never reserved, never charged"
    b = RC.breach_marker(tmp_path)
    assert b["kind"] == "undeclared_task_kind" and b["task"] == "drawings_reply_match" and b["lane"] == "C" and b["context"]["sha256"] == SHA
    assert a.audit()["refusals"][0]["kind"] == "undeclared_task_kind" and rec.events[0]["kind"] == "undeclared_task_kind"
    assert ctl.comparison.startswith("INVALID: contract breach") and all(st["state"] == "terminal" for st in ctl.lanes.values())
    assert ctl.lanes["C"]["streak"] == 0, "a breach never counts toward a failure streak"
    g2, gate2, *_ = chain(tmp_path, lane="B", store=store, allowance=a, task_kinds={"read_submittal_form"}, expected_sha_of=lambda: SHA)
    r2 = g2.complete(req(task="read_submittal_form"))
    assert r2.error == "contract_breach" and "contract_breach_invalid" in r2.error_detail, "every later new request is refused: the run is INVALID"


@pytest.mark.parametrize("ctx,expected,why", [({}, SHA, "no document context"), ({"sha256": None, "page": 1}, SHA, "no document context"),
                                               ({"sha256": "b" * 64, "page": 1}, SHA, "stale context"), ({"sha256": SHA, "page": 1}, None, "stale context")])
def test_a_request_without_or_with_a_stale_context_is_a_contract_breach(tmp_path, ctx, expected, why):
    CS.set_context(**ctx)
    g, gate, a, store, rec, ctl, inner = chain(tmp_path, expected_sha_of=lambda: expected)
    r = g.complete(req())
    assert r.error == "contract_breach" and r.error_detail.startswith("missing_context") and why in r.error_detail and inner.calls == 0
    assert a.used() == 0 and RC.breach_marker(tmp_path)["kind"] == "missing_context"


def test_first_read_failed_the_repeat_is_dispatched_and_charged_as_a_retry_with_its_ordinal(tmp_path):
    CS.set_context(sha256=SHA, page=None, profile="b", variant="off")
    inner = Scripted(AiResponse(data=None, model="claude-sonnet-5", error="timeout"), AiResponse(data={"v": 2}, model="claude-sonnet-5"))
    g, gate, a, store, rec, ctl, inner = chain(tmp_path, lane="B", inner=inner, task_kinds={"read_submittal_form"}, expected_sha_of=lambda: SHA)
    rec.current = "F001"
    assert g.complete(req(task="read_submittal_form")).error == "timeout"
    r = g.complete(req(task="read_submittal_form"))                  # the application's own repeat (the reconcile check)
    assert r.data == {"v": 2} and inner.calls == 2 and a.used("B") == 2, "dispatched again and charged; never refunded"
    au = a.audit()
    assert [c["outcome"] for c in au["charges"]] == ["timeout", "ok"] and au["charges"][1]["note"].startswith("retry 2 of ")
    assert au["retries"][0]["id"] == au["charges"][1]["id"]
    assert store.rows("select ordinal, previous_outcome from retries") == [{"ordinal": 2, "previous_outcome": "timeout"}]
    assert [e["kind"] for e in rec.events] == ["provider_timeout", "retry_dispatched"] and rec.events[1]["retry_ordinal"] == 2
    assert g.complete(req(task="read_submittal_form")).data == {"v": 2} and inner.calls == 2, "the answer is bound now: served, never re-sent"
    assert gate.retried == 1 and rec.documents()["F001"]["retries"] == 1


def test_first_read_answered_the_repeat_is_served(tmp_path):
    CS.set_context(sha256=SHA, page=None, profile="b", variant="off")
    g, gate, a, store, rec, ctl, inner = chain(tmp_path, lane="B", inner=Scripted(AiResponse(data={"v": 1}, model="claude-sonnet-5")),
                                               task_kinds={"read_submittal_form"}, expected_sha_of=lambda: SHA)
    assert g.complete(req(task="read_submittal_form")).data == {"v": 1}
    assert g.complete(req(task="read_submittal_form")).data == {"v": 1} and inner.calls == 1 and a.used() == 1 and gate.retried == 0


def test_a_resume_never_resends_a_request_that_has_a_bound_answer_and_retries_one_that_failed(tmp_path):
    CS.set_context(sha256=SHA, page=1, profile="p", variant="EV1")
    inner1 = Scripted(AiResponse(data={"v": 1}, model="claude-sonnet-5"), AiResponse(data=None, model="claude-sonnet-5", error="invalid_response"))
    g1, _, a, store, *_ = chain(tmp_path, inner=inner1, expected_sha_of=lambda: SHA)
    assert g1.complete(req("answered")).data == {"v": 1} and g1.complete(req("failed")).error == "invalid_response"
    inner2 = Scripted(AiResponse(data={"v": 3}, model="claude-sonnet-5"))                     # the resume: a new invocation, same store
    g2, gate2, *_ = chain(tmp_path, inner=inner2, store=store, allowance=a, expected_sha_of=lambda: SHA)
    assert g2.complete(req("answered")).data == {"v": 1} and inner2.calls == 0, "a bound answer is served on the resume, never re-sent"
    assert g2.complete(req("failed")).data == {"v": 3} and inner2.calls == 1 and gate2.retried == 1, "a failure is never served: retried"
    assert a.used() == 3


def test_an_interrupted_dispatch_is_never_resent_and_dry_refused_is_bound(tmp_path):
    CS.set_context(sha256=SHA, page=1, profile="p", variant="EV1")
    g, gate, a, store, rec, ctl, inner = chain(tmp_path, expected_sha_of=lambda: SHA)
    row, _ = store.reserve("C", "pol", CS.content_key(CS.get_context(), req("x"), "claude-sonnet-5"), CS.get_context(), "discover_page")
    assert g.complete(req("x")).error == "interrupted_charged" and inner.calls == 0, "reserved without an answer: never re-sent"
    assert g.complete(req("y")).error == "dry_refused" and g.complete(req("y")).error == "dry_refused" and inner.calls == 1, \\
        "the dry stub's refusal stands for an answer in dry mode: served, not retried"


def test_r_is_served_cs_answer_after_a_c_retry_and_cs_latest_failure_otherwise(tmp_path):
    CS.set_context(sha256=SHA, page=1, profile="p", variant="EV1")
    c_inner = Scripted(AiResponse(data=None, model="claude-sonnet-5", error="timeout"), AiResponse(data={"v": 9}, model="claude-sonnet-5"),
                       AiResponse(data=None, model="claude-sonnet-5", error="timeout"))
    gc, _, a, store, *_ = chain(tmp_path, inner=c_inner, expected_sha_of=lambda: SHA)
    gc.complete(req("retried"))
    gc.complete(req("retried"))
    gc.complete(req("only-failed"))
    gr, gate_r, _, _, _, _, r_inner = chain(tmp_path, lane="R", reference_from="C", store=store, allowance=a, expected_sha_of=lambda: SHA)
    assert gr.complete(req("retried")).data == {"v": 9}, "C's answer (from its retry) is what R is served"
    assert gr.complete(req("only-failed")).error == "timeout" and r_inner.calls == 0 and a.used("R") == 0, "R never re-sends what C sent"


def test_the_probe_sample_is_frozen_at_ps_first_run(tmp_path):
    store = CS.CaptureStore(tmp_path / "capture.sqlite")
    for i in range(20):
        CS.set_context(sha256=f"{i:064d}", page=1, profile="p", variant="EV1")
        row, _ = store.reserve("C", "pol", f"ck{i}", CS.get_context(), "discover_page")
        store.keep_payload(f"ck{i}", CS.payload_of(CS.get_context(), req(f"t{i}")))
        store.settle(row["seq"], AiResponse(data={"i": i}, model="claude-sonnet-5"))
    a = AL.LaneAllowance(tmp_path / "allowance.sqlite", {"B": 5, "C": 5, "R": 5, "P": 10}, {"limit": 100, "window_s": 100},
                         parent={"total": 25, "input_tokens": 10 ** 9, "output_tokens": 10 ** 9, "elapsed_s": 10 ** 6}, run_key=KEY)
    rec = RC.LaneRecorder("P", [])
    g, *_ = chain(tmp_path, lane="P", store=store, allowance=a, recorder=rec, expected_sha_of=lambda: rec.expected_sha)
    first = RC.probe_r38(store, g, "probe:pol", lambda tier: "claude-sonnet-5", rec)
    for i in range(20, 40):                                 # C gains answered rows later (e.g. its retries in a later invocation)
        CS.set_context(sha256=f"{i:064d}", page=1, profile="p", variant="EV1")
        row, _ = store.reserve("C", "pol", f"ck{i}", CS.get_context(), "discover_page")
        store.settle(row["seq"], AiResponse(data={"i": i}, model="claude-sonnet-5"))
    again = RC.probe_r38(store, g, "probe:pol", lambda tier: "claude-sonnet-5", rec)
    assert [r["seq"] for r in again["rows"]] == [r["seq"] for r in first["rows"]] and again["of"] == first["of"] == 20
    assert first["sample_source"].startswith("drawn now") and again["sample_source"].startswith("the sample frozen")
    assert rec.expected_sha is None and CS.get_context() == {}, "the context is cleared after each probe item"


def test_a_window_deferral_carries_the_earliest_and_the_full_retry_times(tmp_path):
    CS.set_context(sha256=SHA, page=1, profile="p", variant="EV1")
    a = AL.LaneAllowance(tmp_path / "allowance.sqlite", {"B": 9, "C": 9, "R": 1, "P": 1}, {"limit": 2, "window_s": 100},
                         parent={"total": 20, "input_tokens": 10 ** 9, "output_tokens": 10 ** 9, "elapsed_s": 10 ** 6}, run_key=KEY,
                         project_totals={"EP-27331": {"planning": 3.0, "structural": 7}})
    g, gate, a, store, rec, ctl, inner = chain(tmp_path, allowance=a, expected_sha_of=lambda: SHA)
    g.complete(req("one"))
    g.complete(req("two"))
    with pytest.raises(AL.DeferDocument) as d:
        g.complete(req("three"))
    w = d.value.refusal
    assert w.retry_at_full["planning"] < w.retry_at_full["structural"] and w.retry_at <= w.retry_at_full["planning"]
    assert w.remaining == {"planning": 1, "structural": 5} and "retry_at_full" in w.detail
    assert rec.events[-1]["retry_at_full"] == w.retry_at_full
'''

REPL = [
    ('''def req(text="x", task="discover_page"):''', '''def req(text="x", task="discover_page"):'''),
    ('''def chain(tmp_path, lane="C", inner=None, caps=None, win=None, ep="27331", reference_from=None, store=None, allowance=None, recorder=None):''',
     '''def chain(tmp_path, lane="C", inner=None, caps=None, win=None, ep="27331", reference_from=None, store=None, allowance=None, recorder=None,
          task_kinds=("discover_page", "read_identity"), expected_sha_of=None):'''),
    ('''    gate = RC.GateStoreProvider(store, lane, alw, lambda: "pol", lambda tier: "claude-sonnet-5", reference_from=reference_from, allowance=allowance,
                                recorder=rec, ep_of=lambda: ep, run_folder=tmp_path, invocation=1, response_cls=AiResponse, page_of=lambda: CS.get_context().get("page"))''',
     '''    gate = RC.GateStoreProvider(store, lane, alw, lambda: "pol", lambda tier: "claude-sonnet-5", reference_from=reference_from, allowance=allowance,
                                recorder=rec, ep_of=lambda: ep, run_folder=tmp_path, invocation=1, response_cls=AiResponse,
                                page_of=lambda: CS.get_context().get("page"), task_kinds=task_kinds, expected_sha_of=expected_sha_of)'''),
    ('''    rec.current = "F001"
    rec.event("application_document_limit", page=2, detail="calls_per_document")
    d = rec.documents()["F001"]
    assert d["status"] == "INCOMPLETE" and d["classes"] == ["arm_policy"] and d["pages"] == {"2": ["application_document_limit"]}''',
     '''    rec.current = "F001"
    rec.event("application_document_limit", page=2, detail="calls_per_document")
    d = rec.documents()["F001"]
    # ORCH-08C (R39-06): application-internal per-document behaviour leaves the document COMPLETE (its unread pages listed)
    assert d["status"] == "COMPLETE" and d["classes"] == ["arm_policy"] and d["pages"] == {"2": ["application_document_limit"]}
    rec.unread_pages("F001", [{"page": "3", "kind": "application_reader_cap", "partial": False, "reason": "budget: calls per document"}])
    d = rec.documents()["F001"]
    assert d["status"] == "COMPLETE" and d["unread_pages"] == {"3": [{"kind": "application_reader_cap", "partial": False, "reason": "budget: calls per document"}]}
    rec.event("provider_timeout", page=1, detail="timeout")
    assert rec.documents()["F001"]["status"] == "INCOMPLETE", "a failure still makes it INCOMPLETE"'''),
    ('''    assert RC.classify(AiResponse(data=None, error="identity_invalid")) == "identity_mismatch"''',
     '''    assert RC.classify(AiResponse(data=None, error="identity_invalid")) == "identity_mismatch"
    assert RC.classify(AiResponse(data=None, error="contract_breach")) == "contract_breach", "never a provider failure"
    assert RC.event_kind(AiResponse(data=None, error="contract_breach", error_detail="missing_context: x")) == "missing_context"
    assert RC.kind_class("undeclared_task_kind") == "limit" and RC.kind_class("application_reader_cap") == "arm_policy"
    assert RC.kind_class("retry_dispatched") == "retry" and RC.kind_class("application_reader_exception") == "arm_policy"'''),
    ('''    g, *_ = chain(tmp_path, lane="P", store=store, allowance=a, recorder=rec)
    out = RC.probe_r38(store, g, "probe:pol", lambda tier: "claude-sonnet-5", rec)''',
     '''    g, *_ = chain(tmp_path, lane="P", store=store, allowance=a, recorder=rec, expected_sha_of=lambda: rec.expected_sha)
    out = RC.probe_r38(store, g, "probe:pol", lambda tier: "claude-sonnet-5", rec)'''),
    ('''    assert out["population_state"] == "INCOMPLETE" and out["credit"].startswith("none")
    assert json.dumps(out)''', '''    assert out["population_state"] == "INCOMPLETE" and out["credit"].startswith("none")
    assert json.dumps(out)''' + NEW),
    ('''No provider and no model: every inner provider is a refusing / scripted fake. Run: python -m pytest -q test_run_control_r38.py"""''',
     '''ORCH-08C: the declaration check at the gate (undeclared task kind, missing / stale context -> contract breach, the run
INVALID), the failed-read retry (dispatched again, charged, recorded with its ordinal; answers served; interrupted never
re-sent; R served C's answer), the frozen probe sample, the full retry time of a deferral, the COMPLETE-with-unread rule.
No provider and no model: every inner provider is a refusing / scripted fake. Run: python -m pytest -q test_run_control_r38.py"""'''),
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
