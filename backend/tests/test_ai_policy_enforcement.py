"""The project AI policy, enforced fail-closed at the central call path and at
every entry point (ORCH-053; M3 contract B-04, P-10, P-14; ORCH-051 LC-02..LC-13).

A project's documents reach an AI provider only when the project exists and
its `ai_policy` is exactly "allowed". Missing, unknown, ambiguous and blocked
are refused before anything is hashed, scanned, serialised or sent, with a
typed exception (`AiPolicyRefused`) and an audit row (`ai_usage`, outcome
"policy_<reason>", no content, no tokens). The policy is re-read per call, so
a project blocked mid-run stops at its next call or batch, and a job over
several projects is checked per project. Allowed projects behave exactly as
before. No provider is called here: scripted providers stand in, and the
forced-blocked harness (tests/ai_policy_harness.py) blocks and counts any real
dispatch, `claude` subprocess and outbound socket.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.ai import project_policy
from app.ai.budget import JobBudget, Limits, calls_today
from app.ai.project_policy import AiPolicyRefused
from app.ai.provider import AiRequest, RecordingProvider, TextPart, set_provider
from app.compliance import assist
from app.core.config import get_settings
from app.database import SessionLocal
from app.models import AiUsage, Project, ResultCache, User
from tests.test_fa_workflow import w  # noqa: F401 -- the FA workflow's fixture (a project, a drawing, scripted models)

settings = get_settings()
BACKEND = Path(__file__).resolve().parent.parent


# --- helpers ---------------------------------------------------------------------------------------------------


def _project(db, ep: str, policy: str = "allowed") -> Project:
    creator = db.query(User).order_by(User.id).first()
    project = Project(ep_number=ep, project_name="Policy", created_by_id=creator.id, ai_policy=policy)
    db.add(project)
    db.commit()
    return project


def _set_policy(pid: int, policy: str) -> None:
    """Set a project's policy as another request would: its own session, committed."""
    db = SessionLocal()
    try:
        db.query(Project).filter(Project.id == pid).update({"ai_policy": policy})
        db.commit()
    finally:
        db.close()


def _refusals(db, reason: str | None = None) -> list[AiUsage]:
    db.expire_all()
    rows = db.query(AiUsage).filter(AiUsage.outcome.like("policy\\_%", escape="\\")).all()
    return [r for r in rows if reason is None or r.outcome == f"policy_{reason}"]


def _session(db, project_id, provider) -> assist.AssistSession:
    return assist.AssistSession(db=db, project_id=project_id, document_sha256="d" * 64,
                                budget=JobBudget(limits=Limits.from_settings(), calls_today_before=0), provider=provider)


SECRET = "PROJECT-CONTENT-7f3a: the client's drawing text"


def _ask(session, task="policy_probe"):
    return assist.call_task(session, task, "system", [TextPart("content", SECRET)], {"type": "object"}, 100)


# --- the policy itself ---------------------------------------------------------------------------------------


def test_require_fails_closed_while_allowed_keeps_its_read_model_meaning():
    assert project_policy.allowed(None) is True                       # pages: no project, nothing shown blocked
    with pytest.raises(AiPolicyRefused) as missing:
        project_policy.require(None)                                  # requests: no project, nothing sent
    assert missing.value.reason == "missing"
    for policy, reason in (("blocked", "blocked"), ("", "ambiguous"), (None, "ambiguous"), ("Allowed", "ambiguous"),
                           ("maybe", "ambiguous")):
        with pytest.raises(AiPolicyRefused) as refused:
            project_policy.require(SimpleNamespace(id=1, ai_policy=policy))
        assert refused.value.reason == reason
        assert isinstance(refused.value, project_policy.AiBlocked)    # the old catch still catches it
    project_policy.require(SimpleNamespace(id=1, ai_policy="allowed"))


