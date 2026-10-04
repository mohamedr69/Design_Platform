"""M2 review 07 (R7-02, R7-03): the evidence reader's validation policy .2 and its evidence lifecycle.

The reviewer's probes run against both implementations: `tests/fixtures/evidence_reader_r6.py` is the review 06
reader, pinned unchanged as history, and each probe shows it certifying what policy .2 refuses."""
import copy
import importlib.util
import pathlib
import sys

import pymupdf
import pytest

from app.ai import evidence_reader as er
from app.ai.budget import open_budget
from app.ai.provider import RecordingProvider

_spec = importlib.util.spec_from_file_location("evidence_reader_r6", pathlib.Path(__file__).parent / "fixtures" / "evidence_reader_r6.py")
old = importlib.util.module_from_spec(_spec)
sys.modules["evidence_reader_r6"] = old
_spec.loader.exec_module(old)


def blind(value, source="blind_small"):
    return {"source": source, "value": value, "legible": True}


# --- the reviewer's validation probes: validated by .1, refused by .2 --------------------------------------------------


@pytest.mark.parametrize("field, value, texts", [
    ("identity", "ABC-123", [("text", "Drawing No ABC-1234")]),        # a prefix of a longer identity
    ("identity", "AB-SD-1235", [("ocr", "AB-SD-1234")]),               # one OCR character apart
    ("revision", "12", [("text", "Date 12/09/2026")]),                 # a revision found only inside a date
])
def test_support_is_literal_and_bounded(field, value, texts):
    assert old.validate_value(field, [blind(value)], texts, None)["state"] == "validated"
    got = er.validate_value(field, [blind(value)], texts, None)
    assert got["state"] == "candidate" and got["support"] is None


def test_a_decision_needs_corroboration_printed_options_and_one_evidenced_actor():
    marked = dict(source="blind_small", legible=True, marked_option="Approved", mark_type="tick", actor="consultant", options_printed=[])
    assert old.validate_decision([marked])["state"] == "validated"
    assert er.validate_decision([marked], target="X-SD-1")["state"] == "candidate"
    disagree = [dict(marked, source="discovery", actor="consultant", options_printed=["Approved"]),
                dict(marked, actor="contractor", options_printed=["Approved"])]
    assert old.validate_decision(disagree)["state"] == "validated"
    got = er.validate_decision(disagree, target="X-SD-1")
    assert got["state"] == "candidate" and any("disagree on who marked" in r for r in got["reasons"])


def test_quantity_keeps_its_decimal_point():
    row, reading = {"part_number": "P-1", "quantity": "1.5"}, {"part_number": "P-1", "quantity": "15", "legible": True}
    assert old.validate_boq_row(row, reading)["state"] == "validated"
    got = er.validate_boq_row(row, reading)
    assert got["state"] == "conflict" and got["quantity"] == "conflict"


def _page(text="Drawing No X-SD-1 X-SD-2"):
    doc = pymupdf.open()
    page = doc.new_page(width=1684, height=1190)
    page.insert_text((1300, 1100), text, fontsize=9)
    return doc, page


def _run(db, provider, variant="EV2", **kw):
    return er.EvidenceRun(db=db, project_id=None, provider=provider, budget=open_budget(db, None), variant=variant, **kw)


def _discover(identity="", revision="", other_numbers=(), **decision):
    region = [760, 900, 900, 950]
    return {"page_kind": "drawing_sheet", "own_identity": identity, "own_identity_label": "", "own_identity_region": region if identity else [],
            "own_revision": revision, "own_revision_label": "", "own_revision_region": region if revision else [],
            "decision_options_printed": decision.get("options", []), "decision_marked_option": decision.get("marked", ""),
            "decision_mark_type": decision.get("mark", "none"), "decision_actor": decision.get("actor", "unknown"),
            "decision_region": [100, 100, 400, 300] if decision else [], "other_numbers": list(other_numbers), "notes": ""}


def _read(value):
    return {"label_text": "", "value": value, "legible": True, "other_values_in_crop": []}


def test_escalation_keeps_the_earlier_disagreement(db_session):
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


# --- literal and numeric semantics ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("reader, blind_part, state", [
    ("PT-1S", "PT-1S+", "conflict"), ("PT-1S+", "PT-1S+", "part_verified_quantity_unverified"),
    ("0012-A", "12-A", "conflict"), ("SL2-42D3D-CGL-M +SL23I", "SL2-42D3D-CGL-M+SL23I", "part_verified_quantity_unverified"),
])
def test_parts_compare_as_printed(reader, blind_part, state):
    assert er.validate_boq_row({"part_number": reader, "quantity": "2"}, {"part_number": blind_part, "quantity": "", "legible": True})["state"] == state


@pytest.mark.parametrize("reader, blind_qty, part, quantity", [
    ("15", "15", "verified", "verified"), ("1.5", "15", "verified", "conflict"), ("1,250", "1250", "verified", "verified"),
    ("15", "15 m", "verified", "verified"), ("15 m", "15 nos", "verified", "conflict"), ("-3", "3", "verified", "conflict"),
    ("| 15", "15", "verified", "unresolved"), ("1,5", "15", "verified", "unresolved"), ("2", "", "verified", "unverified"),
])
def test_quantities_keep_decimal_sign_and_unit(reader, blind_qty, part, quantity):
    got = er.validate_boq_row({"part_number": "P-1", "quantity": reader}, {"part_number": "P-1", "quantity": blind_qty, "legible": True})
    assert (got["part"], got["quantity"]) == (part, quantity)
    assert got["state"] != "validated" or quantity == "verified"


