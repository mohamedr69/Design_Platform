"""run_set_selector_r32 (plan v2 section 2.3) on the real reference set and on synthetic pools.
Run: python -m pytest -q test_run_set_selector_r32.py"""
import copy

import pytest

import inputs_r32 as I
import labels_adapter_r32 as A
import r32_test_helpers as H
import run_set_selector_r32 as R


@pytest.fixture(scope="module")
def truth():
    x = I.load_all()
    return A.build_truth(x["reviewed2"], renders=x["renders"], source_manifest=x["source_manifest"], selection=x["selection"], verification=x["verification"])


def test_real_proposal_counts_and_shortfall(truth):
    p = R.build_proposal(truth, inputs={})
    assert p["count"] == 24 and p["by_reason"] == {"decision_bearing": 16, "top_up": 4, "negative_control": 4}
    assert {f: v["documents"] for f, v in p["per_field_matched_projection"].items()} == {"identity": 23, "revision": 16, "decision": 16}
    assert p["shortfalls"] == {"unsupported_controls": {"required": 2, "found": 0, "why": p["shortfalls"]["unsupported_controls"]["why"]}}
    assert p["status"].startswith("PROPOSAL")


def test_canonical_ids_only_and_deterministic(truth):
    a, b = R.select(truth), R.select(truth)
    assert a == b
    assert not set(a["picked"]) & set(truth["aliases"]), "no count-once alias is ever drawn"


def test_decision_bearing_first_sixteen_in_seeded_order(truth):
    s = R.select(truth)
    dec = sorted((d for d in truth["documents"].values() if not d["is_alias"] and A.has_fact(truth, d["pool_id"], "decision")), key=R.order_key)
    assert [p for p in s["picked"] if s["reasons"][p] == "decision_bearing"] == [d["pool_id"] for d in dec[:16]]


def test_negative_controls_follow_the_executable_definition(truth):
    s = R.select(truth)
    for p in (p for p in s["picked"] if s["reasons"][p] == "negative_control"):
        rows = [r for r in A.doc_rows(truth, p, "decision") if int(r["page"]) <= truth["documents"][p]["in_scope_pages"]]
        assert rows and all(r["truth_kind"] == "absent" and r["absent_kind"] in ("blank_decision_area", "no_decision_area") for r in rows)
        assert truth["documents"][p]["fields"]["decision"]["resolved_for_scoring"] == "yes"


def test_a_different_seed_gives_a_different_order(truth):
    other = dict(R.RULE, seed="another-seed")
    assert R.select(truth, other)["picked"] != R.select(truth)["picked"]


def test_unsupported_controls_are_drawn_when_the_labels_have_them(truth):
    t = copy.deepcopy(truth)
    for pid in ("F064", "F071"):
        t["rows"][f"{pid}|2|identity"]["state"] = "illegible"
    s = R.select(t)
    assert sorted(p for p in s["picked"] if s["reasons"][p] == "unsupported_control") == ["F064", "F071"]
    assert "unsupported_controls" not in s["shortfalls"]


def test_cap_of_thirty_and_top_up_limit_on_a_large_synthetic_pool():
    T = H.truth(n=40, projects=5, negatives=10)
    for i in range(40):                                  # 40 decision documents, none carrying revision
        T["documents"][f"D{i:02d}"]["fields"]["revision"]["has_fact"] = False
    for j in range(10):
        T["documents"][f"N{j:02d}"]["fields"]["revision"]["has_fact"] = True
    for d in T["documents"].values():
        d["ep"], d["relative_path"] = d["project"], d["pool_id"] + ".pdf"
    s = R.select(T)
    assert len(s["picked"]) <= 30
    assert sum(1 for p in s["picked"] if s["reasons"][p] == "decision_bearing") == 16
    assert sum(1 for p in s["picked"] if s["reasons"][p].startswith("top_up")) == 8, "at most 8 top-ups"
    assert s["shortfalls"]["top_up_target"]["short"] == {"revision": 6}, "8 top-ups + 2 negative controls carry revision: deficit 6, recorded"


def test_no_control_is_replaced_once_a_prediction_exists_for_the_run(truth, tmp_path):
    """ORCH-08 (A-09 point 5): the unsupported-control shortfall stays a declared scope limitation; the selector refuses any
    replacement once the run has a prediction (an invocation, a request row or lane rows)."""
    import json
    import sqlite3

    p = R.build_proposal(truth, inputs={})
    t = copy.deepcopy(truth)
    for pid in ("F064", "F071"):
        t["rows"][f"{pid}|2|identity"]["state"] = "illegible"
    run = tmp_path / "run"
    run.mkdir()
    assert R.prediction_evidence(run) == []
    ok = R.replace_controls(t, p, ["F064"], run_folder=run)          # before any prediction: the definition is checked, nothing is frozen
    assert ok["replacements"] == ["F064"]
    with pytest.raises(R.ReplacementRefused, match="not an eligible unsupported control"):
        R.replace_controls(truth, p, ["F064"], run_folder=run)
    def capture_row(folder):
        con = sqlite3.connect(str(folder / "capture.sqlite"))
        con.executescript("create table requests (seq integer); insert into requests values (1);")
        con.close()

    makers = {"state": lambda f: (f / "RUN-STATE.json").write_text(json.dumps({"invocations": [{"n": 1}]}), encoding="utf-8"),
              "capture": capture_row,
              "rows": lambda f: (f / "inv-1" / "out").mkdir(parents=True) or (f / "inv-1" / "out" / "rows-C.json").write_text("{}", encoding="utf-8")}
    for name, make in makers.items():
        folder = tmp_path / name
        folder.mkdir()
        make(folder)
        assert R.prediction_evidence(folder), name
        with pytest.raises(R.ReplacementRefused, match="a prediction exists for this run"):
            R.replace_controls(t, p, ["F064", "F071"], run_folder=folder)


def test_top_up_stops_once_both_fields_reach_sixteen():
    T = H.truth(n=16, projects=4, negatives=6)
    for d in T["documents"].values():
        d["ep"], d["relative_path"] = d["project"], d["pool_id"] + ".pdf"
    for j in range(6):
        T["documents"][f"N{j:02d}"]["fields"]["revision"]["has_fact"] = True
    s = R.select(T)
    assert not any(r.startswith("top_up") for r in s["reasons"].values()), "16 decision documents already carry identity and revision"
