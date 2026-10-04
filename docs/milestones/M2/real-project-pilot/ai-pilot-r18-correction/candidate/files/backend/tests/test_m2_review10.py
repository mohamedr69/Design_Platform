"""M2 review 10 (R10-01): association compatibility of retained dependent facts -- a targetless legacy fact is never
attached to a changed component (A); a missing current identity never bypasses a known revision constraint (B); the
relationship rules of review10/COMPATIBILITY.md. Scripted providers only. Written to run unchanged on the review 09
candidate (689d95e), where the defect cases fail on behaviour: every new key is read with `.get`, and the evaluator's
judgement (the behavioural assertion) comes first."""
from types import SimpleNamespace

import pymupdf
import pytest

from app.ai import evidence_reader as er
from app.ai.provider import RecordingProvider
from app.models import Project, ProjectDocument, ResultCache, RoleEnum

from .conftest import make_user
from .test_m2_review09 import APPROVAL, SHA, decision_read, discover, doc_row, read  # noqa: F401 -- doc_row is a fixture

LABEL = {"doc": "EP-10/form.pdf", "ep": "10", "cohort": "c", "stratum": "s", "extension": ".pdf", "scan_like": False, "confidence": "high"}


def own(field, value, state="validated", **kw):
    return dict(page=1, component="own", role="own", field=field, value=value, state=state, read="completed", **kw)


def attempt(n, observations, fields):
    return {"attempt": n, "outcome": "complete", "observations": observations,
            "coverage": {"pages": [{"page": 1, "outcome": "evidence", "fields": fields}]}}


def merged(*attempts, onto=None):
    ai = onto
    for a in attempts:
        ai = er.merge_evidence(ai, a, sha256=SHA, profile="default", variant="EV1")
    return ai


REVIEW07_LEGACY = {  # a review 07 page envelope: profile and bytes known, no target on its decision or revision
    "envelopes": {"default|EV1": {"profile": "default", "variant": "EV1", "read_sha256": SHA, "pages": {"1": {
        "observations": [own("identity", "X-SD-1"), own("revision", "02"), own("decision", "ANN")],
        "provenance": {"attempt": 1, "read_sha256": SHA, "profile": "default", "variant": "EV1"}}}}},
    "current_key": "default|EV1", "attempts": [{"attempt": 1, "outcome": "complete", "profile": "default", "variant": "EV1"}]}


def review08_revision_without_target():
    """A review 08 reading: identity and revision read together; revisions recorded no target before reader .4."""
    return merged(attempt(1, [own("identity", "X-SD-1"), own("revision", "02")],
                          {"own:identity": "completed", "own:revision": "completed", "own:decision": "absent_by_discovery"}))


# --- persistence and scoring ---------------------------------------------------------------------------------------------


def persist(d, ai):
    row = d.db.get(ProjectDocument, d.id)
    row.extracted = {**row.extracted, "ai_evidence": ai}
    d.db.commit()
    d.db.expire_all()
    return d.db.get(ProjectDocument, d.id).extracted["ai_evidence"]


def stage(d, answers, provider=None):
    d.db.query(ResultCache).delete()
    d.db.commit()
    row = d.db.get(ProjectDocument, d.id)
    er.evidence_stage(d.db, d.project, [(row, d.path)], provider=provider or RecordingProvider(answers), variant="EV1", profile="default")
    d.db.commit()
    d.db.expire_all()
    return d.db.get(ProjectDocument, d.id).extracted["ai_evidence"]


def score(ai, *, reference, revision="00", decision="approved as noted"):
    from scripts import m2_eval5 as ev

    doc = {**LABEL, "labels": {"kind": "shop-drawing cover", "reference": reference, "revision": revision, "decision": decision}}
    rows = {LABEL["doc"]: {"state": "fresh", "sha256": SHA, "extracted": {"records": [], "profile": "default",
                                                                         "coverage": {"outcome": "complete"}, "ai_evidence": ai}}}
    layer = ev.evaluate({"documents": [doc]}, None, rows, ai_context={"variant": "EV1"})["documents"][0]["layers"]["ai"]
    return SimpleNamespace(judged=lambda f: [(j["value"], j["state"], j["outcome"]) for j in layer["judged"] if j["field"] == f],
                           raw=lambda f: [j for j in layer["judged"] if j["field"] == f],
                           recovery=layer["components"][0]["fields"] if layer["components"] else {})


def selected(ai, key):
    got = er.evidence_for(ai, sha256=SHA, profile="default", variant="EV1")
    assert got["state"] == "current", got
    return next(o for o in got["observations"] if er._field_key(o) == key)


def assoc(ai, key):
    return selected(ai, key).get("association") or {}


