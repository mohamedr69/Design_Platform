"""R21 prerequisite switches: the four declared arm configurations demonstrated with a scripted, keyed provider on ACTUAL
inputs (a rotated drawing sheet: whole-page discovery for L1 / L3, the real located crop for L2 / L4), through the
persisted processing path. Common in every arm: G, Rsup (rotation-correct support), the required-first scheduling, the
deadline policy. Varied: ROI (L2, L4) and the optional targeted read X (L3, L4). Also: identity matrix (flags off ==
accepted; legacy G / T / T+E strings unchanged; four arms distinct), arm-specific caches, cap refusal, restart
accounting. No model, no network."""
import io
import json
import os
import subprocess
import sys

import pymupdf
import pytest
from PIL import Image

from app.ai import evidence_reader as er
from app.ai.budget import JobBudget, Limits, open_budget
from app.models import ProjectDocument, ResultCache

from ._keyed_provider import KeyedProvider
from .test_ai_pilot_r19 import Stage, _clip, crop_answer, read, sheet

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_ENV = {"AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_SUPPORT": "v2", "AI_EVIDENCE_SCHEDULING": "required_first", "AI_EVIDENCE_DEADLINE": "1"}
ARMS = {"L1": {}, "L2": {"AI_EVIDENCE_ROI": "1"}, "L3": {"AI_EVIDENCE_TARGETED": "1"}, "L4": {"AI_EVIDENCE_ROI": "1", "AI_EVIDENCE_TARGETED": "1"}}
ACCEPTED = ("evidence-reader-2026-09-29.7", "evidence-policy-2026-09-29.4")
LEGACY = {  # the reviewed configurations keep their identity strings byte-for-byte (cache continuity of earlier evidence)
    ("AI_EVIDENCE_GUARD",): ("evidence-reader-2026-09-29.7", "evidence-policy-2026-09-29.4+guard-rev-token-2026-09-30.1"),
    ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED"): ("evidence-reader-2026-09-29.7+targeted-2026-09-30.2",
                                                    "evidence-policy-2026-09-29.4+guard-rev-token-2026-09-30.1+region-support-2026-09-30.1+targeted-completion-2026-09-30.2"),
    ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED", "AI_EVIDENCE_EFFICIENT"): (
        "evidence-reader-2026-09-29.7+targeted-2026-09-30.2+located-discovery-2026-09-30.2",
        "evidence-policy-2026-09-29.4+guard-rev-token-2026-09-30.1+region-support-2026-09-30.1+targeted-completion-2026-09-30.2+located-discovery-2026-09-30.2"),
}


@pytest.fixture(autouse=True)
def _no_submittal_reader(monkeypatch):
    from app.ai import submittal_reader
    monkeypatch.setattr(submittal_reader, "available", lambda project, provider=None: None)


