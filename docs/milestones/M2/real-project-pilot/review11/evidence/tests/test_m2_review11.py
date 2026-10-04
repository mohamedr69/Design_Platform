"""M2 review 11 (R11-01): association safety survives bounded history and repeated processing. Dropping audit history,
retrying unrelated fields, restarting or reopening a stored row never improves the acceptance of a retained fact; only
newly read compatible source evidence may. Rows stored by the review 10 reader are built with that exact reader,
pinned unchanged as tests/fixtures/evidence_reader_r10.py (a34d3f8). Scripted providers only; every step goes through
the real `evidence_stage` on a persisted row, reloaded afterwards. Written to run unchanged on a34d3f8, where the R11
cases fail on behaviour (evaluator outcome / recovery first; every new key read with `.get`)."""
import importlib.util
import json
import pathlib
import sys

import pytest

from app.ai import evidence_reader as er

from .test_m2_review09 import APPROVAL, SHA, decision_read, discover, doc_row, ledger_provider, read, timeout  # noqa: F401
from .test_m2_review10 import assoc, persist, score, selected, stage

_spec = importlib.util.spec_from_file_location("evidence_reader_r10", pathlib.Path(__file__).parent / "fixtures" / "evidence_reader_r10.py")
old = importlib.util.module_from_spec(_spec)
sys.modules["evidence_reader_r10"] = old
_spec.loader.exec_module(old)

LIMIT_HISTORY, LIMIT_ATTEMPTS = er.MAX_FIELD_HISTORY, er.MAX_ATTEMPTS_KEPT


def own(field, value, state="validated", **kw):
    return dict(page=1, component="own", role="own", field=field, value=value, state=state, read="completed", **kw)


def stored_by_review10(steps):
    """Evidence as the review 10 reader stored it: its merge, and its stage's attempt numbering (the length of the
    bounded summary list plus one)."""
    ai = None
    for observations in steps:
        n = len(old._normalise_ai(ai)["attempts"]) + 1
        ai = old.merge_evidence(ai, {"attempt": n, "outcome": "complete", "observations": observations, "coverage": {"pages": [
            {"page": 1, "outcome": "evidence", "fields": {er._field_key(o): "completed" for o in observations}}]}},
            sha256=SHA, profile="default", variant="EV1")
    return ai


REVIEW07_WITH_TARGET = {  # a review 07 page (the matched-run shape): the decision records its target, not its revision
    "envelopes": {"default|EV1": {"profile": "default", "variant": "EV1", "read_sha256": SHA, "pages": {"1": {
        "observations": [own("identity", "X-SD-1"), own("revision", "02"), own("decision", "ANN", target="X-SD-1")],
        "provenance": {"attempt": 1, "read_sha256": SHA, "profile": "default", "variant": "EV1"}}}}},
    "current_key": "default|EV1", "attempts": [{"attempt": 1, "outcome": "complete", "profile": "default", "variant": "EV1"}]}

REREAD_REVISION_03 = [discover("X-SD-1", revision="03"), read("X-SD-1"), read("03")]


def decision_outcome(ai, revision="03"):
    s = score(ai, reference="X-SD-1", revision=revision)
    return s.judged("decision"), s.recovery["decision"]


# --- 1. a decision's inferred revision anchor outlives the field history ---------------------------------------------------


def test_a_legacy_decision_stays_held_as_its_old_revision_leaves_history(doc_row):
    persist(doc_row, REVIEW07_WITH_TARGET)
    for n in range(LIMIT_HISTORY + 4):                       # well past the four retained history entries
        ai = stage(doc_row, REREAD_REVISION_03)
        judged, recovery = decision_outcome(ai)
        assert ("ANN", "validated", "correct") not in judged and recovery != "recovered_clean", f"accepted after re-read {n + 1}"
        assert assoc(ai, "own:decision").get("status") == "held:revision_changed"
    dec = selected(ai, "own:decision")
    assert dec["provenance"]["attempt"] == 1 and dec.get("target_revision") is None, "the retained fact itself is unchanged"
    # a genuine re-read of the decision block with revision 03 establishes the association
    ai = stage(doc_row, [discover("X-SD-1", revision="03", decision=APPROVAL), read("X-SD-1"), read("03"), decision_read()])
    assert decision_outcome(ai) == ([("ANN", "validated", "correct")], "recovered_clean")
    assert assoc(ai, "own:decision").get("status") == "current"


