"""Synthetic tests for apply_review33_r32.build_reviewed2 (no frozen data used)."""
import copy
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apply_review33_r32 as A  # noqa: E402

H = {"review33_sha256": "a" * 64, "escalation_rulings_final_sha256": "b" * 64, "dispositions_sha256": "c" * 64}
META = {"reviewed1_sha256": "d" * 64, "generated_at_utc": "2026-10-03T00:00:00Z", "generator_script": "x.py",
        "generator_sha256": "e" * 64}
OQ4 = "OPEN QUESTION (D-004, ...): may a role on other pages settle this page?"
OQ5 = "OPEN QUESTION (D-005, ...): cell 00 or table 01?"
Q5 = "revision: title-block Rev. no. prints 00 but the revision table lists 01"
CANDS5 = [{"literal": "00", "printed_label": "Rev. no.", "role": "title-block revision cell"},
          {"literal": "01", "printed_label": "REV (revision table, latest row)", "role": "latest table entry"}]
REGION5 = [0.04, 0.86, 0.43, 0.99]


def accepted(state="absent", **kw):
    f = {"state": state, "excluded_from_scoring": False, "review_status": "accepted",
         "review_provenance": {"ruling": "accept", "provenance": "B1", "disposition_id": None, "note": "n",
                               "evidence_checked": []}}
    f.update(kw)
    return f


def present(lit):
    return accepted("present", literal=lit, association="resolved", region=[0, 0, 1, 1])


def f069_identity(pg):
    return {"state": "present", "literal": "EP-15744", "printed_label": "Refrence", "association": "resolved",
            "excluded_from_scoring": True, "review_status": "unresolved", "open_question": OQ4,
            "semantic_role": "own quotation reference (equals the project EP number)", "region": [0.8, 0.1, 0.9, 0.2],
            "evidence": ["render F069-p%s.png" % pg], "value_note": "label printed 'Refrence'",
            "review_provenance": {"ruling": "unresolved", "disposition_id": "D-004", "provenance": "B7", "note": "n",
                                  "evidence_checked": []}}


def plain_doc(pid, ep="1"):
    return {"pool_id": pid, "ep": ep, "kind": "k", "confidence": "high", "staged_sha256": pid * 4,
            "pages": {"1": {"identity": present(pid + "-ID"), "revision": present("01"), "decision": accepted(),
                            "page_role": "r"}},
            "review": {"identity": {"resolved_for_scoring": "yes", "carries_fact": "yes", "provenance": "B1",
                                    "disposition_id": None, "note": "n"},
                       "revision": {"resolved_for_scoring": "yes", "carries_fact": "yes", "provenance": "B1",
                                    "disposition_id": None, "note": "n"},
                       "decision": {"resolved_for_scoring": "yes", "carries_fact": "no", "provenance": "B1",
                                    "disposition_id": None, "note": "n"}},
            "questions": [], "unresolved": []}


