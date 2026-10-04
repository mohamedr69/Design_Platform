"""project_bounds_r32 (ORCH-08 / ORCH-08C, A-09 point 1, R38-08, R39-04, R39-16): per-project request bounds across B -> C -> R -> P from the run set and
the HARD application bounds, and the compatible limits. The frozen run set and truth only; no request.
Run: python -m pytest -q test_project_bounds_r32.py"""
import copy
import hashlib
import json
import pathlib

import pytest

import preflight_r32 as PF
import project_bounds_r32 as PB
import r32_test_helpers as H
import runner_r32 as RN

RUN_SET = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review34/RUN-SET-PROPOSAL.json"


@pytest.fixture(scope="module")
def real():
    T = PF.build_truth()
    rs = PF.load_run_set(RUN_SET, T)
    return T, rs, PB.compute(rs, T, RN.DRY_LANE_SWITCHES, window_limit=60, window_s=86400, elapsed_s=604800)


def test_the_hard_bounds_are_read_from_the_bound_code():
    c = PB.code_constants()
    assert (c["max_pages_per_document"], c["reader_soft_calls_per_document"], c["decision_reads_per_page"]) == (4, 8, 3)
    assert (c["ai_max_calls_per_document"], c["ai_max_elapsed_s_per_job"], c["ai_max_calls_per_project_per_day"]) == (12, 120, 60)
    assert (c["ai_read_max_calls_per_project_per_day"], c["b_pages_to_read"]) == (600, 2)


def test_a_changed_bound_source_is_a_packet_mismatch(monkeypatch, tmp_path):
    p = tmp_path / "evidence_reader.py"
    p.write_text("MAX_PAGES_PER_DOCUMENT = 4\n", encoding="utf-8")
    monkeypatch.setitem(PB.SOURCES, "candidate/app/ai/evidence_reader.py", (p, "0" * 64))
    with pytest.raises(PB.PacketMismatch, match="PACKET MISMATCH"):
        PB.code_constants()


def test_per_page_and_per_document_maxima_under_the_declared_switches():
    c = PB.code_constants()
    sw = RN.DRY_LANE_SWITCHES
    assert PB.per_page_max(sw["C"], c) == 9, "discover 1 + identity 1 + revision 1 + locate_decision 1 + read_decision 3 + targeted 2"
    assert PB.per_page_max(sw["R"], c) == 6, "discover 1 + identity 1 + revision 1 + decision 1 + targeted 2"
    assert PB.per_page_max(sw["B"], c) == 0
    assert [PB.document_max(n, sw["C"], c) for n in (1, 2, 3, 4)] == [9, 12, 12, 12], "the reader's 8 is checked between pages: 12 binds"
    assert [PB.document_max(n, sw["R"], c) for n in (1, 2, 3, 4)] == [6, 12, 12, 12]
    assert PB.document_max(1, dict(sw["C"], AI_EVIDENCE_VARIANT="EV2"), c) == 11, "EV2 adds at most 2 escalations per document"


def test_planning_reproduces_the_frozen_orch07_model_and_structural_bounds_exceed_it(real):
    T, rs, b = real
    p = b["projects"]["EP-27331"]
    assert p["planning"] == {"B": 6, "C": 46, "R": 4.1, "P": 6.9, "all_lanes": 63.0}, "declaration-r32's EP-27331 planning (63.0)"
    # ORCH-08C (R39-16): B's reconcile repeat of a FAILED read is dispatched again -> B 2 per document (r38: 1; 154 -> 160)
    assert p["structural_maximum"] == {"B": 12, "C": 72, "R": 40, "P": 36, "all_lanes": 160}
    assert p["structural_before_lane_caps"] == {"B": 12, "C": 72, "R": 72, "P": 36}
    assert p["change_from_r38_model"]["r38_structural_all_lanes"] == 154 and p["change_from_r38_model"]["B_reconcile_retry"] == 6
    # ORCH-08C (R39-04): the drawings-AI path is disabled (counted 0); the enabled alternative is stated for the record
    assert p["drawings_ai"]["if_enabled"] == {"B_add_per_invocation": 10, "structural_all_lanes": 170, "windows_needed": 3,
                                              "r38_model_all_lanes": 164, "application_rows_added": 0}
    assert p["planning_exceeds_window"] and p["structural_exceeds_window"] and p["windows_needed_structural"] == 3
    assert {k: v["planning"]["all_lanes"] for k, v in b["projects"].items()} == {"EP-3563": 17.9, "EP-15744": 9.9, "EP-22349": 29.3,
                                                                              "EP-26687": 25.3, "EP-27331": 63.0, "EP-29255": 9.4}
    assert b["lanes"]["C"]["cap_can_bind"] and b["lanes"]["C"]["structural_sum_before_cap"] == 255 and not b["lanes"]["B"]["cap_can_bind"]


