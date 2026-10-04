"""M2 review 08: field-level evidence lifecycle (R8-01), context-bound selection (R8-02), authoritative ledger scope
(R8-03) and BOQ heading outcome (R8-04). Scripted providers only -- no model is called.

The review 07 reader and ledger are pinned unchanged as `tests/fixtures/evidence_reader_r7.py` / `ledger_r7.py`;
the tests marked "before" show the defect there."""
import importlib.util
import json
import pathlib
import subprocess
import sys
import textwrap
import threading
from types import SimpleNamespace

import pymupdf
import pytest

from app.ai import evidence_reader as er
from app.ai import ledger as L
from app.ai.provider import RecordingProvider
from app.models import Project, ProjectDocument, ResultCache, RoleEnum

from .conftest import make_user

FIX = pathlib.Path(__file__).parent / "fixtures"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, FIX / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


old = _load("evidence_reader_r7")
old_ledger = _load("ledger_r7")

LEGEND = ["A = APPROVED", "B = APPROVED AS NOTED", "C = REVISE AND RESUBMIT"]


def timeout():
    e = RuntimeError("the CLI did not answer")
    e.kind = "timeout"
    return e


def discover(identity="X-SD-1", revision="", decision=None, other_numbers=()):
    region = [760, 900, 900, 950]
    d = decision or {}
    return {"page_kind": "review_form", "own_identity": identity, "own_identity_label": "Drawing No",
            "own_identity_region": region if identity else [], "own_revision": revision, "own_revision_label": "REV",
            "own_revision_region": [900, 900, 990, 950] if revision else [], "decision_options_printed": d.get("options", []),
            "decision_marked_option": d.get("marked", ""), "decision_mark_type": d.get("mark", "none"),
            "decision_actor": d.get("actor", "unknown"), "decision_region": [100, 100, 400, 300] if d else [],
            "other_numbers": list(other_numbers), "notes": ""}


def read(value):
    return {"label_text": "", "value": value, "legible": True, "other_values_in_crop": []}


def decision_read(marked="B = APPROVED AS NOTED", mark="tick"):
    return {"options_printed": LEGEND, "marked_option": marked, "mark_type": mark, "actor": "consultant", "legible": True}


APPROVAL = {"options": LEGEND, "marked": "B = APPROVED AS NOTED", "mark": "tick", "actor": "consultant"}


# --- what a consumer gets ----------------------------------------------------------------------------------------------
# The review 07 code had one accessor, `current_evidence(ai)`, which ignores the requested context; its consumers (the
# evaluator, the API) used it. These adapters call it on a prior candidate so that, run there, the tests fail on
# behaviour rather than on a missing name.


def select(ai, *, sha256, profile, variant, **kw):
    if hasattr(er, "evidence_for"):
        return er.evidence_for(ai, sha256=sha256, profile=profile, variant=variant, **kw)
    env = er.current_evidence(ai)
    if not env:
        return {"state": "unavailable"}
    pages = {}
    for pno, page in (env.get("pages") or {}).items():
        by = {}
        for o in page.get("observations") or []:
            by.setdefault(f"{o.get('component') or 'own'}:{o['field']}", {"observations": [], "status": "completed",
                                                                         "provenance": page.get("provenance") or {}, "history": []})["observations"].append(o)
        pages[pno] = {"fields": by}
    return {"state": "current", "envelope": {**env, "pages": pages}, "observations": env.get("observations") or [], "incomplete": []}


def last_known(ai):
    return er.last_known(ai) if hasattr(er, "last_known") else {"key": ai.get("current_key")}


def attempt_page(ai, n=-1, page="1"):
    got = ai["attempts"][n]["pages"].get(page)
    return got if isinstance(got, dict) else {"outcome": got, "fields": {}}


MISMATCH = getattr(L, "LedgerConfigMismatch", L.LedgerRefused)


# --- a persisted row read through the real stage entry point -----------------------------------------------------------


