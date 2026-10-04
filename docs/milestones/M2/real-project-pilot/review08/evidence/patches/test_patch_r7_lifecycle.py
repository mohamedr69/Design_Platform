import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\tests\test_evidence_reader_r7.py")
s = p.read_text(encoding="utf-8")
i = s.index("# --- evidence lifecycle (R7-03)")
NEW = '''# --- evidence lifecycle (R7-03; field-level and context-bound since review 08) --------------------------------------------


def _attempt(n, pages, outcome="complete", policy=er.EVIDENCE_POLICY_VERSION, value="X-SD-1"):
    obs = [{"page": p, "field": "identity", "value": f"{value}@{n}", "state": "validated"} for p, o in pages if o == "evidence"]
    return {"attempt": n, "outcome": outcome, "version": er.READER_VERSION, "policy": policy, "models": ["m"],
            "coverage": {"pages": [{"page": p, "outcome": o, **({"fields": {"own:identity": "completed"}} if o == "evidence" else {})}
                                   for p, o in pages]}, "observations": obs}


def cur(ai, sha="s1", profile="default", variant="EV1"):
    return er.evidence_for(ai, sha256=sha, profile=profile, variant=variant)


def prov(got, page, key="own:identity"):
    return got["envelope"]["pages"][str(page)]["fields"][key]["provenance"]


def test_a_failed_or_budget_stopped_attempt_keeps_last_good_evidence():
    ai = er.merge_evidence(None, _attempt(1, [(1, "evidence"), (2, "evidence")]), sha256="s1", profile="default", variant="EV1")
    before = copy.deepcopy(cur(ai)["envelope"]["pages"])
    failed = {"attempt": 2, "outcome": "failed", "error": "TimeoutError", "coverage": {"pages": []}, "observations": []}
    ai = er.merge_evidence(ai, failed, sha256="s1", profile="default", variant="EV1")
    assert cur(ai)["envelope"]["pages"] == before and ai["attempts"][-1]["outcome"] == "failed"
    budget = _attempt(3, [(1, "budget: calls_per_document"), (2, "evidence")], outcome="budget")
    ai = er.merge_evidence(ai, budget, sha256="s1", profile="default", variant="EV1")
    got = cur(ai)
    assert prov(got, 1)["attempt"] == 1, "page 1 keeps its last-good evidence and its own provenance"
    assert prov(got, 2)["attempt"] == 3
    assert [o["value"] for o in got["observations"]] == ["X-SD-1@1", "X-SD-1@3"]
    assert [a["attempt"] for a in ai["attempts"]] == [1, 2, 3]


def test_changed_bytes_make_retained_evidence_stale_not_current():
    ai = er.merge_evidence(None, _attempt(1, [(1, "evidence")]), sha256="s1", profile="default", variant="EV1")
    failed = {"attempt": 2, "outcome": "failed", "coverage": {"pages": []}, "observations": []}
    ai = er.merge_evidence(ai, failed, sha256="s2", profile="default", variant="EV1")
    assert cur(ai, sha="s2")["state"] == "pending" and cur(ai, sha="s1")["state"] == "stale"
    ai = er.merge_evidence(ai, _attempt(3, [(1, "evidence")]), sha256="s2", profile="default", variant="EV1")
    got = cur(ai, sha="s2")
    assert got["state"] == "current" and [o["value"] for o in got["observations"]] == ["X-SD-1@3"]
    assert ai["superseded"][0]["read_sha256"] == "s1"


def test_profiles_and_variants_are_separate_axes_and_a_policy_change_does_not_restamp():
    ai = er.merge_evidence(None, _attempt(1, [(1, "evidence")], value="D"), sha256="s", profile="default", variant="EV1")
    ai = er.merge_evidence(ai, _attempt(2, [(1, "evidence")], value="P"), sha256="s", profile="promoted", variant="EV1")
    ai = er.merge_evidence(ai, _attempt(3, [(1, "evidence")], value="E2"), sha256="s", profile="default", variant="EV2")
    assert sorted(ai["envelopes"]) == ["default|EV1", "default|EV2", "promoted|EV1"]
    assert cur(ai, "s")["observations"][0]["value"] == "D@1"
    assert cur(ai, "s", "promoted")["observations"][0]["value"] == "P@2"
    # a later policy re-reads page 2 only: page 1 keeps its older policy in its own provenance
    ai = er.merge_evidence(ai, _attempt(4, [(1, "no_trigger"), (2, "evidence")], policy="evidence-policy-next"), sha256="s", profile="default", variant="EV1")
    got = cur(ai, "s")
    assert prov(got, 1)["policy"] == er.EVIDENCE_POLICY_VERSION and prov(got, 2)["policy"] == "evidence-policy-next"
    # a consumer bound to one policy sees only what was read under it
    only_next = er.evidence_for(ai, sha256="s", profile="default", variant="EV1", policies={"evidence-policy-next"})
    assert sorted(only_next["envelope"]["pages"]) == ["2"]


def test_a_legacy_review06_envelope_is_kept_with_its_profile_unknown():
    legacy = {"version": "evidence-reader-2026-09-29.1", "policy": "evidence-policy-2026-09-29.1", "variant": "EV1", "read_sha256": "s",
              "observations": [{"page": 1, "field": "identity", "value": "L-1", "state": "validated"}], "coverage": {"outcome": "complete"}}
    ai = er.merge_evidence(legacy, {"attempt": 2, "outcome": "failed", "coverage": {"pages": []}, "observations": []}, sha256="s",
                           profile="default", variant="EV1")
    env = ai["envelopes"]["unknown|EV1"]
    assert env["profile"] is None and env["observations"][0]["value"] == "L-1"
    assert env["observations"][0]["provenance"]["policy"] == "evidence-policy-2026-09-29.1"
    # never substituted for a known profile; used only when the caller declares the legacy profile
    assert cur(ai, "s")["state"] == "pending"
    assert er.evidence_for(ai, sha256="s", profile="default", variant="EV1", accept_unknown_profile=True)["state"] == "pending"
    assert er.evidence_for(ai, sha256="s", profile=None, variant="EV1")["observations"][0]["value"] == "L-1"


def _stage_row(tmp_path, sha="9" * 64, name="sheet.pdf"):
    from types import SimpleNamespace

    doc, _page_ = _page("Drawing No X-SD-1")
    path = tmp_path / name
    doc.save(path)
    return SimpleNamespace(sha256=sha, extracted={"records": [], "observations": []}, reference=None, status="UR"), path


def test_the_stage_binds_the_actual_profile_into_the_cache_and_the_envelope(db_session, tmp_path, monkeypatch):
    from types import SimpleNamespace

    from app.ai import submittal_reader

    monkeypatch.setattr(submittal_reader, "available", lambda project, provider=None: None)
    project = SimpleNamespace(id=None)
    answers = lambda: [_discover("X-SD-1"), _read("X-SD-1")]
    row, path = _stage_row(tmp_path)
    first = RecordingProvider(answers())
    er.evidence_stage(db_session, project, [(row, path)], provider=first, variant="EV1", profile="promoted")
    db_session.commit()
    assert cur(row.extracted["ai_evidence"], row.sha256, "promoted")["envelope"]["profile"] == "promoted"
    # the other profile does not reuse the promoted answers ...
    other = RecordingProvider(answers())
    counts = er.evidence_stage(db_session, project, [(row, path)], provider=other, variant="EV1", profile="default")
    assert other.calls == first.calls and counts["cache_hits"] == 0
    # ... and the same profile, with the same content under another path, does
    dup, dup_path = _stage_row(tmp_path, name="copy.pdf")
    again = RecordingProvider()
    counts = er.evidence_stage(db_session, project, [(dup, dup_path)], provider=again, variant="EV1", profile="promoted")
    assert again.calls == 0 and counts["cache_hits"] >= 1
    assert sorted(row.extracted["ai_evidence"]["envelopes"]) == ["default|EV1", "promoted|EV1"]
    assert row.extracted["records"] == [] and row.reference is None and row.status == "UR"


def test_resumed_work_keeps_what_was_read_and_reads_the_rest(db_session, tmp_path, monkeypatch):
    from types import SimpleNamespace

    from app.ai import submittal_reader
    from app.core.config import get_settings

    monkeypatch.setattr(submittal_reader, "available", lambda project, provider=None: None)
    doc = pymupdf.open()
    for text in ("Drawing No X-SD-1", "Drawing No X-SD-2"):
        pg = doc.new_page(width=1684, height=1190)
        pg.insert_text((1300, 1100), text, fontsize=9)
    path = tmp_path / "two.pdf"
    doc.save(path)
    row = SimpleNamespace(sha256="7" * 64, extracted={"records": [], "observations": []}, reference=None, status="UR")
    monkeypatch.setattr(get_settings(), "ai_max_calls_per_document", 2)
    er.evidence_stage(db_session, SimpleNamespace(id=None), [(row, path)],
                      provider=RecordingProvider([_discover("X-SD-1"), _read("X-SD-1")]), variant="EV1", profile="default")
    first = cur(row.extracted["ai_evidence"], row.sha256)
    assert sorted(first["envelope"]["pages"]) == ["1"] and row.extracted["ai_evidence"]["attempts"][-1]["outcome"] == "budget"
    monkeypatch.setattr(get_settings(), "ai_max_calls_per_document", 12)
    resumed = RecordingProvider([_discover("X-SD-2"), _read("X-SD-2")])
    er.evidence_stage(db_session, SimpleNamespace(id=None), [(row, path)], provider=resumed, variant="EV1", profile="default")
    got = cur(row.extracted["ai_evidence"], row.sha256)
    assert sorted(got["envelope"]["pages"]) == ["1", "2"] and resumed.calls == 2, "page 1 came back from the cache; page 2 was read"
    assert [a["outcome"] for a in row.extracted["ai_evidence"]["attempts"]] == ["budget", "complete"]
'''
s = s[:i] + NEW
p.write_text(s, encoding="utf-8")

