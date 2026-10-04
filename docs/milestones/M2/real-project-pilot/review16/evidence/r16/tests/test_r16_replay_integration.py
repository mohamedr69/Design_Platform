"""R16-02 through the ACTUAL replay / reporting path (replay_core.replay_sheet, the function replay_boq_r16.py calls):
a synthetic stored verification run over a synthetic extraction and verified truth. Geometry-ambiguous rows stay
held (candidates, reason, no credit) in row outcomes, summary counts and accounting; controls: a genuine extra row,
a genuinely missed truth row, an unambiguous geometry match. The submitted r15.1 consumer reports the held rows as
extra rows."""
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _budget_env as env  # noqa: E402

bc = env.load(env.CORRECTED, "boq_contract")
rc = env.load(env.CORRECTED, "replay_core")
R15 = Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review15/evidence/r15")


def line(y, desc, part, qty):
    return {"page": 1, "y_px": y, "catalog_no": part, "description": desc, "quantity": qty}


EXTRACTION = {"lines": [line(95, "Speaker", "PT-1S", "1"), line(105, "Speaker", "PT-1S", "1"),     # a / b: both near verified row 6
                        line(300, "Amplifier", "AMP-1", "4"),                                     # unambiguous geometry match (truth 8, qty 1)
                        line(700, "Coffee machine", "CM-9", "1")],                                # genuine extra
              "issues": []}
TRUTH = [{"page": 1, "ordinal": 6, "y": 100, "description": "Speaker", "part_number": "PT-1S", "quantity": "1"},
         {"page": 1, "ordinal": 8, "y": 300, "description": "Amplifier", "part_number": "AMP-1", "quantity": "1"},
         {"page": 1, "ordinal": 9, "y": 500, "description": "Volume control", "part_number": "VC-2", "quantity": "2"}]   # genuinely missed


def stored(y, qty, state="validated", blind_qty="1", part="PT-1S", desc="Speaker"):
    return {"page": 1, "row": {"part_number": part, "quantity": qty, "description": desc, "row_bounds": None, "y_px": y},
            "accepted_by_reader": True, "state": state, "blind": {"part_number": part, "quantity": blind_qty, "description": desc}}


STORED = [stored(95, "1"), stored(105, "1"), stored(300, "4", state="conflict", part="AMP-1", desc="Amplifier"),
          stored(700, "1", part="CM-9", desc="Coffee machine")]


def run():
    return rc.replay_sheet(STORED, rc.build_emitted(EXTRACTION), TRUTH, bc)


def test_geometry_held_rows_stay_held_with_candidates_and_no_credit():
    res = run()
    by = {r["request_order"]: r for r in res["rows"]}
    for n in (1, 2):
        r = by[n]
        assert r["outcome"] == "held_ambiguous_join" and r["join"] == "held" and r["held_candidates"] == [6]
        assert "geometry" in r["held_reason"] and r["truth"] is None and r["reader_right"] is None and r["blind_right"] is None


def test_controls_extra_missed_and_unambiguous_geometry():
    res = run()
    by = {r["request_order"]: r for r in res["rows"]}
    assert by[3]["join"] == "matched_geometry" and by[3]["truth_ordinal"] == 8 and by[3]["outcome"] == "caught_wrong_accepted"
    assert by[4]["outcome"] == "extra_row" and by[4]["join"] == "unmatched"
    assert res["join"]["unmatched_truth"] == [9]


def test_summary_counts_and_accounting_keep_the_held_rows():
    res = run()
    assert res["outcomes"] == {"held_ambiguous_join": 2, "caught_wrong_accepted": 1, "extra_row": 1}
    a = res["accounting"]
    assert a["emitted"] == {"total": 4, "matched": 1, "held": 2, "unmatched": 1, "complete_and_disjoint": True}
    assert a["truth"] == {"total": 3, "matched": 1, "held_candidate": 1, "missed": 1, "complete": True}


def test_replay_script_uses_this_path():
    src = (Path(env.CORRECTED) / "replay_boq_r16.py").read_text(encoding="utf-8")
    assert "rc.replay_sheet(" in src and "rc.build_emitted(" in src


def test_submitted_r15_consumer_reports_the_held_rows_as_extra():
    """The Review 16 defect: r15.1's replay looked only at pairs, so geometry-held rows became extra_row."""
    b15 = env.load(R15, "boq_contract")
    tree = ast.parse((R15 / "replay_boq_r15.py").read_text(encoding="utf-8"))
    ns = {}
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "classify"], type_ignores=[]), "replay_boq_r15.py", "exec"), ns)
    emitted = rc.build_emitted(EXTRACTION)
    j = b15.join_rows(emitted, TRUTH)
    pair_of = {e: (t, st) for e, t, st in j["pairs"]}
    outcomes = [ns["classify"](s, None, pair_of.get(e["id"], (None, None))[1], None, None) for s, e in zip(STORED[:2], emitted[:2])]
    assert j["held"] == {"L0": [6], "L1": [6]} and outcomes == ["extra_row", "extra_row"]