def test_enforce_refuses_missing_unknown_ambiguous_and_blocked_with_an_audit_row_and_no_content(db_session):
    allowed = _project(db_session, "93001")
    blocked = _project(db_session, "93002", "blocked")
    odd = _project(db_session, "93003")
    _set_policy(odd.id, "unsure")                       # neither allowed nor blocked: ambiguous
    project_policy.enforce(db_session, allowed.id, task="t_ok")
    assert _refusals(db_session) == []                  # an allowed request leaves no refusal row
    for pid, reason in ((None, "missing"), (987654, "unknown"), (odd.id, "ambiguous"), (blocked.id, "blocked"),
                        ("7", "unknown"), (True, "unknown")):
        with pytest.raises(AiPolicyRefused) as refused:
            project_policy.enforce(db_session, pid, task="t_probe")
        assert refused.value.reason == reason and refused.value.task == "t_probe"
    rows = _refusals(db_session)
    assert sorted(r.outcome for r in rows) == sorted(["policy_missing", "policy_unknown", "policy_ambiguous",
                                                      "policy_blocked", "policy_unknown", "policy_unknown"])
    for r in rows:
        assert r.task == "t_probe" and r.model.startswith("none") and r.input_tokens is None
        assert r.output_tokens is None and not r.cache_hit and float(r.estimated_cost) == 0
    assert {r.project_id for r in rows} == {None, odd.id, blocked.id}           # an unknown id has no row to name
    assert any(r.model == "none; project_id=987654" for r in rows)              # ... it is named in the audit
    # refusals are not calls: they never spend a project's daily allowance
    assert calls_today(db_session, blocked.id) == 0 and calls_today(db_session, None) == 0


def test_a_block_held_only_in_the_session_is_honoured_too(db_session):
    project = _project(db_session, "93004")
    project.ai_policy = "blocked"                        # not flushed, not committed: the stricter answer wins
    with pytest.raises(AiPolicyRefused):
        project_policy.enforce(db_session, project.id, task="t")


# --- the central call path -----------------------------------------------------------------------------------


@pytest.mark.parametrize("which", ["missing", "unknown", "ambiguous", "blocked"])
def test_call_task_refuses_before_anything_is_hashed_cached_or_sent(db_session, monkeypatch, which):
    if which == "missing":
        pid = None
    elif which == "unknown":
        pid = 987654
    else:
        pid = _project(db_session, "93010", "blocked" if which == "blocked" else "allowed").id
        if which == "ambiguous":
            _set_policy(pid, "")
    provider = RecordingProvider([{"ok": True}])
    scanned = []
    monkeypatch.setattr(assist.guard, "scan_parts", lambda parts: scanned.append(parts) or [])
    keyed = []
    real_key = assist.result_cache.cache_key
    monkeypatch.setattr(assist.result_cache, "cache_key", lambda **kw: keyed.append(kw) or real_key(**kw))
    with pytest.raises(AiPolicyRefused) as refused:
        _ask(_session(db_session, pid, provider))
    assert refused.value.reason == which
    assert provider.calls == 0 and provider.requests == []          # nothing sent
    assert scanned == [] and keyed == []                             # nothing scanned or hashed into a key
    assert db_session.query(ResultCache).count() == 0
    rows = _refusals(db_session, which)
    assert len(rows) == 1 and rows[0].task == "policy_probe"
    assert SECRET not in json.dumps([[r.task, r.model, r.outcome] for r in db_session.query(AiUsage).all()])


def test_an_allowed_project_is_served_exactly_as_before(db_session):
    """Contract: the call, its answer, its cache and its usage row are what they were."""
    project = _project(db_session, "93020")
    provider = RecordingProvider([{"answer": 42}])
    session = _session(db_session, project.id, provider)
    first = _ask(session)
    assert (first.data, first.from_cache, first.error) == ({"answer": 42}, False, None)
    assert provider.calls == 1 and provider.requests[0].parts[0].text == SECRET
    again = _ask(session)                                            # the stored answer, as before
    assert again.from_cache and again.data == {"answer": 42} and provider.calls == 1
    usage = db_session.query(AiUsage).filter(AiUsage.project_id == project.id).order_by(AiUsage.id).all()
    assert [(u.outcome, u.cache_hit) for u in usage] == [("ok", False), ("ok", True)]
    assert _refusals(db_session) == [] and calls_today(db_session, project.id) == 1


def test_a_stored_answer_is_not_served_for_a_blocked_project(db_session):
    project = _project(db_session, "93021")
    provider = RecordingProvider([{"answer": 1}])
    _ask(_session(db_session, project.id, provider))
    _set_policy(project.id, "blocked")
    with pytest.raises(AiPolicyRefused):
        _ask(_session(db_session, project.id, provider))
    assert provider.calls == 1


