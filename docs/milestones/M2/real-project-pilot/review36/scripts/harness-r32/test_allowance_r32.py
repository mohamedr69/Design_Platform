"""allowance_r32: reserve-before-dispatch lane caps, never raised; the project-day limit across lanes; durable across
instances; (Review 34 RC-4 / R34-04) ONE allowance per run key, its caps and day limit bound in the file, never fresh caps
for a second invocation; the capture store bound to the same key. Run: python -m pytest -q test_allowance_r32.py"""
import sqlite3

import pytest

import allowance_r32 as AL

KEY = "a" * 64


class Resp:
    def __init__(self, data=None, model="", error=None, error_detail=None, **kw):
        self.data, self.error = data, error


def test_lane_caps_are_enforced_and_durable(tmp_path):
    a = AL.LaneAllowance(tmp_path / "a.sqlite", {"B": 2, "C": 2, "R": 1, "P": 1}, run_key=KEY)
    a.charge("B", "1")
    a.charge("B", "1")
    with pytest.raises(AL.AllowanceRefused, match="allowance 2 used"):
        a.charge("B", "1")
    b = AL.LaneAllowance(tmp_path / "a.sqlite", {"B": 2, "C": 2, "R": 1, "P": 1}, run_key=KEY, create=False)
    assert b.used("B") == 2, "a new process sees the charges"
    with pytest.raises(AL.AllowanceRefused):
        b.charge("B", "1")


def test_a_cap_is_never_raised(tmp_path):
    AL.LaneAllowance(tmp_path / "a.sqlite", {"B": 2}, run_key=KEY)
    with pytest.raises(AL.AllowanceRefused, match="bound to another run or other limits"):
        AL.LaneAllowance(tmp_path / "a.sqlite", {"B": 3}, run_key=KEY)


def test_the_project_day_limit_counts_every_lane(tmp_path):
    a = AL.LaneAllowance(tmp_path / "a.sqlite", {"B": 10, "C": 10}, project_day_limit=3, run_key=KEY)
    a.charge("B", "3563")
    a.charge("C", "3563")
    a.charge("C", "3563")
    with pytest.raises(AL.AllowanceRefused, match="UTC-day limit 3"):
        a.charge("B", "3563")
    a.charge("B", "15744")


def test_the_default_caps_are_the_plan_caps():
    assert AL.CAPS == {"B": 240, "C": 240, "R": 40, "P": 36} and sum(AL.CAPS.values()) == 556 and AL.PROJECT_DAY_LIMIT == 60


def test_the_allowance_provider_charges_before_the_inner_and_refuses_without_calling_it(tmp_path):
    a = AL.LaneAllowance(tmp_path / "a.sqlite", {"C": 1}, run_key=KEY)
    calls = []

    class Inner:
        def complete(self, request):
            calls.append(request)
            return Resp(data={})

    p = AL.AllowanceProvider(a, "C", Inner(), Resp, ep_of=lambda: "1")
    assert p.complete("r1").error is None and calls == ["r1"]
    assert p.complete("r2").error == "allowance_refused" and calls == ["r1"] and p.refused == 1


# ---- RC-4 -----------------------------------------------------------------------------------------------------------------
def test_an_allowance_is_bound_to_one_run_key_and_refuses_another(tmp_path):
    AL.LaneAllowance(tmp_path / "a.sqlite", {"B": 2}, run_key=KEY)
    with pytest.raises(AL.AllowanceRefused, match="bound to another run"):
        AL.LaneAllowance(tmp_path / "a.sqlite", {"B": 2}, run_key="b" * 64)
    with pytest.raises(AL.AllowanceRefused, match="always bound to a run key"):
        AL.LaneAllowance(tmp_path / "x.sqlite", {"B": 2}, run_key="")


def test_the_day_limit_is_bound_in_the_file_and_never_changed(tmp_path):
    AL.LaneAllowance(tmp_path / "a.sqlite", {"B": 2}, project_day_limit=60, run_key=KEY)
    with pytest.raises(AL.AllowanceRefused, match="project_day_limit"):
        AL.LaneAllowance(tmp_path / "a.sqlite", {"B": 2}, project_day_limit=61, run_key=KEY)


def test_a_second_invocation_reopens_the_same_counts_and_never_gets_fresh_caps(tmp_path):
    caps = {"B": 3, "C": 3, "R": 1, "P": 1}
    first = AL.LaneAllowance(tmp_path / "a.sqlite", caps, run_key=KEY)
    first.charge("C", "1")
    first.charge("C", "1")
    second = AL.LaneAllowance(tmp_path / "a.sqlite", caps, run_key=KEY, create=False)
    assert second.used("C") == 2 and second.caps_fixed() == caps
    second.charge("C", "1")
    with pytest.raises(AL.AllowanceRefused, match="allowance 3 used"):
        second.charge("C", "1")
    con = sqlite3.connect(str(tmp_path / "a.sqlite"))
    assert con.execute("select count(*) from caps").fetchone()[0] == 4 and con.execute("select count(*) from charges").fetchone()[0] == 3
    con.close()


def test_a_lane_never_creates_the_allowance(tmp_path):
    with pytest.raises(AL.AllowanceRefused, match="never creates"):
        AL.LaneAllowance(tmp_path / "missing.sqlite", {"B": 1}, run_key=KEY, create=False)


def test_live_refuses_an_unattributed_request(tmp_path):
    a = AL.LaneAllowance(tmp_path / "a.sqlite", {"P": 2}, run_key=KEY, require_project=True)
    with pytest.raises(AL.AllowanceRefused, match="cannot be attributed to a project"):
        a.charge("P", None)
    assert a.used() == 0


def test_the_capture_store_file_is_bound_to_the_same_run_key(tmp_path):
    p = tmp_path / "capture.sqlite"
    assert AL.bind_store(p, KEY) == {"created": True}
    assert AL.bind_store(p, KEY) == {"created": False} and AL.bound_key(p) == KEY
    with pytest.raises(AL.AllowanceRefused, match="bound to another run"):
        AL.bind_store(p, "c" * 64)
