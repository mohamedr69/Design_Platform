"""R15-02: sparse duplicate rows. A scored value (quantity, part) never selects the truth row; without verified
geometry an indistinguishable duplicate is HELD; missed / extra rows stay visible. The same cases on the submitted
r14.1 contract show the defect."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _budget_env as env  # noqa: E402

old = env.load(env.SUBMITTED, "boq_contract")
new = env.load(env.CORRECTED, "boq_contract")
T6 = {"ordinal": 6, "page": 1, "part_number": "PRS-CSNKP", "quantity": "1", "description": "Numeric Keypad"}
T37 = {"ordinal": 37, "page": 1, "part_number": "PRS-CSNKP", "quantity": "2", "description": "Numeric Keypad"}
FIRST = {"id": "first", "page": 1, "y": 980.5, "part_number": "PRS-CSNKP", "quantity": "2", "description": "Numeric Keypad"}
SECOND = {"id": "second", "page": 1, "y": 2718.5, "part_number": "PRS-CSNKP", "quantity": "2", "description": "Numeric Keypad"}


def test_submitted_contract_lets_the_misread_quantity_choose_its_truth():
    assert old.join_rows([FIRST], [T6, T37])["pairs"] == [("first", 37, "matched")]


def test_missing_second_duplicate_is_held_not_resolved_by_quantity():
    j = new.join_rows([FIRST], [T6, T37])
    assert j["pairs"] == [("first", 6, "ambiguous")] and j["held"] == {"first": [6, 37]}


def test_changing_only_the_emitted_quantity_does_not_change_the_join():
    results = [new.join_rows([dict(FIRST, quantity=q)], [T6, T37]) for q in ("1", "2", "?", None, "0", "37")]
    assert all(r == results[0] for r in results)


def test_changing_only_the_emitted_part_does_not_change_the_join():
    results = [new.join_rows([dict(FIRST, part_number=p)], [T6, T37]) for p in ("PRS-CSNKP", "PRS-CSR", None)]
    assert all(r == results[0] for r in results)


def test_missing_first_versus_missing_second_occurrence_both_held():
    only_second = new.join_rows([SECOND], [T6, T37])
    assert only_second["held"] == {"second": [6, 37]}


def test_verified_geometry_resolves_the_physical_row_and_scores_the_quantity_error():
    g6, g37 = dict(T6, y=980.5), dict(T37, y=2718.5)
    j = new.join_rows([FIRST], [g6, g37])
    assert j["pairs"] == [("first", 6, "matched_geometry")] and j["unmatched_truth"] == [37] and j["held"] == {}
    j2 = new.join_rows([SECOND], [g6, g37])
    assert j2["pairs"] == [("second", 37, "matched_geometry")] and j2["unmatched_truth"] == [6]


def test_extra_emitted_duplicate_is_visible():
    third = dict(FIRST, id="third", y=3000.0)
    j = new.join_rows([FIRST, SECOND, third], [T6, T37])
    paired = {p[0] for p in j["pairs"]}
    assert len(paired) + len(j["unmatched_emitted"]) == 3 and (j["unmatched_emitted"] or j["held"])


def test_shuffled_input_order_with_the_same_geometry_gives_the_same_join():
    rows = [FIRST, SECOND, dict(FIRST, id="cobra", y=788.0, description="Cobra Net Interface", part_number="LBB4404/00")]
    truth = [dict(T6), dict(T37), {"ordinal": 2, "page": 1, "part_number": "LBB4404/00", "quantity": "1", "description": "Cobra Net Interface"}]
    ref = new.join_rows(rows, truth)
    rng = random.Random(15)
    for _ in range(10):
        r, t = rows[:], truth[:]
        rng.shuffle(r)
        rng.shuffle(t)
        got = new.join_rows(r, t)
        assert sorted(got["pairs"]) == sorted(ref["pairs"]) and got["held"] == ref["held"]


def test_complete_two_row_control_still_matches_both():
    j = new.join_rows([FIRST, SECOND], [T6, T37])
    assert sorted(j["pairs"]) == [("first", 6, "matched"), ("second", 37, "matched")] and j["held"] == {}


def test_same_prefix_control_still_matches():
    emitted = [{"id": "a", "page": 1, "y": 1214, "part_number": None, "quantity": "1", "description": "Power Amplifier 8 X 60 W (EU)"},
               {"id": "b", "page": 1, "y": 1260, "part_number": None, "quantity": "1", "description": "Power Amplifier 4 X 125 W (EU)"}]
    truth = [{"ordinal": 11, "page": 1, "part_number": "LBB4428/00-EU", "quantity": "1", "description": "Power Amplifier 8 X 60 W (EU)"},
             {"ordinal": 12, "page": 1, "part_number": "PRS-4P125-EU", "quantity": "3", "description": "Power Amplifier 4 X 125 W (EU)"}]
    assert sorted(new.join_rows(emitted, truth)["pairs"]) == [("a", 11, "matched"), ("b", 12, "matched")]


def test_neighbouring_rows_anchor_a_sparse_duplicate_by_order():
    """With its printed neighbours present, the first keypad can only be row 6 in an order-preserving alignment."""
    truth = [{"ordinal": 5, "page": 1, "part_number": "LBB4430/00", "quantity": "1", "description": "Call Station Basic"}, T6,
             {"ordinal": 7, "page": 1, "part_number": "PRS-CSR", "quantity": "1", "description": "Remote Call Station"},
             {"ordinal": 36, "page": 1, "part_number": "LBB4430/00", "quantity": "2", "description": "Call Station Basic"}, T37,
             {"ordinal": 38, "page": 1, "part_number": "PRS-CSR", "quantity": "2", "description": "Remote Call Station"}]
    emitted = [{"id": "e5", "page": 1, "y": 931, "part_number": "LBB4430/00", "quantity": "4", "description": "Call Station Basic"}, FIRST,
               {"id": "e7", "page": 1, "y": 1026, "part_number": "PRS-CSR", "quantity": "1", "description": "Remote Call Station"},
               {"id": "e36", "page": 1, "y": 2669, "part_number": "LBB4430/00", "quantity": "2", "description": "Call Station Basic"},
               {"id": "e38", "page": 1, "y": 2763, "part_number": "PRS-CSR", "quantity": "2", "description": "Remote Call Station"}]
    j = new.join_rows(emitted, truth)
    assert ("first", 6, "matched") in j["pairs"] and j["unmatched_truth"] == [37]


def test_indistinguishable_rows_are_held():
    emitted = [{"id": "x", "page": 1, "y": 100, "part_number": "A-1", "quantity": "1", "description": "Widget"}]
    truth = [{"ordinal": 1, "page": 1, "part_number": "A-1", "quantity": "1", "description": "Widget"},
             {"ordinal": 2, "page": 1, "part_number": "A-1", "quantity": "1", "description": "Widget"}]
    assert new.join_rows(emitted, truth)["held"] == {"x": [1, 2]}


def test_value_comparisons_are_unchanged_from_r14():
    for a, b in (("PT-1S", "PT-1S+"), ("PRS-X", "PRS-X")):
        assert new.parts_equal(a, b) == old.parts_equal(a, b)
    for a, b in (("1.0", "10"), ("-1", "1"), (0, None), ("1", "1.0"), ("?", "?"), ("1 no.", "1")):
        assert new.quantities_equal(a, b) == old.quantities_equal(a, b)