def make_r1():
    docs = {}
    for pid in ("F001", "F002", "F031", "F038", "F046", "F059", "F067"):
        docs[pid] = plain_doc(pid)
    for alias, canon in (("F031", "F001"), ("F059", "F046")):
        docs[alias]["count_once_alias"] = {"of": canon, "basis": "content duplicate (final convention (c)(ii))"}
        docs[alias]["counted_under"] = canon
        docs[canon]["count_once_members"] = [alias]
    for dup, canon in (("F052", "F038"), ("F070", "F067")):
        d = plain_doc(dup)
        d["pages"] = {}
        d["duplicate_of"] = canon
        d["review"] = {f: {"resolved_for_scoring": None, "carries_fact": None, "provenance": "consolidator",
                           "disposition_id": None, "note": "copy"} for f in A.FIELDS}
        d["count_once_alias"] = {"of": canon, "basis": "byte-identical"}
        d["counted_under"] = canon
        docs[dup] = d
        docs[canon]["count_once_members"] = [dup]
    f069 = plain_doc("F069", ep="15744")
    f069["pages"] = {}
    for pg in ("1", "2", "3", "4"):
        f069["pages"][pg] = {"identity": f069_identity(pg) if pg in ("1", "3") else accepted(),
                             "revision": accepted(), "decision": accepted(absent_kind="no_decision_area"),
                             "page_role": "quotation page %s" % pg}
    f069["review"]["identity"] = {"resolved_for_scoring": "unresolved", "carries_fact": "no", "provenance": "B7",
                                  "disposition_id": "D-004", "note": "n", "open_question": OQ4,
                                  "superseded_value": {"open_question": None, "resolved_for_scoring": "no"}}
    f069["review"]["revision"]["carries_fact"] = "no"
    f069["questions"] = [{"question": "two quotations in one file", "ruling": "two components", "reason": "r",
                          "provenance": "B7", "source": "draft unresolved"}]
    f069["unresolved"] = ["two quotations in one file"]
    docs["F069"] = f069
    f019 = plain_doc("F019", ep="3563")
    f019["pages"]["1"]["revision"] = {
        "state": "ambiguous", "candidates": copy.deepcopy(CANDS5), "association": "resolved", "region": list(REGION5),
        "excluded_from_scoring": True, "review_status": "unresolved", "open_question": OQ5,
        "note": "the title-block date equals row 01; not decided from the page", "evidence": ["crop.png"],
        "review_provenance": {"ruling": "unresolved", "disposition_id": "D-005", "provenance": "B1", "note": "n",
                              "evidence_checked": []}}
    f019["pages"]["1"]["other_identities"] = [{"literal": "D14-22", "printed_label": "(stamp)", "role": "project"}]
    f019["review"]["revision"] = {"resolved_for_scoring": "unresolved", "carries_fact": "unresolved",
                                  "provenance": "B1", "disposition_id": "D-005", "note": "n", "open_question": OQ5,
                                  "superseded_value": {"carries_fact": "no", "open_question": None,
                                                       "resolved_for_scoring": "no"}}
    f019["questions"] = [
        {"question": "decision stamp faint", "ruling": "present, legible enough (accept draft)", "reason": "r",
         "provenance": "B1", "source": "draft unresolved"},
        {"question": Q5, "ruling": "unresolved: escalated (D-005); depends on topic (i)", "reason": "r",
         "provenance": "B1", "source": "draft unresolved", "disposition_id": "D-005", "open_question": OQ5,
         "superseded_value": {"open_question": None, "ruling": "ambiguous (accept draft)"}}]
    f019["unresolved"] = [Q5, "decision stamp faint"]
    docs["F019"] = f019
    esc = [
        {"row": "F019/p1/revision", "level": "page_field", "disposition_id": "D-005", "open_question": OQ5},
        {"row": "F019/revision", "level": "document_field", "disposition_id": "D-005", "open_question": OQ5,
         "resolved_for_scoring": "unresolved", "carries_fact": "unresolved"},
        {"row": "F019 question", "level": "question", "disposition_id": "D-005", "open_question": OQ5,
         "question": Q5},
        {"row": "F069/p1/identity", "level": "page_field", "disposition_id": "D-004", "open_question": OQ4},
        {"row": "F069/p3/identity", "level": "page_field", "disposition_id": "D-004", "open_question": OQ4},
        {"row": "F069/identity", "level": "document_field", "disposition_id": "D-004", "open_question": OQ4,
         "resolved_for_scoring": "unresolved", "carries_fact": "no"},
    ]
    topics = [("(a) uncertain", None), ("(c) duplicates", None), ("(d1) mixed options", None),
              ("(d2) authority marks", None), ("(e) code letters", "D-001"), ("(f) EMAAR letters", None),
              ("(g) revision suffixes", None), ("(g2) reply sheets", "D-002"), ("(h) compilation files", "D-003"),
              ("(h2) job numbers", "D-004"), ("(i) ambiguous conflicts", "D-005"), ("(i2) literal form", None)]
    conv = []
    for t, did in topics:
        c = {"topic": t, "ruling": "rule " + t, "affected_rows": [], "applies_to": "pool", "evidence": "e",
             "source_batches": ["B1"]}
        if did:
            c["disposition_id"] = did
        conv.append(c)
    return {"version": "r32-labels-reviewed-1", "status": "AI-reviewed; NOT human-signed",
            "derived_from": {"draft_version": "r32-labels-draft-1", "draft_sha256": "f" * 64},
            "applied": {"final_response_sha256": "9" * 64, "page_field_status_counts": {}},
            "generated_at_utc": "2026-10-03T06:29:44Z", "generator": {"script": "old.py", "sha256": "8" * 64},
            "agents": [{"label": "R32REV-B1"}], "convention_rulings": conv,
            "count_once_aliases": dict(A.EXPECTED_ALIASES), "escalations": esc, "documents": docs}