@pytest.fixture()
def doc_row(db_session, tmp_path, monkeypatch):
    from app.ai import submittal_reader

    monkeypatch.setattr(submittal_reader, "available", lambda project, provider=None: None)
    pdf = pymupdf.open()
    page = pdf.new_page(width=1684, height=1190)
    page.insert_text((1300, 1100), "Drawing No X-SD-1  REV 02", fontsize=9)
    page.insert_text((200, 200), "B = APPROVED AS NOTED", fontsize=9)
    path = tmp_path / "form.pdf"
    pdf.save(path)
    user = make_user(db_session, "r8@test.local", RoleEnum.admin)
    project = Project(ep_number="R8", project_name="r8", source_folder_path=str(tmp_path), created_by_id=user.id)
    db_session.add(project)
    db_session.flush()
    row = ProjectDocument(project_id=project.id, path=str(path), relative_path="form.pdf", filename="form.pdf", role="document",
                          state="fresh", sha256="8" * 64, extracted={"records": [], "observations": [], "profile": "default"})
    db_session.add(row)
    db_session.commit()
    return SimpleNamespace(db=db_session, project=project, id=row.id, path=path)


def stage(d, answers, *, profile="default", variant="EV1", provider=None):
    """One evidence-stage run on the persisted row, then a reload from the database (a fresh session view)."""
    d.db.query(ResultCache).delete()            # every step asks again: no answer comes back from the result cache
    d.db.commit()
    row = d.db.get(ProjectDocument, d.id)
    er.evidence_stage(d.db, d.project, [(row, d.path)], provider=provider or RecordingProvider(answers), variant=variant, profile=profile)
    d.db.commit()
    d.db.expire_all()
    return d.db.get(ProjectDocument, d.id).extracted["ai_evidence"]


def fields(ai, profile="default", variant="EV1"):
    got = select(ai, sha256="8" * 64, profile=profile, variant=variant)
    assert got["state"] == "current", got
    return got["envelope"]["pages"]["1"]["fields"]


def value(ai, key, **ctx):
    entry = fields(ai, **ctx)[key]
    return entry["observations"][0].get("value"), entry["observations"][0].get("state"), entry["provenance"]["attempt"], entry["status"]


# --- R8-01 ---------------------------------------------------------------------------------------------------------------


def test_a_blind_identity_timeout_keeps_the_old_decision_and_identity(doc_row):
    ai = stage(doc_row, [discover("X-SD-1", decision=APPROVAL), read("X-SD-1"), decision_read()])
    assert value(ai, "own:identity")[:2] == ("X-SD-1", "validated") and value(ai, "own:decision")[:2] == ("ANN", "validated")
    # the reviewer's case: discovery succeeds (it sees the identity only), the blind identity read times out
    ai = stage(doc_row, [discover("X-SD-1"), timeout()])
    assert value(ai, "own:decision") == ("ANN", "validated", 1, "completed"), "the old decision survives"
    assert value(ai, "own:identity") == ("X-SD-1", "validated", 1, "completed")
    page = attempt_page(ai)
    assert page["outcome"] == "partial" and page["fields"]["own:identity"] == "failed:timeout"
    assert page["fields"]["own:decision"] == "absent_by_discovery"
    # discovery sees the decision block too, and both blind reads time out: still nothing replaced
    ai = stage(doc_row, [discover("X-SD-1", decision=APPROVAL), timeout(), timeout()])
    assert attempt_page(ai)["fields"]["own:decision"] == "failed:timeout"
    assert value(ai, "own:decision") == ("ANN", "validated", 1, "completed") and ai["attempts"][-1].get("changed") == []


def test_before_a_blind_identity_timeout_replaced_the_good_page():
    run = SimpleNamespace(**_scripted_run([discover("X-SD-1"), None]))
    found = old._read_page(run, _blank_page(), sha256="s", number=1, facts=old.PageFacts(1, "", [], []), reason="t")
    merged = old.merge_evidence(_old_good(), {"attempt": 2, "outcome": "complete", "observations": found["_observations"],
                                               "coverage": {"pages": [{"page": 1, "outcome": found["_outcome"]}]}},
                                sha256="s", profile="default", variant="EV1")
    assert found["_outcome"] == "evidence"
    assert [(o["field"], o["state"]) for o in old.current_evidence(merged)["observations"]] == [("identity", "candidate")]
    # the review 08 reader records the same page as partial, and the merge keeps both validated fields
    run = SimpleNamespace(**_scripted_run([discover("X-SD-1"), None]))
    found = er._read_page(run, _blank_page(), sha256="s", number=1, facts=er.PageFacts(1, "", [], []), reason="t")
    assert found["_outcome"] == "partial" and found["_fields"]["own:identity"].startswith("failed")
    merged = er.merge_evidence(_old_good(new=True), {"attempt": 2, "outcome": "complete", "observations": found["_observations"],
                                                      "coverage": {"pages": [{"page": 1, "outcome": found["_outcome"], "fields": found["_fields"]}]}},
                               sha256="s", profile="default", variant="EV1")
    got = select(merged, sha256="s", profile="default", variant="EV1")
    assert [(o["field"], o["state"]) for o in got["observations"]] == [("decision", "validated"), ("identity", "validated")]