q = pathlib.Path(r"C:\t\iso\ep-platform\backend\tests\test_evidence_reader.py")
t = q.read_text(encoding="utf-8")
old = '''    stored = er.current_evidence(row.extracted["ai_evidence"])
    assert stored["variant"] == "EV1" and stored["read_sha256"] == row.sha256 and stored["profile"] == "default"'''
new = '''    stored = er.evidence_for(row.extracted["ai_evidence"], sha256=row.sha256, profile="default", variant="EV1")["envelope"]
    assert stored["variant"] == "EV1" and stored["read_sha256"] == row.sha256 and stored["profile"] == "default"'''
assert t.count(old) == 1
q.write_text(t.replace(old, new), encoding="utf-8")

r = pathlib.Path(r"C:\t\iso\ep-platform\backend\tests\test_ai_ledger.py")
u = r.read_text(encoding="utf-8")
old = '''    assert sorted(er.current_evidence(row.extracted["ai_evidence"])["pages"]) == ["1"]'''
new = '''    assert sorted(er.evidence_for(row.extracted["ai_evidence"], sha256=row.sha256, profile="default", variant="EV1")["envelope"]["pages"]) == ["1"]'''
assert u.count(old) == 1
r.write_text(u.replace(old, new), encoding="utf-8")

e = pathlib.Path(r"C:\t\iso\ep-platform\backend\tests\test_m2_eval5.py")
v = e.read_text(encoding="utf-8")
# AI rows in these tests are review 06 flat envelopes (no profile / variant): the evaluated context declares that
v = v.replace('''def fields(result, layer="evidence"):''', '''LEGACY_AI = {"profile": None, "variant": None}   # the tests' AI rows are flat review 06 envelopes: context "unknown|unknown"


def evaluate(*a, **k):
    """Evaluator .7 scores AI evidence only for a declared run context; these tests declare the legacy one."""
    return ev5.evaluate(*a, ai_context=k.pop("ai_context", LEGACY_AI), **k)


def fields(result, layer="evidence"):''')
v = v.replace("ev5.evaluate(", "evaluate(").replace("return evaluate(*a, ai_context", "return ev5.evaluate(*a, ai_context")
e.write_text(v, encoding="utf-8")
print("ok")
