"""The r14 overlay (amended-label schema addition `supported_observations`): targeted tests on synthetic cases for every
branch, and on the STORED small-batch outputs (re-scored files under r14/rescore). Offline; no provider."""
import collections
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from overlay import overlay  # noqa: E402

R = pathlib.Path("C:/t/iso/work/r2x/r14")


def _case(crit_field, crit_value, obs, target=None, anchor=None):
    result = {"documents": [{"doc": "D", "layers": {"evidence": {"judged": [{"page": 2, "field": crit_field, "value": crit_value, "state": "validated"}],
                                                                 "critical": [{"page": 2, "field": crit_field, "value": crit_value}]}}}]}
    rows = {"D": {"extracted": {"ai_evidence": {"envelopes": {"default|EV1": {"pages": {"2": {"fields": {f"own:{crit_field}": {
        "observations": [{"field": crit_field, "value": crit_value, "target": target}], "anchor": {"identity": anchor}}}}}}}}}}}
    labels = {"documents": {"D": {"supported_observations": {"2": obs}}}}
    return overlay(result, labels, rows)


def test_correct_literal_without_target_stays_critical():
    o = _case("revision", "00", [{"field": "revision", "literal": "00", "role": "revision (Document History)"}])
    assert o["critical_typed"][0]["type"] == "correct literal, accepted without a supported target" and o["critical_after_overlay"] == 1
    assert o["supported_raw_observations"] == 1


def test_revision_literal_prefix_is_compared_without_rev():
    o = _case("revision", "0", [{"field": "revision", "literal": "Rev.0", "role": "revision"}])
    assert o["critical_typed"][0]["type"] == "correct literal, accepted without a supported target"


def test_revision_literal_accepted_as_identity_is_a_role_error():
    o = _case("identity", "Rev.0", [{"field": "revision", "literal": "Rev.0", "role": "revision"}])
    assert o["critical_typed"][0]["type"].startswith("role error") and o["critical_after_overlay"] == 1


def test_held_footer_code_accepted_as_identity_is_role_not_established():
    o = _case("identity", "P06/TRANS/R1", [{"field": "identity", "literal": "P06/TRANS/R1", "role": "footer / control-code candidate (HELD)"}])
    assert o["critical_typed"][0]["type"].startswith("role not established") and o["critical_after_overlay"] == 1


def test_target_matching_the_association_proposal_is_held_not_critical():
    o = _case("revision", "00", [{"field": "revision", "literal": "00", "role": "revision", "association_target": "COVER-1"}], target="COVER-1")
    assert o["critical_typed"][0]["type"] == "held association matching the proposal" and o["critical_after_overlay"] == 0


def test_no_supported_observation_is_a_literal_false_accept():
    o = _case("identity", "X-1", [])
    assert o["critical_typed"][0]["type"] == "literal false accept" and o["supported_raw_observations"] == 0


def _stored(track):
    res = json.loads((R / f"rescore/small-{track}__amended-r14.1.json").read_text(encoding="utf-8"))
    labels = json.loads(pathlib.Path("C:/t/iso/work/r2x/labels/r14/SMALL-BATCH-LABELS.amended-r14.1.json").read_text(encoding="utf-8"))
    rows = json.loads(pathlib.Path(f"C:/t/r2x/runs/r2x-small-{track}/out/rows.json").read_text(encoding="utf-8"))
    return overlay(res, labels, rows)


def test_stored_small_batch_B_and_C_criticals_are_retyped_not_removed():
    b, c = _stored("B"), _stored("C")
    assert collections.Counter(t["type"] for t in b["critical_typed"]) == {"correct literal, accepted without a supported target": 2,
                                                                           "role error (a supported revision literal accepted as identity)": 1}
    assert collections.Counter(t["type"] for t in c["critical_typed"]) == {"correct literal, accepted without a supported target": 1,
                                                                           "role not established (held footer / control code accepted as identity)": 1}
    assert b["critical_after_overlay"] == 3 and c["critical_after_overlay"] == 2
    assert all(t["recorded_target"] is None for t in b["critical_typed"] + c["critical_typed"])
