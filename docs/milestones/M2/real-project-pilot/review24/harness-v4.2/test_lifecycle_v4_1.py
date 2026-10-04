"""Lifecycle regressions (R23-01) over lifecycle_probes.py evidence produced with the ACTUAL runner and the scripted
provider (no model request). Set R23_RUN_PROBES=1 to regenerate the evidence first."""
import json
import os
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
EV = HERE.parent / "lifecycle-evidence" / "LIFECYCLE.json"


@pytest.fixture(scope="module")
def S():
    if os.environ.get("R23_RUN_PROBES") == "1" or not EV.exists():
        p = subprocess.run([sys.executable, str(HERE / "lifecycle_probes.py")], cwd=str(HERE), capture_output=True, text=True, timeout=3000)
        assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-3000:]
    return json.loads(EV.read_text(encoding="utf-8"))["scenarios"]


def test_t1_critical_stop_survives_plain_resume_with_zero_sends(S):
    c = S["T1_critical_stop_then_plain_resume"]["checks"]
    assert c["initial_stopped_with_pending_work"] and c["resume_zero_sends"] and c["resume_exit_4_and_refusal_recorded"]
    assert c["stop_reason_and_evidence_preserved"] and c["lists_consistent"] and c["same_binding"]


def test_t2_repeated_resume_still_zero_sends_unchanged_reason(S):
    c = S["T2_repeated_resume"]["checks"]
    assert c["still_zero_sends"] and c["unchanged_reason_and_evidence"] and c["two_refusals_recorded"]


def test_t3_terminal_stop_with_no_remaining_project_is_never_completed(S):
    c = S["T3_terminal_stop_no_remaining_project"]["checks"]
    assert c["stopped_after_last_project"] and c["resume_stays_stopped_never_completed"]


def test_t4_three_provider_failures_are_terminal_but_one_failure_is_not(S):
    c = S["T4_three_consecutive_provider_failures"]["checks"]
    assert c["terminal_failure_stop_persisted"] and c["remaining_project_not_attempted"] and c["resume_cannot_clear_it"]
    b = S["T4b_single_failed_request_is_not_terminal"]["checks"]
    assert b["one_failure_no_stop"] and b["ordinary_resume_not_refused"]


def test_t5_interruption_at_the_persistence_boundary_fails_closed(S):
    a = S["T5a_killed_before_stop_persisted"]["checks"]
    assert a["state_was_indeterminate"] and a["recovery_reconstructed_offline_and_refused"] and a["no_dispatch_on_recovery"]
    b = S["T5b_killed_after_stop_file_before_manifest"]["checks"]
    assert b["file_written_manifest_not"] and b["recovery_refused_on_file"] and b["no_dispatch_on_recovery"]