def test_a_job_over_several_projects_is_checked_per_project_per_call(db_session):
    a = _project(db_session, "93030")
    b = _project(db_session, "93031", "blocked")
    c = _project(db_session, "93032")
    provider = RecordingProvider([{"n": 1}, {"n": 2}, {"n": 3}])
    sent, refused = [], []
    for project in (a, b, c, b, a):
        session = _session(db_session, project.id, provider)
        try:
            result = assist.call_task(session, "multi", "s", [TextPart("content", f"content of {project.ep_number}")],
                                      {"type": "object"}, 100, fresh=True)
            sent.append(project.ep_number)
            assert result.error is None
        except AiPolicyRefused:
            refused.append(project.ep_number)
    assert sent == ["93030", "93032", "93030"] and refused == ["93031", "93031"]
    assert [r.parts[0].text for r in provider.requests] == ["content of 93030", "content of 93032", "content of 93030"]
    assert len(_refusals(db_session, "blocked")) == 2


def test_a_project_blocked_between_two_calls_is_refused_at_the_next(db_session):
    project = _project(db_session, "93040")
    provider = RecordingProvider([{"n": 1}, {"n": 2}])
    session = _session(db_session, project.id, provider)
    assert _ask(session, "first").data == {"n": 1}
    _set_policy(project.id, "blocked")                   # another session, mid-run
    with pytest.raises(AiPolicyRefused):
        _ask(session, "second")
    assert provider.calls == 1


# --- the entry points ------------------------------------------------------------------------------------------


def test_the_drawing_review_is_refused_at_the_route_and_in_the_job(client, db_session, monkeypatch, tmp_path):
    from app.models import BackgroundJob
    from app.review import service as review
    from tests.test_drawing_review_outcome import _drawing

    pid, did, plots = _drawing(client, db_session, monkeypatch, tmp_path, "93050")
    _set_policy(pid, "blocked")
    provider = RecordingProvider([])
    set_provider(provider)
    try:
        started = client.post(f"/projects/{pid}/drawing-review/{did}/jobs", json={"pages": None})
        assert started.status_code == 409 and "switched off for this project" in started.json()["detail"]
        assert db_session.query(BackgroundJob).filter(BackgroundJob.project_id == pid).count() == 0
        with pytest.raises(AiPolicyRefused):                     # a job queued before the block: refused at its start
            review.run(db_session, db_session.get(Project, pid), did)
    finally:
        set_provider(None)
    assert provider.calls == 0 and plots == []                    # not even plotted
    assert {r.task for r in _refusals(db_session, "blocked")} == {review.TASK_WINDOW}


def test_a_review_blocked_mid_run_stops_at_the_next_look(client, db_session, monkeypatch, tmp_path):
    from tests.test_drawing_review_outcome import SHEET, WINDOW, _review
    from tests.test_scoped_drawing_review import _two_floors

    pid, did, _sha = _two_floors(client, db_session, monkeypatch, tmp_path, "93051")

    class BlocksAfterFirst(RecordingProvider):
        def complete(self, request):
            response = super().complete(request)
            _set_policy(pid, "blocked")                          # the engineer blocks the project meanwhile
            return response

    provider = BlocksAfterFirst([WINDOW, SHEET, WINDOW, SHEET])
    _job, view = _review(client, pid, did, provider)
    assert provider.calls == 1                                    # four looks planned, one sent
    assert view["status"] in ("stopped", "done", "failed")
    assert _refusals(db_session, "blocked")


def test_the_fa_workflow_run_and_retry_are_refused_at_routes_and_entry_points(w):
    fa = w
    from app.interfaces import findings, visual, workflow
    from app.models import FaInterfaceRun

    workflow.run_workflow(fa.db, fa.db.get(Project, fa.pid))              # allowed: runs as before
    allowed_requests = len(fa.models.requests)
    assert allowed_requests > 0
    run = fa.db.query(FaInterfaceRun).filter(FaInterfaceRun.project_id == fa.pid).order_by(FaInterfaceRun.id.desc()).first()
    _set_policy(fa.pid, "blocked")
    fa.db.expire_all()
    project = fa.db.get(Project, fa.pid)
    assert fa.client.post(f"/projects/{fa.pid}/fa-interfaces/runs/jobs").status_code == 409
    assert fa.client.post(f"/projects/{fa.pid}/fa-interfaces/runs/{run.id}/retry-review").status_code == 409
    for call in (lambda: workflow.run_workflow(fa.db, project),
                 lambda: workflow.run_retry(fa.db, project, run),
                 lambda: visual.check(fa.db, project, [{"filename": "x"}]),
                 lambda: findings.review_all(fa.db, project, {"verification": [{"id": "g"}]}, [], [], sources_digest="d")):
        with pytest.raises(AiPolicyRefused):
            call()
    assert len(fa.models.requests) == allowed_requests                    # nothing more was sent
    tasks = {r.task for r in _refusals(fa.db, "blocked")}
    assert {visual.TASK, findings.TASK, workflow.TASK_REVIEW} <= tasks


