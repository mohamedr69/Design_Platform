"""R16-01: verified source rows bound every confirmed association on the page (contract r16.1). The GLOBAL property is
asserted -- no confirmed pair crosses any verified row -- on the reviewer's cases, mixed pages, shuffled inputs and a
seeded randomized family of pages; plus the controls (above-anchor, value independence, duplicates, contradictions)."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _budget_env as env  # noqa: E402

bc = env.load(env.CORRECTED, "boq_contract")
r15 = env.load(Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review15/evidence/r15"), "boq_contract")


def crossings(result, emitted, truth):
    """Confirmed pairs that put an emitted row on one side of a verified row and its truth on the other."""
    ey = {e["id"]: e["y"] for e in emitted}
    anchors = [(t["ordinal"], t["y"]) for t in truth if t.get("y") is not None]
    bad = []
    for eid, ordinal, state in result["pairs"]:
        if not state.startswith("matched") or eid in result["held"]:
            continue
        for ao, ay in anchors:
            if ordinal == ao:
                continue
            if (ey[eid] < ay) != (ordinal < ao):
                bad.append((eid, ordinal, ao))
    return bad


def reviewer_rows():
    truth = [dict(page=1, ordinal=1, description="Manual call point", part_number="MCP", quantity=1),
             dict(page=1, ordinal=2, y=200, description="Control panel", part_number="PANEL", quantity=1),
             dict(page=1, ordinal=3, description="Manual call point with cover", part_number="MCP", quantity=2)]
    anchor = dict(page=1, id="anchor", y=200, description="Control panel", part_number="PANEL", quantity=1)
    below = dict(page=1, id="below-anchor", y=300, description="Manual call point", part_number="MCP", quantity=1)
    return truth, anchor, below


def test_submitted_r15_crosses_the_verified_row():
    truth, anchor, below = reviewer_rows()
    for emitted in ([anchor, below], [below]):
        assert crossings(r15.join_rows(emitted, truth), emitted, truth)          # the Review 16 defect


def test_lower_row_never_takes_ordinal_1_with_or_without_the_middle_row():
    truth, anchor, below = reviewer_rows()
    for emitted in ([anchor, below], [below]):
        j = bc.join_rows(emitted, truth)
        assert not crossings(j, emitted, truth)
        assert ("below-anchor", 1, "matched") not in j["pairs"]
        assert ("below-anchor", 3, "matched") in j["pairs"] or "below-anchor" in j["held"]
        assert 1 in j["unmatched_truth"]
    assert 2 in bc.join_rows([below], truth)["unmatched_truth"]                  # the verified row itself: missed, still a boundary


def test_above_anchor_control_in_both_input_orders():
    truth, anchor, above = reviewer_rows()
    above.update(id="above-anchor", y=100)
    for rev in (False, True):
        t, e = truth[:], [above, anchor]
        if rev:
            t.reverse()
            e.reverse()
        j = bc.join_rows(e, t)
        assert ("above-anchor", 1, "matched") in j["pairs"] and ("anchor", 2, "matched_geometry") in j["pairs"]


def test_scored_values_do_not_change_the_join():
    truth, anchor, below = reviewer_rows()
    first = bc.join_rows([anchor, below], truth)
    for qty, part in ((2, "MCP"), (0, "OTHER"), (None, None), ("?", "PANEL")):
        assert bc.join_rows([anchor, dict(below, quantity=qty, part_number=part)], truth) == first


def _mixed_page():
    truth = [dict(page=1, ordinal=1, description="Smoke detector"), dict(page=1, ordinal=2, description="Heat detector"),
             dict(page=1, ordinal=3, y=300, description="Fire alarm panel"), dict(page=1, ordinal=4, description="Smoke detector"),
             dict(page=1, ordinal=5, description="Sounder beacon"), dict(page=1, ordinal=6, y=600, description="Battery"),
             dict(page=1, ordinal=7, description="Smoke detector"), dict(page=1, ordinal=8, description="Heat detector")]
    emitted = [dict(page=1, id="e1", y=100, description="Smoke detector"), dict(page=1, id="e4", y=400, description="Smoke detector"),
               dict(page=1, id="e5", y=500, description="Sounder beacon"), dict(page=1, id="e8", y=800, description="Heat detector"),
               dict(page=1, id="e-panel", y=301, description="Fire alarm panel")]
    for x in truth + emitted:
        x.setdefault("part_number", "P")
        x.setdefault("quantity", "1")
    return truth, emitted


def test_mixed_geometry_and_fallback_rows_respect_every_boundary():
    truth, emitted = _mixed_page()
    j = bc.join_rows(emitted, truth)
    assert not crossings(j, emitted, truth)
    got = {p[0]: p[1] for p in j["pairs"] if p[2].startswith("matched")}
    assert got == {"e1": 1, "e4": 4, "e5": 5, "e8": 8, "e-panel": 3}
    assert sorted(j["unmatched_truth"]) == [2, 6, 7]                           # 6: verified, nothing emitted there


def test_shuffled_input_gives_the_same_join():
    truth, emitted = _mixed_page()
    ref = bc.join_rows(emitted, truth)
    rng = random.Random(16)
    for _ in range(20):
        t, e = truth[:], emitted[:]
        rng.shuffle(t)
        rng.shuffle(e)
        j = bc.join_rows(e, t)
        assert sorted(j["pairs"]) == sorted(ref["pairs"]) and j["held"] == ref["held"] and sorted(j["unmatched_truth"]) == sorted(ref["unmatched_truth"])


def test_randomized_pages_never_cross_a_verified_row():
    rng = random.Random(1616)
    vocab = ["Smoke detector", "Heat detector", "Manual call point", "Sounder", "Control relay module", "Battery"]
    for _ in range(300):
        n = rng.randint(3, 14)
        truth = [dict(page=1, ordinal=i, description=rng.choice(vocab), part_number="X", quantity="1") for i in range(n)]
        ys = sorted(rng.sample(range(50, 50 * (n + 2), 7), n))
        for i in rng.sample(range(n), rng.randint(0, max(1, n // 3))):
            truth[i]["y"] = ys[i]
        emitted = []
        for i in range(n):
            if rng.random() < 0.7:
                emitted.append(dict(page=1, id=f"e{i}", y=ys[i] + rng.uniform(-3, 3),
                                    description=truth[i]["description"] if rng.random() < 0.85 else rng.choice(vocab), part_number="X", quantity="1"))
        j = bc.join_rows(emitted, truth)
        assert not crossings(j, emitted, truth), (truth, emitted, j)
        ids = {e["id"] for e in emitted}
        confirmed = {p[0] for p in j["pairs"] if p[2].startswith("matched") and p[0] not in j["held"]}
        assert confirmed | set(j["held"]) | set(j["unmatched_emitted"]) == ids


def test_sparse_and_full_duplicate_controls_unchanged():
    t6 = {"ordinal": 6, "page": 1, "description": "Numeric Keypad"}
    t37 = {"ordinal": 37, "page": 1, "description": "Numeric Keypad"}
    first = {"id": "first", "page": 1, "y": 980.5, "part_number": "PRS-CSNKP", "quantity": "2", "description": "Numeric Keypad"}
    second = dict(first, id="second", y=2718.5)
    assert bc.join_rows([first], [t6, t37])["held"] == {"first": [6, 37]}
    assert sorted(bc.join_rows([first, second], [t6, t37])["pairs"]) == [("first", 6, "matched"), ("second", 37, "matched")]


def test_contradictory_verified_positions_hold_the_page():
    truth = [dict(page=1, ordinal=1, y=500, description="A"), dict(page=1, ordinal=2, y=100, description="B")]
    emitted = [dict(page=1, id="x", y=100, description="B")]
    j = bc.join_rows(emitted, truth)
    assert j["pairs"] == [] and j["held"] == {"x": [1, 2]} and "contradict" in j["held_reasons"]["x"]


def test_value_comparisons_unchanged_from_r15():
    for a, b in (("PT-1S", "PT-1S+"), ("PRS-X", "PRS-X")):
        assert bc.parts_equal(a, b) == r15.parts_equal(a, b)
    for a, b in (("1.0", "10"), ("-1", "1"), (0, None), ("1", "1.0"), ("?", "?")):
        assert bc.quantities_equal(a, b) == r15.quantities_equal(a, b)
