"""ORCH-08C task item 2 (R39-06; A-09 point 1): pages the application does not read under its own per-document limits are
recorded per page and the document stays COMPLETE with unread_pages; harness and resource refusals make it INCOMPLETE.
Verification 39's scenarios A (4 + 4: the reader's own cap), B (7 + 5: the JobBudget) and C (a reader exception) are
reproduced with the candidate's own reader and budget in a child process (unread_pages_probe_r39.py; read-only use of the
candidate tree, no database, no model). Run: python -m pytest -q test_unread_pages_r39.py"""
import json
import pathlib
import subprocess
import uuid

import pytest

import preflight_r32 as PF
import run_state_r38 as RS
import sandbox_ingest_r32 as SI
import score_bcr_r32 as S

HERE = pathlib.Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def probe():
    root = pathlib.Path(PF.DEFAULT_SANDBOX_BASE) / f"tests-unread-{uuid.uuid4().hex[:8]}"
    (root / "db").mkdir(parents=True)
    env = SI.sandbox_env(root, ai_enabled=False, extra={"AI_EVIDENCE_SCHEDULING": "required_first"})
    out = root / "PROBE.json"
    r = subprocess.run([SI.PY, str(HERE / "unread_pages_probe_r39.py"), str(out)], cwd="C:/t/iso/cand-r29/backend", env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(out.read_text(encoding="utf-8"))


def _doc(unread, events=()):
    rec = RS.LaneRecorder("C", [{"pool_id": "F1"}])
    rec.unread_pages("F1", unread)
    for kind, page in events:
        rec.event(kind, pid="F1", page=page, detail="x")
    rec.set("F1", "COMPLETE", "read by the application's evidence stage")
    return rec.documents()["F1"], rec


def test_scenario_a_the_readers_own_cap_skips_pages_3_and_4_and_they_are_recorded(probe):
    a = probe["A"]
    assert probe["reader_soft_cap"] == 8 and a["run_exhausted"] is None and a["provider_calls"] == 8, "no exhaustion: invisible to review38"
    for shape in (a["coverage"], a["stored_summary"]):
        u = RS.unread_pages_of_attempt(shape, 4)
        assert [(x["page"], x["kind"], x["partial"]) for x in u] == [("3", "application_reader_cap", False), ("4", "application_reader_cap", False)]
    d, rec = _doc(RS.unread_pages_of_attempt(a["stored_summary"], 4))
    assert d["status"] == "COMPLETE" and d["unread_page_count"] == 2 and set(d["unread_pages"]) == {"3", "4"} and d["classes"] == ["arm_policy"]
    assert [e["kind"] for e in rec.events] == ["application_reader_cap", "application_reader_cap"] and [e["page"] for e in rec.events] == ["3", "4"]
    assert "2 page(s) not read" in d["reason"]


def test_scenario_b_the_job_budget_skips_pages_3_and_4_and_they_are_recorded(probe):
    b = probe["B"]
    assert b["run_exhausted"] and b["run_calls"] == probe["job_calls_per_document"] == 12
    u = RS.unread_pages_of_attempt(b["stored_summary"], 4)
    assert [(x["page"], x["kind"]) for x in u] == [("3", "application_document_limit"), ("4", "application_document_limit")]
    assert RS.unread_pages_of_attempt(b["coverage"], 4) == u
    d, _ = _doc(u, events=[("application_document_limit", "2")])      # the lane also records the exhaustion where it happened
    assert d["status"] == "COMPLETE" and d["unread_page_count"] == 2 and d["pages"]["2"] == ["application_document_limit"]


def test_scenario_c_a_reader_exception_leaves_every_in_scope_page_unread_and_recorded(probe):
    c = probe["C"]
    assert probe["evidence_stage_exception_branch_present"] and c["stored_summary"]["outcome"] == "failed" and c["stored_summary"]["pages"] == {}
    u = RS.unread_pages_of_attempt(c["stored_summary"], 4)
    assert [x["page"] for x in u] == ["1", "2", "3", "4"] and {x["kind"] for x in u} == {"application_reader_exception"}
    assert "injected reader exception" in u[0]["reason"]
    d, _ = _doc(u)
    assert d["status"] == "COMPLETE" and d["unread_page_count"] == 4


def test_a_page_read_in_part_under_the_budget_is_listed_as_partial_and_no_trigger_pages_are_not_listed():
    u = RS.unread_pages_of_attempt({"outcome": "budget", "pages": {"1": {"outcome": "completed", "requests": {"discovery": "ok"}},
                                                                   "2": {"outcome": "partial", "requests": {"own:identity": "ok", "own:revision": "budget"}},
                                                                   "3": {"outcome": "no_trigger"}}}, 3)
    assert u == [{"page": "2", "kind": "application_document_limit", "partial": True,
                  "reason": "read in part: request(s) own:revision refused by the application's budget"}]
    d, _ = _doc(u)
    assert d["status"] == "COMPLETE" and d["unread_page_count"] == 0 and d["partially_read_pages"] == ["2"]
    assert RS.unread_pages_of_attempt(None, 4) == [] and RS.unread_pages_of_attempt({"outcome": "complete", "pages": {}}, 2) == []


@pytest.mark.parametrize("kind", ["lane_allowance", "parent_ceiling", "project_window_refused", "breaker", "ledger", "guard", "identity_invalid",
                                  "provider_timeout", "interrupted_charged", "application_project_limit"])
def test_harness_and_resource_refusals_still_make_the_document_incomplete(kind):
    k = "project_window" if kind == "project_window_refused" else kind
    d, _ = _doc([{"page": "3", "kind": "application_reader_cap", "partial": False, "reason": "x"}], events=[(k, "2")])
    if k == "project_window":              # a window refusal defers the document (the lane sets DEFERRED); the event alone never flips it
        assert d["status"] == "COMPLETE"
    else:
        assert d["status"] == "INCOMPLETE" and ("limit" in d["classes"] or "failure" in d["classes"]) and d["unread_page_count"] == 1


def test_a_retry_event_never_changes_the_status():
    rec = RS.LaneRecorder("B", [{"pool_id": "F1"}])
    rec.event("retry_dispatched", pid="F1", detail="retry 2")
    rec.set("F1", "COMPLETE", "processed")
    d = rec.documents()["F1"]
    assert d["status"] == "COMPLETE" and d["retries"] == 1 and d["classes"] == ["retry"]


def test_the_scorer_reports_per_lane_the_documents_with_unread_pages_and_keeps_them_complete():
    lane = {"lane": "C", "documents": {"F1": {"status": "COMPLETE", "unread_pages": {"3": [{"kind": "application_reader_cap"}]}, "unread_page_count": 1,
                                              "partially_read_pages": []},
                                       "F2": {"status": "COMPLETE", "unread_pages": {}, "unread_page_count": 0}}}
    u = S.unread_pages(lane, {"F1", "F2"})
    assert u["documents_with_unread_pages"] == 1 and u["unread_pages"] == 1 and set(u["documents"]) == {"F1"}
    assert S.limit_state(lane, {"F1", "F2"}) == {"deferred": {}, "limit_incomplete": {}, "other_incomplete": {}}, "never a limit, never INCOMPLETE"


def test_the_rule_is_stated_in_the_report_template():
    t = S.report_template({})
    assert "stays COMPLETE" in t and "counted as unread in every denominator" in t and "Harness and resource refusals make a document INCOMPLETE" in t