def identities(env: dict) -> dict:
    base = {k: v for k, v in os.environ.items() if not k.startswith("AI_EVIDENCE_")}
    code = "import json; from app.ai import evidence_reader as er; print(json.dumps([er.READER_VERSION, er.EVIDENCE_POLICY_VERSION, sorted(er.PROMPTS)]))"
    out = subprocess.run([sys.executable, "-c", code], cwd=BACKEND, env={**base, "AI_ENABLED": "false", **env}, capture_output=True, text=True, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_identity_matrix_flags_off_equals_accepted_legacy_unchanged_and_arms_distinct():
    assert identities({})[:2] == list(ACCEPTED)
    for keys, expect in LEGACY.items():
        assert identities({k: "1" for k in keys})[:2] == list(expect), keys
    arms = {a: identities({**BASE_ENV, **e}) for a, e in ARMS.items()}
    ids = [(v[0], v[1]) for v in arms.values()]
    assert len(set(ids)) == 4, arms
    assert all("+region-support" in v[1] and "+guard" in v[1] and "+deadline" in v[0] for v in arms.values())
    assert "discover_region" in arms["L2"][2] and "discover_region" in arms["L4"][2] and "discover_region" not in arms["L1"][2]
    assert "read_field_context" in arms["L3"][2] and "read_field_context" in arms["L4"][2] and "read_field_context" not in arms["L2"][2]


def _set(monkeypatch, arm):
    env = {**BASE_ENV, **ARMS[arm]}
    ids = identities(env)
    for k, v in (("GUARD_ENABLED", True), ("SUPPORT_V2", True), ("REQUIRED_FIRST", True), ("DEADLINE_ENABLED", True), ("EFFICIENT_ENABLED", False),
                 ("ROI_ENABLED", "AI_EVIDENCE_ROI" in env), ("TARGETED_ENABLED", "AI_EVIDENCE_TARGETED" in env),
                 ("READER_VERSION", ids[0]), ("EVIDENCE_POLICY_VERSION", ids[1])):
        monkeypatch.setattr(er, k, v)
    monkeypatch.setattr(er, "PROMPTS", {**er.PROMPTS, "read_field_context": "read-field-context-2026-09-30.1", "discover_region": "discover-region-2026-09-30.1"})
    return ids


def illegible():
    return {"label_text": "", "value": "", "legible": False, "other_values_in_crop": []}


class _Provider(KeyedProvider):
    """Keyed answers, plus the size of every image sent and the request timeouts (the deadline policy's trace)."""

    def complete(self, request):
        self.seen = getattr(self, "seen", []) + [(request.task, [Image.open(io.BytesIO(p.png)).size for p in request.parts if hasattr(p, "png")], request.timeout_s)]
        return super().complete(request)


def _answers(page, clip, *, roi, identity_read):
    full = {**crop_answer(page, page.rect), "own_identity_region": [int(v) for v in _norm(page, page.rect, "DRAWING NO X-SD-1")],
            "own_revision_region": [int(v) for v in _norm(page, page.rect, "REV 02")]}
    return {("discover_region" if roi else "discover_page", None, "small"): crop_answer(page, clip) if roi else full,
            ("read_identity", "identity", "small"): identity_read, ("read_revision", "revision", "small"): read("02"),
            ("read_field_context", "identity", "small"): {"value": "X-SD-1", "printed_label": "DRAWING NO", "role": "own_identity",
                                                          "region": [0, 0, 1000, 1000], "legible": True}}


def _norm(page, clip, literal):
    r = page.search_for(literal)[0] * page.rotation_matrix
    return [(r.x0 - clip.x0) / clip.width * 1000 - 3, (r.y0 - clip.y0) / clip.height * 1000 - 3, (r.x1 - clip.x0) / clip.width * 1000 + 3, (r.y1 - clip.y0) / clip.height * 1000 + 3]


class _Clock:
    def __init__(self, remaining):
        self.inner = JobBudget(limits=Limits(100000, 100000, 12, 1000, 0.0, 120.0, 2, 0.0, 0.0, 0.0), calls_today_before=0)
        self.left = remaining

    def remaining_s(self):
        return self.left

    def __getattr__(self, name):
        return getattr(self.inner, name)


@pytest.mark.parametrize("arm", ["L1", "L2", "L3", "L4"])
def test_arm_configuration_on_a_rotated_sheet(db_session, tmp_path, monkeypatch, arm):
    """L1 / L3: whole-page discovery; L2 / L4: the real located crop. The primary identity read is illegible, so the
    optional targeted read fires in L3 / L4 only. Rotation-correct support (Rsup) validates the revision in EVERY arm on a
    270-degree page; the deadline policy stamps every request's timeout in every arm."""
    ids = _set(monkeypatch, arm)
    roi, x = arm in ("L2", "L4"), arm in ("L3", "L4")
    doc = sheet(rotation=270)
    page = doc[0]
    clip, route = _clip(page)
    s = Stage(db_session, tmp_path, doc, f"arm{arm}")
    p = _Provider(_answers(page, clip, roi=roi, identity_read=illegible()))
    ai = s.run(p)
    f = s.page_fields(ai)
    tasks = [t for t, _, _ in p.seen]
    assert tasks[0] == ("discover_region" if roi else "discover_page")
    w, h = p.seen[0][1][0]
    assert abs(w / h - (clip.width / clip.height if roi else page.rect.width / page.rect.height)) < 0.05, "the discovery image is the crop (ROI) or the whole page"
    assert tasks[1:3] == ["read_identity", "read_revision"], "required reads first, in the fixed order"
    assert ("read_field_context" in tasks) is x, "the optional targeted read is X only"
    assert f["own:revision"] == "completed" and s.selected(ai, "own:revision")[:2] == ("02", "validated"), "rotation-correct support in every arm"
    assert f["own:identity"] == ("completed" if x else "unusable:illegible") and (f.get("own:identity:targeted") == "completed") is x
    assert f["own:decision"] == (er.LOCATED_ABSENCE if roi else "absent_by_discovery")
    assert f.get("discovery:route") == (route if roi else None), "no located route is recorded when discovery saw the whole page (accepted behaviour)"
    assert all(t_s is not None for _, _, t_s in p.seen), "the deadline policy bounds every request (D common)"
    att = ai["attempts"][-1]
    assert att["version"] == ids[0] and att["policy"] == ids[1]


def test_arm_caches_never_cross_and_a_restart_of_the_same_arm_reuses_its_own(db_session, tmp_path, monkeypatch):
    doc = sheet(rotation=0)
    page = doc[0]
    clip, _ = _clip(page)
    s = Stage(db_session, tmp_path, doc, "cache")

    def run_keep_cache(provider):
        row = s.db.get(ProjectDocument, s.id)
        er.evidence_stage(s.db, s.project, [(row, s.path)], provider=provider, variant="EV1", profile="default")
        s.db.commit()
        s.db.expire_all()
        return s.db.get(ProjectDocument, s.id).extracted["ai_evidence"]

    _set(monkeypatch, "L1")
    p1 = _Provider(_answers(page, clip, roi=False, identity_read=read("X-SD-1")))
    run_keep_cache(p1)
    n1 = p1.calls
    _set(monkeypatch, "L1")
    p1b = _Provider(_answers(page, clip, roi=False, identity_read=read("X-SD-1")))
    ai = run_keep_cache(p1b)
    assert p1b.calls == 0 and all(c["cache_hit"] for c in ai["attempts"][-1]["calls"]), "a restart of the SAME arm reuses its own answers (no request)"
    _set(monkeypatch, "L2")
    p2 = _Provider(_answers(page, clip, roi=True, identity_read=read("X-SD-1")))
    ai = run_keep_cache(p2)
    assert p2.calls == n1 and not any(c["cache_hit"] for c in ai["attempts"][-1]["calls"]), "another arm never reuses L1's answers"
    assert db_session.query(ResultCache).count() == 2 * n1


def test_cap_refusal_is_a_recorded_budget_stop_in_the_common_scheduling(db_session, tmp_path, monkeypatch):
    _set(monkeypatch, "L3")
    doc = sheet(rotation=0)
    page = doc[0]
    clip, _ = _clip(page)
    two = JobBudget(limits=Limits(100000, 100000, 2, 1000, 0.0, 120.0, 2, 0.0, 0.0, 0.0), calls_today_before=0)
    p = _Provider(_answers(page, clip, roi=False, identity_read=illegible()))
    run = er.EvidenceRun(db=db_session, project_id=None, provider=p, budget=two, variant="EV1", fresh=True)
    out = er._read_page(run, page, sha256="c" * 64, number=1, facts=er.PageFacts(1, page.get_text(), [], []), reason="probe")
    f = out["_fields"]
    assert [t for t, _, _ in p.seen] == ["discover_page", "read_identity"], "the cap refuses the third request before dispatch"
    assert f["own:revision"] == "budget" and f["own:identity:targeted"] == "not_attempted:budget" and run.exhausted == "calls_per_document"


def test_deadline_floor_refuses_a_request_with_too_little_time_left(db_session, tmp_path, monkeypatch):
    _set(monkeypatch, "L2")
    doc = sheet(rotation=0)
    page = doc[0]
    p = _Provider({})
    run = er.EvidenceRun(db=db_session, project_id=None, provider=p, budget=_Clock(12.0), variant="EV1", fresh=True)
    out = er._read_page(run, page, sha256="d" * 64, number=1, facts=er.PageFacts(1, page.get_text(), [], []), reason="probe")
    assert p.calls == 0 and out["_fields"]["discovery"] == "budget" and run.exhausted == "elapsed_time"
