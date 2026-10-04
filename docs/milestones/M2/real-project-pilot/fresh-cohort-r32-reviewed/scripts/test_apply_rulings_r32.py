"""Synthetic tests for apply_rulings_r32.build_reviewed (no frozen data used)."""
import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apply_rulings_r32 as A  # noqa: E402

BLANK = {k: "" for k in A.REPLACED_KEYS}
BLANK["region"] = []


def fld(**kw):
    base = {"state": "present", "literal": "X-1", "printed_label": "No.", "semantic_role": "own number",
            "region": [0.1, 0.1, 0.2, 0.2], "evidence": ["render F001-p1.png"], "association": "resolved"}
    base.update(kw)
    return base


def page(**fields):
    p = {"page_role": "sheet",
         "identity": fld(),
         "revision": fld(literal="01", printed_label="Rev"),
         "decision": {"state": "absent", "absent_kind": "no_decision_area"}}
    p.update(fields)
    return p


def make_draft():
    return {"version": "r32-labels-draft-1", "documents": {
        "F001": {"pool_id": "F001", "pages": {"1": page()}, "confidence": "high",
                 "unresolved": ["is X-1 the number?"], "ep": "P1"},
        "F002": {"pool_id": "F002", "pages": {"1": page()}, "confidence": "high", "unresolved": [], "ep": "P1"},
        "F003": {"pool_id": "F003", "duplicate_of": "F001", "pages": {}, "confidence": "high", "unresolved": [],
                 "ep": "P1"},
    }}


def pr(pid, pg, field, ruling="accept", **kw):
    r = dict(BLANK)
    r.update({"pool_id": pid, "page": pg, "field": field, "ruling": ruling, "evidence_checked": ["C:/e.png"],
              "note": "n %s/%s/%s" % (pid, pg, field), "provenance": "B1"})
    r.update(kw)
    return r


def dr(pid, field, rs="yes", cf="yes", **kw):
    r = {"pool_id": pid, "field": field, "resolved_for_scoring": rs, "carries_fact": cf, "note": "d",
         "provenance": "B1"}
    r.update(kw)
    return r


def make_final():
    pf = [pr(p, pg, f) for p in ("F001", "F002") for pg in (1,) for f in A.FIELDS]
    df = [dr(p, f) for p in ("F001", "F002") for f in A.FIELDS]
    qs = [{"pool_id": "F001", "question": "is X-1 the number?", "ruling": "yes", "reason": "r", "provenance": "B1"},
          {"pool_id": "F003", "question": "dup of F001?", "ruling": "confirmed", "reason": "r",
           "provenance": "consolidator"}]
    conv = [{"topic": "(d1) mixed", "ruling": "x", "affected_rows": ["F002/p1/decision"]}]
    return {"review_of": {"draft_sha256": "abc"}, "page_field_rulings": pf, "document_field_rulings": df,
            "document_questions": qs, "convention_rulings": conv, "agents": [{"label": "R"}]}


def build(draft=None, final=None, disp=None):
    return A.build_reviewed(draft or make_draft(), final or make_final(), disp, {"draft_sha256": "abc"},
                            other_identity_additions=[])


def find(final, pid, pg, field):
    return [r for r in final["page_field_rulings"] if (r["pool_id"], r["page"], r["field"]) == (pid, pg, field)][0]


def test_accept_keeps_draft_values():
    draft = make_draft()
    out = build(draft)
    f = out["documents"]["F001"]["pages"]["1"]["identity"]
    for k, v in draft["documents"]["F001"]["pages"]["1"]["identity"].items():
        assert f[k] == v
    assert f["review_status"] == "accepted" and f["excluded_from_scoring"] is False
    assert "draft_value" not in f
    assert f["review_provenance"]["ruling"] == "accept" and f["review_provenance"]["disposition_id"] is None


def test_correct_replaces_and_keeps_draft_value():
    final = make_final()
    r = find(final, "F002", 1, "revision")
    r.update({"ruling": "correct", "state": "absent", "absent_kind": "", "referenced_revision": {"literal": "01"},
              "evidence_checked": ["C:/t/r2x/r32-stage/renders/F002-p1.png"]})
    draft = make_draft()
    out = build(draft, final)
    f = out["documents"]["F002"]["pages"]["1"]["revision"]
    assert f["state"] == "absent"
    for k in ("literal", "printed_label", "semantic_role", "region", "association"):
        assert k not in f  # empty ruling values clear the key
    assert f["evidence"] == ["C:/t/r2x/r32-stage/renders/F002-p1.png"]
    assert f["referenced_revision"] == {"literal": "01"}
    assert f["draft_value"] == draft["documents"]["F002"]["pages"]["1"]["revision"]
    assert f["review_status"] == "corrected"


def test_reject_behaves_like_correct():
    final = make_final()
    find(final, "F002", 1, "identity").update({"ruling": "reject", "state": "ambiguous", "literal": "Y"})
    f = build(final=final)["documents"]["F002"]["pages"]["1"]["identity"]
    assert f["state"] == "ambiguous" and f["literal"] == "Y" and f["review_status"] == "rejected"
    assert f["draft_value"]["literal"] == "X-1"


