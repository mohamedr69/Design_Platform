"""M2 review 09: usable reads (R9-01), retained facts keep their association (R9-02), unknown source bytes are not
exact-file evidence (R9-03), a heading is confirmed only without item evidence (R9-04), and the ledger's documented
amendment behaviour. Scripted providers only -- no model is called. Written to run unchanged on the review 08
candidate (e02a8c1), where the R9 cases fail on behaviour: every new key is read with `.get`, and the behavioural
assertion of each test comes first."""
from types import SimpleNamespace

import pymupdf
import pytest

from app.ai import evidence_reader as er
from app.ai import ledger as L
from app.ai.provider import RecordingProvider
from app.models import Project, ProjectDocument, ResultCache, RoleEnum

from .conftest import make_user
from .test_evidence_reader import _run as _er_run

SHA = "9" * 64
LEGEND = ["A = APPROVED", "B = APPROVED AS NOTED", "C = REVISE AND RESUBMIT"]
APPROVAL = {"options": LEGEND, "marked": "B = APPROVED AS NOTED", "mark": "tick", "actor": "consultant"}
UNMARKED = {"options": LEGEND, "marked": "", "mark": "none", "actor": "consultant"}
RESUBMIT = {"options": LEGEND, "marked": "C = REVISE AND RESUBMIT", "mark": "tick", "actor": "consultant"}


def timeout():
    e = RuntimeError("the CLI did not answer")
    e.kind = "timeout"
    return e


def discover(identity="X-SD-1", revision="", decision=None, other_numbers=()):
    d = decision or {}
    return {"page_kind": "review_form", "own_identity": identity, "own_identity_label": "Drawing No",
            "own_identity_region": [760, 900, 900, 950] if identity else [], "own_revision": revision, "own_revision_label": "REV",
            "own_revision_region": [900, 900, 990, 950] if revision else [], "decision_options_printed": d.get("options", []),
            "decision_marked_option": d.get("marked", ""), "decision_mark_type": d.get("mark", "none"),
            "decision_actor": d.get("actor", "unknown"), "decision_region": [100, 100, 400, 300] if d else [],
            "other_numbers": list(other_numbers), "notes": ""}


def read(value, legible=True):
    return {"label_text": "", "value": value, "legible": legible, "other_values_in_crop": []}


ILLEGIBLE = {"label_text": "", "value": "", "legible": False, "other_values_in_crop": []}


def decision_read(marked="B = APPROVED AS NOTED", mark="tick", legible=True):
    return {"options_printed": LEGEND if legible else [], "marked_option": marked, "mark_type": mark,
            "actor": "consultant" if legible else "unknown", "legible": legible}


# --- a persisted row read through the real stage entry point, reloaded after every step -------------------------------


@pytest.fixture()
def doc_row(db_session, tmp_path, monkeypatch):
    from app.ai import submittal_reader

    monkeypatch.setattr(submittal_reader, "available", lambda project, provider=None: None)
    pdf = pymupdf.open()
    page = pdf.new_page(width=1684, height=1190)
    page.insert_text((1300, 1100), "Drawing No X-SD-1 X-SD-9", fontsize=9)
    page.insert_text((1540, 1100), "REV 02 03", fontsize=9)
    page.insert_text((200, 200), "B = APPROVED AS NOTED", fontsize=9)
    path = tmp_path / "form.pdf"
    pdf.save(path)
    user = make_user(db_session, "r9@test.local", RoleEnum.admin)
    project = Project(ep_number="R9", project_name="r9", source_folder_path=str(tmp_path), created_by_id=user.id)
    db_session.add(project)
    db_session.flush()
    row = ProjectDocument(project_id=project.id, path=str(path), relative_path="form.pdf", filename="form.pdf", role="document",
                          state="fresh", sha256=SHA, extracted={"records": [], "observations": [], "profile": "default"})
    db_session.add(row)
    db_session.commit()
    return SimpleNamespace(db=db_session, project=project, id=row.id, path=path)


def stage(d, answers, *, provider=None):
    d.db.query(ResultCache).delete()            # every step asks again: nothing comes back from the result cache
    d.db.commit()
    row = d.db.get(ProjectDocument, d.id)
    er.evidence_stage(d.db, d.project, [(row, d.path)], provider=provider or RecordingProvider(answers), variant="EV1", profile="default")
    d.db.commit()
    d.db.expire_all()
    return d.db.get(ProjectDocument, d.id).extracted["ai_evidence"]