def make_er():
    row4 = {"state": "ambiguous", "literal": None,
            "candidates": [{"literal": "EP-15744", "printed_label": "Refrence", "role": "not established on the page"}],
            "association": "resolved", "excluded_from_scoring": True, "review_status": "ruled (Review 33, D-004)"}
    row5 = {"state": "ambiguous", "literal": None, "candidates": copy.deepcopy(CANDS5), "association": "resolved",
            "region": list(REGION5), "excluded_from_scoring": True, "review_status": "ruled (Review 33, D-005)",
            "note": "the page does not establish which revision is current"}
    co = [{"item": A.CO_F031 + " (content duplicate)", "ruling": "s", "final_ruling": "ADOPTED. " + A.F031_CAVEAT},
          {"item": A.CO_F059 + " (content duplicate)", "ruling": "s", "final_ruling": "ADOPTED, same amendment."},
          {"item": A.CO_BYTE, "ruling": "s", "final_ruling": "Unchanged: frozen section 1 applies; count once."},
          {"item": A.CO_D1 + "; 9 rows)", "ruling": "s", "final_ruling": "record (d1)"},
          {"item": A.CO_E + " 'Not Approved'", "ruling": "s", "final_ruling": "record (e)"},
          {"item": A.CO_INTERP, "ruling": "s", "final_ruling": "record interpretations"},
          {"item": A.CO_D005, "final_ruling": "record D-005 reading"}]
    return {"dispositions_sha256": H["dispositions_sha256"],
            "supersedes_for_application": {"file": "ESCALATION-RULINGS.json", "sha256": "7" * 64},
            "D-004": {"rows": ["F069/p1/identity", "F069/p3/identity", "F069/identity (document)"],
                      "ruling": "AMBIGUOUS (page only)",
                      "resulting_rows": {"F069/p1/identity": copy.deepcopy(row4),
                                         "F069/p3/identity": copy.deepcopy(row4),
                                         "other_identities": "unchanged (no role asserted)"},
                      "document_level": {"F069/identity": {"resolved_for_scoring": "no", "carries_fact": "no"}},
                      "count_impact": "None.", "owner_alternative": "absent under (h2)"},
            "D-005": {"rows": ["F019/p1/revision", "F019/revision (document)", "F019 question"],
                      "ruling": "AMBIGUOUS (page-specific)",
                      "resulting_rows": {"F019/p1/revision": row5},
                      "document_level": {"F019/revision": {"resolved_for_scoring": "no", "carries_fact": "no"}},
                      "count_impact": "None.", "owner_alternative": "present 00 under cell-first"},
            "carried_over": co}


def build(r1=None, er=None, **kw):
    return A.build_reviewed2(r1 or make_r1(), er or make_er(), dict(H), dict(META), **kw)


def test_f069_page_rows_ruled_ambiguous():
    r1 = make_r1()
    r2 = build(r1)
    for pg in ("1", "3"):
        f = r2["documents"]["F069"]["pages"][pg]["identity"]
        old = r1["documents"]["F069"]["pages"][pg]["identity"]
        assert f["state"] == "ambiguous" and f["literal"] is None
        assert f["candidates"] == [{"literal": "EP-15744", "printed_label": "Refrence",
                                    "role": "not established on the page"}]
        assert f["association"] == "resolved" and f["excluded_from_scoring"] is True
        assert f["review_status"] == "ruled (Review 33, D-004)"
        assert "open_question" not in f
        blk = f["review33_ruling"]
        assert blk["open_question_closed"]["question"] == OQ4
        assert blk["open_question_closed"]["status"] == "closed: ruled (Review 33, D-004)"
        assert H["review33_sha256"] in blk["open_question_closed"]["closed_by"]
        assert blk["review33_sha256"] == H["review33_sha256"]
        assert blk["superseded_value"] == {"state": "present", "literal": "EP-15744", "review_status": "unresolved"}
        assert blk["added_keys"] == ["candidates"]
        for k in ("printed_label", "semantic_role", "region", "evidence", "value_note", "review_provenance"):
            assert f[k] == old[k]
    for pg in ("2", "4"):
        assert r2["documents"]["F069"]["pages"][pg] == r1["documents"]["F069"]["pages"][pg]


