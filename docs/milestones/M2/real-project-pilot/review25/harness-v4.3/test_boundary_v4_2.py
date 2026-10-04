"""Provider-failure boundary regressions (R24-01) over provider_boundary_probes.py evidence produced with the ACTUAL
runner and the scripted provider, plus the journals the eight runner controls wrote (cache hits and budget refusals are
journalled but never counted as failures). No model request. R24_RUN_PROBES=1 regenerates the evidence first."""
import json
import os
import pathlib
import subprocess
import sys

import pytest

import provider_journal as pj

HERE = pathlib.Path(__file__).resolve().parent
EV = HERE.parent / "boundary-evidence" / "BOUNDARY.json"
PROBES = pathlib.Path(os.environ.get("R22_PROBES_ROOT", "C:/t/r2x/dry-runs/r25-probes"))


@pytest.fixture(scope="module")
def S():
    if os.environ.get("R24_RUN_PROBES") == "1" or not EV.exists():
        p = subprocess.run([sys.executable, str(HERE / "provider_boundary_probes.py")], cwd=str(HERE), capture_output=True, text=True, timeout=3000)
        assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-3000:]
    return json.loads(EV.read_text(encoding="utf-8"))["scenarios"]


def ok(s):
    return all(s["checks"].values()), {k: v for k, v in s["checks"].items() if not v}


def test_p1_provider_stop_ordinary_resume(S):
    assert ok(S["P1_provider_stop_ordinary"])[0], ok(S["P1_provider_stop_ordinary"])[1]


def test_p2_provider_stop_killed_before_file_is_reconstructed_and_refused(S):
    assert ok(S["P2_provider_stop_killed_before_file"])[0], ok(S["P2_provider_stop_killed_before_file"])[1]


def test_p3_provider_stop_killed_after_file_is_refused(S):
    assert ok(S["P3_provider_stop_killed_after_file"])[0], ok(S["P3_provider_stop_killed_after_file"])[1]


def test_p4_repeated_resume_keeps_the_first_stop_and_charges(S):
    assert ok(S["P4_repeated_resume_of_recovered_provider_stop"])[0], ok(S["P4_repeated_resume_of_recovered_provider_stop"])[1]


def test_p5_no_false_terminal_and_breaker_not_reset(S):
    for k in ("P5a_two_failures_and_an_unresolved_request", "P5b_success_between_failures", "P5c_breaker_not_reset_by_restart"):
        assert ok(S[k])[0], (k, ok(S[k])[1])


def test_p6_unusable_evidence_refuses_without_dispatch_or_fabrication(S):
    for k in ("P6a_torn_record", "P6b_journal_missing", "P6c_other_binding", "P6d_result_without_attempt"):
        assert ok(S[k])[0], (k, ok(S[k])[1])


def _journal_of(scenario, tag):
    root = PROBES / scenario
    run = json.loads((root / "runs" / tag / "out/RUN.json").read_text(encoding="utf-8"))
    binding = {"declaration_sha256": run["declaration_sha256"], "arm": run["arm"], "tag": run["tag"], "a_tag": run["a_tag"], "allowance_scope": run["allowance_key"]["scope"],
               "allowance_profile": run["allowance_key"]["profile"], "policy": run["context"]["policies"][0]}
    decl = json.loads(((root / "R22-DECLARATION.dry.json") if (root / "R22-DECLARATION.dry.json").exists() else pathlib.Path("C:/t/r2x/dry-runs/r22/R22-DECLARATION.dry.json")).read_text(encoding="utf-8"))
    return pj.load(root / "runs" / tag / "out/PROVIDER-OUTCOMES.jsonl", binding, planned_sha256={p["sha256"] for p in decl["sources"]["sample"]["documents_planned"]})


def test_controls_journal_budget_and_cache_hits_without_counting_them():
    s2 = _journal_of("s2-kill-resume", "L3")
    s5 = _journal_of("s5-cache-hit", "L1")
    assert s2["state"] == "ok" and s2["result_counts"]["budget"] >= 1 and s2["result_counts"]["failure"] == 0 and s2["streak"] == 0 and s2["processes"] == 2 and len(s2["unresolved"]) == 1
    assert s5["state"] == "ok" and s5["result_counts"]["cache_hit"] >= 20 and s5["result_counts"]["failure"] == 0 and s5["streak"] == 0 and s5["processes"] == 2
