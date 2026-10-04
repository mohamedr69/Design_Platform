"""One-off patch of the r39 development copy of test_visibility_r38.py (exact replacements; refuses on a missing anchor)."""
import pathlib
import sys

P = pathlib.Path("C:/t/iso/work/r2x/r39/harness-r32/test_visibility_r38.py")
s = P.read_text(encoding="utf-8")

NEW_TESTS = '''def test_an_undeclared_task_kind_is_a_contract_breach_visible_everywhere_and_never_resumed(tmp_path, ledger_before):
    res, folder, loc = _run(tmp_path, "undeclared_task_kind")
    r1 = _rep(folder, 1)
    b = r1["contract_breach"]
    assert r1["candidate_outcome"] == "INVALID" and r1["run_state"] == "INVALID" and r1["comparison_state"].startswith("INVALID: contract breach")
    assert b["kind"] == "undeclared_task_kind" and b["lane"] == "B" and b["task"] == "drawings_reply_match" and b["context"]["sha256"]
    assert (folder / "CONTRACT-BREACH.json").is_file() and res["steps"][1]["result"] == "refused" and "contract breach" in res["steps"][1]["why"]
    a = _audit(folder, 1)
    assert any(r["kind"] == "undeclared_task_kind" and r["task"] == "drawings_reply_match" for r in a["refusals"])
    assert not any(c["task"] == "drawings_reply_match" for c in a["charges"]), "the refused request was never charged"
    assert any(x["kind"] == "undeclared_task_kind" for x in loc["lane_rows"]) and loc["run_state"] and loc["scorer"] and loc["audit"]
    assert r1["stop_controller"]["lanes"]["B"]["streak"] == 0, "a breach never counts toward a failure streak"
    _no_silent_skip(folder)
    assert PF.ledger_counts(LEDGER) == ledger_before


def test_a_request_without_a_document_context_is_a_contract_breach(tmp_path, ledger_before):
    res, folder, loc = _run(tmp_path, "missing_context")
    r1 = _rep(folder, 1)
    b = r1["contract_breach"]
    assert r1["candidate_outcome"] == "INVALID" and b["kind"] == "missing_context" and b["lane"] == "C" and b["context"]["sha256"] is None
    a = _audit(folder, 1)
    assert any(r["kind"] == "missing_context" and r["lane"] == "C" for r in a["refusals"])
    assert a["lanes"]["C"]["charged"] == 1, "only the first document's request; the breach was never charged"
    assert any(x["kind"] == "missing_context" for x in loc["lane_rows"]) and loc["run_state"] and loc["audit"]
    _no_silent_skip(folder)
    assert PF.ledger_counts(LEDGER) == ledger_before


def test_pages_left_unread_by_the_application_are_listed_and_the_document_stays_complete(tmp_path, ledger_before):
    res, folder, loc = _run(tmp_path, "unread_pages")
    r1 = _rep(folder, 1)
    c = r1["documents"]["C"]
    assert c["SYN001"]["status"] == "COMPLETE" and "4" in c["SYN001"]["unread_pages"] and c["SYN001"]["unread_page_count"] >= 1
    assert all(u["kind"] == "application_document_limit" for v in c["SYN001"]["unread_pages"].values() for u in v)
    assert c["SYN003"]["status"] == "COMPLETE" and set(c["SYN003"]["unread_pages"]) == {"1", "2", "3", "4"}
    assert all(u["kind"] == "application_reader_exception" for v in c["SYN003"]["unread_pages"].values() for u in v)
    sl = json.loads((folder / "inv-1" / "out" / "lane-C.r32.json").read_text(encoding="utf-8"))
    assert sl["documents"]["SYN003"]["unread_page_count"] == 4 and "SYN003" in sl["unread"]["documents_with_unread_pages"]
    sb = json.loads((folder / "inv-1" / "out" / "SCORE-BCR-R32.json").read_text(encoding="utf-8"))
    assert set(sb["unread_pages"]["C"]["documents"]) >= {"SYN001", "SYN003"} and sb["unread_pages"]["C"]["unread_pages"] >= 5
    assert "SYN003" not in sb["limit_incomplete"]["C"]["limit_incomplete"], "application-internal behaviour is never a limit"
    a = _audit(folder, 1)
    assert sum(1 for r in a["refusals"] if r["kind"] == "application_reader_exception") == 4
    assert loc["run_state"] and loc["lane_rows"] and loc["scorer"] and loc["audit"]
    assert PF.ledger_counts(LEDGER) == ledger_before


def test_the_full_resume_policy_records_both_times_and_refuses_an_early_resume(tmp_path, ledger_before):
    res, folder, loc = _run(tmp_path, "retry_policy_full")
    st = _st(folder)
    deferred = [i for i in st["invocations"] if i.get("run_state") == "DEFERRED"]
    assert deferred and all(i["resume_policy"] == "full" and i["retry_at_full_utc"]["structural"] and i["retry_at_full_utc"]["planning"]
                            and i["resume_not_before"] >= i["earliest_retry"] for i in deferred)
    assert st["invocations"][-1]["run_state"] == "FINISHED"
    early = [s for s in res["steps"] if s.get("early") or s.get("between_earliest_and_full")]
    assert early and all(s["result"] == "refused" and "'full'" in s["why"] and "nothing was created" in s["why"] for s in early)
    assert len(st["invocations"]) == 1 + sum(1 for s in res["steps"][1:] if not (s.get("early") or s.get("between_earliest_and_full")))
    assert any("retry_at_full" in x["where"] for x in loc["run_state"]) and loc["audit"]
    rec = [r for r in _audit(folder, 1)["refusals"] if r["kind"] == "project_window"]
    assert rec and all("retry_at_full" in r["detail"] for r in rec), "every deferral states both times"
    assert V.capture_duplicates(folder) == 0
    _no_silent_skip(folder)
    assert PF.ledger_counts(LEDGER) == ledger_before


def test_a_failed_form_read_is_retried_on_the_applications_path_charged_never_served_its_failure(tmp_path, ledger_before):
    res, folder, loc = _run(tmp_path, "failed_read_retry")
    a = _audit(folder, 1)
    b = [c for c in a["charges"] if c["lane"] == "B"]
    assert [c["outcome"] for c in b] == ["timeout", "dry_refused"] and b[1]["note"].startswith("retry 2 of "), "dispatched again and charged"
    assert a["retries"] and a["retries"][0]["lane"] == "B" and a["retries"][0]["task"] == "read_submittal_form"
    lb = json.loads((folder / "inv-1" / "out" / "LANE-B.json").read_text(encoding="utf-8"))
    ev = [e for e in lb["limit_events"] if e["kind"] == "retry_dispatched"]
    assert ev and ev[0]["retry_ordinal"] == 2 and ev[0]["previous_outcome"] == "timeout" and lb["retries"]["dispatched"] == 1
    con = sqlite3.connect(f"file:{(folder / 'capture.sqlite').as_posix()}?mode=ro", uri=True)
    assert con.execute("select ordinal, previous_outcome from retries").fetchall() == [(2, "timeout")]
    con.close()
    assert any(x["kind"] == "retry_dispatched" for x in loc["lane_rows"]) and any("retries[" in x["where"] for x in loc["audit"])
    assert PF.ledger_counts(LEDGER) == ledger_before


def test_the_drill_scenarios_cover_every_kind_the_task_names():
    names = set(V.SCENARIOS)
    assert {"lane_allowance", "project_window", "breaker", "ledger", "provider_timeout", "interrupted", "unsaved", "identity_mismatch",
            "application_path", "deferral_beyond_bound", "bound_passed_while_deferred", "undeclared_task_kind", "missing_context",
            "unread_pages", "retry_policy_full", "failed_read_retry"} <= names'''

