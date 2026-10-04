"""Harness v4 tests (offline, synthetic): the v3 coverage / harness cases re-pointed at v4 (behaviour unchanged) plus the
Review 22 contracts: (R22-01) eligibility binding through the ACTUAL scoring entry point (score_arm, the function
main() calls) -- correct-source control, planned-source mismatch, missing required hash, wrong arm / context, mixed
valid / invalid rows with an unchanged denominator, and the reviewer's all-mismatch example emitting no valid claim;
(R22-02) page bounds: page 3 of a one-page PDF, page 1 control, page 3 of a six-page PDF (in scope), page 5 of a
six-page PDF (beyond the reader scope), invalid page identifiers failing closed -- and the same carried through main()
on a copy of the stored dry runs with injected facts. Run: pytest test_harness_v4.py (cwd harness-v4)."""
import hashlib
import json
import os
import pathlib
import shutil
import sys

import pytest

import coverage_v4 as cv
import score_arms_v4 as sa

CTX = {"variant": "EV1", "profile": "default", "policy": "pol-L1"}
PLAN = [{"doc": "d1", "sha256": "a" * 64, "pages": 1, "extension": ".pdf"}, {"doc": "d6", "sha256": "b" * 64, "pages": 6, "extension": ".pdf"},
        {"doc": "w", "sha256": "c" * 64, "pages": None, "extension": ".docx"}, {"doc": "gone", "sha256": "d" * 64, "pages": 2, "extension": ".pdf"}]


def full(ident="completed", rev="completed", dec="absent_by_discovery"):
    return {"outcome": "evidence", "fields": {"own:identity": ident, "own:revision": rev, "own:decision": dec}}


def attempt(pages, *, policy="pol-L1", read="a" * 64, calls=None):
    return {"policy": policy, "profile": "default", "variant": "EV1", "read_sha256": read, "pages": pages, "calls": calls or [{"outcome": "ok"}]}


def row(sha, attempts, obs=None):
    env = {"default|EV1": {"profile": "default", "variant": "EV1", "pages": obs or {}}}
    return {"sha256": sha, "extracted": {"ai_evidence": {"attempts": attempts, "envelopes": env}}}


# --- v3 behaviour kept -------------------------------------------------------------------------------------------------


def test_binding_rejects_source_context_and_policy_mismatches():
    p = PLAN[0]
    assert cv.select_attempt(None, p, CTX) == (None, "no_row")
    assert cv.select_attempt(row("z" * 64, [attempt({"1": full()})]), p, CTX)[1] == "source_mismatch"
    assert cv.select_attempt(row("a" * 64, [attempt({"1": full()}, policy="pol-L2")]), p, CTX)[1] == "context_mismatch"
    assert cv.select_attempt(row("a" * 64, [attempt({"1": full()}, read="q" * 64)]), p, CTX)[1] == "not_attempted"
    assert cv.select_attempt(row("a" * 64, [attempt({"1": full()})]), {**p, "sha256": ""}, CTX)[1] == "planned_hash_missing"


def test_mixed_supported_unsupported_and_missing_pages_and_unattempted_documents():
    rows = {"d1": row("a" * 64, [attempt({"1": full()})]), "d6": row("b" * 64, [attempt({"1": full(), "2": full(), "3": {"outcome": "no_trigger"}}, read="b" * 64)])}
    c = sa.arm_coverage(PLAN, rows, CTX, max_pages=4)
    s = c["summary"]
    assert s["documents_planned"] == 4 and s["documents_unsupported_input"] == 1 and s["documents_unattempted"] == 1
    d6 = next(d for d in c["documents"] if d["doc"] == "d6")
    assert d6["pages"]["4"]["own:identity"] == "missing_page" and d6["pages"]["5"]["own:identity"] == "unsupported:beyond_reader_scope" and d6["state"] == "incomplete"
    assert s["complete_ids"] == ["d1"] and c["transport"]["gone"] == "not_attempted"


