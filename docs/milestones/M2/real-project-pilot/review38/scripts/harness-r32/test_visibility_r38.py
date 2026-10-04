"""The visibility drill as tests (ORCH-08, A-09 points 1, 2, 3 and 7): every injected refusal kind -- lane allowance, project
window (deferral and resume), deferral beyond the elapsed bound, an elapsed bound passed while deferred, a ledger breaker, a
ledger refusal, provider timeouts, an interrupted dispatch, a dispatched-but-unsaved response, a model identity mismatch,
and the application path on SYNTHETIC EP-990001 documents -- is recorded in the run state, the lane rows, the scorer (the
documents stay in the denominators) and the audit view; silent skipping anywhere is a test failure. Each failure kind is
also a two-invocation drill: the resume never resets an allowance, a charge or a terminal stop. Dry runs only (refusing
stub, no provider, no model request; FAKE ledgers inside the dry run folder); the AI ledger reads the same before and after.
Run: python -m pytest -q test_visibility_r38.py"""
import json
import pathlib
import sqlite3

import pytest

import allowance_r32 as AL
import model_identity_r38 as MI
import preflight_r32 as PF
import runner_r32 as RN
import visibility_r38 as V

LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"


@pytest.fixture(scope="module")
def ledger_before():
    return PF.ledger_counts(LEDGER)


def _run(tmp_path, name):
    res = V.run_scenario(name, tmp_path / name)
    folder = pathlib.Path(res["run_folder"])
    return res, folder, V.locate(folder, V.KINDS[name])


def _st(folder):
    return json.loads((folder / "RUN-STATE.json").read_text(encoding="utf-8"))


def _rep(folder, n):
    return json.loads((folder / f"inv-{n}" / "out" / "RUN-REPORT.json").read_text(encoding="utf-8"))


def _audit(folder, n):
    return json.loads((folder / f"inv-{n}" / "out" / "ALLOWANCE-AUDIT.json").read_text(encoding="utf-8"))


def _no_silent_skip(folder):
    """Every run-set document has a status in every lane of every invocation report, and in every normalised lane."""
    st = _st(folder)
    for inv in st["invocations"]:
        if inv.get("status") != "finished":
            continue
        rep = _rep(folder, inv["n"])
        ids = {d["pool_id"] for d in rep["run_set_keys"]}
        for lane, docs in rep["documents"].items():
            if lane == "P":
                continue
            assert ids <= set(docs), (lane, ids - set(docs))
            assert all(d["status"] in ("COMPLETE", "INCOMPLETE", "DEFERRED") for d in docs.values())
        for lane in ("B", "C", "R"):
            p = folder / f"inv-{inv['n']}" / "out" / f"lane-{lane}.r32.json"
            if p.is_file():
                assert set(json.loads(p.read_text(encoding="utf-8"))["documents"]) == ids, lane


def test_lane_allowance_refusal_is_visible_everywhere_and_the_resume_keeps_the_stop(tmp_path, ledger_before):
    res, folder, loc = _run(tmp_path, "lane_allowance")
    assert [s["result"] for s in res["steps"]] == ["finished", "finished"]
    r1 = _rep(folder, 1)
    assert r1["comparison_state"] == "INCOMPLETE" and r1["documents"]["C"]["F009"]["status"] == "INCOMPLETE"
    assert {d["status"] for p, d in r1["documents"]["C"].items() if p != "F037"} == {"INCOMPLETE"}, "every later C document is visible"
    assert loc["run_state"] and loc["lane_rows"] and loc["scorer"] and loc["audit"]
    a1, a2 = _audit(folder, 1), _audit(folder, 2)
    assert a1["stops"]["C"]["kind"] == "lane_allowance" and a2["stops"] == a1["stops"], "a resume never resets a terminal stop"
    assert a2["lanes"]["C"]["charged"] == a1["lanes"]["C"]["charged"] == 1 and a2["total_charged"] == a1["total_charged"], "nothing charged twice"
    assert any(r["kind"] == "terminal_stop" for r in a2["refusals"]), "the second invocation is refused by the durable stop, visibly"
    sb = json.loads((folder / "inv-1" / "out" / "SCORE-BCR-R32.json").read_text(encoding="utf-8"))
    assert set(sb["limit_incomplete"]["C"]["limit_incomplete"]) == {"F009", "F051", "F066"} and sb["outcome"] == "INCOMPLETE"
    assert sb["metrics"]["C"]["fields"]["decision"]["coverage_resolved"]["status_rows"], "retained in the denominator, shown apart"
    _no_silent_skip(folder)
    assert PF.ledger_counts(LEDGER) == ledger_before


