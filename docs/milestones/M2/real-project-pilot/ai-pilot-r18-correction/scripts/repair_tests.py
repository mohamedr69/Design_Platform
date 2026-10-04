"""R18-03: repair the three scripted-provider tests that failed with T on, so answers are selected by task / field / tier
(tests/_keyed_provider.py) instead of being consumed as the next unrelated answer. Every original assertion is kept;
T-specific expectations are stated explicitly; the later stages that never ran under e5a0a94 T now run. Also updates
the e5a0a94 wrong-role test to the successor's declared contract (a wrong-role reading is kept, excluded from
validation, and never completes the field). Applied to C:/t/iso/cand-ai2 (line endings preserved)."""
import pathlib

T = pathlib.Path("C:/t/iso/cand-ai2/backend/tests")


def edit(name, pairs):
    p = T / name
    raw = p.read_bytes()
    crlf = b"\r\n" in raw
    s = raw.decode("utf-8").replace("\r\n", "\n")
    for old, new in pairs:
        assert s.count(old) == 1, (name, old[:100])
        s = s.replace(old, new)
    p.write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))


# --- R7: the escalation disagreement ----------------------------------------------------------------------------------
edit("test_evidence_reader_r7.py", [
    ('''def test_escalation_keeps_the_earlier_disagreement(db_session):
    doc, page = _page()
    provider = RecordingProvider([_discover("X-SD-1"), _read("X-SD-2"), _read("X-SD-2")])
    facts = er.PageFacts(1, page.get_text(), [], [])
    out = er._read_page(_run(db_session, provider), page, sha256="a" * 64, number=1, facts=facts, reason="probe")
    identity = next(o for o in out["_observations"] if o["field"] == "identity" and o["role"] == "own")
    assert [r["source"] for r in identity["readings"]] == ["discovery", "blind_small", "blind_standard"]
    assert identity["state"] == "conflict" and identity["candidates"] == ["X-SD-1", "X-SD-2"]
''', '''def test_escalation_keeps_the_earlier_disagreement(db_session):
    """M2 review 18 (R18-03): answers keyed by task / field / tier. With T the conflict also gets one independent
    context read (it disagrees with the blind reads): the disagreement is kept, never resolved by the extra reading."""
    from ._keyed_provider import KeyedProvider

    doc, page = _page()
    provider = KeyedProvider({("discover", None, "small"): _discover("X-SD-1"), ("read_identity", "identity", "small"): _read("X-SD-2"),
                              ("read_identity", "identity", "standard"): _read("X-SD-2"),
                              ("read_field_context", "identity", "small"): {"value": "X-SD-1", "printed_label": "Drawing No",
                                                                            "role": "own_identity", "region": [0, 0, 1000, 1000], "legible": True}})
    facts = er.PageFacts(1, page.get_text(), [], [])
    out = er._read_page(_run(db_session, provider), page, sha256="a" * 64, number=1, facts=facts, reason="probe")
    identity = next(o for o in out["_observations"] if o["field"] == "identity" and o["role"] == "own")
    t_on = getattr(er, "TARGETED_ENABLED", False)
    assert [r["source"] for r in identity["readings"]] == ["discovery", "blind_small", "blind_standard"] + (["blind_context"] if t_on else [])
    assert identity["state"] == "conflict" and identity["candidates"] == ["X-SD-1", "X-SD-2"]
    asked = [k[0] if not k[0].startswith("discover") else "discover" for k in provider.requests]
    assert asked == ["discover", "read_identity", "read_identity"] + (["read_field_context"] if t_on else [])
    assert [k[2] for k in provider.requests][:3] == ["small", "small", "standard"]
'''),
])

