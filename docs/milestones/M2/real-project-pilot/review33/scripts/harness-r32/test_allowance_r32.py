"""allowance_r32: reserve-before-dispatch lane caps, never raised; the project day limit; durable across instances.
Run: python -m pytest -q test_allowance_r32.py"""
import pytest

import allowance_r32 as AL


class Resp:
    def __init__(self, data=None, model="", error=None, error_detail=None, **kw):
        self.data, self.error = data, error


def test_lane_caps_are_enforced_and_durable(tmp_path):
    a = AL.LaneAllowance(tmp_path / "a.sqlite", {"B": 2, "C": 2, "R": 1, "P": 1})
    a.charge("B", "1")
    a.charge("B", "1")
    with pytest.raises(AL.AllowanceRefused, match="allowance 2 used"):
        a.charge("B", "1")
    b = AL.LaneAllowance(tmp_path / "a.sqlite", {"B": 2, "C": 2, "R": 1, "P": 1})
    assert b.used("B") == 2, "a new process sees the charges"
    with pytest.raises(AL.AllowanceRefused):
        b.charge("B", "1")


def test_a_cap_is_never_raised(tmp_path):
    AL.LaneAllowance(tmp_path / "a.sqlite", {"B": 2})
    with pytest.raises(AL.AllowanceRefused, match="never raised"):
        AL.LaneAllowance(tmp_path / "a.sqlite", {"B": 3})


def test_the_project_day_limit_counts_every_lane(tmp_path):
    a = AL.LaneAllowance(tmp_path / "a.sqlite", {"B": 10, "C": 10}, project_day_limit=3)
    a.charge("B", "3563")
    a.charge("C", "3563")
    a.charge("C", "3563")
    with pytest.raises(AL.AllowanceRefused, match="day limit"):
        a.charge("B", "3563")
    a.charge("B", "15744")


def test_the_default_caps_are_the_plan_caps():
    assert AL.CAPS == {"B": 240, "C": 240, "R": 40, "P": 36} and sum(AL.CAPS.values()) == 556


def test_the_allowance_provider_charges_before_the_inner_and_refuses_without_calling_it(tmp_path):
    a = AL.LaneAllowance(tmp_path / "a.sqlite", {"C": 1})
    calls = []

    class Inner:
        def complete(self, request):
            calls.append(request)
            return Resp(data={})

    p = AL.AllowanceProvider(a, "C", Inner(), Resp, ep_of=lambda: "1")
    assert p.complete("r1").error is None and calls == ["r1"]
    assert p.complete("r2").error == "allowance_refused" and calls == ["r1"] and p.refused == 1