def test_the_required_application_limit_counts_rows_in_one_lane_database(real):
    T, rs, b = real
    app = b["projects"]["EP-27331"]["application_rows_maximum"]
    assert app == {"B_database": 12, "C_database": 84, "R_database": 84, "P": 0, "max": 84}, "R's served answers write rows too"
    assert b["compatible_limits"]["required_minimum"] == {"AI_MAX_CALLS_PER_PROJECT_PER_DAY": 84, "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY": 84}
    assert b["compatible_limits"]["binding_project"] == "EP-27331" and b["compatible_limits"]["tree_defaults"]["AI_MAX_CALLS_PER_PROJECT_PER_DAY"] == 60


def test_check_compatible(real):
    T, rs, b = real
    env = {"AI_MAX_CALLS_PER_PROJECT_PER_DAY": "84", "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY": "600", "AI_MAX_CALLS_PER_DOCUMENT": "12",
           "AI_MAX_ELAPSED_S_PER_JOB": "120.0"}
    assert PB.check_compatible(env, b) == []
    assert any("could refuse before the harness" in x for x in PB.check_compatible(env | {"AI_MAX_CALLS_PER_PROJECT_PER_DAY": "60"}, b))
    assert any("could refuse" in x for x in PB.check_compatible(env | {"AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY": "x"}, b))
    assert any("bounds assume 12" in x for x in PB.check_compatible(env | {"AI_MAX_CALLS_PER_DOCUMENT": "20"}, b))
    short = PB.compute(rs, T, RN.DRY_LANE_SWITCHES, window_limit=60, window_s=86400, elapsed_s=3600)
    assert any("cannot complete within the elapsed bound" in x for x in PB.check_compatible(env, short))


def test_the_bounds_are_deterministic_and_the_cli_writes_them(real, tmp_path):
    T, rs, b = real
    assert PB.compute(rs, T, RN.DRY_LANE_SWITCHES, window_limit=60, window_s=86400, elapsed_s=604800) == b
    out = tmp_path / "PROJECT-REQUEST-BOUNDS.json"
    assert PB.main(["x", RUN_SET, str(out)]) == 0
    x = json.loads(out.read_text(encoding="utf-8"))
    assert x["projects"] == b["projects"] and x["run_set"]["sha256"] == hashlib.sha256(pathlib.Path(RUN_SET).read_bytes()).hexdigest()
    assert out.read_text(encoding="utf-8") == PB.text(x)


def test_a_project_window_below_the_planning_needs_more_windows(real):
    T, rs, _ = real
    b = PB.compute(rs, T, RN.DRY_LANE_SWITCHES, window_limit=20, window_s=86400, elapsed_s=604800)
    assert b["projects"]["EP-27331"]["windows_needed_structural"] == 8 and b["projects"]["EP-27331"]["fits_elapsed_bound"] is False
    assert b["projects"]["EP-15744"]["fits_elapsed_bound"] is True


def test_the_helper_bounds_equal_the_module(real):
    assert copy.deepcopy(H.bounds_for())["projects"] == real[2]["projects"]