# --- R8: partial reread keeps last-good; the timeout / budget outcomes ---------------------------------------------------
edit("test_m2_review08.py", [
    ('''def test_identity_completes_while_revision_times_out_and_decision_is_refused_by_budget(doc_row, tmp_path):
    ai = stage(doc_row, [discover("X-SD-1", revision="02", decision=APPROVAL), read("X-SD-1"), read("02"), decision_read()])
    assert value(ai, "own:revision")[:2] == ("02", "validated")
    # step 2: a fresh ledger admits discovery, identity and revision (which times out); the decision read is refused
    led = L.Ledger(str(tmp_path / "led.sqlite"), "r8", L.Limits(requests=3))
    inner = RecordingProvider([discover("X-SD-9", revision="03", decision=APPROVAL), read("X-SD-9"), timeout()])
    inner.name = "claude-code"
    ai = stage(doc_row, None, provider=L.LedgerProvider(inner, led))
    assert value(ai, "own:revision") == ("02", "validated", 1, "completed"), "the timed-out read replaces nothing"
    assert value(ai, "own:decision")[:3] == ("ANN", "validated", 1), "the refused read replaces nothing"
    assert value(ai, "own:identity")[0] == "X-SD-9" and value(ai, "own:identity")[2] == 2, "the completed read replaces"
    f = attempt_page(ai)["fields"]
    assert f["own:identity"] == "completed" and f["own:revision"] == "failed:timeout" and f["own:decision"] == "budget"
''', '''def test_identity_completes_while_revision_times_out_and_decision_is_refused_by_budget(doc_row, tmp_path):
    """M2 review 18 (R18-03): answers keyed by task / field / tier, so no request can receive another field's answer.
    With T the optional context read of the unsupported X-SD-9 comes only after every required read (required-first):
    by then the ledger has refused the decision read and the run is exhausted, so it is not attempted."""
    from ._keyed_provider import KeyedProvider

    t_on = getattr(er, "TARGETED_ENABLED", False)
    ctx = lambda v, role: {"value": v, "printed_label": "", "role": role, "region": [0, 0, 1000, 1000], "legible": True}
    first = KeyedProvider({("discover", None, "small"): discover("X-SD-1", revision="02", decision=APPROVAL),
                           ("read_identity", "identity", "small"): read("X-SD-1"), ("read_revision", "revision", "small"): read("02"),
                           ("read_decision", "decision", "small"): decision_read()})
    ai = stage(doc_row, None, provider=first)
    assert value(ai, "own:revision")[:2] == ("02", "validated")
    assert not [k for k in first.requests if k[0] == "read_field_context"], "validated fields get no targeted read"
    # step 2: a fresh ledger admits discovery, identity and revision (which times out); the decision read is refused
    led = L.Ledger(str(tmp_path / "led.sqlite"), "r8", L.Limits(requests=3))
    inner = KeyedProvider({("discover", None, "small"): discover("X-SD-9", revision="03", decision=APPROVAL),
                           ("read_identity", "identity", "small"): read("X-SD-9"), ("read_revision", "revision", "small"): timeout(),
                           ("read_decision", "decision", "small"): decision_read(),
                           ("read_field_context", "identity", "small"): ctx("X-SD-9", "own_identity")})
    inner.name = "claude-code"
    ai = stage(doc_row, None, provider=L.LedgerProvider(inner, led))
    assert value(ai, "own:revision") == ("02", "validated", 1, "completed"), "the timed-out read replaces nothing"
    assert value(ai, "own:decision")[:3] == ("ANN", "validated", 1), "the refused read replaces nothing"
    assert value(ai, "own:identity")[0] == "X-SD-9" and value(ai, "own:identity")[2] == 2, "the completed read replaces"
    f = attempt_page(ai)["fields"]
    assert f["own:identity"] == "completed" and f["own:revision"] == "failed:timeout" and f["own:decision"] == "budget"
    assert [k[0] for k in inner.requests][1:] == ["read_identity", "read_revision"], "the ledger refused the decision before the provider"
    if t_on:
        assert f.get("own:identity:targeted") == "not_attempted:budget", "no optional read after the budget stop"
        assert f.get("own:revision:targeted") == "not_attempted:after_failure", "no targeted read after the timeout"
'''),
])