def current(ai, sha=SHA):
    got = er.evidence_for(ai, sha256=sha, profile="default", variant="EV1")
    assert got["state"] == "current", got
    return got


def field(ai, key):
    return current(ai)["envelope"]["pages"]["1"]["fields"][key]


def fact(ai, key):
    """(value, state, attempt) of a field's current evidence."""
    entry = field(ai, key)
    o = entry["observations"][0]
    return o.get("value"), o.get("state"), entry["provenance"]["attempt"]


def last(ai):
    page = ai["attempts"][-1]["pages"]["1"]
    return page if isinstance(page, dict) else {"outcome": page, "fields": {}}


def ledger_provider(tmp_path, answers, requests):
    led = L.Ledger(str(tmp_path / f"led-{requests}.sqlite"), f"r9-{requests}", L.Limits(requests=requests))
    inner = RecordingProvider(answers)
    inner.name = "claude-code"
    return L.LedgerProvider(inner, led)


# --- R9-01: a returned response is not a usable read -------------------------------------------------------------------


def test_an_illegible_blind_identity_keeps_the_last_good_identity(doc_row):
    ai = stage(doc_row, [discover("X-SD-1", decision=APPROVAL), read("X-SD-1"), decision_read()])
    assert fact(ai, "own:identity") == ("X-SD-1", "validated", 1)
    # the reviewer's case: discovery reads X-SD-9, the blind read of the region returns legible=false
    ai = stage(doc_row, [discover("X-SD-9"), ILLEGIBLE])
    assert fact(ai, "own:identity") == ("X-SD-1", "validated", 1), "a discovery-only candidate never replaces a good field"
    assert field(ai, "own:identity")["history"] == []
    assert fact(ai, "own:decision")[:2] == ("ANN", "validated")
    page = last(ai)
    assert page["outcome"] == "partial" and page["fields"]["own:identity"] == "unusable:illegible"
    assert page.get("requests", {}).get("own:identity") == "ok", "the request completed; the field is not usable"
    assert [(u["field"], u["value"], u["state"]) for u in ai["attempts"][-1].get("unapplied", [])] == [("identity", "X-SD-9", "candidate")]
    # a later legible read replaces it under the existing contract, keeping the old value as history
    ai = stage(doc_row, [discover("X-SD-9"), read("X-SD-9")])
    assert fact(ai, "own:identity") == ("X-SD-9", "validated", 3)
    assert [h["observations"][0]["value"] for h in field(ai, "own:identity")["history"]] == ["X-SD-1"]


def test_an_illegible_blind_revision_keeps_the_last_good_revision(doc_row):
    stage(doc_row, [discover("X-SD-1", revision="02"), read("X-SD-1"), read("02")])
    ai = stage(doc_row, [discover("X-SD-1", revision="03"), read("X-SD-1"), ILLEGIBLE])
    assert fact(ai, "own:revision") == ("02", "validated", 1)
    assert last(ai)["fields"]["own:revision"] == "unusable:illegible" and last(ai)["fields"]["own:identity"] == "completed"
    # a legible blind reading with no value is not a usable read either (there is no verified absence of a revision)
    ai = stage(doc_row, [discover("X-SD-1", revision="03"), read("X-SD-1"), read("", legible=True)])
    assert fact(ai, "own:revision") == ("02", "validated", 1)
    assert last(ai)["fields"]["own:revision"] == "unusable:empty"


def test_an_unmarked_discovery_and_an_illegible_blind_read_never_erase_a_decision(doc_row):
    stage(doc_row, [discover("X-SD-1", decision=APPROVAL), read("X-SD-1"), decision_read()])
    ai = stage(doc_row, [discover("X-SD-1", decision=UNMARKED), read("X-SD-1"), decision_read("", "unclear", legible=False)])
    assert fact(ai, "own:decision") == ("ANN", "validated", 1), "no legible blind confirmation of absence"
    assert last(ai)["fields"]["own:decision"] == "unusable:illegible"
    assert field(ai, "own:decision")["history"] == []
    assert [u["field"] for u in ai["attempts"][-1].get("unapplied", [])] == ["decision"]


