"""Runner integration regressions (R22-03) over the evidence runner_probes.py produced with the ACTUAL arm runner, the
scripted provider and a fake clock (no model request). Set R22_RUN_PROBES=1 to regenerate the evidence first."""
import json
import os
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
EV = HERE.parent / "runner-evidence" / "RUNNER-INTEGRATION.json"


@pytest.fixture(scope="module")
def R():
    if os.environ.get("R22_RUN_PROBES") == "1" or not EV.exists():
        p = subprocess.run([sys.executable, str(HERE / "runner_probes.py")], cwd=str(HERE), capture_output=True, text=True, timeout=3000)
        assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-3000:]
    return json.loads(EV.read_text(encoding="utf-8"))["scenarios"]


def test_s1_charged_before_dispatch_equals_sent_and_controls(R):
    s = R["S1_baseline"]
    assert s["run"]["exit"] == 0 and s["status"] == "completed"
    assert s["charged_equals_sent"] and s["no_trigger_control_sent"] == 0
    assert all(v == 24 for v in s["worst_case_reserved"].values()) and all(v == 60 for v in s["capacity_before"].values())
    assert sum(s["counter_used"].values()) == sum(s["requests"].values())
    last = s["tripwire_binding"][-1]["binding"]
    assert last["rejected"] == 0 and all(v == "eligible" for d, v in last["eligibility"].items() if d.endswith(".pdf")) and last["eligibility"]["EP-17428/synth/note.docx"] == "ineligible"


def test_s2_durable_cap_holds_across_kill_and_resume(R):
    s = R["S2_kill_resume"]
    assert s["killed"]["exit_97_expected"] and s["killed"]["lost_request_charged"] and s["killed"]["open_attempt_visible_after_kill"]
    r = s["resumed"]
    assert r["run"]["exit"] == 0 and r["status"] == "completed" and r["interrupted_seen"]
    six = r["six_page_doc"]
    assert six["capped_at_12"] and six["attempted_beyond_cap"] and six["sent_plus_lost_equals_charged"]
    assert r["one_page_doc_not_resent"] and any(st == "interrupted" for st in r["attempt_statuses"][list(r["attempt_statuses"])[0]] + sum(r["attempt_statuses"].values(), []))


def test_s3_new_tag_never_recreates_an_allowance(R):
    s = R["S3_new_tag"]
    assert s["refused"]["refused_before_dispatch"] and s["refused"]["charged_unchanged"] and not s["refused"]["sandbox_created"]
    o = s["override_dry_only"]
    assert o["cap_holds_across_tags"] and o["all_within_cap"] and o["allowance_refusals"] > 0 and o["six_page_doc_charged"] == 12


def test_s4_second_writer_refused_and_document_lock_busy(R):
    s = R["S4_second_writer"]
    assert s["second_refused_before_dispatch"] and s["document_lock_probe"]["busy_while_held"] is True
    assert s["slow_writer_exit"] == 0 and s["slow_writer_status"] == "completed"


def test_s5_cache_hit_spends_nothing(R):
    s = R["S5_cache_hit"]
    assert s["reread"]["exit"] == 0 and s["cache_hits_in_reread"] >= s["fresh_sends_first_run"] > 0
    docs = s["per_document"]
    assert all(d["fresh_equals_charge_delta"] for d in docs.values()), "a cache hit charges nothing; a fresh send is charged once"
    assert all(d["completed_doc_unchanged"] for d in docs.values() if not d["first_reading_budget_stopped"]) and any(not d["first_reading_budget_stopped"] for d in docs.values())
    assert s["counter_delta"] == s["fresh_sends_in_reread"] == sum(s["requests_in_reread_process"].values()) and all(d["charged_after"] <= 12 for d in docs.values())


def test_s6_arm_scope_exhaustion_is_a_budget_stop(R):
    s = R["S6_scope_exhaust"]
    assert s["run"]["exit"] == 0 and s["exhaustion_is_a_budget_stop"] and s["counter_equals_sent"] and s["documents_budget_stopped"] >= 1
    assert s["charged_total"] == s["requests_sent"] == s["arm_cap"] and s["ledger_precheck_refusals"] >= 1


def test_s7_whole_project_deferral_then_resume_on_the_next_window(R):
    s = R["S7_deferral"]
    f, r = s["first"], s["resumed"]
    assert f["run"]["exit"] == 0 and f["status"] == "deferred" and f["zero_requests_for_deferred_project"]
    assert [d["ep"] for d in f["deferred"]] == ["16830"] and f["deferred"][0]["needed_worst_case"] == 24 and f["deferred"][0]["capacity"] == 10
    assert r["run"]["exit"] == 0 and r["status"] == "completed" and r["deferred_after"] == [] and r["requests"].get("16830", 0) > 0
    assert r["charged_17428_unchanged"] and r["sent_17428_unchanged"] and r["skipped_projects"] == ["17428"] and "17428" not in r["requests"]


def test_s8_refusals_before_dispatch(R):
    s = R["S8_refusals"]
    assert s["both_refused_before_dispatch"] and s["first_run_exit"] == 0
    assert sum(s["counter_after"].values()) == s["requests_first_run"] and all(x["requests_sent"] == 0 for x in s["refusal_records"])