def test_transport_success_with_unusable_fields_is_not_coverage():
    c = sa.arm_coverage(PLAN[:1], {"d1": row("a" * 64, [attempt({"1": full("unusable:illegible", "incomplete:no_region", "incomplete:located_region_only")})])}, CTX, max_pages=4)
    assert c["transport"]["d1"] == "no_transport_stop" and c["summary"]["documents_required_complete"] == 0


def test_field_specific_matched_subsets_with_ids():
    a = sa.arm_coverage(PLAN[:2], {"d1": row("a" * 64, [attempt({"1": full()})]), "d6": row("b" * 64, [attempt({str(i): full() for i in range(1, 5)}, read="b" * 64)])}, CTX, max_pages=4)
    b = sa.arm_coverage(PLAN[:2], {"d1": row("a" * 64, [attempt({"1": full(rev="budget")})]), "d6": row("b" * 64, [attempt({str(i): full() for i in range(1, 5)}, read="b" * 64)])}, CTX, max_pages=4)
    assert sa.field_read_in_both(a, b, "own:identity", PLAN[:2]) == ["d1", "d6"] and sa.field_read_in_both(a, b, "own:revision", PLAN[:2]) == ["d6"]
    assert sa.field_read_in_both(a, b, "own:decision", PLAN[:2]) == []


# --- R22-02: page bounds ---------------------------------------------------------------------------------------------------


def _fact(page, policy="pol-L1"):
    return {str(page): {"fields": {"own:identity": {"observations": [{"field": "identity", "value": "X-3", "state": "validated", "policy": policy}]}}}}


@pytest.mark.parametrize("plan, page, why", [
    (PLAN[0], 3, ["page_not_in_document"]), (PLAN[0], 1, []), (PLAN[1], 3, []), (PLAN[1], 5, ["page_beyond_reader_scope"]),
    (PLAN[1], 7, ["page_not_in_document"]), (PLAN[0], "x", ["invalid_page_identifier"]), (PLAN[0], "0", ["invalid_page_identifier"]), (PLAN[0], "1.5", ["invalid_page_identifier"]),
], ids=["p3-of-1", "p1-of-1-control", "p3-of-6-in-scope", "p5-of-6-beyond-reader", "p7-of-6-nonexistent", "non-numeric", "zero", "fractional"])
def test_page_position_against_document_and_reader_ranges(plan, page, why):
    r = row(plan["sha256"], [], _fact(page))
    got = cv.extra_facts(r, plan, CTX, max_pages=4)
    assert ([g["why"] for g in got] == [why]) if why else got == []


def test_extra_facts_keep_other_context_rules_and_unplanned_documents():
    r = row("b" * 64, [], {**_fact(2, policy="pol-OTHER"), **_fact(9)})
    why = sorted(tuple(x["why"]) for x in cv.extra_facts(r, PLAN[1], CTX, max_pages=4))
    assert why == [("other_policy",), ("page_not_in_document",)]
    assert [x["why"] for x in cv.extra_facts({"sha256": "e" * 64, "extracted": {"ai_evidence": {"envelopes": {"default|EV1": {"profile": "default", "variant": "EV1", "pages": _fact(1)}}}}}, None, CTX, max_pages=4)] == [["unplanned_document"]]


# --- R22-01: eligibility through the actual scoring entry point -----------------------------------------------------------


HERE = pathlib.Path(__file__).resolve().parent
LABELS = pathlib.Path("C:/t/iso/work/r2x/review21/labels-dry")
DRY_DECL = pathlib.Path("C:/t/r2x/dry-runs/R21-DECLARATION.dry.json")


@pytest.fixture(scope="module")
def evaluator():
    os.environ.setdefault("AI_ENABLED", "false")
    os.environ.setdefault("DATABASE_URL", "sqlite:///C:/t/iso/tmp/score-no-db.db")
    for k in list(os.environ):
        if k.startswith("AI_EVIDENCE_"):
            os.environ.pop(k)
    sys.path.insert(0, "C:/t/iso/frozen-r12/backend")
    cwd = os.getcwd()
    os.chdir("C:/t/iso/frozen-r12/backend")
    from scripts import m2_eval5 as EV
    os.chdir(cwd)
    return EV