def test_a_marked_discovery_and_an_illegible_blind_read_never_replace_a_decision(doc_row):
    stage(doc_row, [discover("X-SD-1", decision=APPROVAL), read("X-SD-1"), decision_read()])
    ai = stage(doc_row, [discover("X-SD-1", decision=RESUBMIT), read("X-SD-1"), decision_read("", "unclear", legible=False)])
    assert fact(ai, "own:decision") == ("ANN", "validated", 1)
    assert last(ai)["fields"]["own:decision"] == "unusable:illegible"


def test_a_first_read_with_an_illegible_blind_answer_is_incomplete_never_verified(doc_row):
    ai = stage(doc_row, [discover("X-SD-1", decision=RESUBMIT), read("X-SD-1"), decision_read("", "unclear", legible=False)])
    entry = field(ai, "own:decision")
    assert entry["status"] == "incomplete" and entry["observations"][0]["state"] != "validated"
    assert "own:decision" in " ".join(current(ai)["incomplete"])


def test_a_legible_unmarked_block_read_both_ways_supersedes(doc_row):
    """Control: a genuinely completed, legible negative still supersedes (the old decision goes to history)."""
    stage(doc_row, [discover("X-SD-1", decision=APPROVAL), read("X-SD-1"), decision_read()])
    ai = stage(doc_row, [discover("X-SD-1", decision=UNMARKED), read("X-SD-1"), decision_read("", "none")])
    assert fact(ai, "own:decision") == (None, "no_decision_marked", 2)
    assert field(ai, "own:decision")["history"][-1]["observations"][0]["value"] == "ANN"
    assert last(ai)["fields"]["own:decision"] == "completed"


def test_completed_conflicting_readings_stay_an_explicit_conflict(doc_row):
    """Control: a legible blind reading that disagrees with discovery is completed evidence -- a conflict, not hidden."""
    stage(doc_row, [discover("X-SD-1"), read("X-SD-1")])
    ai = stage(doc_row, [discover("X-SD-9"), read("X-SD-1")])
    value, state, attempt = fact(ai, "own:identity")
    assert state == "conflict" and attempt == 2


def test_timeout_and_budget_controls(doc_row, tmp_path):
    stage(doc_row, [discover("X-SD-1", decision=APPROVAL), read("X-SD-1"), decision_read()])
    ai = stage(doc_row, [discover("X-SD-9", decision=UNMARKED), timeout(), timeout()])
    assert fact(ai, "own:identity") == ("X-SD-1", "validated", 1) and fact(ai, "own:decision") == ("ANN", "validated", 1)
    assert last(ai)["fields"]["own:identity"] == "failed:timeout"
    ai = stage(doc_row, None, provider=ledger_provider(tmp_path, [discover("X-SD-9", decision=UNMARKED)], requests=1))
    assert fact(ai, "own:identity") == ("X-SD-1", "validated", 1) and fact(ai, "own:decision") == ("ANN", "validated", 1)
    assert last(ai)["fields"]["own:identity"] == "budget"


# --- R9-02: a retained fact keeps its association ------------------------------------------------------------------------


LABEL = {"doc": "EP-9/form.pdf", "ep": "9", "cohort": "c", "stratum": "s", "extension": ".pdf", "scan_like": False, "confidence": "high"}


def score(ai, *, reference, decision, revision="00"):
    """The AI layer's judgement of the labelled page (one component) against this evidence."""
    from scripts import m2_eval5 as ev

    doc = {**LABEL, "labels": {"kind": "shop-drawing cover", "reference": reference, "revision": revision, "decision": decision}}
    rows = {LABEL["doc"]: {"state": "fresh", "sha256": SHA, "extracted": {"records": [], "profile": "default", "coverage": {"outcome": "complete"},
                                                                         "ai_evidence": ai}}}
    result = ev.evaluate({"documents": [doc]}, None, rows, ai_context={"variant": "EV1"})
    layer = result["documents"][0]["layers"]["ai"]
    return layer, result["totals"]


def decisions(layer):
    return [(j["value"], j["state"], j["outcome"]) for j in layer["judged"] if j["field"] == "decision"]


def association(ai, key="own:decision"):
    o = next(o for o in current(ai)["observations"] if er._field_key(o) == key)
    return o.get("association") or {}