def test_a_description_count_is_a_located_quantity_and_a_part_alone_does_not_verify_a_row():
    got = er.validate_boq_row({"part_number": "4-AUDTELS", "quantity": "1"},
                              {"part_number": "4-AUDTELS", "quantity": "", "description": "( 1 ) Audio and Telephone Interface", "legible": True})
    assert (got["state"], got["quantity_source"]) == ("validated", "description_count")
    got = er.validate_boq_row({"part_number": "4-AUDTELS", "quantity": "1"}, {"part_number": "4-AUDTELS", "quantity": "", "legible": True})
    assert got["state"] == "part_verified_quantity_unverified" and got["part"] == "verified" and got["quantity"] == "unverified"


@pytest.mark.parametrize("field, value, text, supported", [
    ("identity", "0012", "Doc No 12", False),                    # leading zeros are significant
    ("identity", "AB-12", "Ref XAB-12", False),                  # a longer identity with a prefix
    ("identity", "AB-12", "Ref AB-12-01", False),                # ... or a suffix
    ("identity", "AB-12", "Ref: AB-12 dated", True),
    ("revision", "3", "Drawing AB-12-R3", False),                 # a revision inside an identity
    ("revision", "03", "REV 03   Date 03/05/2026", True),        # the REV cell, beside a date that also has 03
    ("revision", "05", "Date 03/05/2026", False),                # only inside the date
])
def test_region_support_boundaries(field, value, text, supported):
    support, _why = er.region_support(field, value, [("text", text)])
    assert (support is not None) is supported


def test_support_is_bound_to_the_read_region_not_the_page(db_session):
    doc = pymupdf.open()
    page = doc.new_page(width=1684, height=1190)
    page.insert_text((100, 100), "Referenced drawing X-SD-9", fontsize=9)      # far from the title block
    page.insert_text((1300, 1100), "Drawing No X-SD-1", fontsize=9)
    region = (1290, 1090, 1400, 1105)
    texts = er.region_texts(page, region, [])
    assert "X-SD-1" in texts[0][1] and "X-SD-9" not in texts[0][1]
    assert er.validate_value("identity", [blind("X-SD-9")], texts, None)["state"] == "candidate"
    assert er.validate_value("identity", [blind("X-SD-1")], texts, None)["state"] == "validated"
    # title-block OCR words count only inside the region
    ocr = [[1300, 1092, 1380, 1102, "X-SD-7"], [100, 90, 180, 100, "X-SD-8"]]
    t2 = er.region_texts(page, region, ocr)
    assert ("ocr", "X-SD-7") in t2 and all("X-SD-8" not in t for _s, t in t2)


def test_decisions_map_only_through_the_forms_printed_legend():
    legend = ["A = NO OBJECTION", "B = NO OBJECTION AS NOTED", "C = REVISE AND RESUBMIT"]
    both = lambda **kw: [dict(source="discovery", legible=True, mark_type="tick", actor="consultant", options_printed=legend, **kw),
                         dict(source="blind_small", legible=True, mark_type="tick", actor="consultant", options_printed=legend, **kw)]
    got = er.validate_decision(both(marked_option="B"), target="MTS-E-0018")
    assert (got["state"], got["decision"]) == ("validated", "ANN")
    # a code that is not on this form's legend maps to nothing
    got = er.validate_decision(both(marked_option="D"), target="MTS-E-0018")
    assert got["state"] == "candidate" and got["decision"] is None
    for words in ("Comply", "RECEIVED 14.05.26"):
        opts = [words, "Not comply"] if words == "Comply" else [words]
        got = er.validate_decision([dict(r, options_printed=opts) for r in both(marked_option=words)], target="X")
        assert got["state"] == "not_a_decision"


def test_the_pages_own_identity_and_the_identities_it_references_are_different_facts(db_session):
    doc, page = _page("Drawing No TR/0127/26")
    provider = RecordingProvider([_discover("TR/0127/26", other_numbers=[{"role": "listed_item", "literal": "25H-S202-NCC-MAS-MEP-ELE-005-R3"}]),
                                  _read("TR/0127/26")])
    facts = er.PageFacts(1, page.get_text(), [], [])
    out = er._read_page(_run(db_session, provider, "EV1"), page, sha256="b" * 64, number=1, facts=facts, reason="t")["_observations"]
    own = [o for o in out if o["field"] == "identity" and o["role"] == "own"]
    refs = [o for o in out if o["role"] == "listed_item"]
    assert own[0]["value"] == "TR/0127/26" and own[0]["component"] == "own"
    assert refs[0]["value"] == "25H-S202-NCC-MAS-MEP-ELE-005-R3" and refs[0]["state"] == "observed_reference" and refs[0]["component"] == "ref0"


# --- evidence lifecycle (R7-03; field-level and context-bound since review 08) --------------------------------------------


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