def test_f069_document_identity_no_no():
    r2 = build()
    e = r2["documents"]["F069"]["review"]["identity"]
    assert (e["resolved_for_scoring"], e["carries_fact"]) == ("no", "no")
    assert "open_question" not in e
    assert e["review33_ruling"]["superseded_value"] == {"resolved_for_scoring": "unresolved"}
    assert e["review33_ruling"]["open_question_closed"]["status"] == "closed: ruled (Review 33, D-004)"
    assert e["superseded_value"] == {"open_question": None, "resolved_for_scoring": "no"}  # reviewed-1 key kept
    assert r2["documents"]["F069"]["questions"] == make_r1()["documents"]["F069"]["questions"]


def test_f019_page_revision_status_fields_only():
    r1 = make_r1()
    r2 = build(r1)
    f = r2["documents"]["F019"]["pages"]["1"]["revision"]
    old = r1["documents"]["F019"]["pages"]["1"]["revision"]
    assert f["state"] == "ambiguous" and f["candidates"] == CANDS5 and f["excluded_from_scoring"] is True
    assert f["review_status"] == "ruled (Review 33, D-005)"
    assert "literal" not in f and "open_question" not in f
    assert f["note"] == old["note"] and f["region"] == old["region"]
    assert f["review33_ruling"]["ruling_row_note"] == "the page does not establish which revision is current"
    assert f["review33_ruling"]["superseded_value"] == {"review_status": "unresolved"}
    assert r2["documents"]["F019"]["pages"]["1"]["identity"] == r1["documents"]["F019"]["pages"]["1"]["identity"]


def test_f019_document_question_and_unresolved_marked_ruled():
    r1 = make_r1()
    r2 = build(r1)
    d = r2["documents"]["F019"]
    assert (d["review"]["revision"]["resolved_for_scoring"], d["review"]["revision"]["carries_fact"]) == ("no", "no")
    assert d["review"]["revision"]["review33_ruling"]["superseded_value"] == {
        "resolved_for_scoring": "unresolved", "carries_fact": "unresolved"}
    q = d["questions"][1]
    assert q["ruling"] == "ruled (Review 33, D-005)" and "open_question" not in q
    assert q["review33_ruling"]["superseded_value"]["ruling"].startswith("unresolved")
    assert q["review33_ruling"]["open_question_closed"]["question"] == OQ5
    assert d["questions"][0] == r1["documents"]["F019"]["questions"][0]
    assert d["unresolved"] == r1["documents"]["F019"]["unresolved"]
    marks = d["unresolved_review33_marks"]
    assert len(marks) == 1 and marks[0]["item"] == Q5 and marks[0]["index"] == 0
    assert marks[0]["status"] == "ruled (Review 33, D-005)" and marks[0]["question_index"] == 1
    assert d["review"]["identity"] == r1["documents"]["F019"]["review"]["identity"]


def test_escalations_marked_ruled_with_hashes():
    r1 = make_r1()
    r2 = build(r1)
    assert len(r2["escalations"]) == 6
    for old, new in zip(r1["escalations"], r2["escalations"]):
        rid = old["disposition_id"]
        assert new["status"] == "ruled (Review 33, %s)" % rid
        assert new["ruled_by"]["review33_sha256"] == H["review33_sha256"]
        assert new["ruled_by"]["escalation_rulings_final_sha256"] == H["escalation_rulings_final_sha256"]
        assert {k: v for k, v in new.items() if k not in ("status", "ruled_by")} == old
    by_row = {x["row"]: x["ruled_by"]["resulting_value"] for x in r2["escalations"]}
    assert by_row["F069/identity"] == {"resolved_for_scoring": "no", "carries_fact": "no"}
    assert by_row["F069/p1/identity"]["state"] == "ambiguous"
    assert by_row["F019/p1/revision"]["literal"] == A.ABSENT
    assert by_row["F019 question"]["ruling"] == "ruled (Review 33, D-005)"
    assert r2["applied"]["escalations_open"] == 0