def test_a_changed_identity_does_not_inherit_the_retained_decision(doc_row):
    stage(doc_row, [discover("X-SD-1", decision=APPROVAL), read("X-SD-1"), decision_read()])
    ai = stage(doc_row, [discover("X-SD-9"), read("X-SD-9")])          # identity completed; no decision block seen
    assert fact(ai, "own:identity") == ("X-SD-9", "validated", 2)
    layer, _ = score(ai, reference="X-SD-9", decision="approved as noted")
    # the retained ANN was validated for X-SD-1: never accepted, never recovered for X-SD-9
    assert ("ANN", "validated", "correct") not in decisions(layer)
    assert layer["components"][0]["fields"]["decision"] != "recovered_clean"
    assert fact(ai, "own:decision") == ("ANN", "validated", 1), "the fact itself is kept, with its original target"
    assert field(ai, "own:decision")["observations"][0]["target"] == "X-SD-1"
    assert association(ai).get("status") == "held:target_changed" and association(ai).get("target") == "X-SD-1"
    assert decisions(layer) == [("ANN", "held", "held_unassociated")], "held and visible, not dropped"
    assert next(j for j in layer["judged"] if j["field"] == "decision").get("target") == "X-SD-1"


def test_a_same_identity_retry_keeps_its_decision_associated(doc_row):
    stage(doc_row, [discover("X-SD-1", decision=APPROVAL), read("X-SD-1"), decision_read()])
    ai = stage(doc_row, [discover("X-SD-1"), read("X-SD-1")])
    layer, _ = score(ai, reference="X-SD-1", decision="approved as noted")
    assert decisions(layer) == [("ANN", "validated", "correct")] and layer["components"][0]["fields"]["decision"] == "recovered_clean"
    assert association(ai).get("status", "current") == "current"   # a control: e02a8c1 records no association and passes


def test_a_decision_with_no_usable_current_identity_associates_only_by_its_target():
    """No AI identity on the page (the decision's target came from the deterministic reading): it is associated by its
    recorded target, never by the page's other component."""
    obs = [dict(page=1, component="own", field="decision", value="ANN", target="X-SD-1", state="validated")]
    ai = er.merge_evidence(None, {"attempt": 1, "outcome": "complete", "observations": obs, "coverage": {"pages": [
        {"page": 1, "outcome": "evidence", "fields": {"own:identity": "absent_by_discovery", "own:decision": "completed"}}]}},
        sha256=SHA, profile="default", variant="EV1")
    other, _ = score(ai, reference="X-SD-7", decision="approved as noted")
    assert ("ANN", "validated", "correct") not in decisions(other) and other["components"][0]["fields"]["decision"] != "recovered_clean"
    assert association(ai).get("status") == "by_target"
    same, _ = score(ai, reference="X-SD-1", decision="approved as noted")
    assert decisions(same) == [("ANN", "validated", "correct")], "its own target still associates"


def test_a_changed_revision_holds_a_decision_made_for_the_earlier_revision(doc_row):
    stage(doc_row, [discover("X-SD-1", revision="02", decision=APPROVAL), read("X-SD-1"), read("02"), decision_read()])
    ai = stage(doc_row, [discover("X-SD-1", revision="03"), read("X-SD-1"), read("03")])
    assert fact(ai, "own:revision") == ("03", "validated", 2)
    layer, _ = score(ai, reference="X-SD-1", revision="03", decision="approved as noted")
    assert ("ANN", "validated", "correct") not in decisions(layer)
    assert field(ai, "own:decision")["observations"][0].get("target_revision") == "02"
    assert association(ai).get("status") == "held:revision_changed"


def test_multiple_components_on_a_page_keep_their_own_associations(doc_row):
    stage(doc_row, [discover("X-SD-1", decision=APPROVAL, other_numbers=[{"role": "reviewed_drawing", "literal": "L-100"}]),
                    read("X-SD-1"), decision_read()])
    # the own identity changes to X-SD-9; the page now lists X-SD-1 as a referenced number: the ANN stays X-SD-1's
    ai = stage(doc_row, [discover("X-SD-9", other_numbers=[{"role": "reviewed_drawing", "literal": "X-SD-1"}]), read("X-SD-9")])
    layer, _ = score(ai, reference="X-SD-9", decision="approved as noted")
    assert ("ANN", "validated", "correct") not in decisions(layer)
    assert association(ai).get("status") == "held:target_changed"
    refs = [(j["value"], j["state"]) for j in layer["judged"] if j["field"] == "referenced_identity"]
    assert refs == [("X-SD-1", "observed_reference")], "the reference stays a reference"