# --- R10: the revision association of a decision without an AI identity ---------------------------------------------
edit("test_m2_review10.py", [
    ('''def stage(d, answers):
    d.db.query(ResultCache).delete()
    d.db.commit()
    row = d.db.get(ProjectDocument, d.id)
    er.evidence_stage(d.db, d.project, [(row, d.path)], provider=RecordingProvider(answers), variant="EV1", profile="default")''',
     '''def stage(d, answers, provider=None):
    d.db.query(ResultCache).delete()
    d.db.commit()
    row = d.db.get(ProjectDocument, d.id)
    er.evidence_stage(d.db, d.project, [(row, d.path)], provider=provider or RecordingProvider(answers), variant="EV1", profile="default")'''),
    ('''def test_a_known_revision_constraint_holds_a_decision_without_an_ai_identity(det_row):
    ai = stage(det_row, [discover("", revision="02", decision=APPROVAL), read("02"), decision_read()])
    dec = selected(ai, "own:decision")
    assert (dec["value"], dec["state"], dec.get("target"), dec.get("target_revision")) == ("ANN", "validated", "X-SD-1", "02")
    assert "own:identity" not in er.evidence_for(ai, sha256=SHA, profile="default", variant="EV1")["envelope"]["pages"]["1"]["fields"]
    ai = stage(det_row, [discover("", revision="03"), read("03")])          # the same target now reads revision 03
''', '''def _keyed(identity_context=None, **answers):
    """M2 review 18 (R18-03): answers keyed by task / field / tier. `identity_context`: T's context read of the identity
    the deterministic reader names (no AI region): an illegible answer keeps this scenario 'without an AI identity'."""
    from ._keyed_provider import KeyedProvider

    keyed = {("discover", None, "small"): answers["discover"]}
    if "revision" in answers:
        keyed[("read_revision", "revision", "small")] = answers["revision"]
    if "decision" in answers:
        keyed[("read_decision", "decision", "small")] = answers["decision"]
    if getattr(er, "TARGETED_ENABLED", False):
        keyed[("read_field_context", "identity", "small")] = identity_context or {"value": "", "printed_label": "", "role": "other",
                                                                                   "region": [0, 0, 1000, 1000], "legible": False}
    return KeyedProvider(keyed)


def test_a_known_revision_constraint_holds_a_decision_without_an_ai_identity(det_row):
    ai = stage(det_row, None, provider=_keyed(discover=discover("", revision="02", decision=APPROVAL), revision=read("02"), decision=decision_read()))
    dec = selected(ai, "own:decision")
    assert (dec["value"], dec["state"], dec.get("target"), dec.get("target_revision")) == ("ANN", "validated", "X-SD-1", "02")
    assert "own:identity" not in er.evidence_for(ai, sha256=SHA, profile="default", variant="EV1")["envelope"]["pages"]["1"]["fields"]
    ai = stage(det_row, None, provider=_keyed(discover=discover("", revision="03"), revision=read("03")))   # the same target now reads revision 03
'''),
])

# --- e5a0a94's wrong-role test, to the successor's declared contract ---------------------------------------------------
edit("test_ai_pilot_2026_09_30.py", [
    ('''    out = er._read_page(_run(db_session, provider), page, sha256="d" * 64, number=1, facts=er.PageFacts(1, "", [], []), reason="probe")
    ident = _own(out)
    assert ident["state"] == "candidate" and "referenced_identity" in " ".join(ident["reasons"])
''', '''    out = er._read_page(_run(db_session, provider), page, sha256="d" * 64, number=1, facts=er.PageFacts(1, "", [], []), reason="probe")
    ident = _own(out)
    # successor (M2 review 18): the wrong-role reading is kept on the observation, excluded from validation, and
    # never completes the field (e5a0a94 appended it to the readings and downgraded a validation afterwards)
    assert ident["state"] == "candidate" and ident["targeted"] == "unusable:wrong_role" and ident["read"] != "completed"
    kept = [r for r in ident["readings"] if r["source"] == "blind_context"]
    assert kept and "referenced_identity" in kept[0]["excluded"]
'''),
])
print("tests repaired")