def test_a_budget_attempt_without_field_outcomes_never_overwrites_with_a_candidate():
    """The reviewer's third probe: an attempt that recorded no field outcomes (pre-review-08 shape)."""
    candidate = {"attempt": 3, "outcome": "budget", "observations": [dict(page=1, field="identity", value="X-SD-NEW", state="candidate")],
                 "coverage": {"pages": [{"page": 1, "outcome": "evidence"}, {"page": 2, "outcome": "budget: requests"}]}}
    before = old.merge_evidence(_old_good(), candidate, sha256="s", profile="default", variant="EV1")
    assert [o["value"] for o in old.current_evidence(before)["observations"]] == ["X-SD-NEW"]
    after = er.merge_evidence(_old_good(new=True), candidate, sha256="s", profile="default", variant="EV1")
    got = select(after, sha256="s", profile="default", variant="EV1")
    assert [(o["field"], o["value"]) for o in got["observations"]] == [("decision", "ANN"), ("identity", "X-SD-1")]
    assert after["attempts"][-1].get("changed") == []


def test_identity_completes_while_revision_times_out_and_decision_is_refused_by_budget(doc_row, tmp_path):
    ai = stage(doc_row, [discover("X-SD-1", revision="02", decision=APPROVAL), read("X-SD-1"), read("02"), decision_read()])
    assert value(ai, "own:revision")[:2] == ("02", "validated")
    # step 2: a fresh ledger admits discovery, identity and revision (which times out); the decision read is refused
    led = L.Ledger(str(tmp_path / "led.sqlite"), "r8", L.Limits(requests=3))
    inner = RecordingProvider([discover("X-SD-9", revision="03", decision=APPROVAL), read("X-SD-9"), timeout()])
    inner.name = "claude-code"
    ai = stage(doc_row, None, provider=L.LedgerProvider(inner, led))
    assert value(ai, "own:revision") == ("02", "validated", 1, "completed"), "the timed-out read replaces nothing"
    assert value(ai, "own:decision")[:3] == ("ANN", "validated", 1), "the refused read replaces nothing"
    assert value(ai, "own:identity")[0] == "X-SD-9" and value(ai, "own:identity")[2] == 2, "the completed read replaces"
    f = attempt_page(ai)["fields"]
    assert f["own:identity"] == "completed" and f["own:revision"] == "failed:timeout" and f["own:decision"] == "budget"


def test_one_component_completes_and_another_fails_without_contaminating_each_other(doc_row):
    ai = stage(doc_row, [discover("X-SD-1", other_numbers=[{"role": "listed_item", "literal": "L-100"}]), read("X-SD-1")])
    assert value(ai, "ref0:identity")[0] == "L-100"
    ai = stage(doc_row, [discover("X-SD-1", other_numbers=[{"role": "listed_item", "literal": "L-200"}]), timeout()])
    assert value(ai, "ref0:identity")[:3] == ("L-200", "observed_reference", 2), "the reference component completed"
    assert value(ai, "own:identity")[:3] == ("X-SD-1", "validated", 1), "the own component failed and keeps its evidence"


def test_a_later_resume_completes_the_missing_work_with_its_own_provenance(doc_row):
    stage(doc_row, [discover("X-SD-1", revision="02"), read("X-SD-1"), read("02")])
    stage(doc_row, [discover("X-SD-1", revision="02"), timeout(), timeout()])
    ai = stage(doc_row, [discover("X-SD-1", revision="02"), read("X-SD-1"), read("02")])
    assert value(ai, "own:revision")[:3] == ("02", "validated", 3)
    entry = fields(ai)["own:revision"]
    assert [h["provenance"]["attempt"] for h in entry["history"]] == [1], "the replaced value is kept with its own provenance"
    assert [attempt_page(ai, n)["outcome"] for n in range(len(ai["attempts"]))] == ["evidence", "partial", "evidence"]