def test_a_legacy_fact_without_a_recorded_target_is_never_given_one():
    legacy = {"version": "evidence-reader-2026-09-29.1", "policy": "evidence-policy-2026-09-29.1", "variant": "EV1", "read_sha256": SHA,
              "observations": [{"page": 1, "field": "identity", "value": "X-SD-1", "state": "validated"},
                               {"page": 1, "field": "decision", "value": "ANN", "state": "validated"}]}
    got = er.evidence_for(legacy, sha256=SHA, profile="default", variant="EV1", accept_unknown_profile=True)
    dec = next(o for o in got["observations"] if o["field"] == "decision")
    assert "target" not in dec and (dec.get("association") or {}).get("status", "not_recorded") == "not_recorded"
    from scripts import m2_eval5 as ev

    doc = {**LABEL, "labels": {"kind": "shop-drawing cover", "reference": "X-SD-1", "revision": "00", "decision": "approved as noted"}}
    rows = {LABEL["doc"]: {"state": "fresh", "sha256": SHA, "extracted": {"records": [], "profile": "default", "ai_evidence": legacy}}}
    layer = ev.evaluate({"documents": [doc]}, None, rows, ai_context={"variant": "EV1", "accept_unknown_profile": True})["documents"][0]["layers"]["ai"]
    assert decisions(layer) == [("ANN", "validated", "correct")], "scored as it always was: grouped with its page's identity"
    assert next(j for j in layer["judged"] if j["field"] == "decision").get("target") is None



def test_target_and_association_survive_on_unscored_pages_too():
    from scripts import m2_eval5 as ev

    g = {"page": 7, "layer": "ai", "kind": "ai_evidence", "reader": "ai:EV1", "component": "ai:7:own@X-SD-1", "association_identity": "X-SD-1",
         "facts": [{"field": "decision", "value": "ANN", "state": "held", "target": "X-SD-1", "association": "held:target_changed"}]}
    judged = ev.score_layer([g], [], set(), set(), {1})["judged"]
    assert [(j["outcome"], j.get("target"), j.get("association")) for j in judged] == [("unscored_page", "X-SD-1", "held:target_changed")]

# --- R9-03: unknown bytes are not exact-file evidence --------------------------------------------------------------------


def _good(sha=SHA):
    obs = [dict(page=1, component="own", field="identity", value="X-SD-1", state="validated")]
    return er.merge_evidence(None, {"attempt": 1, "outcome": "complete", "observations": obs,
                                    "coverage": {"pages": [{"page": 1, "outcome": "evidence", "fields": {"own:identity": "completed"}}]}},
                             sha256=sha, profile="default", variant="EV1")


def _unknown():
    ai = _good()
    env = ai["envelopes"]["default|EV1"]
    env["read_sha256"] = None
    for f in env["pages"]["1"]["fields"].values():
        f["provenance"]["read_sha256"] = None
    return ai


def test_unknown_envelope_and_field_hashes_are_not_current():
    got = er.evidence_for(_unknown(), sha256=SHA, profile="default", variant="EV1")
    assert got["state"] != "current" and not got.get("observations")
    assert got["state"] == "unknown_source"


def test_legacy_flat_evidence_without_a_hash_is_not_current_even_with_the_legacy_profile_declared():
    flat = {"version": "evidence-reader-2026-09-29.1", "policy": "evidence-policy-2026-09-29.1", "variant": "EV1",
            "observations": [{"page": 1, "field": "identity", "value": "L-1", "state": "validated"}]}
    got = er.evidence_for(flat, sha256=SHA, profile="default", variant="EV1", accept_unknown_profile=True)
    assert got["state"] == "unknown_source" and not got.get("observations")
    with_hash = {**flat, "read_sha256": SHA}
    assert er.evidence_for(with_hash, sha256=SHA, profile="default", variant="EV1", accept_unknown_profile=True)["state"] == "current"