@pytest.fixture()
def det_row(db_session, tmp_path, monkeypatch):
    """A page whose deterministic reading carries the identity X-SD-1 (a record), so that a decision can take its
    target from it while the AI reads no identity of its own."""
    from app.ai import submittal_reader

    monkeypatch.setattr(submittal_reader, "available", lambda project, provider=None: None)
    pdf = pymupdf.open()
    page = pdf.new_page(width=1684, height=1190)
    page.insert_text((1300, 1100), "Drawing No X-SD-1", fontsize=9)
    page.insert_text((1540, 1100), "REV 02 03", fontsize=9)
    page.insert_text((200, 200), "B = APPROVED AS NOTED", fontsize=9)
    path = tmp_path / "det.pdf"
    pdf.save(path)
    user = make_user(db_session, "r10@test.local", RoleEnum.admin)
    project = Project(ep_number="R10", project_name="r10", source_folder_path=str(tmp_path), created_by_id=user.id)
    db_session.add(project)
    db_session.flush()
    row = ProjectDocument(project_id=project.id, path=str(path), relative_path="det.pdf", filename="det.pdf", role="document", state="fresh",
                          sha256=SHA, extracted={"records": [{"reference": "X-SD-1", "page": 1}], "observations": [], "profile": "default"})
    db_session.add(row)
    db_session.commit()
    return SimpleNamespace(db=db_session, project=project, id=row.id, path=path)


# --- A: a targetless retained fact is never attached to a changed component ---------------------------------------------


def test_a_review08_revision_without_a_target_is_held_when_the_identity_changes(doc_row):
    persist(doc_row, review08_revision_without_target())
    ai = stage(doc_row, [discover("X-SD-9"), read("X-SD-9")])             # identity only: the revision is retained
    s = score(ai, reference="X-SD-9", revision="02")
    assert ("02", "validated", "correct") not in s.judged("revision"), "revision 02 was read for X-SD-1, not X-SD-9"
    assert s.recovery["revision"] != "recovered_clean"
    assert s.judged("revision") == [("02", "held", "held_unassociated")], "held and visible, never dropped"
    rev = selected(ai, "own:revision")
    assert rev.get("target") is None and rev["provenance"]["attempt"] == 1, "no target invented; original provenance kept"
    a = assoc(ai, "own:revision")
    assert a.get("status") == "held:context_changed" and a.get("context_identity") == "X-SD-1"
    assert s.raw("revision")[0].get("association") == "held:context_changed"


def test_a_review07_decision_without_a_target_is_held_when_the_identity_changes(doc_row):
    persist(doc_row, REVIEW07_LEGACY)
    ai = stage(doc_row, [discover("X-SD-9"), read("X-SD-9")])
    s = score(ai, reference="X-SD-9")
    assert ("ANN", "validated", "correct") not in s.judged("decision") and s.recovery["decision"] != "recovered_clean"
    assert s.judged("decision") == [("ANN", "held", "held_unassociated")]
    assert assoc(ai, "own:decision").get("status") == "held:context_changed"


def test_a_targetless_decision_is_held_when_its_components_revision_changes(doc_row):
    persist(doc_row, REVIEW07_LEGACY)
    ai = stage(doc_row, [discover("X-SD-1", revision="03"), read("X-SD-1"), read("03")])   # same identity, revision 03
    s = score(ai, reference="X-SD-1", revision="03")
    assert ("ANN", "validated", "correct") not in s.judged("decision") and s.recovery["decision"] != "recovered_clean"
    assert s.recovery["revision"] == "recovered_clean", "the new revision itself is current evidence"
    assert assoc(ai, "own:decision").get("status") == "held:revision_changed"


def test_a_targetless_fact_read_before_any_identity_is_unresolved_once_one_is_read():
    ai = merged(attempt(1, [own("revision", "02")], {"own:identity": "absent_by_discovery", "own:revision": "completed",
                                                     "own:decision": "absent_by_discovery"}),
                attempt(2, [own("identity", "X-SD-9")], {"own:identity": "completed", "own:revision": "absent_by_discovery",
                                                         "own:decision": "absent_by_discovery"}))
    s = score(ai, reference="X-SD-9", revision="02")
    assert ("02", "validated", "correct") not in s.judged("revision") and s.recovery["revision"] != "recovered_clean"
    assert assoc(ai, "own:revision").get("status") == "held:context_unknown"


# --- B: a missing identity never bypasses a known revision constraint ----------------------------------------------------


def _keyed(identity_context=None, **answers):
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
    assert selected(ai, "own:revision").get("target") == "X-SD-1"
    s = score(ai, reference="X-SD-1", revision="03")
    assert ("ANN", "validated", "correct") not in s.judged("decision") and s.recovery["decision"] != "recovered_clean"
    assert assoc(ai, "own:decision").get("status") == "held:revision_changed"
    assert s.judged("decision") == [("ANN", "held", "held_correct")], "held for its own target X-SD-1, visible"
    assert s.raw("decision")[0].get("target_revision") == "02"


def test_the_reviewers_synthetic_revision_case():
    ai = merged(attempt(1, [own("revision", "02", target="X-SD-1"), own("decision", "ANN", target="X-SD-1", target_revision="02")],
                        {"own:revision": "completed", "own:decision": "completed"}),
                attempt(2, [own("revision", "03", target="X-SD-1")], {"own:revision": "completed"}))
    s = score(ai, reference="X-SD-1", revision="03")
    assert ("ANN", "validated", "correct") not in s.judged("decision") and s.recovery["decision"] != "recovered_clean"
    assert assoc(ai, "own:decision").get("status") == "held:revision_changed"