def test_aliases_annotated_and_mapping_unchanged():
    r1 = make_r1()
    r2 = build(r1)
    assert r2["count_once_aliases"] == r1["count_once_aliases"] == A.EXPECTED_ALIASES
    ann = r2["count_once_alias_annotations"]
    assert {k: v["of"] for k, v in ann.items()} == A.EXPECTED_ALIASES
    assert ann["F031"]["ruling"] == ann["F059"]["ruling"] == "Review 33 (c)(ii)"
    assert ann["F031"]["caveat"] == A.F031_CAVEAT and "caveat" not in ann["F059"]
    assert "amendment to frozen convention section 1" in ann["F031"]["basis"]
    assert ann["F052"]["ruling"] == ann["F070"]["ruling"] == "frozen convention section 1"
    for a in ("F031", "F052", "F059", "F070"):
        assert r2["documents"][a] == r1["documents"][a]


def test_amendment_list_complete_and_verbatim():
    r2 = build()
    am = r2["convention_amendments_and_interpretations"]
    assert am["condition_c2_verbatim"] == A.C2_TEXT and am["condition"] == "C-2"
    ids = [x["id"] for x in am["items"]]
    assert ids == ["(c)(ii)", "(d1)", "(e)/D-001", "(g)(1)", "(g2)/D-002", "(h)/D-003", "(d2)", "(f)",
                   "D-005 page reading"]
    kinds = {x["id"]: x["kind"] for x in am["items"]}
    assert [i for i in ids if kinds[i] == "amendment"] == ["(c)(ii)", "(d1)", "(e)/D-001"]
    item = {x["id"]: x for x in am["items"]}
    assert item["(e)/D-001"]["label_review_disposition_id"] == "D-001"
    assert item["(h)/D-003"]["label_review_convention_topic"] == "(h) compilation files"
    assert A.ROW_F031 in item["(c)(ii)"]["review33_verbatim"]
    assert item["D-005 page reading"]["escalation_rulings_final_verbatim"][0]["final_ruling"] == "record D-005 reading"
    assert all(A.C2_TEXT in x["review33_verbatim"] for x in am["items"])


def test_metadata_and_lineage():
    r1 = make_r1()
    r2 = build(r1)
    assert r2["version"] == "r32-labels-reviewed-2"
    assert "NOT human-signed" in r2["status"] and "Review 33" in r2["status"]
    assert r2["derived_from"] == {"version": "r32-labels-reviewed-1", "sha256": META["reviewed1_sha256"]}
    ap = r2["applied"]
    assert ap["review33_sha256"] == H["review33_sha256"]
    assert ap["escalation_rulings_final_sha256"] == H["escalation_rulings_final_sha256"]
    assert ap["dispositions_sha256"] == H["dispositions_sha256"]
    assert ap["conditions_applied"] == ["C-1", "C-2"]
    assert ap["page_field_status_counts"]["identity"]["ruled (Review 33, D-004)"] == 2
    assert ap["page_field_status_counts"]["revision"]["ruled (Review 33, D-005)"] == 1
    assert "unresolved" not in json.dumps(ap["page_field_status_counts"])
    assert r2["generator"] == {"script": "x.py", "sha256": META["generator_sha256"]}
    assert r2["generated_at_utc"] == META["generated_at_utc"]
    for k in A.METADATA_KEYS:
        assert r2["lineage"]["reviewed_1"][k] == r1[k]
    assert r2["agents"] == r1["agents"] and r2["convention_rulings"] == r1["convention_rulings"]


def test_change_log_provenance_and_equals_diff():
    r1 = make_r1()
    r2 = build(r1)
    log = r2["change_log"]
    assert all(e["provenance"].startswith("Review 33 ") for e in log)
    assert all(e["review33_sha256"] == H["review33_sha256"] for e in log)
    doc_paths = {e["path"] for e in log if e["path"].split("/")[0] in ("documents", "escalations")}
    diffed = {"/".join(map(str, p)) for p, _ in A.diff_paths(r1, r2) if p[0] in ("documents", "escalations")}
    assert doc_paths == diffed
    prov = {e["path"]: e["provenance"] for e in log}
    assert prov["documents/F069/pages/1/identity/state"] == "Review 33 D-004"
    assert prov["documents/F019/review/revision/carries_fact"] == "Review 33 D-005"
    assert prov["count_once_alias_annotations/F031"] == "Review 33 (c)(ii)"
    assert prov["convention_amendments_and_interpretations/items/(f)"] == "Review 33 C-2"
    assert "documents/F069/review/identity/carries_fact" not in prov  # stays "no"