def test_a_completed_negative_supersedes_but_absence_by_discovery_or_a_failure_never_does(doc_row):
    stage(doc_row, [discover("X-SD-1", decision=APPROVAL), read("X-SD-1"), decision_read()])
    # discovery sees no decision block: its region is never read -- not a negative
    ai = stage(doc_row, [discover("X-SD-1"), read("X-SD-1")])
    assert value(ai, "own:decision")[:3] == ("ANN", "validated", 1)
    assert attempt_page(ai)["fields"]["own:decision"] == "absent_by_discovery"
    # discovery fails: the page is not visited -- nothing changes
    ai = stage(doc_row, [timeout()])
    assert attempt_page(ai)["outcome"] == "failed" and value(ai, "own:decision")[:3] == ("ANN", "validated", 1)
    # the block is read, and it is unmarked: a completed, source-supported negative supersedes (the approval is history)
    ai = stage(doc_row, [discover("X-SD-1", decision={"options": LEGEND, "marked": "", "mark": "none", "actor": "consultant"}),
                         read("X-SD-1"), decision_read(marked="", mark="none")])
    entry = fields(ai)["own:decision"]
    assert entry["observations"][0]["state"] == "no_decision_marked" and entry["status"] == "completed"
    assert entry["history"][-1]["observations"][0]["value"] == "ANN"


def test_a_field_known_only_from_an_unsuccessful_read_is_incomplete_never_verified(doc_row):
    ai = stage(doc_row, [discover("X-SD-7"), timeout()])
    entry = fields(ai)["own:identity"]
    assert entry["status"] == "incomplete" and entry["observations"][0]["state"] == "candidate"
    got = select(ai, sha256="8" * 64, profile="default", variant="EV1")
    assert got["incomplete"] == ["1:own:identity"]
    ai = stage(doc_row, [discover("X-SD-1"), read("X-SD-1")])
    assert value(ai, "own:identity")[:2] == ("X-SD-1", "validated") and fields(ai)["own:identity"]["status"] == "completed"


def _scripted_run(answers):
    answers = list(answers)
    log = []

    def call(**kw):
        a = answers.pop(0)
        log.append({"outcome": "ok" if a is not None else "timeout"})
        return a
    return {"call": call, "variant": "EV1", "profile": "default", "escalations": 0, "exhausted": None, "log": log}


def _blank_page():
    pdf = pymupdf.open()
    page = pdf.new_page(width=1684, height=1190)
    page.insert_text((1300, 1100), "Drawing No X-SD-1", fontsize=9)
    return page


def _old_good(new=False):
    obs = [dict(page=1, field="identity", value="X-SD-1", state="validated"), dict(page=1, field="decision", value="ANN", state="validated")]
    mod = er if new else old
    return mod.merge_evidence(None, {"attempt": 1, "outcome": "complete", "observations": obs, "coverage": {"pages": [{"page": 1, "outcome": "evidence"}]}},
                              sha256="s", profile="default", variant="EV1")


# --- R8-02 ---------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("good, switched", [("default", "promoted"), ("promoted", "default")])
def test_a_failed_profile_switch_is_pending_never_the_other_profile(doc_row, good, switched):
    stage(doc_row, [discover("X-SD-1"), read("X-SD-1")], profile=good)
    ai = stage(doc_row, [timeout()], profile=switched)
    assert select(ai, sha256="8" * 64, profile=switched, variant="EV1")["state"] == "pending"
    assert select(ai, sha256="8" * 64, profile=good, variant="EV1")["state"] == "current"
    assert last_known(ai)["key"] == f"{good}|EV1", "history stays available, labelled as history"
    # a successful retry makes the requested context current, with its own provenance
    ai = stage(doc_row, [discover("X-SD-2"), read("X-SD-2")], profile=switched)
    got = select(ai, sha256="8" * 64, profile=switched, variant="EV1")
    assert got["state"] == "current" and got["observations"][0]["value"] == "X-SD-2" and got["observations"][0]["provenance"]["profile"] == switched