# --- the other rules of the table ----------------------------------------------------------------------------------------


def test_an_unrelated_revision_never_supplies_an_anchor():
    """A revision of another target (or of an unknown context) is not compared: the decision stays associated by its
    own target, with its own revision constraint untested -- neither held nor confirmed by that revision."""
    base = attempt(1, [own("decision", "ANN", target="X-SD-1", target_revision="02")], {"own:decision": "completed"})
    other = merged(base, attempt(2, [own("revision", "03", target="X-SD-7")], {"own:revision": "completed"}))
    assert assoc(other, "own:decision").get("status") == "by_target"
    assert score(other, reference="X-SD-1").judged("decision") == [("ANN", "validated", "correct")]
    unknown = merged(base, attempt(2, [own("revision", "03")], {"own:revision": "completed"}))
    assert assoc(unknown, "own:decision").get("status") == "by_target"


def test_a_candidate_anchor_never_establishes_an_association():
    explicit = merged(attempt(1, [own("identity", "X-SD-1"), own("decision", "ANN", target="X-SD-1")],
                              {"own:identity": "completed", "own:decision": "completed"}),
                      attempt(2, [own("identity", "X-SD-1", state="candidate")], {"own:identity": "completed"}))
    assert assoc(explicit, "own:decision").get("status") == "by_target", "same literal, not established: associated only by its target"
    legacy = merged(attempt(2, [own("identity", "X-SD-9", state="candidate")], {"own:identity": "completed"}), onto=REVIEW07_LEGACY)
    s = score(legacy, reference="X-SD-9")
    assert ("ANN", "validated", "correct") not in s.judged("decision")
    assert assoc(legacy, "own:decision").get("status") == "held:context_changed"


# --- positive controls ---------------------------------------------------------------------------------------------------


def test_control_a_same_context_retry_keeps_the_legacy_association(doc_row):
    persist(doc_row, REVIEW07_LEGACY)
    ai = stage(doc_row, [discover("X-SD-1"), read("X-SD-1")])               # the same identity, re-read
    s = score(ai, reference="X-SD-1", revision="02")
    assert s.judged("decision") == [("ANN", "validated", "correct")] and s.recovery["decision"] == "recovered_clean"
    assert s.recovery["revision"] == "recovered_clean"
    assert assoc(ai, "own:decision").get("status", "not_recorded") == "not_recorded"


def test_control_unchanged_legacy_evidence_scores_as_before():
    s = score(REVIEW07_LEGACY, reference="X-SD-1", revision="02")
    assert s.judged("decision") == [("ANN", "validated", "correct")] and s.recovery == {"identity": "recovered_clean",
                                                                                       "revision": "recovered_clean", "decision": "recovered_clean"}
    flat = {"version": "evidence-reader-2026-09-29.1", "variant": "EV1", "read_sha256": SHA,
            "observations": [{"page": 1, "field": "identity", "value": "X-SD-1", "state": "validated"},
                             {"page": 1, "field": "decision", "value": "ANN", "state": "validated"}]}
    from scripts import m2_eval5 as ev

    doc = {**LABEL, "labels": {"kind": "shop-drawing cover", "reference": "X-SD-1", "revision": "00", "decision": "approved as noted"}}
    rows = {LABEL["doc"]: {"state": "fresh", "sha256": SHA, "extracted": {"records": [], "profile": "default", "ai_evidence": flat}}}
    layer = ev.evaluate({"documents": [doc]}, None, rows, ai_context={"variant": "EV1", "accept_unknown_profile": True})["documents"][0]["layers"]["ai"]
    assert [(j["value"], j["outcome"]) for j in layer["judged"] if j["field"] == "decision"] == [("ANN", "correct")]


def test_control_a_reread_that_records_its_target_establishes_the_association(doc_row):
    persist(doc_row, review08_revision_without_target())
    stage(doc_row, [discover("X-SD-9"), read("X-SD-9")])
    ai = stage(doc_row, [discover("X-SD-9", revision="02"), read("X-SD-9"), read("02")])   # revision re-read for X-SD-9
    s = score(ai, reference="X-SD-9", revision="02")
    assert s.judged("revision") == [("02", "validated", "correct")] and s.recovery["revision"] == "recovered_clean"
    assert assoc(ai, "own:revision").get("status", "current") == "current"


def test_control_an_explicit_compatible_target_stays_current(doc_row):
    stage(doc_row, [discover("X-SD-1", revision="02", decision=APPROVAL), read("X-SD-1"), read("02"), decision_read()])
    ai = stage(doc_row, [discover("X-SD-1", revision="02"), read("X-SD-1"), read("02")])
    s = score(ai, reference="X-SD-1", revision="02")
    assert s.judged("decision") == [("ANN", "validated", "correct")] and s.recovery["decision"] == "recovered_clean"
    assert assoc(ai, "own:decision").get("status") == "current"
