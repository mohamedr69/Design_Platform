"""M2 review 12 (R12-01): legacy anchor reconstruction carries the exact historical entry (A) and requires reliable
order for every context entry it uses (B); anchors reader .6 already saved are re-derived from recorded history or
held (expectations frozen in review12/COMPATIBILITY.md before the code changed). Stored shapes come from the pinned
prior readers: tests/fixtures/evidence_reader_r10.py (a34d3f8) and evidence_reader_r11.py (a977364). Scripted
providers only; the stage runs on a persisted row reloaded after every attempt. Written to run unchanged on a977364,
where the R12 cases fail on behaviour (the evaluator's judgement / the accessor's association come first; every new
key is read with `.get`)."""
import copy
import importlib.util
import json
import pathlib
import random
import sys

from app.ai import evidence_reader as er

from .test_m2_review09 import APPROVAL, SHA, decision_read, discover, doc_row, read  # noqa: F401 -- doc_row is a fixture
from .test_m2_review10 import assoc, persist, score, selected, stage


def _pinned(name):
    spec = importlib.util.spec_from_file_location(name, pathlib.Path(__file__).parent / "fixtures" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


r10 = _pinned("evidence_reader_r10")        # a34d3f8: stores no anchors
r11 = _pinned("evidence_reader_r11")        # a977364: stamps anchors (its reconstruction selects revisions by value)


def own(field, value, state="validated", **kw):
    return dict(page=1, component="own", role="own", field=field, value=value, state=state, read="completed", **kw)


def add(module, ai, n, observations):
    return module.merge_evidence(copy.deepcopy(ai), {"attempt": n, "outcome": "complete", "observations": observations, "coverage": {"pages": [
        {"page": 1, "outcome": "evidence", "fields": {er._field_key(o): "completed" for o in observations}}]}},
        sha256=SHA, profile="default", variant="EV1")


def review10_rows(other_revision="02"):
    """The reviewer's sequence as the review 10 reader stored it: X-SD-1 / rev 02 / ANN (target, no target revision);
    then X-SD-7 / rev `other_revision` for X-SD-7, the decision retained."""
    first = add(r10, None, 1, [own("identity", "X-SD-1"), own("revision", "02", target="X-SD-1"), own("decision", "ANN", target="X-SD-1")])
    return add(r10, first, 2, [own("identity", "X-SD-7"), own("revision", other_revision, target="X-SD-7")])


REREAD_X1_REV03 = [discover("X-SD-1", revision="03"), read("X-SD-1"), read("03")]


def outcome(ai, reference="X-SD-1", revision="03"):
    s = score(ai, reference=reference, revision=revision)
    return s.judged("decision"), s.recovery["decision"], assoc(ai, "own:decision").get("status")


def fields_of(ai):
    return ai["envelopes"]["default|EV1"]["pages"]["1"]["fields"]


# --- R12-01A: the exact historical entry, never a reselection by value --------------------------------------------------


def test_a_repeated_revision_literal_of_another_drawing_never_removes_the_constraint(doc_row):
    persist(doc_row, review10_rows("02"))
    ai = stage(doc_row, REREAD_X1_REV03)                     # candidate read: X-SD-1 / rev 03, no decision re-read
    judged, recovery, status = outcome(ai)
    assert ("ANN", "validated", "correct") not in judged and recovery != "recovered_clean", "ANN was read with revision 02"
    assert status == "held:revision_changed"
    anchor = fields_of(ai)["own:decision"].get("anchor") or {}
    assert anchor.get("revision") == "02" and (anchor.get("revision_entry") or {}).get("target") == "X-SD-1"
    assert (anchor.get("revision_entry") or {}).get("attempt") == 1


def test_the_unrelated_drawings_revision_literal_does_not_change_the_outcome(doc_row):
    persist(doc_row, review10_rows("09"))
    held_09 = outcome(stage(doc_row, REREAD_X1_REV03))
    ai = er.merge_evidence(review10_rows("02"), {"attempt": 3, "outcome": "complete", "observations": [
        own("identity", "X-SD-1"), own("revision", "03", target="X-SD-1")], "coverage": {"pages": [{"page": 1, "outcome": "evidence",
        "fields": {"own:identity": "completed", "own:revision": "completed"}}]}}, sha256=SHA, profile="default", variant="EV1")
    assert outcome(ai) == held_09
    assert held_09[2] == "held:revision_changed"


def test_selection_does_not_depend_on_the_physical_order_of_history():
    base = add(r10, review10_rows("02"), 3, [own("identity", "X-SD-7"), own("revision", "02", target="X-SD-7")])
    results = set()
    for seed in range(6):
        shuffled = copy.deepcopy(base)
        for entry in fields_of(shuffled).values():
            random.Random(seed).shuffle(entry.get("history") or [])
        ai = er.merge_evidence(shuffled, {"attempt": 4, "outcome": "complete", "observations": [own("identity", "X-SD-1"),
                               own("revision", "03", target="X-SD-1")], "coverage": {"pages": [{"page": 1, "outcome": "evidence",
                               "fields": {"own:identity": "completed", "own:revision": "completed"}}]}}, sha256=SHA, profile="default", variant="EV1")
        results.add(json.dumps([outcome(ai), (fields_of(ai)["own:decision"].get("anchor") or {}).get("revision")]))
    assert len(results) == 1 and '"held:revision_changed"' in results.pop()


def test_explicit_target_revision_and_same_context_controls(doc_row):
    explicit = add(r10, None, 1, [own("identity", "X-SD-1"), own("revision", "02", target="X-SD-1"),
                                  own("decision", "ANN", target="X-SD-1", target_revision="02")])
    explicit = add(r10, explicit, 2, [own("identity", "X-SD-7"), own("revision", "02", target="X-SD-7")])
    persist(doc_row, explicit)
    assert outcome(stage(doc_row, REREAD_X1_REV03))[2] == "held:revision_changed"
    # same context: nothing changed for X-SD-1 -> the legacy decision stays current and recovered
    same = add(r10, None, 1, [own("identity", "X-SD-1"), own("revision", "02", target="X-SD-1"), own("decision", "ANN", target="X-SD-1")])
    same = er.merge_evidence(same, {"attempt": 2, "outcome": "complete", "observations": [own("identity", "X-SD-1"),
                             own("revision", "02", target="X-SD-1")], "coverage": {"pages": [{"page": 1, "outcome": "evidence",
                             "fields": {"own:identity": "completed", "own:revision": "completed"}}]}}, sha256=SHA, profile="default", variant="EV1")
    assert outcome(same, revision="02")[:2] == ([("ANN", "validated", "correct")], "recovered_clean")


# --- R12-01B: every context entry needs a reliable order ------------------------------------------------------------


def _unordered_identity():
    ai = add(r10, None, 1, [own("identity", "X-SD-9"), own("revision", "02")])
    ai["envelopes"]["default|EV1"]["pages"]["1"]["fields"]["own:identity"]["provenance"]["attempt"] = None
    return ai


def test_a_context_entry_without_order_is_never_attempt_zero(doc_row):
    ai = _unordered_identity()
    s = score(ai, reference="X-SD-9", revision="02")
    assert ("02", "validated", "correct") not in s.judged("revision") and s.recovery["revision"] != "recovered_clean"
    assert assoc(ai, "own:revision").get("status") == "held:context_unavailable"
    persist(doc_row, ai)                                      # through the stage: still held after a merge and a reload
    ai = stage(doc_row, [discover("X-SD-9"), read("X-SD-9")])
    assert score(ai, reference="X-SD-9", revision="02").recovery["revision"] != "recovered_clean"
    assert assoc(ai, "own:revision").get("status") == "held:context_unavailable"


def test_two_different_context_entries_with_one_order_are_ambiguous():
    ai = add(r10, None, 1, [own("identity", "X-SD-1"), own("revision", "02")])
    ai = add(r10, ai, 2, [own("identity", "X-SD-9")])
    ident = fields_of(ai)["own:identity"]
    ident["provenance"]["attempt"] = 1                        # X-SD-9 now claims attempt 1 as well: duplicated order
    s = score(ai, reference="X-SD-9", revision="02")
    assert ("02", "validated", "correct") not in s.judged("revision") and s.recovery["revision"] != "recovered_clean"
    assert assoc(ai, "own:revision").get("status", "").startswith("held:")


def test_controls_flat_legacy_numbered_history_and_known_absence():
    flat = {"version": "evidence-reader-2026-09-29.1", "variant": "EV1", "profile": "default", "read_sha256": SHA,
            "observations": [{"page": 1, "field": "identity", "value": "X-SD-1", "state": "validated"},
                             {"page": 1, "field": "revision", "value": "02", "state": "validated"},
                             {"page": 1, "field": "decision", "value": "ANN", "state": "validated"}]}
    flat_after = er.merge_evidence(flat, {"attempt": 2, "outcome": "complete", "observations": [own("identity", "X-SD-1")], "coverage": {
        "pages": [{"page": 1, "outcome": "evidence", "fields": {"own:identity": "completed"}}]}}, sha256=SHA, profile="default", variant="EV1")
    for ai in (flat, flat_after):                             # the explicit flat `legacy` format: one reading, ordered first
        from scripts import m2_eval5 as ev

        doc = {"doc": "EP-10/form.pdf", "ep": "10", "cohort": "c", "stratum": "s", "extension": ".pdf", "scan_like": False, "confidence": "high",
               "labels": {"kind": "shop-drawing cover", "reference": "X-SD-1", "revision": "02", "decision": "approved as noted"}}
        rows = {doc["doc"]: {"state": "fresh", "sha256": SHA, "extracted": {"records": [], "profile": "default", "ai_evidence": ai}}}
        ctx = {"variant": "EV1", "profile": "default", "accept_unknown_profile": True}
        layer = ev.evaluate({"documents": [doc]}, None, rows, ai_context=ctx)["documents"][0]["layers"]["ai"]
        assert [(j["value"], j["outcome"]) for j in layer["judged"] if j["field"] == "decision"] == [("ANN", "correct")]
    numbered = add(r10, None, 1, [own("identity", "X-SD-1"), own("revision", "02", target="X-SD-1"), own("decision", "ANN", target="X-SD-1")])
    numbered = er.merge_evidence(numbered, {"attempt": 2, "outcome": "complete", "observations": [own("identity", "X-SD-1")], "coverage": {
        "pages": [{"page": 1, "outcome": "evidence", "fields": {"own:identity": "completed"}}]}}, sha256=SHA, profile="default", variant="EV1")
    assert outcome(numbered, revision="02")[:2] == ([("ANN", "validated", "correct")], "recovered_clean")
    # known absence: ANN read when no revision existed (history below its bound), a revision read afterwards
    absent = add(r10, None, 1, [own("identity", "X-SD-1"), own("decision", "ANN", target="X-SD-1")])
    absent = er.merge_evidence(absent, {"attempt": 2, "outcome": "complete", "observations": [own("revision", "03", target="X-SD-1")],
                               "coverage": {"pages": [{"page": 1, "outcome": "evidence", "fields": {"own:revision": "completed"}}]}},
                               sha256=SHA, profile="default", variant="EV1")
    assert outcome(absent)[2] in ("current", "by_target")      # a control: an established absence imposes no constraint
    assert (fields_of(absent)["own:decision"].get("anchor") or {}).get("revision_status", "absent") == "absent"


def test_a_revision_context_that_may_have_been_pruned_is_unverifiable_never_absent():
    ai = add(r10, None, 1, [own("identity", "X-SD-1"), own("revision", "02", target="X-SD-1"), own("decision", "ANN", target="X-SD-1")])
    for n, rev in zip(range(2, 8), ("04", "05", "06", "07", "08", "09")):   # revision 02 pushed out of the 4-entry history
        ai = add(r10, ai, n, [own("revision", rev, target="X-SD-7")])
    ai = er.merge_evidence(ai, {"attempt": 8, "outcome": "complete", "observations": [own("revision", "03", target="X-SD-1")], "coverage": {
        "pages": [{"page": 1, "outcome": "evidence", "fields": {"own:revision": "completed"}}]}}, sha256=SHA, profile="default", variant="EV1")
    judged, recovery, status = outcome(ai)
    assert ("ANN", "validated", "correct") not in judged and recovery != "recovered_clean"
    assert status == "held:revision_unverifiable"


# --- anchors a977364 already saved ------------------------------------------------------------------------------------


def _saved_by_a977364(other_revision="02"):
    """E10: the review 10 rows, then one merge by the pinned a977364 reader -- which saves the erroneous anchor."""
    return r11.merge_evidence(review10_rows(other_revision), {"attempt": 3, "outcome": "complete", "observations": [
        own("identity", "X-SD-1"), own("revision", "03", target="X-SD-1")], "coverage": {"pages": [{"page": 1, "outcome": "evidence",
        "fields": {"own:identity": "completed", "own:revision": "completed"}}]}}, sha256=SHA, profile="default", variant="EV1")


def test_an_erroneous_anchor_saved_by_a977364_is_re_derived_from_history_not_trusted(doc_row):
    saved = _saved_by_a977364()
    bad = fields_of(saved)["own:decision"]["anchor"]
    assert bad.get("revision") is None and bad.get("revision_known") is True, "the a977364 reconstruction selected by value"
    judged, recovery, status = outcome(saved)
    assert ("ANN", "validated", "correct") not in judged and recovery != "recovered_clean" and status == "held:revision_changed"
    persist(doc_row, saved)
    ai = stage(doc_row, [discover("X-SD-1"), read("X-SD-1")])       # an unrelated re-read: the anchor is repaired, never trusted
    entry = fields_of(ai)["own:decision"]
    assert entry["anchor"].get("revision") == "02" and entry["anchor"].get("replaced_anchor") == bad
    assert outcome(ai)[2] == "held:revision_changed"


def test_an_erroneous_saved_anchor_whose_history_is_gone_is_held_until_a_genuine_reread(doc_row):
    saved = _saved_by_a977364()
    for n, rev in zip(range(4, 10), ("04", "05", "06", "07", "08", "09")):   # a977364 keeps processing: 02 leaves history
        saved = r11.merge_evidence(saved, {"attempt": n, "outcome": "complete", "observations": [own("revision", rev, target="X-SD-7")],
                                           "coverage": {"pages": [{"page": 1, "outcome": "evidence", "fields": {"own:revision": "completed"}}]}},
                                   sha256=SHA, profile="default", variant="EV1")
    saved = r11.merge_evidence(saved, {"attempt": 10, "outcome": "complete", "observations": [own("revision", "03", target="X-SD-1")],
                                       "coverage": {"pages": [{"page": 1, "outcome": "evidence", "fields": {"own:revision": "completed"}}]}},
                               sha256=SHA, profile="default", variant="EV1")
    persist(doc_row, saved)
    ai = stage(doc_row, [discover("X-SD-1"), read("X-SD-1")])
    judged, recovery, status = outcome(ai)
    assert ("ANN", "validated", "correct") not in judged and recovery != "recovered_clean" and status.startswith("held:")
    ai = stage(doc_row, [discover("X-SD-1", revision="03", decision=APPROVAL), read("X-SD-1"), read("03"), decision_read()])
    assert outcome(ai)[:2] == ([("ANN", "validated", "correct")], "recovered_clean"), "a genuine compatible re-read resolves it"


def test_read_time_anchors_are_never_rewritten(doc_row):
    stage(doc_row, [discover("X-SD-1", revision="02", decision=APPROVAL), read("X-SD-1"), read("02"), decision_read()])
    before = json.dumps(fields_of(stage(doc_row, [discover("X-SD-1"), read("X-SD-1")]))["own:decision"]["anchor"], sort_keys=True)
    for _ in range(er.MAX_ATTEMPTS_KEPT + 1):
        ai = stage(doc_row, REREAD_X1_REV03)
    assert json.dumps(fields_of(ai)["own:decision"]["anchor"], sort_keys=True) == before
    assert outcome(ai)[2] == "held:revision_changed"