def test_known_mismatch_is_stale_and_an_exact_match_is_current():
    assert er.evidence_for(_good(), sha256="0" * 64, profile="default", variant="EV1")["state"] == "stale"
    assert er.evidence_for(_good(), sha256=SHA, profile="default", variant="EV1")["state"] == "current"


def test_a_request_without_a_source_hash_gets_no_exact_file_evidence():
    got = er.evidence_for(_good(), sha256=None, profile="default", variant="EV1")
    assert got["state"] != "current" and got["state"] == "source_required"


def test_mixed_and_partial_rereads_never_relabel_retained_fields():
    ai = _unknown()
    rev = [dict(page=1, component="own", field="revision", value="02", state="validated")]
    ai = er.merge_evidence(ai, {"attempt": 2, "outcome": "partial", "observations": rev, "coverage": {"pages": [
        {"page": 1, "outcome": "partial", "fields": {"own:identity": "failed:timeout", "own:revision": "completed"}}]}},
        sha256=SHA, profile="default", variant="EV1")
    fields = ai["envelopes"]["default|EV1"]["pages"]["1"]["fields"]
    assert fields["own:identity"]["provenance"]["read_sha256"] is None, "the retained field keeps its (unknown) source"
    assert fields["own:revision"]["provenance"]["read_sha256"] == SHA
    got = er.evidence_for(ai, sha256=SHA, profile="default", variant="EV1")
    assert [o["field"] for o in got.get("observations") or []] == ["revision"], "only the field read from these bytes is current"
    assert got["state"] == "current" and got.get("withheld") == {"1:own:identity": "unknown_source"}


def test_an_explicit_historical_binding_is_a_separate_manifest_backed_mode():
    ai = _unknown()
    assert er.evidence_for(ai, sha256=SHA, profile="default", variant="EV1")["state"] == "unknown_source"
    bound = er.evidence_for(ai, sha256=SHA, profile="default", variant="EV1", historical_source={"manifest": "RUN-X.json", "sha256": SHA})
    assert bound["state"] == "current" and bound["mode"] == "historical" and bound["observations"][0]["source_binding"] == "historical:RUN-X.json"
    other = er.evidence_for(ai, sha256=SHA, profile="default", variant="EV1", historical_source={"manifest": "RUN-X.json", "sha256": "0" * 64})
    assert other["state"] == "unknown_source", "a manifest binding other bytes establishes nothing"
    assert er.evidence_for(_good("1" * 64), sha256=SHA, profile="default", variant="EV1",
                           historical_source={"manifest": "RUN-X.json", "sha256": SHA})["state"] == "stale", "never over a known mismatch"


def test_the_evaluator_scores_unknown_bytes_only_under_a_declared_historical_manifest():
    from scripts import m2_eval5 as ev

    doc = {**LABEL, "labels": {"kind": "shop-drawing cover", "reference": "X-SD-1", "revision": "00", "decision": "rejected"}}
    rows = {LABEL["doc"]: {"state": "fresh", "sha256": SHA, "extracted": {"records": [], "profile": "default", "ai_evidence": _unknown()}}}
    plain = ev.evaluate({"documents": [doc]}, None, rows, ai_context={"variant": "EV1"})
    assert plain["totals"]["ai_evidence_states"] == {"unknown_source": 1}
    assert not [j for j in plain["documents"][0]["layers"]["ai"]["judged"] if j["field"] == "identity"]
    ctx = {"variant": "EV1", "historical_source": {"manifest": "RUN-X.json", "sha256_by_doc": {LABEL["doc"]: SHA}}}
    bound = ev.evaluate({"documents": [doc]}, None, rows, ai_context=ctx)
    assert [(j["value"], j["outcome"]) for j in bound["documents"][0]["layers"]["ai"]["judged"] if j["field"] == "identity"] == [("X-SD-1", "correct")]


# --- R9-04: a heading is confirmed only without item evidence ----------------------------------------------------------