@pytest.fixture(scope="module")
def stored():
    """The stored synthetic dry run (L1) and its declaration: a real end-to-end input of the scorer."""
    decl = json.loads(DRY_DECL.read_text(encoding="utf-8"))
    rows = json.loads(pathlib.Path("C:/t/r2x/dry-runs/r21dry-L1/out/rows.json").read_text(encoding="utf-8"))
    reg = json.loads((LABELS / "DRY-REGISTER-LABELS.json").read_text(encoding="utf-8"))
    page = json.loads((LABELS / "DRY-PAGE-LABELS.json").read_text(encoding="utf-8"))
    ctx = {"variant": "EV1", "profile": "default", "policies": [decl["arms"]["L1"]["identities"]["EVIDENCE_POLICY_VERSION"]]}
    return decl, rows, reg, page, ctx


def _score(EV, st, planned, rows):
    decl, _, reg, page, ctx = st
    ev, entry, cov = sa.score_arm(EV, reg, page, planned, rows, ctx, max_pages=4)
    return entry, cov


def test_correct_source_control_earns_recovery(evaluator, stored):
    decl, rows, *_ = stored
    entry, cov = _score(evaluator, stored, decl["sources"]["sample"]["documents_planned"], rows)
    assert entry["valid_accuracy_claim"] and entry["eligibility_counts"].get("eligible", 0) >= 1
    assert entry["recovery_all_planned"]["identity"]["recovery"].get("recovered_clean", 0) >= 1


def test_all_planned_sources_mismatched_emits_no_valid_claim(evaluator, stored):
    """The reviewer's example: every planned hash changed; the stored rows are unchanged."""
    decl, rows, *_ = stored
    planned = [dict(p, sha256="f" * 64) for p in decl["sources"]["sample"]["documents_planned"]]
    entry, cov = _score(evaluator, stored, planned, rows)
    assert not entry["valid_accuracy_claim"]
    assert all(v["state"] == "ineligible" for v in entry["eligibility"].values() if v["reason"] != "no_row")
    assert "INVALID" in entry["recovery_all_planned"]["identity"]["invalid_reason"]
    assert entry["recovery_all_planned"]["identity"]["recovery"].get("recovered_clean", 0) == 0
    assert cov["summary"]["documents_planned"] == len(planned) and cov["summary"]["binding_reasons"].get("source_mismatch") == 4
    assert len(entry["rejected_evidence"]) == 4


def test_missing_required_hash_is_ineligible(evaluator, stored):
    decl, rows, *_ = stored
    planned = [dict(p, sha256="") for p in decl["sources"]["sample"]["documents_planned"]]
    entry, cov = _score(evaluator, stored, planned, rows)
    assert not entry["valid_accuracy_claim"] and {v["reason"] for v in entry["eligibility"].values()} <= {"planned_hash_missing", "no_row"}


def test_wrong_arm_context_scores_the_raw_layer_only(evaluator, stored):
    decl, rows, reg, page, ctx = stored
    wrong = {**ctx, "policies": ["not-this-arm"]}
    planned = decl["sources"]["sample"]["documents_planned"]
    ev, entry, cov = sa.score_arm(evaluator, reg, page, planned, rows, wrong, max_pages=4)
    assert entry["eligibility_counts"].get("raw_only", 0) >= 1 and entry["eligibility_counts"].get("eligible", 0) == 0
    assert all(x["why"] == "ai_evidence_of_another_context" for x in entry["rejected_evidence"])
    ai = ev["totals"]["ai"]["fields"]["identity"]["recovery_counts"]
    assert ai.get("recovered_clean", 0) == 0 and ai.get("held_only", 0) == 0, "no AI credit from another arm's evidence"


