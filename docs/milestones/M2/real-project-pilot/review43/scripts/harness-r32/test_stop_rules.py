"""R31-04 stop contract. Run: python -m pytest -q test_stop_rules.py (cwd harness)."""
from stop_rules import StopController


def test_a_resolved_critical_in_b_invalidates_the_comparison_and_blocks_c():
    s = StopController()
    st = s.observe("B", "critical", resolved=True, detail="x")
    assert st["lanes"]["B"]["state"] == "terminal" and st["comparison"].startswith("INVALID") and not s.can_dispatch("C")


def test_a_resolved_critical_in_c_is_a_valid_failed_safety_result():
    s = StopController()
    st = s.observe("C", "critical", resolved=True)
    assert st["lanes"]["C"]["state"] == "terminal" and st["comparison"].startswith("RESULT: candidate failed the safety gate")
    assert s.can_dispatch("B") and not s.can_dispatch("C")


def test_a_critical_in_the_reference_never_stops_a_live_arm():
    s = StopController()
    st = s.observe("R", "critical", resolved=True)
    assert st["comparison"] == "PENDING" and all(v["state"] == "running" for v in st["lanes"].values())
    assert st["findings"][0]["stop"] is False and "no live arm stopped" in st["findings"][0]["note"]


def test_unresolved_criticals_are_reported_not_stops():
    s = StopController()
    for lane in ("B", "C", "R", "P"):
        s.observe(lane, "critical", resolved=False)
    st = s.state()
    assert st["comparison"] == "PENDING" and len(st["findings"]) == 4 and all(v["state"] == "running" for v in st["lanes"].values())


def test_failure_streaks_are_per_lane():
    s = StopController()
    for _ in range(2):
        s.observe("C", "provider_failure")
    s.observe("R", "provider_failure")
    s.observe("P", "provider_failure")
    assert s.lanes["C"]["streak"] == 2 and s.lanes["C"]["state"] == "running", "reference / probe failures never count toward C"
    s.observe("C", "provider_failure")
    assert s.lanes["C"]["state"] == "terminal" and s.comparison.startswith("INCOMPLETE")


def test_an_ok_resets_the_streak_and_reference_lane_failures_stop_only_r():
    s = StopController()
    s.observe("C", "provider_failure")
    s.observe("C", "ok")
    assert s.lanes["C"]["streak"] == 0
    for _ in range(3):
        s.observe("R", "provider_failure")
    assert s.lanes["R"]["state"] == "terminal" and s.comparison == "PENDING" and s.can_dispatch("C")


def test_budget_refusals_are_budget_stops_never_raised():
    s = StopController()
    s.observe("C", "budget_refusal")
    assert s.lanes["C"]["state"] == "budget_stopped" and s.comparison.startswith("INCOMPLETE") and not s.can_dispatch("C")
    s.observe("C", "ok")
    assert s.lanes["C"]["state"] == "budget_stopped", "nothing re-opens a budget stop"


def test_three_b_failures_invalidate():
    s = StopController()
    for _ in range(3):
        s.observe("B", "provider_failure")
    assert s.comparison.startswith("INVALID") and not s.can_dispatch("C")