def test_an_explicit_target_revision_stays_held_past_the_history_limit(doc_row):
    stage(doc_row, [discover("X-SD-1", revision="02", decision=APPROVAL), read("X-SD-1"), read("02"), decision_read()])
    for _ in range(LIMIT_HISTORY + 3):
        ai = stage(doc_row, REREAD_REVISION_03)
    assert decision_outcome(ai)[1] != "recovered_clean" and assoc(ai, "own:decision").get("status") == "held:revision_changed"


# --- 2. a targetless legacy revision across the attempt limit and the old counter collision ------------------------------


def test_a_targetless_legacy_revision_is_never_recovered_across_the_attempt_limit(doc_row):
    persist(doc_row, stored_by_review10([[own("identity", "X-SD-1"), own("revision", "02")]] * 13))   # stored attempt 13
    for actual in range(14, 14 + LIMIT_ATTEMPTS):            # the independent sequence: reads 14, 15, ... past the cap
        ai = stage(doc_row, [discover("X-SD-9"), read("X-SD-9")])
        s = score(ai, reference="X-SD-9", revision="02")
        assert ("02", "validated", "correct") not in s.judged("revision") and s.recovery["revision"] != "recovered_clean", \
            f"recovered for X-SD-9 at actual read {actual}"
        assert assoc(ai, "own:revision").get("status") == "held:context_changed"
    assert selected(ai, "own:revision")["provenance"]["attempt"] == 13


# --- 3. restart / reload past both limits: attempt identity never collides ----------------------------------------------


def test_attempt_identity_is_persistent_and_unique_across_reloads_past_both_limits(doc_row):
    stage(doc_row, [discover("X-SD-1", revision="02", decision=APPROVAL), read("X-SD-1"), read("02"), decision_read()])
    retained = None
    numbers = []
    for n in range(LIMIT_ATTEMPTS + 3):
        ai = stage(doc_row, REREAD_REVISION_03 if n % 2 else [discover("X-SD-1"), read("X-SD-1")])   # each call reloads the row
        numbers.append(ai["attempts"][-1]["attempt"])
        entry = ai["envelopes"]["default|EV1"]["pages"]["1"]["fields"]["own:decision"]
        retained = retained or json.dumps({k: entry[k] for k in ("observations", "provenance") if k in entry}, sort_keys=True)
        assert json.dumps({k: entry[k] for k in ("observations", "provenance") if k in entry}, sort_keys=True) == retained, \
            "the retained decision's evidence and provenance never change"
    assert numbers == sorted(set(numbers)) and len(numbers) == LIMIT_ATTEMPTS + 3, f"attempt numbers repeat: {numbers}"
    assert numbers[-1] > LIMIT_ATTEMPTS + 1
    assert len(ai["attempts"]) == LIMIT_ATTEMPTS, "the summaries stay bounded"


# --- 4. rows already stored with duplicate or missing attempt order -------------------------------------------------------


def _collided():
    """A row the review 10 reader kept processing past its cap: identity re-read as X-SD-9 under the repeated number 13."""
    ai = stored_by_review10([[own("identity", "X-SD-1"), own("revision", "02")]] * 13)
    for _ in range(3):
        ai = old.merge_evidence(ai, {"attempt": len(old._normalise_ai(ai)["attempts"]) + 1, "outcome": "complete",
                                     "observations": [own("identity", "X-SD-9")],
                                     "coverage": {"pages": [{"page": 1, "outcome": "evidence", "fields": {"own:identity": "completed"}}]}},
                                sha256=SHA, profile="default", variant="EV1")
    assert [a["attempt"] for a in ai["attempts"]][-3:] == [13, 13, 13]
    return ai


