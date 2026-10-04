"""tripwire_r32: facts from an application row through the frozen evaluator .10 emission functions, and the per-field
attribution of criticals (resolved stops, unresolved reports). Synthetic rows only. Run: python -m pytest -q test_tripwire_r32.py"""
import json
import subprocess
import sys

import pytest

import r32_test_helpers as H
import tripwire_r32 as TW


@pytest.fixture(scope="module")
def EV():
    return TW.load_evaluator()


def row(reference, revision, status, page=1):
    return {"sha256": "x" * 64, "state": "fresh", "extracted": {"records": [{"page": page, "reference": reference, "revision": revision,
                                                                            "printed_revision": revision, "revision_source": "printed", "status": status,
                                                                            "flags": [], "decision_candidates": []}]}}


def test_register_records_become_accepted_facts(EV):
    f = TW.facts_from_row(EV, row("ID-3", "01", "approved"), None, None)
    got = {(x["field"], x["state"]) for x in f}
    assert ("identity", "accepted") in got and ("revision", "accepted") in got and ("decision", "accepted") in got
    assert all(x["page"] == "1" for x in f)


def test_a_wrong_accepted_value_is_a_resolved_critical_attributed_to_its_field(EV):
    T = H.truth(n=4, projects=2)
    f = TW.facts_from_row(EV, row("ID-3", "07", "approved"), None, None)
    res = TW.tripwire(T, "D03", f)
    assert [(c["pool_id"], c["page"], c["field"]) for c in res["resolved"]] == [("D03", "1", "revision")]
    assert res["fields"]["revision"]["critical"] == 1 and res["fields"]["identity"]["critical"] == 0


def test_a_not_scorable_row_gives_an_unresolved_report_never_a_resolved_critical(EV):
    T = H.truth(n=4, projects=2)
    T["rows"]["D03|1|revision"] = H.row("D03", 1, "revision", "not_scorable", candidates=["00", "01"])
    res = TW.tripwire(T, "D03", TW.facts_from_row(EV, row("ID-3", "07", "approved"), None, None))
    assert res["resolved"] == [] and [u["field"] for u in res["unresolved"]] == ["revision"]


def test_a_correct_row_is_quiet_and_held_values_never_trip(EV):
    T = H.truth(n=4, projects=2)
    assert TW.tripwire(T, "D03", TW.facts_from_row(EV, row("ID-3", "01", "approved"), None, None))["resolved"] == []
    held = {"extracted": {"observations": [{"kind": "decision_unpromoted", "page": 1, "candidates": [{"status": "rejected"}]}]}}
    assert TW.tripwire(T, "D03", TW.facts_from_row(EV, held, None, None))["resolved"] == []


def test_the_cli_used_by_lane_b(tmp_path):
    T = H.truth(n=4, projects=2)
    tp, rp, op = tmp_path / "t.json", tmp_path / "r.json", tmp_path / "o.json"
    tp.write_text(json.dumps(T), encoding="utf-8", newline="\n")
    rp.write_text(json.dumps({"D01": row("ID-1", "01", "approved"), "D02": row("WRONG", "01", "approved")}), encoding="utf-8", newline="\n")
    r = subprocess.run([sys.executable, str(TW.pathlib.Path(TW.__file__).resolve()), str(tp), str(rp), str(op)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = json.loads(op.read_text(encoding="utf-8"))
    assert out["D01"]["resolved"] == [] and [c["field"] for c in out["D02"]["resolved"]] == ["identity"]