def test_the_preparation_plan_is_refused_at_its_route_and_entry(client, db_session):
    from app.redesign import ai as RA
    from app.redesign import service as redesign
    from tests.conftest import login

    login(client, settings.default_admin_email, settings.default_admin_password)
    pid = client.post("/projects", json={"ep_number": "93060", "project_name": "Prep", "design_sheets": []}).json()["id"]
    _set_policy(pid, "blocked")
    assert client.post(f"/projects/{pid}/redesign/1/plan/jobs").status_code == 409
    with pytest.raises(AiPolicyRefused):
        redesign.plan(db_session, db_session.get(Project, pid), 1)
    assert {r.task for r in _refusals(db_session, "blocked")} == {RA.TASK}


def test_the_scoped_cli_preflight_refuses_a_blocked_project_before_any_provider_is_built(client, db_session,
                                                                                         monkeypatch, tmp_path):
    from app.review import scoped
    from tests.test_scoped_drawing_review import _scope, _two_floors

    pid, did, sha = _two_floors(client, db_session, monkeypatch, tmp_path, "93070")
    _set_policy(pid, "blocked")
    built = []
    with pytest.raises(scoped.Refused) as refused:
        scoped.run(_scope("93070", did, sha), lambda: built.append(1) or RecordingProvider([]))
    assert "switched off for this project" in str(refused.value)
    assert built == []                                                 # --live's _build is never reached
    assert _refusals(db_session, "blocked")


def test_the_ifc_symbol_review_is_refused_per_project(db_session, monkeypatch):
    from app.ifc.services import ai_symbol_review as SR

    project = _project(db_session, "93080", "blocked")
    monkeypatch.setattr(settings, "ai_enabled", True)
    monkeypatch.setattr(settings, "ifc_ai_symbol_review_enabled", True)
    provider = RecordingProvider([])
    set_provider(provider)
    try:
        item = SimpleNamespace(signature="sig", key="k1", group={}, candidates=[])
        report = SR.review(db_session, [item], project_id=project.id, drawing_name="FA.dwg")
    finally:
        set_provider(None)
    assert provider.calls == 0 and report.enabled is False and "switched off for this project" in report.note
    assert report.verdicts["sig"].outcome == "engineer"
    assert _refusals(db_session, "blocked")[0].task == SR.TASK_METADATA


def test_the_drawings_ai_review_is_refused_per_project(db_session, monkeypatch):
    from app.services import drawing_ai_review as DR

    project = _project(db_session, "93090", "blocked")
    provider = RecordingProvider([])
    set_provider(provider)
    try:
        report = DR.Report()
        data, error = DR._ask(DR.TASK_REPLY, DR.REPLY_SCHEMA, {"reply": {"reference": SECRET}}, sha="s" * 64,
                              project_id=project.id, db=db_session, report=report)
    finally:
        set_provider(None)
    assert data is None and "switched off for this project" in error and provider.calls == 0
    assert _refusals(db_session, "blocked")[0].task == DR.TASK_REPLY


def test_the_drf_read_at_project_creation_names_no_project_and_is_refused(db_session, monkeypatch, tmp_path):
    from app.ai import verification

    monkeypatch.setattr(settings, "ai_enabled", True)
    drf = tmp_path / "DRF.pdf"
    drf.write_bytes(b"%PDF-1.4 not read")
    provider = RecordingProvider([])
    with pytest.raises(AiPolicyRefused) as refused:
        verification.read_drf(db_session, drf, project=None, provider=provider)
    assert "names no project" in str(refused.value) and provider.calls == 0
    assert _refusals(db_session, "missing")[0].task == "verify_drf"


def test_the_extraction_call_is_gated_per_call(db_session):
    from app.extraction import pipeline

    project = _project(db_session, "93100", "blocked")
    provider = RecordingProvider([])
    request = AiRequest(task="read_cell", system="s", parts=[TextPart("cell", SECRET)], schema={}, max_output_tokens=10)
    evidence = SimpleNamespace(request=request, fingerprint="f", sent_regions=[])
    with pytest.raises(AiPolicyRefused):
        pipeline.ask(db_session, project_id=project.id, run_id=None, document_sha256="d", evidence=evidence, context={},
                     budget=JobBudget(limits=Limits.from_settings(), calls_today_before=0), provider=provider,
                     allowed_target="quantity")
    assert provider.calls == 0


