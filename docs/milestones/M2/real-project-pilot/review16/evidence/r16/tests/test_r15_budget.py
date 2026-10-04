"""R15-01: interrupted, resumed, failed and concurrent use of one (scope, profile, document) allowance. Real child
processes are terminated inside a chunk. Scripted provider only; the frozen application's own JobBudget classes."""
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import _budget_env as env  # noqa: E402

CHILD = str(Path(env.__file__).resolve())


def _crash_child(code_dir, folder, after=5):
    p = subprocess.run([sys.executable, CHILD, "crash", str(code_dir), str(folder), str(after)], capture_output=True, text=True)
    assert p.returncode == 91, (p.returncode, p.stderr[-800:])


def test_submitted_harness_regrants_requests_lost_in_an_interrupted_chunk(tmp_path):
    """The Review 15 defect on the submitted r14.1 harness: 5 sent, 0 durable, 12 more on resume = 17 > 12."""
    _crash_child(env.SUBMITTED, tmp_path)
    assert env.provider_log_count(tmp_path) == 5
    bh = env.load(env.SUBMITTED, "boq_harness")
    assert bh.DocAllowance(str(tmp_path / "allowance.sqlite")).load("frozen-scope", "EV2", "same-document-sha")["calls"] == 0
    env.run_sheet(env.SUBMITTED, tmp_path)
    assert env.provider_log_count(tmp_path) == 17


def test_child_terminated_inside_a_chunk_then_fresh_process_resume_stays_within_12(tmp_path):
    _crash_child(env.CORRECTED, tmp_path)
    assert env.provider_log_count(tmp_path) == 5
    bh = env.load(env.CORRECTED, "boq_harness")
    al = bh.DocAllowance(str(tmp_path / "allowance.sqlite"))
    assert al.load("frozen-scope", "EV2", "same-document-sha")["calls"] == 5          # durable before the child died
    r = env.run_sheet(env.CORRECTED, tmp_path)
    assert r["sent"] == 7 and env.provider_log_count(tmp_path) == 12
    assert r["calls_before"] == 5 and r["calls_after"] == 12 and r["exhausted"] == "calls_per_document"
    assert len(r["interrupted_attempts_found"]) == 1                                   # the dead attempt is found ...
    statuses = [a["status"] for a in al.attempts("frozen-scope", "EV2", "same-document-sha")]
    assert statuses == ["interrupted", "stopped: calls_per_document"]                  # ... and labelled


def test_crash_at_the_cap_then_resume_sends_nothing(tmp_path):
    _crash_child(env.CORRECTED, tmp_path, after=12)
    r = env.run_sheet(env.CORRECTED, tmp_path)
    assert r["sent"] == 0 and env.provider_log_count(tmp_path) == 12
    assert all(x["state"] == "budget_refused" for x in r["results"])


def test_normal_completion_then_resume_sends_nothing(tmp_path):
    first = env.run_sheet(env.CORRECTED, tmp_path)
    second = env.run_sheet(env.CORRECTED, tmp_path)
    assert (first["sent"], second["sent"]) == (12, 0) and env.provider_log_count(tmp_path) == 12
    assert second["calls_before"] == 12 and second["interrupted_attempts_found"] == []


def test_failure_after_dispatch_is_consumed(tmp_path):
    r = env.run_sheet(env.CORRECTED, tmp_path, fail_at=3)
    assert r["sent"] == 12                                          # the failed request counted like any other
    assert sum(1 for x in r["results"] if x["state"] == "failed_after_dispatch") == 1
    assert env.run_sheet(env.CORRECTED, tmp_path)["sent"] == 0


def test_refusal_beyond_the_cap_keeps_earlier_evidence(tmp_path):
    r = env.run_sheet(env.CORRECTED, tmp_path, rows=25)
    states = [x["state"] for x in r["results"]]
    assert states[:12] == ["read"] * 12 and states[12:] == ["budget_refused"] * 13
    assert r["exhausted"] == "calls_per_document"


def test_a_second_live_writer_is_refused_and_can_proceed_after_the_holder_ends(tmp_path):
    p = subprocess.Popen([sys.executable, CHILD, "hold", str(env.CORRECTED), str(tmp_path), "6"])
    for _ in range(200):
        if (tmp_path / "holding").exists():
            break
        time.sleep(0.05)
    bh = env.load(env.CORRECTED, "boq_harness")
    with pytest.raises(bh.AllowanceBusy):
        env.run_sheet(env.CORRECTED, tmp_path)
    assert env.provider_log_count(tmp_path) == 0
    p.wait(timeout=30)
    assert env.run_sheet(env.CORRECTED, tmp_path)["sent"] == 12


def test_a_killed_lock_holder_does_not_block_for_ever(tmp_path):
    p = subprocess.Popen([sys.executable, CHILD, "hold", str(env.CORRECTED), str(tmp_path), "60"])
    for _ in range(200):
        if (tmp_path / "holding").exists():
            break
        time.sleep(0.05)
    p.kill()
    p.wait(timeout=30)
    assert env.run_sheet(env.CORRECTED, tmp_path)["sent"] == 12


def test_elapsed_basis_is_the_first_start_across_a_crash(tmp_path):
    _crash_child(env.CORRECTED, tmp_path)
    db = tmp_path / "allowance.sqlite"
    con = sqlite3.connect(db, isolation_level=None)
    first = con.execute("select first_started from allowance").fetchone()[0]
    con.execute("update allowance set first_started = ?", (first - 125,))            # the key started 125 s ago
    con.close()
    r = env.run_sheet(env.CORRECTED, tmp_path)
    assert r["sent"] == 0 and r["exhausted"] == "elapsed_time"


def test_escalations_are_durable_across_processes(tmp_path):
    r1 = env.run_sheet(env.CORRECTED, tmp_path, rows=1, escalate=True)
    r2 = env.run_sheet(env.CORRECTED, tmp_path, rows=1, escalate=True)
    r3 = env.run_sheet(env.CORRECTED, tmp_path, rows=1, escalate=True)
    assert (r1["sent"], r2["sent"], r3["sent"]) == (1, 1, 0) and r3["exhausted"] == "escalations_per_document"


def test_other_profiles_and_documents_have_their_own_allowance(tmp_path):
    env.run_sheet(env.CORRECTED, tmp_path)
    assert env.run_sheet(env.CORRECTED, tmp_path, profile="EV1")["sent"] == 12
