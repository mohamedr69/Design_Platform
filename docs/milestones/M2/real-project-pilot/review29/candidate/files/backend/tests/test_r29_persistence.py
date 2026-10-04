"""Review 29 -- feature isolation, identities, persistence, cache, retry, profile and repeated processing. Each switch has
its own identity (bound into every cache key and attempt); none implies another; CA / DR / PA refuse to start without
the explicit required-first scheduling; flags off are the accepted identities. No model."""
import pytest

from app.ai import evidence_reader as er
from app.models import ProjectDocument, ResultCache

from ._keyed_provider import KeyedProvider, failure
from ._r29 import (configure, decision_read, discovery, env_for, identities, no_submittal_reader, norm_region,  # noqa: F401
                   text_page, value_read)
from .test_ai_pilot_r19 import Stage

ACCEPTED = ("evidence-reader-2026-09-29.7", "evidence-policy-2026-09-29.4")
L3 = ("evidence-reader-2026-09-29.7+targeted-2026-09-30.2+deadline-2026-09-30.1",
      "evidence-policy-2026-09-29.4+guard-rev-token-2026-09-30.1+region-support-2026-09-30.1+targeted-completion-2026-09-30.2")
SUFFIX = {"ig": ("", "+identity-role-guard-2026-10-02.2"), "ca": ("", "+conflict-adjudication-2026-10-02.2"),
          "dr": ("+decision-region-2026-10-02.1", "+decision-region-2026-10-02.1"), "pa": ("", "+page-association-2026-10-02.1")}


@pytest.fixture(autouse=True)
def _ready(no_submittal_reader):
    yield


def test_flags_off_identities_are_the_accepted_ones_and_the_frozen_arms_are_unchanged():
    assert identities({})[:2] == ACCEPTED
    assert identities(env_for(x=True))[:2] == L3, "the frozen L3 identity is byte-for-byte unchanged"
    assert "locate_decision" not in identities(env_for(x=True))[2]


@pytest.mark.parametrize("flag", ["ig", "ca", "dr", "pa"])
def test_each_switch_adds_only_its_own_suffix(flag):
    reader, policy, prompts = identities(env_for(x=True, **{flag: True}))
    assert reader == L3[0] + SUFFIX[flag][0] and policy == L3[1] + SUFFIX[flag][1]
    assert ("locate_decision" in prompts) is (flag == "dr")


def test_combined_identity_is_the_four_suffixes_in_order():
    reader, policy, _ = identities(env_for(x=True, ig=True, ca=True, dr=True, pa=True))
    assert reader == L3[0] + "+decision-region-2026-10-02.1"
    assert policy == L3[1] + "+identity-role-guard-2026-10-02.2+conflict-adjudication-2026-10-02.2+decision-region-2026-10-02.1+page-association-2026-10-02.1"


@pytest.mark.parametrize("var", ["AI_EVIDENCE_ADJUDICATE", "AI_EVIDENCE_DECISION_REGION", "AI_EVIDENCE_ASSOC"])
def test_no_scheduling_is_ever_implied(var):
    with pytest.raises(RuntimeError, match="requires AI_EVIDENCE_SCHEDULING=required_first"):
        identities({var: "1"})
    with pytest.raises(RuntimeError, match="requires AI_EVIDENCE_SCHEDULING=required_first"):
        identities({var: "1", "AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_TARGETED": "1"}), "not even through T's legacy implication"
    assert identities({"AI_EVIDENCE_IDGUARD": "1"})[1] == ACCEPTED[1] + "+identity-role-guard-2026-10-02.2", "IG needs no scheduling"


def _doc():
    return text_page([(0.10, 0.20, "Submittal No. 42", 11), (0.40, 0.20, "Rev 00", 11), (0.10, 0.24, "Dwg. Ref. AB-12-345", 11),
                      (0.10, 0.55, "CONSULTANT STATUS: A - APPROVED   B - APPROVED AS NOTED", 9),
                      *[(0.1, 0.30 + 0.012 * i, f"Item {i} cable tray support bracket detail and fixing schedule text", 8) for i in range(30)]])


LEGEND = ["A - APPROVED", "B - APPROVED AS NOTED"]


def _answers(page, *, decision=None):
    return {("discover_page", None, "small"): discovery(page_kind="submittal_form", own_identity="42", own_identity_label="Submittal No.",
                                                        own_identity_region=norm_region(page, "Submittal No. 42"), own_revision="00",
                                                        own_revision_label="Rev", own_revision_region=norm_region(page, "Rev 00")),
            ("read_identity", "identity", "small"): value_read("42", "Submittal No."), ("read_revision", "revision", "small"): value_read("00", "Rev"),
            ("read_decision", "decision", "small"): decision if decision is not None else [decision_read("B", LEGEND), decision_read("B", LEGEND)]}