def test_a_stored_row_with_colliding_attempt_numbers_invents_no_chronology(doc_row):
    ai = persist(doc_row, _collided())
    s = score(ai, reference="X-SD-9", revision="02")
    assert ("02", "validated", "correct") not in s.judged("revision") and s.recovery["revision"] != "recovered_clean"
    assert assoc(ai, "own:revision").get("status", "").startswith("held:")
    ai = stage(doc_row, [discover("X-SD-9"), read("X-SD-9")])          # processed again: still held, never accepted
    assert score(ai, reference="X-SD-9", revision="02").recovery["revision"] != "recovered_clean"


def test_missing_attempt_order_is_held_and_single_attempt_history_is_unchanged():
    unordered = json.loads(json.dumps(REVIEW07_WITH_TARGET).replace('"attempt": 1', '"attempt": null'))
    unordered = er.merge_evidence(unordered, {"attempt": 2, "outcome": "complete", "observations": [own("identity", "X-SD-9")],
                                              "coverage": {"pages": [{"page": 1, "outcome": "evidence", "fields": {"own:identity": "completed"}}]}},
                                  sha256=SHA, profile="default", variant="EV1")
    s = score(unordered, reference="X-SD-9", revision="02")
    assert ("ANN", "validated", "correct") not in s.judged("decision") and ("02", "validated", "correct") not in s.judged("revision")
    # controls: a historical single attempt (review 07 page, review 06 flat) scores exactly as before
    assert decision_outcome(REVIEW07_WITH_TARGET, revision="02") == ([("ANN", "validated", "correct")], "recovered_clean")
    targetless = json.loads(json.dumps(REVIEW07_WITH_TARGET).replace(', "target": "X-SD-1"', ""))
    assert decision_outcome(targetless, revision="02") == ([("ANN", "validated", "correct")], "recovered_clean")


# --- 5. truncation never improves acceptance: several retention cycles, failed and budget-stopped attempts -------------


def test_retention_cycles_with_failed_and_budget_stopped_attempts_never_improve_acceptance(doc_row, tmp_path):
    persist(doc_row, REVIEW07_WITH_TARGET)
    seen = []
    for n in range(2 * LIMIT_ATTEMPTS + 2):                  # more than two full cycles of both limits
        if n % 4 == 1:
            ai = stage(doc_row, [timeout()])
        elif n % 4 == 3:
            ai = _budget_stage(doc_row, tmp_path, n)
        else:
            ai = stage(doc_row, REREAD_REVISION_03)
        judged, recovery = decision_outcome(ai)
        seen.append(recovery)
        assert ("ANN", "validated", "correct") not in judged and recovery != "recovered_clean", f"improved at step {n}: {seen}"
    assert len(ai["attempts"]) == LIMIT_ATTEMPTS


def _budget_stage(d, tmp_path, n):
    from app.models import ProjectDocument, ResultCache

    d.db.query(ResultCache).delete()
    d.db.commit()
    row = d.db.get(ProjectDocument, d.id)
    er.evidence_stage(d.db, d.project, [(row, d.path)], provider=ledger_provider(tmp_path / f"b{n}", [discover("X-SD-1", revision="03")], requests=1),
                      variant="EV1", profile="default")
    d.db.commit()
    d.db.expire_all()
    return d.db.get(ProjectDocument, d.id).extracted["ai_evidence"]


# --- 6. positive controls ----------------------------------------------------------------------------------------------


def test_control_same_context_retries_past_both_limits_keep_legacy_recovery(doc_row):
    persist(doc_row, REVIEW07_WITH_TARGET)
    for _ in range(LIMIT_ATTEMPTS + 2):
        ai = stage(doc_row, [discover("X-SD-1", revision="02"), read("X-SD-1"), read("02")])
    assert decision_outcome(ai, revision="02") == ([("ANN", "validated", "correct")], "recovered_clean")


def test_control_a_legacy_targetless_revision_is_resolved_only_by_a_genuine_reread(doc_row):
    persist(doc_row, stored_by_review10([[own("identity", "X-SD-1"), own("revision", "02")]] * 13))
    for _ in range(3):
        stage(doc_row, [discover("X-SD-9"), read("X-SD-9")])
    ai = stage(doc_row, [discover("X-SD-9", revision="02"), read("X-SD-9"), read("02")])
    s = score(ai, reference="X-SD-9", revision="02")
    assert s.judged("revision") == [("02", "validated", "correct")] and s.recovery["revision"] == "recovered_clean"