def test_classification_rechecks_the_policy_before_every_batch(db_session, tmp_path, monkeypatch):
    from app.ai import provider as provider_module
    from app.services import document_classification_ai as AI
    from tests.test_document_classification_ai import CERTIFICATE_TEXT, DATASHEET_TEXT, _answer, _doc
    from tests.test_document_classification_ai import _project as classification_project

    monkeypatch.setattr(settings, "document_classification_v2", True)
    monkeypatch.setattr(settings, "document_classification_ai_enabled", True)
    monkeypatch.setattr(settings, "document_classification_ai_batch", 1)
    project = classification_project(db_session, tmp_path, "93110")
    _doc(db_session, project, tmp_path, "05- Misc/scan 001.pdf", DATASHEET_TEXT, "sha-a")
    _doc(db_session, project, tmp_path, "05- Misc/scan 002.pdf", CERTIFICATE_TEXT, "sha-b")

    class BlocksAfterFirst(RecordingProvider):
        def complete(self, request):
            response = super().complete(request)
            _set_policy(project.id, "blocked")
            return response

    provider = BlocksAfterFirst([_answer(("DATASHEET", "FAS", "fire_alarm", "high", "data sheet")),
                                 _answer(("CERTIFICATE", "ELS", "emergency_lighting", "medium", "certificate"))])
    provider_module.set_provider(provider)
    try:
        counts = AI.run(db_session, project)
    finally:
        provider_module.set_provider(None)
    assert provider.calls == 1 and counts["calls"] == 1                   # the second batch was never sent
    assert "switched off for this project" in counts["stopped"]
    assert "CERTIFICATE OF APPROVAL" not in json.dumps([p.text for r in provider.requests for p in r.parts])
    assert _refusals(db_session, "blocked")[0].task == AI.TASK


def test_the_chat_keeps_its_check_and_now_records_the_refusal(db_session, monkeypatch):
    from app.services import drawings_chat

    project = _project(db_session, "93120", "blocked")
    monkeypatch.setattr(settings, "drawings_chat_ai_enabled", True)
    provider = RecordingProvider([])
    set_provider(provider)
    try:
        with pytest.raises(drawings_chat.ChatUnavailable):
            drawings_chat.ask(db_session, project, "FA", SECRET)
    finally:
        set_provider(None)
    assert provider.calls == 0 and _refusals(db_session, "blocked")[0].task == drawings_chat.TASK


# --- caps and switches ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("feature,setting,task", [
    ("review", "drawing_review_max_calls_per_project_per_day", "fa_drawing_review_window"),
    ("fa_visual", "fa_visual_max_calls_per_project_per_day", "fa_interfaces_visual"),
    ("prep", "prep_max_calls_per_project_per_day", "fa_prep_coordination"),
])
def test_review_fa_visual_and_preparation_have_their_own_daily_cap_per_project(db_session, monkeypatch, feature,
                                                                              setting, task):
    from app.ai.budget import BudgetExceeded
    from app.review import service as review

    assert getattr(settings, setting) > 0                                    # a real number, owner-settable
    monkeypatch.setattr(settings, setting, 3)
    project = _project(db_session, f"9313{len(feature)}")
    for t in (task, task, "some_other_task", "some_other_task"):              # the other task does not count
        db_session.add(AiUsage(project_id=project.id, task=t, model="m", estimated_cost=0, latency_ms=0,
                               cache_hit=False, escalated=False, outcome="ok"))
    db_session.add(AiUsage(project_id=project.id, task=task, model="none", estimated_cost=0, latency_ms=0,
                           cache_hit=False, escalated=False, outcome="policy_blocked"))   # a refusal is not a call
    db_session.commit()
    budget = review._budget(db_session, project, feature)
    assert budget.limits.max_calls_per_project_per_day == 3 and budget.calls_today_before == 2
    budget.reserve(10, 10)
    with pytest.raises(BudgetExceeded) as over:
        budget.reserve(10, 10)
    assert over.value.limit == "calls_per_project_per_day"


