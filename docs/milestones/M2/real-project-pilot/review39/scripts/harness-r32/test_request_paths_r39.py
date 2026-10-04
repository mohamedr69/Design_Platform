"""ORCH-08C task item 1 (R39-04; A-09 points 1 and 3): the request paths of every lane, the declared application
environment that switches the drawings-AI review off, and the proof that the drawings-AI outputs feed no measured field.
No provider and no model: the static analysis reads source files; the probes run the application trees read-only in
child processes with a local fake provider and a database under the r39 sandbox base. Run:
python -m pytest -q test_request_paths_r39.py"""
import json
import pathlib
import subprocess
import uuid

import pytest

import preflight_r32 as PF
import project_bounds_r32 as PB
import r32_test_helpers as H
import request_paths_r39 as RP
import runner_r32 as RN
import sandbox_ingest_r32 as SI

HERE = pathlib.Path(__file__).resolve().parent
TREES = {"baseline": "C:/t/iso/frozen-r12/backend", "candidate": "C:/t/iso/cand-r29/backend"}
# Every provider-calling function the over-approximating static graph reaches from a lane's entry point, with its status
# under the declared configuration (REQUEST-PATHS.md gives the reading of each):
EXPECTED = {
    "B": {"app.ai.submittal_reader:check": "declared: read_submittal_form (the reconcile check's repeat; readiness via get_provider)",
          "app.ai.submittal_reader:available": "readiness only (get_provider().ready; no request)",
          "app.compliance.assist:_call": "declared: read_submittal_form (assist.call_task from submittal_reader._Run.call)",
          "app.services.document_processing:run": "readiness only (provider or get_provider(); no request)",
          "app.ai.evidence_reader:evidence_stage": "disabled: AI_EVIDENCE_VARIANT=off in B (returns before any request)",
          "app.ai.evidence_reader:EvidenceRun.call": "disabled: AI_EVIDENCE_VARIANT=off in B",
          "app.ai.ledger:LedgerProvider.complete": "the ledger wrapper of the declared provider (live only; not a request kind)",
          "app.services.drawing_ai_review:enabled": "readiness only; returns False under application_env",
          "app.services.drawing_ai_review:_ask": "disabled: DRAWINGS_AI_REVIEW_ENABLED=false (application_env)"},
    "C": {"app.ai.evidence_reader:evidence_stage": "declared: readiness (provider given) and the evidence reader",
          "app.ai.evidence_reader:EvidenceRun.call": "declared: the evidence reader's task kinds under C's switches",
          "app.ai.submittal_reader:available": "readiness only (the lane makes it return None: available)",
          "app.ai.ledger:LedgerProvider.complete": "the ledger wrapper of the declared provider (live only)",
          "app.compliance.assist:_call": "static false positive: evidence_reader._read_page's run.call is EvidenceRun.call, not submittal_reader._Run.call"},
}
EXPECTED["R"] = dict(EXPECTED["C"])


@pytest.fixture(scope="module")
def graph():
    out = {}
    for t, root in RP.TREES.items():
        out[t] = RP.analyse(root)
    return out


def test_every_reached_provider_site_is_listed_with_its_status(graph):
    for lane, (t, entries) in RP.ENTRIES.items():
        g = graph[t]
        parent = RP.reach(g, entries)
        reached = {s["function"] for s in g["sites"] if s["function"] in parent}
        assert reached == set(EXPECTED[lane]), (lane, sorted(reached ^ set(EXPECTED[lane])))


def test_the_drawings_path_is_reachable_from_b_only_and_not_from_c_or_r(graph):
    b = RP.reach(graph["baseline"], RP.ENTRIES["B"][1])
    c = RP.reach(graph["candidate"], RP.ENTRIES["C"][1])
    path = RP.path_to(b, "app.services.drawing_ai_review:_ask")
    assert path[0] == "app.services.document_processing:run" and "app.services.shop_drawings:reconcile" in path and "app.services.shop_drawings:_ai_review" in path
    assert "app.services.drawing_ai_review:_ask" not in c and "app.services.shop_drawings:reconcile" not in c


def test_sites_never_reached_by_any_lane(graph):
    """sheet reading, verification, extraction, IFC symbol review, compliance sessions and evaluation have no path from any lane."""
    for lane, (t, entries) in RP.ENTRIES.items():
        parent = RP.reach(graph[t], entries)
        for f in ("app.ai.sheet_reader:read_design_sheet", "app.ai.verification:verify_boq", "app.ai.verification:read_drf",
                  "app.extraction.pipeline:ask", "app.ifc.services.ai_symbol_review:_call", "app.compliance.assist:open_session",
                  "app.ai.evaluation:run_case"):
            assert f not in parent, (lane, f)