def test_project_window_deferral_resumes_after_the_window_frees_and_never_resends(tmp_path, ledger_before):
    res, folder, loc = _run(tmp_path, "project_window")
    st = _st(folder)
    assert st["invocations"][0]["run_state"] == "DEFERRED" and st["invocations"][0]["earliest_retry_utc"]
    assert st["invocations"][-1]["run_state"] == "FINISHED", [i.get("run_state") for i in st["invocations"]]
    early = [s for s in res["steps"] if s.get("early")]
    assert early and all(s["result"] == "refused" and "has not freed yet" in s["why"] for s in early), "an early resume creates nothing"
    assert len(st["invocations"]) == 1 + sum(1 for s in res["steps"][1:] if not s.get("early"))
    assert loc["lane_rows"] and loc["audit"] and loc["run_state"]
    assert any(x["kind"] == "project_window" and x["retry_at_utc"] for x in loc["audit"]), "every deferral is in the audit with its retry time"
    assert V.capture_duplicates(folder) == 0, "a bound fingerprint is never re-sent"
    last = _audit(folder, len(st["invocations"]))
    con = sqlite3.connect(f"file:{(folder / 'capture.sqlite').as_posix()}?mode=ro", uri=True)
    rows = con.execute("select count(*) from requests").fetchone()[0]
    con.close()
    assert last["total_charged"] == rows, "every charge is one first dispatch; a deferral is never charged"
    _no_silent_skip(folder)
    assert PF.ledger_counts(LEDGER) == ledger_before


def test_a_deferral_beyond_the_elapsed_bound_ends_incomplete_and_visible(tmp_path):
    res, folder, loc = _run(tmp_path, "deferral_beyond_bound")
    r1 = _rep(folder, 1)
    assert r1["documents"]["B"]["F009"]["status"] == "INCOMPLETE" and "deferral_beyond_bound" in r1["documents"]["B"]["F009"]["kinds"]
    assert r1["comparison_state"].startswith("INCOMPLETE") and r1["run_state"] != "DEFERRED"
    assert loc["audit"] and loc["lane_rows"] and loc["run_state"]


def test_an_elapsed_bound_that_passes_while_deferred_closes_the_run_incomplete(tmp_path):
    res, folder, loc = _run(tmp_path, "bound_passed_while_deferred")
    st = _st(folder)
    assert st["invocations"][0]["run_state"] == "DEFERRED"
    assert res["steps"][1]["result"] == "refused" and "elapsed bound" in res["steps"][1]["why"]
    assert st["invocations"][-1]["status"] == "closed" and st["invocations"][-1]["comparison_state"].startswith("INCOMPLETE")
    assert st["invocations"][-1]["deferred_now_incomplete"], "the deferred documents are listed, now INCOMPLETE"
    assert res["steps"][2]["result"] == "refused" and "closed" in res["steps"][2]["why"]
    assert any(x["where"].endswith("(closed)") for x in loc["run_state"])


@pytest.mark.parametrize("name,kind", [("breaker", "breaker"), ("ledger", "ledger")])
def test_breaker_and_ledger_refusals_from_the_applications_ledger_are_visible_and_reconciled(tmp_path, name, kind, ledger_before):
    res, folder, loc = _run(tmp_path, name)
    r1 = _rep(folder, 1)
    assert r1["comparison_state"] == "INCOMPLETE" and any(kind in d["kinds"] for d in r1["documents"]["C"].values())
    a = _audit(folder, 1)
    assert a["stops"]["C"]["kind"] == kind
    assert any(c["outcome"] == "budget" and c["ledger_entry"] for c in a["charges"]), "the refused request names its ledger entry"
    rec = a["reconciliation"]
    assert rec["ledger"].endswith("FAKE-LEDGER.sqlite") and rec["ledger_refused_entries"] >= 1 and rec["charges_with_ledger_entry"] >= 1
    assert loc["lane_rows"] and loc["scorer"] and loc["audit"]
    assert PF.ledger_counts(LEDGER) == ledger_before, "the fake ledger is not the AI ledger"


def test_provider_timeouts_are_visible_per_page_and_the_terminal_stop_survives_the_resume(tmp_path):
    res, folder, loc = _run(tmp_path, "provider_timeout")
    r1 = _rep(folder, 1)
    assert r1["comparison_state"].startswith("INCOMPLETE") and r1["stop_controller"]["lanes"]["C"]["state"] == "terminal"
    assert [d["status"] for d in r1["documents"]["C"].values()] == ["INCOMPLETE"] * 4
    assert any(x["kind"] == "provider_timeout" and x["page"] == "1" for x in loc["lane_rows"])
    a1, a2 = _audit(folder, 1), _audit(folder, 2)
    assert [c["outcome"] for c in a1["charges"] if c["lane"] == "C"] == ["timeout"] * 3, "timed-out requests stay charged"
    assert a2["stops"]["C"] == a1["stops"]["C"] and a2["lanes"]["C"]["charged"] == 3, "the resume never resets the stop or the charges"
    _no_silent_skip(folder)