def test_before_a_failed_switch_returned_the_previous_profile_as_current():
    base = old.merge_evidence(None, {"attempt": 1, "outcome": "complete", "observations": [dict(page=1, field="identity", value="X", state="validated")],
                                     "coverage": {"pages": [{"page": 1, "outcome": "evidence"}]}}, sha256="s", profile="default", variant="EV1")
    failed = old.merge_evidence(base, {"attempt": 2, "outcome": "failed", "observations": [], "coverage": {"pages": []}}, sha256="s",
                                profile="promoted", variant="EV1")
    assert old.current_evidence(failed)["profile"] == "default"
    assert er.current_evidence(failed) == {"state": "context_required", "reason": "name the source hash, profile and variant (evidence_for)"}
    assert select(failed, sha256="s", profile="promoted", variant="EV1")["state"] == "pending"


def test_a_budget_stopped_variant_switch_and_changed_bytes(doc_row, tmp_path):
    stage(doc_row, [discover("X-SD-1"), read("X-SD-1")], variant="EV1")
    led = L.Ledger(str(tmp_path / "led.sqlite"), "r8b", L.Limits(requests=0))
    inner = RecordingProvider()
    inner.name = "claude-code"
    ai = stage(doc_row, None, variant="EV2", provider=L.LedgerProvider(inner, led))
    assert inner.calls == 0 and select(ai, sha256="8" * 64, profile="default", variant="EV2")["state"] == "pending"
    assert select(ai, sha256="8" * 64, profile="default", variant="EV1")["state"] == "current"
    assert select(ai, sha256="9" * 64, profile="default", variant="EV1")["state"] == "stale"


def test_unknown_legacy_profiles_are_used_only_when_the_caller_declares_them():
    legacy = {"version": "evidence-reader-2026-09-29.1", "policy": "evidence-policy-2026-09-29.1", "variant": "EV1", "read_sha256": "s",
              "observations": [{"page": 1, "field": "identity", "value": "L-1", "state": "validated"}]}
    assert select(legacy, sha256="s", profile="default", variant="EV1")["state"] == "unavailable"
    got = select(legacy, sha256="s", profile="default", variant="EV1", accept_unknown_profile=True)
    assert got["state"] == "current" and got["via"] and got["observations"][0]["field_status"] == "legacy"


def test_the_evaluator_scores_ai_evidence_only_for_the_declared_context():
    from scripts import m2_eval5 as ev

    doc = {"doc": "EP-1/a.pdf", "ep": "1", "cohort": "c", "stratum": "s", "extension": ".pdf", "scan_like": False, "confidence": "high",
           "labels": {"kind": "shop-drawing cover", "reference": "X-SD-1", "revision": "00", "decision": "rejected"}}
    ai = er.merge_evidence(None, {"attempt": 1, "outcome": "complete", "observations": [dict(page=1, field="identity", value="WRONG-9", state="validated")],
                                  "coverage": {"pages": [{"page": 1, "outcome": "evidence", "fields": {"own:identity": "completed"}}]}},
                           sha256="s", profile="default", variant="EV1")
    ai = er.merge_evidence(ai, {"attempt": 2, "outcome": "failed", "observations": [], "coverage": {"pages": []}}, sha256="s", profile="promoted", variant="EV1")
    rows = {"EP-1/a.pdf": {"state": "fresh", "sha256": "s", "extracted": {"records": [], "profile": "promoted", "coverage": {"outcome": "complete"}, "ai_evidence": ai}}}
    import inspect

    if "ai_context" not in inspect.signature(ev.evaluate).parameters:
        before = ev.evaluate({"documents": [doc]}, None, rows)
        assert before["totals"]["introduced_ai_errors"] == [], "the promoted run is scored with the default profile's evidence"
    promoted = ev.evaluate({"documents": [doc]}, None, rows, ai_context={"variant": "EV1"})
    assert promoted["totals"]["introduced_ai_errors"] == [] and promoted["totals"]["ai_evidence_states"] == {"pending": 1}
    default = ev.evaluate({"documents": [doc]}, None, rows, ai_context={"variant": "EV1", "profile": "default"})
    assert [c["value"] for c in default["totals"]["introduced_ai_errors"]] == ["WRONG-9"]
    assert ev.evaluate({"documents": [doc]}, None, rows)["totals"]["ai_evidence_states"] == {"no_context": 1}