REPL = [
    ('''    assert early and all(s["result"] == "refused" and "has not freed yet" in s["why"] for s in early), "an early resume creates nothing"''',
     '''    assert early and all(s["result"] == "refused" and "allows a resume at" in s["why"] and "nothing was created" in s["why"] for s in early), \\
        "an early resume creates nothing"
    assert all(i.get("resume_policy") == "earliest" for i in st["invocations"] if i.get("run_state") == "DEFERRED")'''),
    ('''Run: python -m pytest -q test_visibility_r38.py"""''',
     '''ORCH-08C adds: an undeclared task kind and a context-free request (contract breaches: the run INVALID), pages the
application leaves unread under its own per-document limits and a reader exception (COMPLETE with unread pages), the 'full'
resume policy (retry_at_earliest / retry_at_full, refusal before the policy's time) and the retry of a failed form read.
Run: python -m pytest -q test_visibility_r38.py"""'''),
    ('''def test_the_drill_scenarios_cover_every_kind_the_task_names():
    names = set(V.SCENARIOS)
    assert {"lane_allowance", "project_window", "breaker", "ledger", "provider_timeout", "interrupted", "unsaved", "identity_mismatch",
            "application_path", "deferral_beyond_bound", "bound_passed_while_deferred"} <= names''', NEW_TESTS),
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