def test_mixed_valid_and_invalid_rows_keep_the_denominator(evaluator, stored):
    decl, rows, *_ = stored
    planned = decl["sources"]["sample"]["documents_planned"]
    good, cov_good = _score(evaluator, stored, planned, rows)
    mixed = list(planned)
    mixed[0] = dict(mixed[0], sha256="f" * 64)
    entry, cov = _score(evaluator, stored, mixed, rows)
    assert entry["valid_accuracy_claim"] and entry["eligibility"][mixed[0]["doc"]]["state"] == "ineligible"
    assert cov["summary"]["documents_planned"] == cov_good["summary"]["documents_planned"] == len(planned)
    rec = lambda e: e["recovery_all_planned"]["identity"]["recovery"]
    readable = lambda r: sum(r.get(k, 0) for k in ("recovered_clean", "recovered_mixed", "wrong_only", "held_only", "missed"))
    assert readable(rec(entry)) == readable(rec(good)), "the readable denominator does not shrink"
    assert rec(entry).get("recovered_clean", 0) <= rec(good).get("recovered_clean", 0)


# --- R22-02 through main() -------------------------------------------------------------------------------------------------


def test_page_bounds_carry_through_the_real_scorer(tmp_path, stored):
    decl, *_ = stored
    runs = tmp_path / "runs"
    for tag in ("r21dry-A", "r21dry-L1"):
        shutil.copytree(pathlib.Path("C:/t/r2x/dry-runs") / tag, runs / tag)
    rows_f = runs / "r21dry-L1/out/rows.json"
    rows = json.loads(rows_f.read_text(encoding="utf-8"))
    one = next(k for k, v in rows.items() if k.endswith("rot270-sheet.pdf"))
    six = next(k for k, v in rows.items() if k.endswith("long-6pages.pdf"))
    pol = decl["arms"]["L1"]["identities"]["EVIDENCE_POLICY_VERSION"]
    ver = decl["arms"]["L1"]["identities"]["READER_VERSION"]
    fact = lambda: {"fields": {"own:identity": {"status": "completed", "provenance": {"attempt": 1, "seq": 1, "version": ver, "policy": pol, "prompts": {}},
                                                 "observations": [{"page": 0, "kind": "ai_evidence", "version": ver, "policy": pol, "variant": "EV1", "profile": "default", "field": "identity",
                                                                   "component": "own", "role": "own", "value": "INJ", "value_literal": "INJ", "value_normalized": "INJ", "candidates": ["INJ"],
                                                                   "state": "candidate", "reasons": ["injected"], "support": None, "readings": [], "region": None, "deterministic": None,
                                                                   "read": "completed", "request": "ok", "targeted": None}]}}}
    for key, pno in ((one, "3"), (six, "3"), (six, "5"), (six, "x")):
        rows[key]["extracted"]["ai_evidence"]["envelopes"]["default|EV1"]["pages"][pno] = fact()
    rows_f.write_text(json.dumps(rows), encoding="utf-8")
    d2 = json.loads(DRY_DECL.read_text(encoding="utf-8"))
    d2["harness_dir"] = "C:/t/iso/work/r2x/review21"
    d2["doc_arms"] = ["L1"]
    f = tmp_path / "decl.json"
    f.write_text(json.dumps(d2), encoding="utf-8")
    m = sa.main(["--declaration", str(f), "--declaration-sha", hashlib.sha256(f.read_bytes()).hexdigest(), "--runs", str(runs), "--tags", "A=r21dry-A,L1=r21dry-L1", "--out", str(tmp_path / "out")])
    why = sorted((x["doc"].split("/")[-1], x["page"], tuple(x["why"])) for x in m["coverage"]["L1"]["extra_facts_outside_scope"])
    assert why == [("long-6pages.pdf", "5", ("page_beyond_reader_scope",)), ("long-6pages.pdf", "x", ("invalid_page_identifier",)), ("rot270-sheet.pdf", "3", ("page_not_in_document",))]
    assert m["arms"]["L1"]["valid_accuracy_claim"] and m["valid_accuracy_claims"]["L1"]
