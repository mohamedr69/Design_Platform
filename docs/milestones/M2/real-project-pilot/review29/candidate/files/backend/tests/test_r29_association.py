"""Review 29 C4 -- the page / target association invariant: the reader side (PA) and evaluator .10. The D26 shape: a
two-page specification whose continuation page repeats the section header and carries a running footer revision. The
same page-2 revision observation must score the same whatever the page-2 identity emission was (.10); .9 reproduces the
alternation. A dependent fact with no target established on its own page is held, keeps its reason and candidates,
survives merge / evidence_for, and earns no recovery credit. No model."""
import pytest

from app.ai import evidence_reader as er
from scripts import m2_eval5 as EV9
from scripts import m2_eval6 as EV10

from ._keyed_provider import KeyedProvider
from ._r29 import configure, discovery, no_submittal_reader, norm_region, text_page, value_read  # noqa: F401
from .test_ai_pilot_r19 import Stage

CTX = {"variant": "EV1", "profile": "default"}


@pytest.fixture(autouse=True)
def _ready(no_submittal_reader):
    yield


def _spec():
    doc = text_page([(0.30, 0.25, "SECTION 11 22 33", 14), (0.30, 0.30, "VIDEO SURVEILLANCE", 12), (0.70, 0.95, "Rev. 00 - Jan 2020", 8), (0.86, 0.95, "Page 1 of 9", 8)])
    # the same running footer on both pages, with its page counter (identical crops would be one cached answer)
    text_page([(0.30, 0.21, "SECTION 11 22 33", 10), (0.10, 0.40, "TABLE OF CONTENTS", 10), (0.70, 0.95, "Rev. 00 - Jan 2020", 8),
               (0.86, 0.95, "Page 2 of 9", 8)], doc=doc)
    return doc


def _answers(doc, *, p2_identity_legible, p2_revision_blind):
    p1, p2 = doc[0], doc[1]
    d1 = discovery(page_kind="cover_sheet", own_identity="11 22 33", own_identity_label="SECTION", own_identity_region=norm_region(p1, "SECTION 11 22 33"),
                   own_revision="00", own_revision_label="Rev.", own_revision_region=norm_region(p1, "Rev. 00 - Jan 2020"))
    d2 = discovery(page_kind="other", own_identity="11 22 33", own_identity_label="SECTION", own_identity_region=norm_region(p2, "SECTION 11 22 33"),
                   own_revision="Rev. 00 - Jan 2020", own_revision_label="Rev.", own_revision_region=norm_region(p2, "Rev. 00 - Jan 2020"))
    return {("discover_page", None, "small"): [d1, d2],
            ("read_identity", "identity", "small"): [value_read("11 22 33", "SECTION"),
                                                     value_read("11 22 33", "SECTION") if p2_identity_legible else value_read("", "", legible=False)],
            ("read_revision", "revision", "small"): [value_read("00", "Rev."), value_read(p2_revision_blind, "Rev.")]}


def _score(ev, row, doc_key):
    exp = [{"_id": 0, "page": 1, "component": "page1", "reference": "11 22 33", "printed_revision": "00", "decision": "n/a", "confidence": "high"}]
    groups = ev.ai_groups(row, CTX, doc_key)
    layer = ev.score_layer(groups, exp, {2}, set(), {1, 2})
    return {(j["page"], j["field"]): (j["state"], j["outcome"]) for j in layer["judged"] if str(j.get("group", "")).find(":own") >= 0 or j["group"].endswith("own")}


def _read(db, tmp_path, monkeypatch, name, *, pa, p2_identity_legible, p2_revision_blind):
    configure(monkeypatch, pa=pa)
    doc = _spec()
    s = Stage(db, tmp_path, doc, name)
    ai = s.run(KeyedProvider(_answers(doc, p2_identity_legible=p2_identity_legible, p2_revision_blind=p2_revision_blind)))
    row = {"sha256": s.sha, "extracted": {"ai_evidence": ai, "profile": "default"}}
    return s, ai, row


def test_d26_shape_evaluator_9_alternates_and_10_does_not(db_session, tmp_path, monkeypatch):
    """Two emissions of page 2, both with the footer revision HELD (discovery 'Rev. 00 - Jan 2020' vs blind '00'): in one
    the page-2 header identity is held (illegible blind read), in the other it is validated. .9 judges the same held
    revision held_on_negative vs held_correct (inherited through the identity's cross-page copy); .10 judges it
    held_on_negative both times. The identity copy itself is credited by both (the .6 rule kept)."""
    _s, _ai, held_id = _read(db_session, tmp_path, monkeypatch, "d26a", pa=False, p2_identity_legible=False, p2_revision_blind="00")
    _s, _ai, valid_id = _read(db_session, tmp_path, monkeypatch, "d26b", pa=False, p2_identity_legible=True, p2_revision_blind="00")
    r9 = (_score(EV9, held_id, "d"), _score(EV9, valid_id, "d"))
    r10 = (_score(EV10, held_id, "d"), _score(EV10, valid_id, "d"))
    assert r9[0][(2, "revision")][0] == "held" and r9[1][(2, "revision")][0] == "held", "the same held revision observation in both"
    assert r9[0][(2, "revision")][1] == "held_on_negative" and r9[1][(2, "revision")][1] == "held_correct", "the .9 alternation reproduces"
    assert r10[0][(2, "revision")][1] == r10[1][(2, "revision")][1] == "held_on_negative", ".10: the same observation, the same outcome"
    assert r9[1][(2, "identity")][1] == r10[1][(2, "identity")][1] == "correct", "a copy of the document identity on a continuation page"