def test_unresolved_keeps_values_and_is_excluded():
    final = make_final()
    oq = "OPEN QUESTION (D-9): which?"
    find(final, "F001", 1, "revision").update({"ruling": "unresolved", "state": "ambiguous", "disposition_id": "D-9",
                                               "open_question": oq, "state_options": ["a", "b"]})
    [r for r in final["document_field_rulings"] if r["pool_id"] == "F001" and r["field"] == "revision"][0].update(
        {"resolved_for_scoring": "unresolved", "carries_fact": "unresolved", "disposition_id": "D-9",
         "open_question": oq})
    disp = {"dispositions": [{"id": "D-9", "open_question": oq}]}
    out = build(final=final, disp=disp)
    f = out["documents"]["F001"]["pages"]["1"]["revision"]
    assert f["state"] == "present" and f["literal"] == "01"  # draft values kept
    assert f["review_status"] == "unresolved" and f["excluded_from_scoring"] is True
    assert f["open_question"] == oq
    assert f["review_provenance"]["disposition_id"] == "D-9"
    rows = [e["row"] for e in out["escalations"]]
    assert "F001/p1/revision" in rows and "F001/revision" in rows


def test_unresolved_open_question_mismatch_raises():
    final = make_final()
    find(final, "F001", 1, "revision").update({"ruling": "unresolved", "disposition_id": "D-9",
                                               "open_question": "A"})
    with pytest.raises(A.ApplyError):
        build(final=final, disp={"dispositions": [{"id": "D-9", "open_question": "B"}]})


def test_every_ruling_consumed_once():
    out = build()
    a = out["applied"]
    assert a["page_field_rulings_applied"] == 6
    assert a["document_field_rulings_applied"] == 6
    assert a["question_rulings_applied"] == 2
    q = out["documents"]["F001"]["questions"][0]
    assert q["source"] == "draft unresolved"
    assert out["documents"]["F003"]["questions"][0]["source"] == "review worklist"


def test_leftover_page_ruling_raises():
    final = make_final()
    final["page_field_rulings"].append(pr("F002", 2, "identity"))
    with pytest.raises(A.ApplyError, match="not consumed"):
        build(final=final)


def test_duplicate_ruling_raises():
    final = make_final()
    final["page_field_rulings"].append(copy.deepcopy(final["page_field_rulings"][0]))
    with pytest.raises(A.ApplyError, match="duplicated"):
        build(final=final)


def test_draft_field_without_ruling_raises():
    final = make_final()
    final["page_field_rulings"] = [r for r in final["page_field_rulings"]
                                   if not (r["pool_id"] == "F002" and r["field"] == "decision")]
    with pytest.raises(A.ApplyError, match="without a ruling"):
        build(final=final)


def test_leftover_document_ruling_and_question_raise():
    final = make_final()
    final["document_field_rulings"].append(dr("F099", "identity"))
    with pytest.raises(A.ApplyError, match="not consumed"):
        build(final=final)
    final = make_final()
    final["document_questions"].append({"pool_id": "F099", "question": "q", "ruling": "r", "reason": "",
                                        "provenance": "B1"})
    with pytest.raises(A.ApplyError, match="not consumed"):
        build(final=final)


def test_draft_question_without_ruling_raises():
    draft = make_draft()
    draft["documents"]["F002"]["unresolved"] = ["unanswered?"]
    with pytest.raises(A.ApplyError, match="without a question ruling"):
        build(draft=draft)


def test_count_once_aliases_byte_identical_and_content():
    final = make_final()
    for r in final["document_field_rulings"]:
        if r["pool_id"] == "F002":
            r["gate_count_once_with"] = "F001"
    out = build(final=final)
    assert out["count_once_aliases"] == {"F002": "F001", "F003": "F001"}
    assert out["documents"]["F003"]["counted_under"] == "F001"
    assert out["documents"]["F002"]["counted_under"] == "F001"
    assert out["documents"]["F001"]["count_once_members"] == ["F002", "F003"]
    assert out["documents"]["F003"]["review"]["identity"]["resolved_for_scoring"] is None


def test_resubmission_required_on_d1_rows_only():
    out = build()
    assert out["documents"]["F002"]["pages"]["1"]["decision"]["resubmission_required"] == "yes"
    assert "resubmission_required" not in out["documents"]["F001"]["pages"]["1"]["decision"]


def test_other_identity_addition_requires_quoted_source():
    final = make_final()
    find(final, "F002", 1, "revision")["note"] = "value 'Z-9' printed as OLD NO."
    add = {"pool_id": "F002", "page": "1", "entry": {"literal": "Z-9", "printed_label": "OLD NO.", "role": "r"},
           "source": {"kind": "page_field_ruling", "pool_id": "F002", "page": 1, "field": "revision", "key": "note"},
           "must_quote": ["'Z-9' printed as OLD NO."], "basis": "b"}
    out = A.build_reviewed(make_draft(), final, None, {}, other_identity_additions=[add])
    oi = out["documents"]["F002"]["pages"]["1"]["other_identities"]
    assert oi[0]["literal"] == "Z-9" and oi[0]["added_by_review"]["source"]["field"] == "revision"
    bad = dict(add, must_quote=["not in the note"])
    with pytest.raises(A.ApplyError):
        A.build_reviewed(make_draft(), final, None, {}, other_identity_additions=[bad])


def test_metadata_binds_hashes():
    meta = {"draft_sha256": "abc", "final_response_sha256": "fff", "dispositions_sha256": "ddd"}
    out = A.build_reviewed(make_draft(), make_final(), None, meta, other_identity_additions=[])
    assert out["version"] == "r32-labels-reviewed-1"
    assert "NOT human-signed" in out["status"]
    assert out["derived_from"] == {"draft_version": "r32-labels-draft-1", "draft_sha256": "abc"}
    assert out["applied"]["final_response_sha256"] == "fff"
    with pytest.raises(A.ApplyError, match="different draft"):
        A.build_reviewed(make_draft(), make_final(), None, {"draft_sha256": "zzz"}, other_identity_additions=[])