# --- R8-03 ---------------------------------------------------------------------------------------------------------------


def test_the_reviewers_case_a_reopened_scope_cannot_loosen_its_saved_cap(tmp_path):
    path = str(tmp_path / "ledger.sqlite")
    first = L.Ledger(path, "fixed", L.Limits(requests=1))
    first.settle(first.reserve("t", 1, 1), input_tokens=1, output_tokens=1)
    with pytest.raises((MISMATCH, L.LedgerRefused)):
        L.Ledger(path, "fixed", L.Limits(requests=2)).reserve("t", 1, 1)       # no silent second reservation
    with pytest.raises(MISMATCH):
        L.Ledger(path, "fixed", L.Limits(requests=2))
    reopened = L.Ledger(path, "fixed")
    with pytest.raises(L.LedgerRefused):
        reopened.reserve("t", 1, 1)
    # before: the review 07 ledger took the looser handle's limit
    p2 = str(tmp_path / "old.sqlite")
    o1 = old_ledger.Ledger(p2, "fixed", old_ledger.Limits(requests=1))
    o1.settle(o1.reserve("t", 1, 1), input_tokens=1, output_tokens=1)
    old_ledger.Ledger(p2, "fixed", old_ledger.Limits(requests=2)).reserve("t", 1, 1)


def _child(code: str) -> subprocess.CompletedProcess:
    root = str(pathlib.Path(L.__file__).parents[2])
    return subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, {root!r})\n" + textwrap.dedent(code)],
                          capture_output=True, text=True)


def test_another_process_with_different_or_partial_limits(tmp_path):
    path = str(tmp_path / "ledger.sqlite")
    L.Ledger(path, "shared", L.Limits(requests=3, input_tokens=1000))
    different = _child(f"""
        from app.ai import ledger as L
        L.Ledger({path!r}, "shared", L.Limits(requests=5)).reserve("t", 1, 1)
    """)
    assert different.returncode != 0 and "LedgerConfigMismatch" in different.stderr
    stricter = _child(f"""
        from app.ai import ledger as L
        L.Ledger({path!r}, "shared", L.Limits(requests=2))
    """)
    assert stricter.returncode != 0 and "LedgerConfigMismatch" in stricter.stderr, "a stricter handle is a second policy too"
    partial = _child(f"""
        from app.ai import ledger as L
        led = L.Ledger({path!r}, "shared", L.Limits(requests=3))
        try:
            led.reserve("t", 2000, 1)
            print("RESERVED")
        except L.LedgerRefused as e:
            print("REFUSED", e.limit)
    """)
    assert partial.returncode == 0 and partial.stdout.strip() == "REFUSED input_tokens", "the stored input cap applies"


def test_simultaneous_workers_with_conflicting_settings(tmp_path):
    path = str(tmp_path / "ledger.sqlite")
    outcomes = []
    barrier = threading.Barrier(8)

    def worker(n):
        barrier.wait()
        try:
            led = L.Ledger(path, "race", L.Limits(requests=2 if n % 2 else 3))
            outcomes.append(("open", led.limits.requests))
        except MISMATCH:
            outcomes.append(("mismatch", None))

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    opened = {v for k, v in outcomes if k == "open"}
    assert len(opened) == 1, "one policy wins the creation; every handle that opened agrees with it"
    assert sum(1 for k, _ in outcomes if k == "mismatch") == 4


def test_restart_after_reservations_a_timeout_and_settlement(tmp_path):
    path = str(tmp_path / "ledger.sqlite")
    led = L.Ledger(path, "restart", L.Limits(requests=3, output_tokens=100))
    done = led.reserve("t", 50, 40)
    in_flight = led.reserve("t", 50, 40)
    led.settle(done, input_tokens=60, output_tokens=30)
    del led                                                     # the worker dies with a request in flight
    again = L.Ledger(path, "restart")
    assert again.totals()["in_flight"] == 1 and again.limits.output_tokens == 100
    again.settle(in_flight, input_tokens=None, output_tokens=None, outcome="timeout")   # unknown usage: charged at its reservation
    t = again.totals()
    assert t["usage_unknown"] == 1 and t["output_tokens"] == 70 and t["in_flight"] == 0
    with pytest.raises(L.LedgerRefused) as exc:
        again.reserve("t", 50, 40)                              # 70 + 40 > 100: the stored output cap
    assert exc.value.limit == "output_tokens"