def test_health_reports_every_ai_switch(client):
    body = client.get("/health").json()
    flags, ai = body["flags"], body["ai"]
    for name in ("ai_enabled", "fa_ai_enabled", "prep_ai_enabled", "drawing_review_ai_enabled", "drawings_chat_ai_enabled",
                 "drawings_chat_enabled", "document_classification_ai_enabled", "document_classification_v2",
                 "ifc_ai_symbol_review_enabled", "ifc_ai_visual_review_enabled", "drawings_ai_review_enabled",
                 "ai_verify_auto", "ai_read_full_second_pass"):
        assert isinstance(flags[name], bool), name
    assert isinstance(ai["disabled_tasks"], list) and ai["provider"] == settings.ai_provider
    assert ai["policy_enforcement"] == "fail_closed"
    caps = ai["daily_caps_per_project"]
    assert set(caps) >= {"platform", "drawing_review", "fa_visual", "prep", "drawings_chat", "document_classification",
                         "fa_findings", "fa_orchestrator"}


# --- the forced-blocked harness ------------------------------------------------------------------------------

# Every test module that drives an AI entry point: routes, jobs (run inline), workers' runners and the scoped CLI.
HARNESS_MODULES = [
    "tests/test_drawing_review.py", "tests/test_drawing_review_outcome.py", "tests/test_scoped_drawing_review.py",
    "tests/test_review_duplicates_and_concurrency.py", "tests/test_fa_workflow.py", "tests/test_fa_opus_review.py",
    "tests/test_fa_review_fixes.py", "tests/test_drawing_prep.py", "tests/test_drawings_chat.py",
    "tests/test_document_classification_ai.py", "tests/test_ifc_worker_and_ai.py",
    # the paths that were gated before (extraction, verification, compliance, sample requests), kept covered
    "tests/test_ai_assist.py", "tests/test_ai_evaluation.py", "tests/test_ai_verification.py",
    "tests/test_ai_sheet_reader.py", "tests/test_details_check.py", "tests/test_compliance_ai_autofill.py",
    "tests/test_compliance_knowledge.py", "tests/test_sample_request.py",
]
CONTROL_MODULES = ["tests/test_drawing_review.py", "tests/test_fa_workflow.py", "tests/test_drawing_prep.py"]


def _harness(tmp_path: Path, modules: list[str], force_blocked: bool) -> dict:
    out = tmp_path / ("blocked.json" if force_blocked else "control.json")
    env = {**os.environ, "EP_AI_POLICY_HARNESS_OUT": str(out), "EP_AI_POLICY_FORCE_BLOCKED": "1" if force_blocked else "0"}
    env.pop("PYTEST_ADDOPTS", None)
    subprocess.run([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-p", "tests.ai_policy_harness",
                    "-q", "--basetemp", str(tmp_path / ("bt-blocked" if force_blocked else "bt-control")), *modules],
                   cwd=str(BACKEND), env=env, capture_output=True, text=True, timeout=3000)
    return json.loads(out.read_text(encoding="utf-8"))


def _from_app(record: dict, key: str = "requests") -> list[dict]:
    """What the application built: a provider's or the evaluation harness's own unit tests build their
    requests themselves (origin tests.*), with no project."""
    return [r for r in record[key] if not r["origin"].startswith("tests.")]


def test_with_every_project_blocked_no_entry_point_sends_or_serialises_anything(tmp_path):
    blocked = _harness(tmp_path, HARNESS_MODULES, force_blocked=True)
    assert blocked["force_blocked"] is True and blocked["tests"] >= 250
    built = _from_app(blocked)
    assert built == [], f"project content was put into {len(built)} request(s): {built[:3]}"
    assert _from_app(blocked, "provider_inputs") == []   # the scripted providers were given nothing of a project
    # no real dispatch of anything the application built (a provider's own unit tests build theirs: blocked too)
    assert [d for d in blocked["real_dispatches"] if not d["origin"].startswith("tests.")] == []
    assert (blocked["claude_subprocess"], blocked["socket_connect_non_local"]) == (0, 0)
    # the control: the same harness sees what an allowed project sends, so the zero above is not blindness
    control = _harness(tmp_path, CONTROL_MODULES, force_blocked=False)
    assert control["outcomes"].get("failed", 0) == 0
    assert len(_from_app(control)) >= 10 and _from_app(control, "provider_inputs")
    assert [d for d in control["real_dispatches"] if not d["origin"].startswith("tests.")] == []
    assert (control["claude_subprocess"], control["socket_connect_non_local"]) == (0, 0)