@pytest.mark.parametrize("row, blind, state", [
    ({"part_number": None, "quantity": None, "description": "( 2 ) Dual Input Module"}, {"description": "Dual Input Module"}, "conflict"),
    ({"part_number": None, "quantity": None, "description": "Dual Input Module"}, {"description": "( 2 ) Dual Input Module"}, "conflict"),
    ({"part_number": None, "quantity": 0}, {}, "conflict"),
    ({"part_number": None, "quantity": "0"}, {}, "conflict"),
    ({"part_number": None, "quantity": None}, {"quantity": 0}, "conflict"),
    ({"part_number": "P-1", "quantity": None}, {}, "conflict"),
    ({"part_number": None, "quantity": ""}, {"quantity": "  "}, "not_an_item"),
    ({"part_number": None, "quantity": None, "description": "FIRE ALARM SYSTEM"}, {"description": "FIRE ALARM SYSTEM"}, "not_an_item"),
    ({"part_number": None, "quantity": "0"}, {"legible": False}, "unverified"),
])
def test_a_heading_answer_against_item_evidence(row, blind, state):
    got = er.validate_boq_row(row, {"row_is_heading": True, "legible": True, **blind})
    assert got["state"] == state
    if state == "conflict":
        assert got.get("row_type") == "disputed"


def test_numeric_zero_is_a_present_quantity_in_the_item_comparison_too():
    got = er.validate_boq_row({"part_number": "P-1", "quantity": "0"}, {"part_number": "P-1", "quantity": 0, "legible": True})
    assert got["state"] == "validated" and got["quantity"] == "verified"


def _sheet(lines):
    """A sheet printing each line's description at its own row, so that every row crop is a distinct image (identical
    crops would come back from the result cache as the first row's answer)."""
    doc = pymupdf.open()
    page = doc.new_page(width=842, height=595)
    for line in lines:
        page.insert_text((40, line["y_px"] * 72 / 300 + 3), f"{line['y_px']} {line.get('description') or ''}", fontsize=8)
    return doc


def _line(n, **kw):
    return {"page": 1, "y_px": 300 + 200 * n, "table_span": [100, 3000], "quantity_span": [100, 300], **kw}


def test_the_normal_verifier_carries_the_readers_description_and_keeps_every_line(db_session):
    lines = [_line(0, catalog_no=None, quantity=None, description="( 2 ) Dual Input Module"),
             _line(1, catalog_no=None, quantity=0, description="Spare"),
             _line(2, catalog_no=None, quantity="0", description="Spare"),
             _line(3, catalog_no="P-1", quantity=None, description="Relay"),
             _line(4, catalog_no=None, quantity=None, description="FIRE ALARM SYSTEM"),
             _line(5, catalog_no=None, quantity="", description="( 4 ) Sounder")]
    heading = {"part_number": "", "quantity": "", "description": "Dual Input Module", "legible": True, "row_is_heading": True}
    answers = [heading, dict(heading, description="Spare"), dict(heading, description="Spare"), dict(heading, description="Relay"),
               dict(heading, description="FIRE ALARM SYSTEM"), dict(heading, description="Sounder", legible=False)]
    results = er.verify_boq_rows(_er_run(db_session, RecordingProvider(answers), "EV2"), _sheet(lines), sha256="5" * 64,
                                 extraction={"lines": [dict(l) for l in lines], "issues": []}, render_dpi=300)
    assert [r["state"] for r in results] == ["conflict", "conflict", "conflict", "conflict", "not_an_item", "unverified"]
    assert len(results) == len(lines), "every line is reported; none removed"
    assert [r["row"]["quantity"] for r in results] == [None, 0, "0", None, None, ""], "the reader's literals are kept"
    assert [r["row"]["description"] for r in results] == [l["description"] for l in lines]
    assert "( 2 )" in " ".join(results[0]["reasons"])


# --- the ledger's documented amendment behaviour (R8-03, accepted) -------------------------------------------------------


def test_an_open_handle_reads_the_amended_policy_and_a_new_handle_with_the_old_limits_is_refused(tmp_path):
    path = str(tmp_path / "ledger.sqlite")
    open_handle = L.Ledger(path, "amend", L.Limits(requests=1))
    open_handle.settle(open_handle.reserve("t", 1, 1), input_tokens=1, output_tokens=1)
    L.Ledger(path, "amend").amend_limits(L.Limits(requests=2), authorized_by="owner (test)", reason="declared addendum")
    open_handle.reserve("t", 1, 1)            # the already-open handle reserves under the saved, amended policy
    with pytest.raises(L.LedgerConfigMismatch):
        L.Ledger(path, "amend", L.Limits(requests=1))
    assert "already open" in L.__doc__ and "newly opened" in L.__doc__