def _run_keep_cache(s, provider):
    row = s.db.get(ProjectDocument, s.id)
    er.evidence_stage(s.db, s.project, [(row, s.path)], provider=provider, variant="EV1", profile="default")
    s.db.commit()
    s.db.expire_all()
    return s.db.get(ProjectDocument, s.id).extracted["ai_evidence"]


def test_configurations_never_share_answers_and_a_repeat_of_one_reuses_only_its_own(db_session, tmp_path, monkeypatch):
    doc = _doc()
    page = doc[0]
    s = Stage(db_session, tmp_path, doc, "iso")
    s.db.query(ResultCache).delete()
    s.db.commit()
    configure(monkeypatch, ig=True, dr=True)
    p1 = KeyedProvider(_answers(page))
    ai1 = _run_keep_cache(s, p1)
    n = p1.calls
    obs1 = er.evidence_for(ai1, sha256=s.sha, profile="default", variant="EV1")["envelope"]["observations"]
    configure(monkeypatch, ig=True, dr=True)
    p2 = KeyedProvider(_answers(page))
    ai2 = _run_keep_cache(s, p2)
    assert p2.calls == 0 and all(c["cache_hit"] for c in ai2["attempts"][-1]["calls"]), "repeated processing: its own answers, no request"
    strip = lambda obs: [{k: v for k, v in o.items() if k != "provenance"} for o in obs]
    assert strip(er.evidence_for(ai2, sha256=s.sha, profile="default", variant="EV1")["envelope"]["observations"]) == strip(obs1), "idempotent"
    configure(monkeypatch, dr=True)
    p3 = KeyedProvider(_answers(page))
    ai3 = _run_keep_cache(s, p3)
    assert p3.calls == n and not any(c["cache_hit"] for c in ai3["attempts"][-1]["calls"]), "another switch set never reuses IG+DR answers"
    policies = [a["policy"] for a in ai3["attempts"]]
    assert len(set(policies)) == 2 and policies[-1].endswith("+decision-region-2026-10-02.1") and "+identity-role-guard" in policies[0]


def test_a_failed_decision_read_is_retried_and_the_last_good_evidence_kept(db_session, tmp_path, monkeypatch):
    doc = _doc()
    page = doc[0]
    s = Stage(db_session, tmp_path, doc, "retry")
    s.db.query(ResultCache).delete()
    s.db.commit()
    configure(monkeypatch, dr=True)
    ai = _run_keep_cache(s, KeyedProvider(_answers(page, decision=failure("timeout"))))
    assert s.page_fields(ai)["own:decision"].startswith("failed")
    configure(monkeypatch, dr=True)
    p = KeyedProvider(_answers(page))
    ai = _run_keep_cache(s, p)
    assert p.requests.count(("read_decision", "decision", "small")) == 2 and p.requests.count(("discover_page", None, "small")) == 0, \
        "only the failed read is requested again; the discovery and value reads come from this switch set's own cache"
    assert s.page_fields(ai)["own:decision"] == er.COMPLETED
    dec = [o for o in er.evidence_for(ai, sha256=s.sha, profile="default", variant="EV1")["envelope"]["observations"] if o.get("field") == "decision"]
    assert dec and dec[0]["value"] == "ANN"


def test_profile_and_variant_keep_their_own_envelopes(db_session, tmp_path, monkeypatch):
    doc = _doc()
    page = doc[0]
    s = Stage(db_session, tmp_path, doc, "profile")
    configure(monkeypatch, ig=True)
    _run_keep_cache(s, KeyedProvider(_answers(page)))
    row = s.db.get(ProjectDocument, s.id)
    er.evidence_stage(s.db, s.project, [(row, s.path)], provider=KeyedProvider(_answers(page)), variant="EV1", profile="strict")
    s.db.commit()
    s.db.expire_all()
    ai = s.db.get(ProjectDocument, s.id).extracted["ai_evidence"]
    assert set(ai["envelopes"]) == {"default|EV1", "strict|EV1"}
    assert er.evidence_for(ai, sha256=s.sha, profile="default", variant="EV1")["state"] == "current"
    assert er.evidence_for(ai, sha256=s.sha, profile="strict", variant="EV1")["state"] == "current"