def test_nothing_else_changed_and_injected_changes_are_caught():
    r1 = make_r1()
    r2 = build(r1)
    assert A.check_only_enumerated_changes(r1, r2) == []
    changed_docs = {p[1] for p, _ in A.diff_paths(r1["documents"], r2["documents"], ("documents",))
                    if len(p) > 1}
    assert changed_docs == {"F019", "F069"}
    for mutate in (lambda r: r["documents"]["F002"]["pages"]["1"]["identity"].__setitem__("literal", "X"),
                   lambda r: r["documents"]["F069"]["pages"]["1"]["identity"].__setitem__("printed_label", "Ref"),
                   lambda r: r["documents"]["F069"]["review"]["identity"].__setitem__("carries_fact", "yes"),
                   lambda r: r["documents"]["F019"]["pages"]["1"].__setitem__("other_identities", []),
                   lambda r: r["escalations"][0].__setitem__("row", "F019/p2/revision"),
                   lambda r: r["count_once_aliases"].__setitem__("F031", "F002"),
                   lambda r: r["lineage"]["reviewed_1"].__setitem__("version", "x")):
        bad = copy.deepcopy(r2)
        mutate(bad)
        assert A.check_only_enumerated_changes(r1, bad) != []


@pytest.mark.parametrize("breaker", [
    "f069_already_ambiguous", "f019_candidates_differ", "dispositions_hash", "extra_escalation",
    "ruling_extra_key", "f069_carries_fact_yes", "wrong_version", "alias_mapping", "missing_hash"])
def test_preconditions_raise(breaker):
    r1, er, h = make_r1(), make_er(), dict(H)
    if breaker == "f069_already_ambiguous":
        r1["documents"]["F069"]["pages"]["1"]["identity"]["state"] = "ambiguous"
    elif breaker == "f019_candidates_differ":
        r1["documents"]["F019"]["pages"]["1"]["revision"]["candidates"] = CANDS5[:1]
    elif breaker == "dispositions_hash":
        er["dispositions_sha256"] = "0" * 64
    elif breaker == "extra_escalation":
        r1["escalations"].append({"row": "F002/p1/identity", "level": "page_field", "disposition_id": "D-009"})
    elif breaker == "ruling_extra_key":
        er["D-004"]["resulting_rows"]["F069/p1/identity"]["semantic_role"] = "x"
    elif breaker == "f069_carries_fact_yes":
        er["D-004"]["document_level"]["F069/identity"]["carries_fact"] = "yes"
    elif breaker == "wrong_version":
        r1["version"] = "r32-labels-draft-1"
    elif breaker == "alias_mapping":
        r1["count_once_aliases"]["F031"] = "F002"
    elif breaker == "missing_hash":
        h.pop("review33_sha256")
    with pytest.raises(A.ApplyError):
        A.build_reviewed2(r1, er, h, dict(META))


def test_pure_and_deterministic():
    r1, er = make_r1(), make_er()
    r1c, erc = copy.deepcopy(r1), copy.deepcopy(er)
    a = A.build_reviewed2(r1, er, dict(H), dict(META))
    b = A.build_reviewed2(r1, er, dict(H), dict(META))
    assert r1 == r1c and er == erc
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_review33_text_quote_check():
    quotes = [A.C2_TEXT, A.ITEM8_TEXT, A.ITEM7_CII_TEXT, A.ITEM7_S1_TEXT, A.LINE_D005_PAGE_ONLY]
    for a in A.AMENDMENTS + A.ALIAS_SPECS:
        quotes += a["review33_verbatim"]
    text = "\n".join(quotes) + "\n" + H["escalation_rulings_final_sha256"] + " " + H["dispositions_sha256"]
    build(review33_text=text)
    with pytest.raises(A.ApplyError):
        build(review33_text=text.replace("F031→F001", "F031->F001"))
    with pytest.raises(A.ApplyError):
        build(review33_text=text.replace(H["dispositions_sha256"], ""))
