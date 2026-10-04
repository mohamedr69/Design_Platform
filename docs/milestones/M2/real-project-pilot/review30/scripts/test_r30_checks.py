"""The R30-01 checks fail on the stale cases and pass on the corrected documents. Run: python -m pytest -q test_r30_checks.py
(cwd C:/t/iso/work/r2x/r30). Uses the REAL Review 29 package documents (read-only) and its JUnit evidence."""
import pathlib

import r30_checks as C

R29 = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review29")
_HERE = pathlib.Path(__file__).resolve().parent
OVERLAY = next(p for p in (_HERE / "pkg-src" / "review29-overlay", _HERE.parent / "review29-overlay") if p.exists())   # work folder or package
FINAL = "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d"
KNOWN = ["a4ce6a3", FINAL]
JUNIT = C.junit_module_counts(R29 / "tests" / "FOCUSED-final.xml")


def test_junit_counts_are_the_collected_ones():
    assert {k: v for k, v in JUNIT.items() if k.startswith("test_r29_")} == {
        "test_r29_identity_guard": 40, "test_r29_adjudication": 20, "test_r29_decision_region": 14, "test_r29_association": 6, "test_r29_persistence": 12}


def test_stale_commit_statement_fails():
    bad = {"x.md": "**Candidate tree.** The candidate is `C:/t/iso/cand-r29`, commit **`a4ce6a3`**. Its parent is `719e8de`."}
    v = C.check_commit_statements(bad, FINAL, KNOWN)
    assert v and v[0]["commits"] == ["a4ce6a3"]


def test_a_historical_commit_presented_as_final_fails_even_with_a_marker():
    bad = {"x.md": "The final candidate is `a4ce6a3` (its patch is kept)."}
    assert C.check_commit_statements(bad, FINAL, KNOWN)


def test_an_explicitly_historical_mention_passes_and_the_final_commit_passes():
    ok = {"x.md": "The first candidate commit `a4ce6a3` and its contract freeze are kept as history.\n"
                  "The final candidate is `a8aaced`.\nThe earlier run on `a4ce6a3` had the same two failures."}
    assert C.check_commit_statements(ok, FINAL, KNOWN) == []


def test_stale_count_fails_and_unknown_module_fails():
    bad = {"x.md": "| `backend/tests/test_r29_identity_guard.py` | New. 39 tests: C1 controls |\n| `test_r29_unknown.py` | 3 | x |"}
    v = C.check_test_counts(bad, JUNIT)
    assert {x["module"] for x in v} == {"test_r29_identity_guard", "test_r29_unknown"}


def test_suite_total_is_checked():
    assert C.check_test_counts({"x.md": "| Review 29 tests (91) | pass |"}, JUNIT)
    assert not C.check_test_counts({"x.md": "| Review 29 tests (92) | pass |"}, JUNIT)


def test_the_original_review29_change_map_fails_both_checks():
    text = {"CHANGE-MAP.md": (R29 / "CHANGE-MAP.md").read_text(encoding="utf-8")}
    assert C.check_commit_statements(text, FINAL, KNOWN), "the stale a4ce6a3 candidate statement is caught"
    assert {x["module"] for x in C.check_test_counts(text, JUNIT)} == {"test_r29_identity_guard", "test_r29_adjudication"}


def test_the_original_review29_commands_fails_the_commit_check():
    assert C.check_commit_statements({"COMMANDS.md": (R29 / "COMMANDS.md").read_text(encoding="utf-8")}, FINAL, KNOWN)


def test_the_corrected_overlay_passes_both_checks():
    texts = {p.name: p.read_text(encoding="utf-8") for p in OVERLAY.glob("*.md")}
    assert texts, "the overlay exists"
    assert C.check_commit_statements(texts, FINAL, KNOWN) == []
    assert C.check_test_counts(texts, JUNIT) == []


def test_the_unchanged_review29_documents_pass():
    for name in ("CORRECTION-REPORT.md", "TESTS-AND-REGRESSIONS.md", "OFFLINE-REPLAY.md", "CONTRACTS.md", "FRESH-VALIDATION-PLAN.md"):
        text = {name: (R29 / name).read_text(encoding="utf-8")}
        assert C.check_commit_statements(text, FINAL, KNOWN) == [], name
        assert C.check_test_counts(text, JUNIT) == [], name