def test_declared_task_kinds_follow_the_switches():
    k = PF.task_kinds_for(RN.DRY_LANE_SWITCHES)
    assert k["B"] == ["read_submittal_form"]
    assert k["C"] == ["discover_page", "locate_decision", "read_decision", "read_field_context", "read_identity", "read_revision"]
    assert k["R"] == ["discover_page", "read_decision", "read_field_context", "read_identity", "read_revision"]
    assert k["P"] == k["C"]
    assert not {"drawings_reply_match", "drawings_reference_conflict", "drawings_floor_alias"} & set(sum(k.values(), []))
    assert "discover_region" in PF.evidence_task_kinds({"AI_EVIDENCE_VARIANT": "EV1", "AI_EVIDENCE_ROI": "1"})
    assert PF.evidence_task_kinds({"AI_EVIDENCE_VARIANT": "off"}) == []


def test_the_application_env_is_exactly_the_drawings_switch_and_sandbox_env_sets_it(tmp_path):
    assert PF.APPLICATION_ENV == {"DRAWINGS_AI_REVIEW_ENABLED": "false"} == SI.APPLICATION_ENV
    env = SI.sandbox_env(tmp_path / "root", ai_enabled=True)
    assert env["DRAWINGS_AI_REVIEW_ENABLED"] == "false"
    assert PB.DRAWINGS_AI_ENABLE_KEY in PF.APPLICATION_ENV
    for tree in TREES.values():                       # the setting the key drives, in both config.py files (b4fbc07f...)
        text = (pathlib.Path(tree) / "app/core/config.py").read_text(encoding="utf-8")
        assert "    drawings_ai_review_enabled: bool = True" in text and "env_prefix" not in text


def _probe(tree, mode, flag, base=PF.DEFAULT_SANDBOX_BASE):
    root = pathlib.Path(base) / f"tests-dai-{uuid.uuid4().hex[:8]}"
    (root / "db").mkdir(parents=True)
    env = SI.sandbox_env(root, ai_enabled=True, extra={"DRAWINGS_AI_REVIEW_ENABLED": flag})
    out = root / "out" / "PROBE.json"
    out.parent.mkdir()
    r = subprocess.run([SI.PY, str(HERE / "drawings_ai_probe_r39.py"), mode, str(out)], cwd=tree, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(out.read_text(encoding="utf-8"))


@pytest.mark.parametrize("tree", sorted(TREES.values()))
def test_the_declared_setting_switches_the_drawings_review_off_in_both_trees(tree):
    off = _probe(tree, "switch", "false")
    assert off["settings"]["drawings_ai_review_enabled"] is False and off["enabled"]["on"] is False
    assert "DRAWINGS_AI_REVIEW_ENABLED" in off["enabled"]["why"] and off["provider_calls"] == [] and off["ai_review"].startswith("returned at enabled()")
    on = _probe(tree, "switch", "true")                # the converse: the key is the effective switch (a ready provider, AI on)
    assert on["settings"]["drawings_ai_review_enabled"] is True and on["enabled"]["on"] is True and on["ai_review"].startswith("went past enabled()")


@pytest.mark.parametrize("tree", sorted(TREES.values()))
def test_drawings_ai_outputs_feed_no_measured_field(tree):
    """1(d): even ENABLED and answered (test sandbox only), the drawings review writes no project_documents column the
    scorer reads (identity / revision / decision come from those rows and their extracted evidence)."""
    x = _probe(tree, "feed", "true")
    assert x["provider_calls"] == ["drawings_reply_match"], "the path ran: the provider was asked"
    assert x["revision_before"] == {"status": "under_review", "source": "sync"} and x["revision_after"] == {"status": "approved", "source": "ai"}, \
        "its answer was applied to the shop-drawing records"
    assert x["measured_unchanged"] is True and x["project_documents_before"] == x["project_documents_after"]
    assert x["project_documents_flushed_during_review"] == []
    assert set(x["measured_columns"]) == {"role", "state", "error", "sha256", "reference", "revision", "status", "system_code", "extracted"}


def test_the_scorer_reads_only_project_documents_rows():
    """The measured fields' inputs: lane_r32.dump_rows selects project_documents (joined to projects for the EP number)
    and nothing from the shop-drawing tables; score_lane_r32 reads only that dump."""
    lane = (HERE / "lane_r32.py").read_text(encoding="utf-8")
    i = lane.index("def dump_rows")
    body = lane[i:lane.index("\n\n\n", i)]
    assert "from project_documents d join projects p" in body
    assert "shop_drawing" not in body.lower() and "drawing_issue" not in body.lower()
    score = (HERE / "score_lane_r32.py").read_text(encoding="utf-8")
    assert "shop_drawing" not in score.lower() and "drawing_ai" not in score.lower()


def test_the_bounds_count_the_drawings_path_as_disabled_and_state_the_alternative():
    b = H.bounds_for()
    p = b["projects"]["EP-27331"]
    assert p["planning"]["all_lanes"] == 63.0 and p["structural_maximum"]["all_lanes"] == 160
    assert p["drawings_ai"]["if_enabled"]["structural_all_lanes"] == 170 and p["drawings_ai"]["if_enabled"]["r38_model_all_lanes"] == 164
    assert p["change_from_r38_model"]["r38_structural_all_lanes"] == 154 and p["windows_needed_structural"] == 3
    assert b["drawings_ai"]["counted"] == 0 and b["compatible_limits"]["required_minimum"]["AI_MAX_CALLS_PER_PROJECT_PER_DAY"] == 84