def test_input_output_and_time_caps_are_one_scope_policy(tmp_path):
    path = str(tmp_path / "ledger.sqlite")
    L.Ledger(path, "caps", L.Limits(input_tokens=500, output_tokens=50, elapsed_s=3600))
    for looser in (L.Limits(input_tokens=5000), L.Limits(output_tokens=500), L.Limits(elapsed_s=7200)):
        with pytest.raises(MISMATCH):
            L.Ledger(path, "caps", looser)
    led = L.Ledger(path, "caps", L.Limits(elapsed_s=3600))
    with pytest.raises(L.LedgerRefused) as exc:
        led.reserve("t", 600, 1)
    assert exc.value.limit == "input_tokens"


def test_an_authorised_amendment_is_explicit_versioned_and_audited(tmp_path):
    path = str(tmp_path / "ledger.sqlite")
    led = L.Ledger(path, "amend", L.Limits(requests=1))
    led.settle(led.reserve("t", 1, 1), input_tokens=1, output_tokens=1)
    with pytest.raises(ValueError):
        led.amend_limits(L.Limits(requests=2), authorized_by="", reason="more")
    result = led.amend_limits(L.Limits(requests=2), authorized_by="owner (test)", reason="declared addendum")
    assert result["version"] == 2 and result["old"] == {"requests": 1}
    led.reserve("t", 1, 1)
    audit = led.amendments()
    assert [(a["version"], json.loads(a["new"]), a["authorized_by"]) for a in audit] == [(2, {"requests": 2}, "owner (test)")]
    with pytest.raises(MISMATCH):
        L.Ledger(path, "amend", L.Limits(requests=1)), "a handle on the earlier version is refused"
    assert L.Ledger(path, "amend", L.Limits(requests=2)).effective_limits().requests == 2


# --- R8-04 ---------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("row, blind, state, row_type", [
    ({"part_number": "P-1", "quantity": None}, {"row_is_heading": True, "legible": True}, "conflict", "disputed"),   # part-only row
    ({"part_number": None, "quantity": "3"}, {"row_is_heading": True, "legible": True}, "conflict", "disputed"),
    ({"part_number": None, "quantity": None}, {"row_is_heading": True, "legible": True, "description": "FIRE ALARM PANEL"}, "not_an_item", "heading_confirmed"),
    ({"part_number": None, "quantity": None}, {"row_is_heading": True, "legible": True, "description": "( 2 ) Dual Input Module"}, "conflict", "disputed"),
    ({"part_number": None, "quantity": None}, {"row_is_heading": True, "legible": False}, "unverified", "unverified"),
])
def test_a_heading_answer_is_a_row_type_outcome_never_validated_data(row, blind, state, row_type):
    got = er.validate_boq_row(row, blind)
    assert (got["state"], got.get("row_type")) == (state, row_type) and got["state"] != "validated"


def test_before_a_heading_answer_validated_a_part_only_row():
    assert old.validate_boq_row({"part_number": "P-1", "quantity": None}, {"row_is_heading": True, "legible": True})["state"] == "validated"


def test_part_and_quantity_stay_separate_for_absent_and_unreadable_quantities():
    part_only = er.validate_boq_row({"part_number": "P-1", "quantity": "2"}, {"part_number": "P-1", "quantity": "", "legible": True})
    assert part_only["state"] == "part_verified_quantity_unverified"
    unreadable = er.validate_boq_row({"part_number": "P-1", "quantity": "2"}, {"part_number": "P-1", "quantity": "2", "legible": False})
    assert unreadable["state"] == "unverified"
    counted = er.validate_boq_row({"part_number": "P-1", "quantity": "2"}, {"part_number": "P-1", "quantity": "", "description": "( 2 ) Module", "legible": True})
    assert counted["state"] == "validated" and counted["quantity_source"] == "description_count"