def test_d26_shape_a_targetless_footer_revision_is_held_by_pa_not_a_false_positive(db_session, tmp_path, monkeypatch):
    """The L2 emission: page-2 identity illegible (held), footer revision validated with no target. PA off: .9 and .10
    both judge it a false positive (it is asserted). PA on: the reader holds it (no target established on page 2), with
    its reason and candidates; it survives merge / evidence_for; both evaluators judge it held_on_negative."""
    _s, _ai, off = _read(db_session, tmp_path, monkeypatch, "d26c", pa=False, p2_identity_legible=False, p2_revision_blind="Rev. 00 - Jan 2020")
    assert _score(EV9, off, "d")[(2, "revision")][1] == "fp" and _score(EV10, off, "d")[(2, "revision")][1] == "fp"
    s, ai, on = _read(db_session, tmp_path, monkeypatch, "d26d", pa=True, p2_identity_legible=False, p2_revision_blind="Rev. 00 - Jan 2020")
    got = er.evidence_for(ai, sha256=s.sha, profile="default", variant="EV1")
    rev2 = [o for o in got["envelope"]["observations"] if o.get("page") == 2 and o.get("field") == "revision" and o.get("component") == "own"][0]
    assert rev2["state"] == "candidate" and "target" not in rev2
    assert rev2["association"]["status"] == "held:no_page_target" and rev2["association"]["candidates"] == ["11 22 33"]
    assert rev2["page_binding"] == {"page": 2, "basis": None, "rule": er.ASSOC_VERSION}
    assert _score(EV9, on, "d")[(2, "revision")][1] == "held_on_negative" and _score(EV10, on, "d")[(2, "revision")][1] == "held_on_negative"


def test_pa_binds_a_page_one_revision_only_to_page_one_and_keeps_its_credit(db_session, tmp_path, monkeypatch):
    s, ai, on = _read(db_session, tmp_path, monkeypatch, "d26e", pa=True, p2_identity_legible=True, p2_revision_blind="00")
    got = er.evidence_for(ai, sha256=s.sha, profile="default", variant="EV1")
    rev1 = [o for o in got["envelope"]["observations"] if o.get("page") == 1 and o.get("field") == "revision" and o.get("component") == "own"][0]
    assert rev1["target"] == "11 22 33" and rev1["page_binding"]["basis"] == "own_page_identity" and rev1["state"] == "validated"
    assert _score(EV10, on, "d")[(1, "revision")][1] == "correct"


def test_a_page_with_no_established_identity_holds_its_revision_and_earns_no_credit(db_session, tmp_path, monkeypatch):
    """Page 1's identity read is illegible: PA holds page 1's validated revision (no target on its page). On a labelled
    page with one component .10 judges it held_unassociated: no recovery credit, no false positive."""
    configure(monkeypatch, pa=True)
    doc = _spec()
    s = Stage(db_session, tmp_path, doc, "noid")
    answers = _answers(doc, p2_identity_legible=False, p2_revision_blind="00")
    answers[("read_identity", "identity", "small")] = [value_read("", "", legible=False), value_read("", "", legible=False)]
    ai = s.run(KeyedProvider(answers))
    row = {"sha256": s.sha, "extracted": {"ai_evidence": ai, "profile": "default"}}
    out = _score(EV10, row, "d")
    assert out[(1, "revision")] == ("held", "held_unassociated")


def test_association_of_never_reattaches_a_pa_hold():
    o = {"field": "revision", "component": "own", "page": 2, "value": "00", "state": "candidate",
         "association": {"status": "held:no_page_target", "candidates": ["X"], "rule": er.ASSOC_VERSION}, "page_binding": {"page": 2, "basis": None}}
    assert er.association_of(o, {"own:identity": {"observations": [{"value": "X", "state": "validated"}]}}, None, None)["status"] == "held:no_page_target"
    legacy = {k: v for k, v in o.items() if k != "page_binding"}       # not written by PA: the accepted rules apply as before
    assert er.association_of(legacy, {}, None, None)["status"] != "held:no_page_target"


def test_evaluator_10_changes_nothing_but_cross_page_dependents():
    exp = [{"_id": 0, "page": 1, "component": "page1", "reference": "QX-1", "printed_revision": "A", "decision": "n/a", "confidence": "high"}]
    g_same = {"page": 1, "layer": "ai", "kind": "ai_evidence", "reader": "ai:EV1", "component": "ai:1:own", "facts": [
        {"field": "identity", "value": "QX-1", "state": "validated"}, {"field": "revision", "value": "A", "state": "validated"}], "provenance": {}}
    assert EV9.score_layer([g_same], exp, set(), set(), {1})["judged"] == EV10.score_layer([g_same], exp, set(), set(), {1})["judged"]
    g_cross = {**g_same, "page": 2, "component": "ai:2:own"}
    j9 = {r["field"]: r["outcome"] for r in EV9.score_layer([g_cross], exp, {2}, set(), {1, 2})["judged"]}
    j10 = {r["field"]: r["outcome"] for r in EV10.score_layer([g_cross], exp, {2}, set(), {1, 2})["judged"]}
    assert j9 == {"identity": "correct", "revision": "correct"} and j10 == {"identity": "correct", "revision": "fp"}