@pytest.mark.parametrize("name", ["interrupted", "unsaved"])
def test_an_interrupted_or_unsaved_dispatch_stays_charged_and_is_visible_on_the_resume(tmp_path, name):
    res, folder, loc = _run(tmp_path, name)
    st = _st(folder)
    assert [i["status"] for i in st["invocations"]] == ["interrupted", "finished"] and res["steps"][0]["result"] == "error"
    a2 = _audit(folder, 2)
    assert [c["outcome"] for c in a2["charges"] if c["lane"] == "C"].count("dispatched") == 1, "charged, never settled, never refunded"
    assert any(x["kind"] == "interrupted_charged" and x["served"] for x in loc["lane_rows"])
    assert _rep(folder, 2)["documents"]["C"]["F009"]["status"] == "INCOMPLETE"
    assert V.capture_duplicates(folder) == 0
    log = (folder / "inv-1" / "IDENTITY-LOG-C.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(log) == (2 if name == "unsaved" else 1), "an unsaved response was logged before the process died; an interrupted one never came back"


def test_an_identity_mismatch_makes_the_run_invalid_and_records_the_offending_request(tmp_path):
    res, folder, loc = _run(tmp_path, "identity_mismatch")
    r1 = _rep(folder, 1)
    assert r1["candidate_outcome"] == "INVALID" and r1["run_state"] == "INVALID"
    m = MI.invalid_marker(folder)
    assert m["returned_model"] == "claude-sonnet-5-1" and m["expected_model"] == "claude-sonnet-5" and m["lane"] == "C" and m["invocation"] == 1
    assert r1["lane_gates"]["R"].startswith("not started") and r1["identity_invalid"] == m
    assert res["steps"][1]["result"] == "refused" and "INVALID" in res["steps"][1]["why"], "never resumed"
    a = _audit(folder, 1)
    assert any(c["outcome"] == "identity_mismatch" for c in a["charges"])
    assert loc["lane_rows"] and loc["audit"] and loc["run_state"]
    _no_silent_skip(folder)


def test_the_application_path_on_synthetic_documents_records_pages(tmp_path, ledger_before):
    res, folder, loc = _run(tmp_path, "application_path")
    r1 = _rep(folder, 1)
    assert r1["lanes"]["C"]["application_reader_run"] is True and r1["model_requests"] == 0
    c = r1["documents"]["C"]
    assert c["SYN001"]["status"] == "INCOMPLETE" and c["SYN001"]["pages"].get("1") == ["provider_timeout"], "the timed-out page is named"
    assert any(x["kind"] == "lane_allowance" for x in loc["audit"]) and any(x["kind"] == "lane_allowance" for x in loc["lane_rows"])
    assert all(p.startswith("SYN") for p in c)
    assert PF.ledger_counts(LEDGER) == ledger_before


def test_the_applications_own_project_limit_refusing_first_is_recorded_never_silent(tmp_path, ledger_before):
    """R38-08's failure mode (the application's per-project limit refusing before the harness) is impossible with compatible
    limits (preflight); if it ever fires it is recorded per document and page, in the audit too, and the comparison is
    INCOMPLETE. Dry drill: the limit is lowered to 1 on SYNTHETIC EP-990001 documents."""
    res, folder, loc = _run(tmp_path, "application_project_limit")
    r1 = _rep(folder, 1)
    c = r1["documents"]["C"]
    assert any("application_project_limit" in d["kinds"] and d["status"] == "INCOMPLETE" for d in c.values())
    assert any(x["kind"] == "application_project_limit" and x["class"] == "limit" and x["page"] == "1" for x in loc["lane_rows"])
    assert any(x["kind"] == "application_project_limit" for x in loc["audit"]), "in the audit view as a refusal"
    sb = json.loads((folder / "inv-1" / "out" / "SCORE-BCR-R32.json").read_text(encoding="utf-8"))
    assert sb["limit_incomplete"]["C"]["limit_incomplete"], "a limit refusal in C makes the comparison INCOMPLETE"
    assert PF.ledger_counts(LEDGER) == ledger_before


def test_the_drill_scenarios_cover_every_kind_the_task_names():
    names = set(V.SCENARIOS)
    assert {"lane_allowance", "project_window", "breaker", "ledger", "provider_timeout", "interrupted", "unsaved", "identity_mismatch",
            "application_path", "deferral_beyond_bound", "bound_passed_while_deferred"} <= names
    assert all(not s.get("synthetic") or all(d["pool_id"].startswith("SYN") for d in s["synthetic"]["documents"]) for s in V.SCENARIOS.values())
    assert AL.PERMANENT_KINDS and RN.INJECTION_KINDS
