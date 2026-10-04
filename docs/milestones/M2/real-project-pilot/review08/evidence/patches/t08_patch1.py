import pathlib

p = pathlib.Path(r"C:/t/iso/ep-platform/backend/tests/test_m2_review08.py")
s = p.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new)


i = s.index("def test_a_blind_identity_timeout_keeps_the_old_decision_and_identity(doc_row):")
j = s.index("def test_identity_completes_while_revision_times_out")
s = s[:i] + '''def test_a_blind_identity_timeout_keeps_the_old_decision_and_identity(doc_row):
    ai = stage(doc_row, [discover("X-SD-1", decision=APPROVAL), read("X-SD-1"), decision_read()])
    assert value(ai, "own:identity")[:2] == ("X-SD-1", "validated") and value(ai, "own:decision")[:2] == ("ANN", "validated")
    # the reviewer's case: discovery succeeds (it sees the identity only), the blind identity read times out
    ai = stage(doc_row, [discover("X-SD-1"), timeout()])
    page = ai["attempts"][-1]["pages"]["1"]
    assert page["outcome"] == "partial" and page["fields"]["own:identity"] == "failed:timeout"
    assert page["fields"]["own:decision"] == "absent_by_discovery"
    assert value(ai, "own:identity") == ("X-SD-1", "validated", 1, "completed")
    assert value(ai, "own:decision") == ("ANN", "validated", 1, "completed"), "the old decision survives"
    # discovery sees the decision block too, and both blind reads time out: still nothing replaced
    ai = stage(doc_row, [discover("X-SD-1", decision=APPROVAL), timeout(), timeout()])
    assert ai["attempts"][-1]["pages"]["1"]["fields"]["own:decision"] == "failed:timeout"
    assert value(ai, "own:decision") == ("ANN", "validated", 1, "completed") and ai["attempts"][-1]["changed"] == []


def test_before_a_blind_identity_timeout_replaced_the_good_page():
    run = SimpleNamespace(**_scripted_run([discover("X-SD-1"), None]))
    found = old._read_page(run, _blank_page(), sha256="s", number=1, facts=old.PageFacts(1, "", [], []), reason="t")
    merged = old.merge_evidence(_old_good(), {"attempt": 2, "outcome": "complete", "observations": found["_observations"],
                                               "coverage": {"pages": [{"page": 1, "outcome": found["_outcome"]}]}},
                                sha256="s", profile="default", variant="EV1")
    assert found["_outcome"] == "evidence"
    assert [(o["field"], o["state"]) for o in old.current_evidence(merged)["observations"]] == [("identity", "candidate")]
    # the review 08 reader records the same page as partial, and the merge keeps both validated fields
    run = SimpleNamespace(**_scripted_run([discover("X-SD-1"), None]))
    found = er._read_page(run, _blank_page(), sha256="s", number=1, facts=er.PageFacts(1, "", [], []), reason="t")
    assert found["_outcome"] == "partial" and found["_fields"]["own:identity"].startswith("failed")
    merged = er.merge_evidence(_old_good(new=True), {"attempt": 2, "outcome": "complete", "observations": found["_observations"],
                                                      "coverage": {"pages": [{"page": 1, "outcome": found["_outcome"], "fields": found["_fields"]}]}},
                               sha256="s", profile="default", variant="EV1")
    got = er.evidence_for(merged, sha256="s", profile="default", variant="EV1")
    assert [(o["field"], o["state"]) for o in got["observations"]] == [("decision", "validated"), ("identity", "validated")]


def test_a_budget_attempt_without_field_outcomes_never_overwrites_with_a_candidate():
    """The reviewer's third probe: an attempt that recorded no field outcomes (pre-review-08 shape)."""
    candidate = {"attempt": 3, "outcome": "budget", "observations": [dict(page=1, field="identity", value="X-SD-NEW", state="candidate")],
                 "coverage": {"pages": [{"page": 1, "outcome": "evidence"}, {"page": 2, "outcome": "budget: requests"}]}}
    before = old.merge_evidence(_old_good(), candidate, sha256="s", profile="default", variant="EV1")
    assert [o["value"] for o in old.current_evidence(before)["observations"]] == ["X-SD-NEW"]
    after = er.merge_evidence(_old_good(new=True), candidate, sha256="s", profile="default", variant="EV1")
    got = er.evidence_for(after, sha256="s", profile="default", variant="EV1")
    assert [(o["field"], o["value"]) for o in got["observations"]] == [("decision", "ANN"), ("identity", "X-SD-1")]
    assert after["attempts"][-1]["changed"] == []


''' + s[j:]
sub('''def _old_good():
    obs = [dict(page=1, field="identity", value="X-SD-1", state="validated"), dict(page=1, field="decision", value="ANN", state="validated")]
    return old.merge_evidence(None, {"attempt": 1, "outcome": "complete", "observations": obs, "coverage": {"pages": [{"page": 1, "outcome": "evidence"}]}},
                              sha256="s", profile="default", variant="EV1")''',
    '''def _old_good(new=False):
    obs = [dict(page=1, field="identity", value="X-SD-1", state="validated"), dict(page=1, field="decision", value="ANN", state="validated")]
    mod = er if new else old
    return mod.merge_evidence(None, {"attempt": 1, "outcome": "complete", "observations": obs, "coverage": {"pages": [{"page": 1, "outcome": "evidence"}]}},
                              sha256="s", profile="default", variant="EV1")''')
sub('''    stage(doc_row, [discover("X-SD-1", revision="03"), timeout(), timeout()])
    ai = stage(doc_row, [discover("X-SD-1", revision="03"), read("X-SD-1"), read("03")])
    assert value(ai, "own:revision")[:3] == ("03", "validated", 3)''',
    '''    stage(doc_row, [discover("X-SD-1", revision="02"), timeout(), timeout()])
    ai = stage(doc_row, [discover("X-SD-1", revision="02"), read("X-SD-1"), read("02")])
    assert value(ai, "own:revision")[:3] == ("02", "validated", 3)''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
