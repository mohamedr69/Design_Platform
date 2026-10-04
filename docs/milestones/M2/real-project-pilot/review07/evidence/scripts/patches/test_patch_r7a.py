import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\tests\test_evidence_reader.py")
s = p.read_text(encoding="utf-8")


def between(start, end, new):
    global s
    i, j = s.index(start), s.index(end)
    s = s[:i] + new + s[j:]


between("def test_model_agreement_without_source_support_is_only_a_candidate():", "def test_decision_policy():", '''def test_model_agreement_without_source_support_is_only_a_candidate():
    texts = [("text", "nothing printed here"), ("ocr", "")]
    readings = [{"source": "discovery", "value": "AB-77-001"}, {"source": "blind_small", "value": "AB-77-001", "legible": True}]
    assert er.validate_value("identity", readings, texts, None)["state"] == "candidate"
    assert er.validate_value("identity", readings, [("text", "Drawing No AB-77-001")], None)["state"] == "validated"
    assert er.validate_value("identity", readings[:1], [("text", "AB-77-001")], None)["state"] == "candidate"
    disagree = readings + [{"source": "blind_standard", "value": "AB-77-00I", "legible": True}]
    assert er.validate_value("identity", disagree, [("text", "AB-77-001")], None)["state"] == "conflict"
    assert er.validate_value("identity", [{"source": "blind_small", "value": "", "legible": False}], texts, None)["state"] == "unreadable"
    # Policy .2 (review 07): a one-character near match is a candidate, never support -- in either direction.
    near = er.validate_value("identity", [{"source": "blind_small", "value": "CDS-DOC-01943", "legible": True}],
                             [("ocr", "Reference ICDS-DOC-01943")], None)
    assert near["support"] is None and near["state"] == "candidate"
    assert any("near match" in r or "not in the read region" in r for r in near["reasons"])


''')
between("def test_decision_policy():", "def test_the_same_question_is_not_asked_twice_and_variants_do_not_share_answers(db_session):", '''def test_decision_policy():
    options = ["A = NO OBJECTION", "B = NO OBJECTION AS NOTED", "C = REVISE AND RESUBMIT"]
    marked = {"options_printed": options, "marked_option": "B = NO OBJECTION AS NOTED", "mark_type": "tick", "actor": "consultant", "legible": True}
    got = er.validate_decision([{"source": "discovery", **marked}, {"source": "blind_small", **marked}], target="X-SD-1")
    assert (got["state"], got["decision"], got["reasons"]) == ("validated", "ANN", [])
    assert er.validate_decision([{"source": "discovery", **marked}], target="X-SD-1")["state"] == "candidate"
    contractor = dict(marked, actor="contractor")
    assert er.validate_decision([{"source": "discovery", **contractor}, {"source": "blind_small", **contractor}], target="X-SD-1")["state"] == "candidate"
    blank = dict(marked, marked_option="", mark_type="none")
    assert er.validate_decision([{"source": "blind_small", **blank}])["state"] == "no_decision_marked"
    other = dict(marked, marked_option="C = REVISE AND RESUBMIT")
    assert er.validate_decision([{"source": "discovery", **marked}, {"source": "blind_small", **other}], target="X-SD-1")["state"] == "conflict"
    # no target component: not validated
    assert er.validate_decision([{"source": "discovery", **marked}, {"source": "blind_small", **marked}])["state"] == "candidate"


''')
s = s.replace('''    assert er.evidence_stage(db_session, project, [(row, path)], provider=RecordingProvider()) == \\
        {"variant": "off", "documents": 0, "calls": 0, "cache_hits": 0, "failed": 0, "budget_stopped": 0}''',
              '''    off = er.evidence_stage(db_session, project, [(row, path)], provider=RecordingProvider())
    assert off["variant"] == "off" and off["documents"] == off["calls"] == 0''')
s = s.replace('''    stored = row.extracted["ai_evidence"]
    assert stored["variant"] == "EV1" and stored["read_sha256"] == row.sha256 and stored["calls"]''',
              '''    stored = er.current_evidence(row.extracted["ai_evidence"])
    assert stored["variant"] == "EV1" and stored["read_sha256"] == row.sha256 and stored["profile"] == "default"
    assert row.extracted["ai_evidence"]["attempts"][-1]["calls"]''')
p.write_text(s, encoding="utf-8")
print("ok")
