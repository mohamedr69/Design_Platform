"""R15-03: the overlay is an annotation layer inside the evaluator's contract. Replaces r14's test that endorsed
removing a critical error when an accepted target equalled an unapproved proposal. Synthetic adversarial cases
(context, envelope order, stale content, proposals, punctuation, explicit states) and the stored single-context
small-batch results, kept apart."""
import collections
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _budget_env as env  # noqa: E402

old = env.load(env.SUBMITTED, "overlay")
ov = env.load(env.CORRECTED, "overlay")
ACTIVE = {"variant": "EV1", "profile": "default"}


def case(value="00", literal="00", target="COVER-1", field="revision", assoc="proposal_only", role="revision", with_ctx=True, state="validated"):
    fact = {"page": 2, "field": field, "value": value, "state": state, "reader": "ai:EV1", "group": "ai:2:own"}
    result = {"documents": [{"doc": "D", "layers": {"evidence": {"judged": [fact], "critical": [fact]}}}]}
    if with_ctx:
        result["ai_context"] = dict(ACTIVE)
    labels = {"documents": {"D": {"supported_observations": {"2": [{"field": field, "literal": literal, "role_state": role, "association_state": assoc,
                                                                   "association_target": "COVER-1"}]}}}}
    env_ = {"read_sha256": "CURRENT", "pages": {"2": {"fields": {f"own:{field}": {"observations": [{"field": field, "value": value, "target": target,
                                                                                                    "state": state}], "anchor": {"identity": None}}}}}}
    rows = {"D": {"sha256": "CURRENT", "extracted": {"ai_evidence": {"envelopes": {"default|EV1": env_}}}}}
    return result, labels, rows


def test_submitted_overlay_removed_a_critical_for_an_unapproved_proposal():
    r, l, rows = case()
    l["documents"]["D"]["supported_observations"]["2"][0]["role"] = "revision"
    assert old.overlay(r, l, rows)["critical_after_overlay"] == 0          # the Review 15 defect


def test_accepted_target_equal_to_an_unapproved_proposal_stays_critical():
    o = ov.overlay(*case())
    a = o["annotations"][0]
    assert o["critical_after_overlay"] == 1 and a["critical"] is True
    assert a["context_status"] == "found" and a["recorded_target"] == "COVER-1" and a["association_state"] == "proposal_only"
    assert "UNAPPROVED" in a["annotation"]


def test_even_an_approved_association_does_not_remove_the_evaluators_critical():
    o = ov.overlay(*case(assoc="approved"))
    assert o["critical_after_overlay"] == 1                                 # annotation only: the evaluator decides


def _two_envelopes(order):
    r, l, rows = case(target=None)
    active = rows["D"]["extracted"]["ai_evidence"]["envelopes"]["default|EV1"]
    foreign = copy.deepcopy(active)
    foreign["read_sha256"] = "OLD-CONTENT"
    foreign["pages"]["2"]["fields"]["own:revision"]["observations"][0]["target"] = "COVER-1"
    envs = {"promoted|EV2": foreign, "default|EV1": active} if order == "foreign_first" else {"default|EV1": active, "promoted|EV2": foreign}
    rows["D"]["extracted"]["ai_evidence"]["envelopes"] = envs
    return ov.overlay(r, l, rows)


def test_envelope_order_and_foreign_context_do_not_change_the_result():
    a, b = _two_envelopes("foreign_first"), _two_envelopes("active_first")
    assert a == b
    assert a["annotations"][0]["recorded_target"] is None and a["annotations"][0]["context"] == "default|EV1"
    assert a["critical_after_overlay"] == 1


def test_only_a_foreign_context_present_is_context_unknown():
    r, l, rows = case()
    envs = rows["D"]["extracted"]["ai_evidence"]["envelopes"]
    envs["promoted|EV2"] = envs.pop("default|EV1")
    a = ov.overlay(r, l, rows)["annotations"][0]
    assert a["context_status"] == "context_unknown" and a["recorded_target"] is None and a["critical"] is True


def test_stale_content_envelope_is_isolated():
    r, l, rows = case()
    rows["D"]["extracted"]["ai_evidence"]["envelopes"]["default|EV1"]["read_sha256"] = "OLD-CONTENT"
    assert ov.overlay(r, l, rows)["annotations"][0]["context_status"] == "context_mismatch"


def test_no_declared_context_is_never_guessed():
    a = ov.overlay(*case(with_ctx=False))["annotations"][0]
    assert a["context_status"] == "context_unknown" and a["critical"] is True
    b = ov.overlay(*case(with_ctx=False), ai_context=ACTIVE)["annotations"][0]
    assert b["context_status"] == "found"                                   # an explicit context is used as given


def test_missing_target_control():
    a = ov.overlay(*case(target=None))["annotations"][0]
    assert a["annotation"] == "literal supported; reader accepted without a target" and a["critical"] is True


def test_revision_punctuation_is_kept():
    a = ov.overlay(*case(value="1.0", literal="10"))
    assert a["annotations"][0]["literal_supported"] is False and a["supported_raw_observations"] == 0
    b = ov.overlay(*case(value="0", literal="Rev.0", target=None))
    assert b["annotations"][0]["literal_supported"] is True and b["supported_raw_observations"] == 1
    assert ov.rev_literal("Rev.0") == "0" and ov.rev_literal("1.0") == "1.0" and ov.rev_literal("REV 01") == "01"


def test_states_are_explicit_enums_not_free_text():
    r, l, rows = case(field="identity", value="P06/TRANS/R1", literal="P06/TRANS/R1", target=None)
    o = l["documents"]["D"]["supported_observations"]["2"][0]
    o.pop("role_state")
    o["role"] = "footer / control-code candidate (HELD)"                    # the r14 free text: NOT authority
    a = ov.overlay(r, l, rows)["annotations"][0]
    assert a["role_state"] == "unknown" and "role not established" not in a["annotation"]


def test_held_fact_state_is_reported_as_the_reader_recorded_it():
    a = ov.overlay(*case(state="held"))["annotations"][0]
    assert a["recorded_state"] == "held" and a["fact_state"] == "held"


# --- stored single-context results (historic; kept apart from the adversarial cases) ------------------------------------
def _stored(track):
    res = json.loads(Path(f"C:/t/iso/work/r2x/r14/rescore/small-{track}__amended-r14.1.json").read_text(encoding="utf-8"))
    labels = json.loads(Path("C:/t/iso/work/r2x/labels/r15/SMALL-BATCH-LABELS.amended-r15.1.json").read_text(encoding="utf-8"))
    rows = json.loads(Path(f"C:/t/r2x/runs/r2x-small-{track}/out/rows.json").read_text(encoding="utf-8"))
    return res, ov.overlay(res, labels, rows)


def test_stored_small_batch_keeps_the_evaluators_criticals_and_finds_each_fact_in_its_own_context():
    for track, n in (("B", 3), ("C", 2)):
        res, o = _stored(track)
        assert o["critical_after_overlay"] == o["critical_evaluator"] == len(res["totals"]["evidence"]["critical"]) == n
        assert all(a["context_status"] == "found" and a["recorded_target"] is None for a in o["annotations"])
    kinds_b = collections.Counter(a["annotation"] for a in _stored("B")[1]["annotations"])
    kinds_c = collections.Counter(a["annotation"] for a in _stored("C")[1]["annotations"])
    assert kinds_b == {"literal supported; reader accepted without a target": 2, "literal of another role (revision) accepted as identity": 1}
    assert kinds_c == {"literal supported; reader accepted without a target": 1, "role not established (held) but accepted": 1}
