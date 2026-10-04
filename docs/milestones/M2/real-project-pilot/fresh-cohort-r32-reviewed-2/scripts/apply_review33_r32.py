"""ORCH-04.1 (R32APPLY2-IMPL) step 2: apply the Independent Preparation Review 33 rulings to r32-labels-reviewed-1.

Mechanical application only: no image is read, no ruling is re-made, no model or provider call.

build_reviewed2(reviewed1, escalation_rulings_final, review33_hashes, meta=None, review33_text=None) -> reviewed2
    Pure function (no I/O, no clock; `meta` supplies the reviewed-1 sha256, the timestamp and the generator).
    Applies exactly the row changes of Review 33 section 4.4 / ESCALATION-RULINGS.final.json (D-004, D-005),
    annotates the count-once aliases (section 4.3 / 4.4 item 7), adds the C-2 amendment and interpretation list
    (section 4.3 / 4.4 item 8), marks the six escalations ruled, and writes the version metadata and a change log.
    It then diffs reviewed-1 against reviewed-2 and raises ApplyError if any key outside the enumerated set differs,
    or if the change log and the diff disagree.

check_only_enumerated_changes(reviewed1, reviewed2) -> list of unexpected differing paths (empty when clean).

CLI: verifies the frozen hashes, reads reviewed-1, ESCALATION-RULINGS.final.json and INDEPENDENT-REVIEW.md, and
writes fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json (refuses to overwrite).
"""
import argparse
import copy
import datetime
import hashlib
import json
import os
import sys

FIELDS = ("identity", "revision", "decision")
VERSION = "r32-labels-reviewed-2"
PREV_VERSION = "r32-labels-reviewed-1"
STATUS_TEXT = ("AI-reviewed: owner-delegated independent Claude AI review (ORCH-01A) with the Independent Preparation "
               "Review 33 rulings applied; NOT human-signed; NOT a human review")
REVIEW33_NAME = "Independent Preparation Review 33 (FINAL; ORCH-03.4; agent R33-FINAL)"
REVIEW33_VERDICT = "PREPARATION ACCEPTED WITH CONDITIONS"
CONDITIONS_APPLIED = ["C-1", "C-2"]
EXPECTED_ALIASES = {"F031": "F001", "F052": "F038", "F059": "F046", "F070": "F067"}
RULED = {"D-004": "ruled (Review 33, D-004)", "D-005": "ruled (Review 33, D-005)"}
OUTCOME = {"D-004": "AMBIGUOUS", "D-005": "AMBIGUOUS"}
ABSENT = "<absent>"

# top-level keys whose reviewed-1 values are replaced (kept verbatim under lineage.reviewed_1) and new keys
METADATA_KEYS = ("version", "status", "derived_from", "applied", "generated_at_utc", "generator")
NEW_KEYS = ("lineage", "change_log", "count_once_alias_annotations", "convention_amendments_and_interpretations")
UNCHANGED_TOP_KEYS = ("agents", "convention_rulings", "count_once_aliases")

# ---- Review 33 section 4.4 rows 1, 2 and 4 (page-field rows)
PAGE_ROW_SPECS = (
    {"row": "F069/p1/identity", "ruling_id": "D-004", "section": "4.1; 4.4 item 1",
     "pre": {"state": "present", "literal": "EP-15744", "review_status": "unresolved"},
     "apply": ("state", "literal", "candidates", "review_status"),
     "must_equal": ("association", "excluded_from_scoring"),
     "null_equals_absent": (), "not_applied": {}},
    {"row": "F069/p3/identity", "ruling_id": "D-004", "section": "4.1; 4.4 item 2",
     "pre": {"state": "present", "literal": "EP-15744", "review_status": "unresolved"},
     "apply": ("state", "literal", "candidates", "review_status"),
     "must_equal": ("association", "excluded_from_scoring"),
     "null_equals_absent": (), "not_applied": {}},
    {"row": "F019/p1/revision", "ruling_id": "D-005", "section": "4.2; 4.4 item 4",
     "pre": {"state": "ambiguous", "review_status": "unresolved"},
     "apply": ("review_status",),
     "must_equal": ("state", "candidates", "association", "region", "excluded_from_scoring"),
     "null_equals_absent": ("literal",),
     "not_applied": {"note": "ESCALATION-RULINGS.final.json D-005 row_change says 'status fields only' and Review 33 "
                             "section 4.4 item 4 lists no note change; the reviewed-1 note is kept and the ruling's "
                             "note wording is recorded under review33_ruling.ruling_row_note"}},
)
# ---- Review 33 section 4.4 rows 3 and 5 (document-field rows)
DOC_SPECS = (
    {"row": "F069/identity", "doc": "F069", "field": "identity", "ruling_id": "D-004", "section": "4.1; 4.4 item 3",
     "pre": {"resolved_for_scoring": "unresolved", "carries_fact": "no"}, "changes": ("resolved_for_scoring",)},
    {"row": "F019/revision", "doc": "F019", "field": "revision", "ruling_id": "D-005", "section": "4.2; 4.4 item 5",
     "pre": {"resolved_for_scoring": "unresolved", "carries_fact": "unresolved"},
     "changes": ("resolved_for_scoring", "carries_fact")},
)
QUESTION_SECTION = {"D-004": "4.1; 4.4 item 3", "D-005": "4.2; 4.4 item 5"}
ESCALATION_SECTION = "4.4 item 6"

# ---- verbatim text of INDEPENDENT-REVIEW.md (8d20baec...) used in the annotations; checked by substring
C2_TEXT = ("Record in reviewed-2 and in the declaration's amendment and interpretation list: count-once (c)(ii), ruled "
           "ADOPTED here as an amendment to convention section 1 with the F031 p3/p4 caveat; (d1); (e)/D-001; (g)(1); "
           "(g2)/D-002; (h)/D-003; (d2); (f); and the page-specific D-005 reading of sections 2 and 4.")
ITEM8_TEXT = ("8. **An amendment and interpretation list** is added: (c)(ii); (d1); (e)/D-001; (g)(1); (g2)/D-002; "
              "(h)/D-003; (d2); (f); and the D-005 page reading.")
ITEM7_CII_TEXT = ("F031\u2192F001 and F059\u2192F046 are annotated as the Review 33 (c)(ii) ruling (an amendment to "
                  "section 1), with the F031 p3/p4 caveat.")
ITEM7_S1_TEXT = "F052\u2192F038 and F070\u2192F067 are annotated as frozen section 1."
ROW_F031 = ("| Count-once F031\u2192F001 | p1 and p2 renders differ by 0 px (SYNTH, CRITIC and FINAL). F031 p3 is a "
            "Comments Resolution Sheet showing MAT \u2013 116 and Rev 02, the same values as F001 (FINAL read). F031 p4 "
            "carries no field | **ADOPTED** for this cohort as a Review 33 ruling (C-005 adopted). It is recorded as an "
            "amendment to frozen section 1, with the caveat that F031 has pages 3 and 4, which F001 lacks, but adds no "
            "field value | No row change; the alias annotation is recorded in reviewed-2. Counts 57/38/38. The owner "
            "may reverse it, giving 59/40/39 |")
ROW_F059 = ("| Count-once F059\u2192F046 | 1,183 px differ by more than 64 levels, only in a seal outside the title "
            "block. The title blocks are identical (SYNTH, CRITIC and FINAL) | **ADOPTED**, under the same amendment | "
            "Included above |")
ROW_BYTE = ("| Byte-identical F052\u2192F038 and F070\u2192F067 | Identical `staged_sha256` | Frozen section 1 applies | "
            "Count once |")
ROW_D1 = ("| (d1) resubmission_required on mixed options (9 rows) | Marks such as \"Approved as noted / Resubmit\" and "
          "\"B+R\" (D3) | Defensible. Record it as an amendment and define the scorer tolerance | C-2, C-6 |")
ROW_E = ("| (e)/D-001 F025 Code C \"Not Approved (Re-submit\u2026)\" | Legend on F025-p1 (D3) | Revise and resubmit is "
         "defensible. Record it as an amendment | C-2 |")
ROW_INTERP = ("| (g)(1), (g2)/D-002, (h)/D-003, (d2), (f) | F034-p3, F028-p4, F043 (D3) | Record them as "
              "interpretations. D-003 adds 1 to revision (already counted) | C-2 |")
ROW_D005 = ("| D-005 page-specific reading of sections 2 and 4 | F019-p1 | Record it as an interpretation, not a general "
            "topic (i) rule | C-2 |")
LINE_D005_PAGE_ONLY = "- **Page-specific only.** This ruling adopts no general cell-against-table rule (topic (i))."
F031_CAVEAT = ("Caveat: F031 has pages 3-4 that F001 lacks; p3 (Comments Resolution Sheet) repeats F001's identity "
               "MAT - 116 and revision 02, and p4 carries no field, so F031 adds no field value.")

# carried_over items of ESCALATION-RULINGS.final.json, located by the start of their "item" text
CO_F031 = "count-once alias F031 -> F001"
CO_F059 = "count-once alias F059 -> F046"
CO_BYTE = "byte-identical aliases F052 -> F038, F070 -> F067"
CO_D1 = "resubmission_required on mixed-option rows ((d1)"
CO_E = "(e)/D-001 F025 Code C"
CO_INTERP = "(g)(1), (g2)/D-002, (h)/D-003, (d2), (f) interpretive rulings"
CO_D005 = "D-005 page-specific ambiguity ruling"

AMENDMENTS = (
    {"id": "(c)(ii)", "kind": "amendment",
     "scope": "this cohort; amendment to frozen convention section 1 (which covers byte-identical files only)",
     "review33_verbatim": [C2_TEXT, ROW_F031, ROW_F059, ITEM7_CII_TEXT],
     "carried_over": [CO_F031, CO_F059], "label_review_topic": "(c)", "label_review_disposition": None,
     "effect": "count once F031->F001 and F059->F046 (no row change); counts 57/38/38 with it, 59/40/39 without; "
               "the owner may reverse it"},
    {"id": "(d1)", "kind": "amendment", "scope": "this cohort",
     "review33_verbatim": [C2_TEXT, ROW_D1], "carried_over": [CO_D1], "label_review_topic": "(d1)",
     "label_review_disposition": None,
     "effect": "no row change (resubmission_required already recorded in reviewed-1 on the 9 rows); scorer tolerance "
               "to be defined (C-6)"},
    {"id": "(e)/D-001", "kind": "amendment", "scope": "this cohort",
     "review33_verbatim": [C2_TEXT, ROW_E], "carried_over": [CO_E], "label_review_topic": "(e)",
     "label_review_disposition": "D-001", "effect": "no row change"},
    {"id": "(g)(1)", "kind": "interpretation", "scope": "this cohort",
     "review33_verbatim": [C2_TEXT, ROW_INTERP], "carried_over": [CO_INTERP], "label_review_topic": "(g)",
     "label_review_disposition": None, "effect": "no row change"},
    {"id": "(g2)/D-002", "kind": "interpretation", "scope": "this cohort",
     "review33_verbatim": [C2_TEXT, ROW_INTERP], "carried_over": [CO_INTERP], "label_review_topic": "(g2)",
     "label_review_disposition": "D-002", "effect": "no row change"},
    {"id": "(h)/D-003", "kind": "interpretation", "scope": "this cohort",
     "review33_verbatim": [C2_TEXT, ROW_INTERP], "carried_over": [CO_INTERP], "label_review_topic": "(h)",
     "label_review_disposition": "D-003",
     "effect": "no row change in reviewed-2; D-003 adds 1 to revision, already counted in reviewed-1 (38)"},
    {"id": "(d2)", "kind": "interpretation", "scope": "this cohort",
     "review33_verbatim": [C2_TEXT, ROW_INTERP], "carried_over": [CO_INTERP], "label_review_topic": "(d2)",
     "label_review_disposition": None, "effect": "no row change"},
    {"id": "(f)", "kind": "interpretation", "scope": "this cohort",
     "review33_verbatim": [C2_TEXT, ROW_INTERP], "carried_over": [CO_INTERP], "label_review_topic": "(f)",
     "label_review_disposition": None, "effect": "no row change"},
    {"id": "D-005 page reading", "kind": "interpretation",
     "scope": "page-specific (F019 p1) reading of frozen sections 2 and 4; not a general topic (i) rule",
     "review33_verbatim": [C2_TEXT, ROW_D005, LINE_D005_PAGE_ONLY], "carried_over": [CO_D005],
     "label_review_topic": "(i)", "label_review_disposition": "D-005",
     "effect": "F019 p1 revision ambiguous and excluded; F019 revision no/no (applied as rows in this version)"},
)
ALIAS_SPECS = (
    {"alias": "F031", "of": "F001", "ruling": "Review 33 (c)(ii)", "carried_over": CO_F031,
     "basis": "content duplicate; count once ADOPTED for this cohort by the Review 33 ruling on (c)(ii), recorded as an "
              "amendment to frozen convention section 1 (which covers byte-identical files only)",
     "review33_verbatim": [ITEM7_CII_TEXT, ROW_F031], "caveat": F031_CAVEAT},
    {"alias": "F052", "of": "F038", "ruling": "frozen convention section 1", "carried_over": CO_BYTE,
     "basis": "byte-identical staged file (identical staged_sha256); frozen convention section 1 applies",
     "review33_verbatim": [ITEM7_S1_TEXT, ROW_BYTE], "caveat": None},
    {"alias": "F059", "of": "F046", "ruling": "Review 33 (c)(ii)", "carried_over": CO_F059,
     "basis": "content duplicate (render-identical except a seal outside the title block); count once ADOPTED for this "
              "cohort by the Review 33 ruling on (c)(ii), under the same amendment to frozen convention section 1",
     "review33_verbatim": [ITEM7_CII_TEXT, ROW_F059], "caveat": None},
    {"alias": "F070", "of": "F067", "ruling": "frozen convention section 1", "carried_over": CO_BYTE,
     "basis": "byte-identical staged file (identical staged_sha256); frozen convention section 1 applies",
     "review33_verbatim": [ITEM7_S1_TEXT, ROW_BYTE], "caveat": None},
)


class ApplyError(Exception):
    pass


# ------------------------------------------------------------------ helpers
def _split_row(row):
    pid, pg, field = row.split("/")
    return pid, pg[1:], field


def _carried(er, prefix):
    hits = [c for c in er.get("carried_over", []) if c.get("item", "").startswith(prefix)]
    if len(hits) != 1:
        raise ApplyError("carried_over item %r found %d times" % (prefix, len(hits)))
    return hits[0]


def _topic(reviewed1, prefix):
    hits = [c for c in reviewed1["convention_rulings"] if c["topic"].startswith(prefix + " ")]
    if len(hits) != 1:
        raise ApplyError("label-review convention topic %r found %d times" % (prefix, len(hits)))
    return hits[0]


def _canon(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


def _path(*parts):
    return "/".join(str(p) for p in parts)


def diff_paths(a, b, path=()):
    """Yield (path tuple, kind) for every place where two JSON values differ (dict keys recursed, equal-length lists
    recursed by index, leaves compared by canonical JSON so that 1 and true differ)."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                yield path + (k,), "added"
            elif k not in b:
                yield path + (k,), "removed"
            else:
                yield from diff_paths(a[k], b[k], path + (k,))
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            yield from diff_paths(x, y, path + (i,))
    elif _canon(a) != _canon(b):
        yield path, "changed"


def _ruled_question_indexes(reviewed1, pid, ruling_id):
    return [j for j, q in enumerate(reviewed1["documents"][pid].get("questions") or [])
            if q.get("disposition_id") == ruling_id]


def _marked_unresolved(reviewed1, pid, ruling_id):
    d = reviewed1["documents"][pid]
    ruled_q = {d["questions"][j]["question"]: j for j in _ruled_question_indexes(reviewed1, pid, ruling_id)}
    return [(i, s, ruled_q[s]) for i, s in enumerate(d.get("unresolved") or []) if s in ruled_q]


def enumerated_paths(reviewed1):
    """Every documents/... and escalations/... path that Review 33 section 4.4 allows to differ."""
    allowed = set()
    for spec in PAGE_ROW_SPECS:
        pid, pg, field = _split_row(spec["row"])
        for k in tuple(spec["apply"]) + ("open_question", "review33_ruling"):
            allowed.add(_path("documents", pid, "pages", pg, field, k))
    for spec in DOC_SPECS:
        for k in tuple(spec["changes"]) + ("open_question", "review33_ruling"):
            allowed.add(_path("documents", spec["doc"], "review", spec["field"], k))
        for j in _ruled_question_indexes(reviewed1, spec["doc"], spec["ruling_id"]):
            for k in ("ruling", "open_question", "review33_ruling"):
                allowed.add(_path("documents", spec["doc"], "questions", j, k))
        if _marked_unresolved(reviewed1, spec["doc"], spec["ruling_id"]):
            allowed.add(_path("documents", spec["doc"], "unresolved_review33_marks"))
    for i, _ in enumerate(reviewed1.get("escalations") or []):
        allowed.add(_path("escalations", i, "status"))
        allowed.add(_path("escalations", i, "ruled_by"))
    return allowed


def check_only_enumerated_changes(reviewed1, reviewed2):
    """Return the differing paths that are not enumerated by Review 33 section 4.4 (empty list when clean)."""
    allowed = enumerated_paths(reviewed1)
    unexpected = []
    for p, kind in diff_paths(reviewed1, reviewed2):
        top = p[0]
        if top in METADATA_KEYS or top in NEW_KEYS:
            continue
        s = _path(*p)
        if s not in allowed:
            unexpected.append({"path": s, "kind": kind})
    for k in METADATA_KEYS:
        if k not in reviewed2:
            unexpected.append({"path": k, "kind": "removed"})
    lineage = (reviewed2.get("lineage") or {}).get("reviewed_1") or {}
    for k in METADATA_KEYS:
        if _canon(lineage.get(k)) != _canon(reviewed1.get(k)):
            unexpected.append({"path": "lineage/reviewed_1/" + k, "kind": "not the verbatim reviewed-1 value"})
    return unexpected


def _status_counts(docs):
    counts = {f: {} for f in FIELDS}
    for d in docs.values():
        for page in (d.get("pages") or {}).values():
            for f in FIELDS:
                if f in page:
                    s = page[f]["review_status"]
                    counts[f][s] = counts[f].get(s, 0) + 1
    return {f: dict(sorted(v.items())) for f, v in counts.items()}


# ------------------------------------------------------------------ main function
def build_reviewed2(reviewed1, escalation_rulings_final, review33_hashes, meta=None, review33_text=None):
    """Return r32-labels-reviewed-2. Pure: no I/O, no clock."""
    meta = dict(meta or {})
    er = escalation_rulings_final
    h = {k: review33_hashes.get(k) for k in ("review33_sha256", "escalation_rulings_final_sha256",
                                             "dispositions_sha256")}
    if not all(h.values()):
        raise ApplyError("review33_hashes must give review33_sha256, escalation_rulings_final_sha256 and "
                         "dispositions_sha256")
    if reviewed1.get("version") != PREV_VERSION:
        raise ApplyError("input is not %s: %r" % (PREV_VERSION, reviewed1.get("version")))
    if er.get("dispositions_sha256") != h["dispositions_sha256"]:
        raise ApplyError("ESCALATION-RULINGS.final.json binds dispositions %r, not %r"
                         % (er.get("dispositions_sha256"), h["dispositions_sha256"]))
    if _canon(reviewed1.get("count_once_aliases")) != _canon(EXPECTED_ALIASES):
        raise ApplyError("reviewed-1 count_once_aliases differ from the four Review 33 names: %r"
                         % (reviewed1.get("count_once_aliases"),))
    if review33_text is not None:
        quotes = {C2_TEXT, ITEM8_TEXT, ITEM7_CII_TEXT, ITEM7_S1_TEXT, LINE_D005_PAGE_ONLY}
        for a in AMENDMENTS:
            quotes.update(a["review33_verbatim"])
        for a in ALIAS_SPECS:
            quotes.update(a["review33_verbatim"])
        missing = sorted(q for q in quotes if q not in review33_text)
        if missing:
            raise ApplyError("INDEPENDENT-REVIEW.md does not contain verbatim: %r" % (missing,))
        for name in ("escalation_rulings_final_sha256", "dispositions_sha256"):
            if h[name] not in review33_text:
                raise ApplyError("INDEPENDENT-REVIEW.md does not name %s %s" % (name, h[name]))

    ref = {"review": REVIEW33_NAME, "review33_sha256": h["review33_sha256"],
           "escalation_rulings_final_sha256": h["escalation_rulings_final_sha256"],
           "dispositions_sha256": h["dispositions_sha256"]}

    # ---- the rulings file must name exactly the rows this function applies
    for rid in ("D-004", "D-005"):
        if rid not in er:
            raise ApplyError("ESCALATION-RULINGS.final.json has no %s" % rid)
    page_rows_expected = {s["row"] for s in PAGE_ROW_SPECS}
    page_rows_given = set()
    for rid in ("D-004", "D-005"):
        for k, v in er[rid]["resulting_rows"].items():
            if k == "other_identities":
                if not (isinstance(v, str) and v.startswith("unchanged")):
                    raise ApplyError("%s other_identities ruling is not 'unchanged': %r" % (rid, v))
                continue
            page_rows_given.add(k)
    if page_rows_given != page_rows_expected:
        raise ApplyError("resulting_rows %r differ from the section 4.4 page rows %r"
                         % (sorted(page_rows_given), sorted(page_rows_expected)))
    doc_rows_given = {k for rid in ("D-004", "D-005") for k in er[rid]["document_level"]}
    if doc_rows_given != {s["row"] for s in DOC_SPECS}:
        raise ApplyError("document_level rows %r differ from the section 4.4 document rows" % (sorted(doc_rows_given),))

    r2 = {k: copy.deepcopy(v) for k, v in reviewed1.items() if k not in METADATA_KEYS}
    docs = r2["documents"]
    change_log = []

    def log(path, kind, before, after, rid, section):
        e = {"path": path, "change": kind, "provenance": "Review 33 %s" % rid, "review33_section": section,
             "review33_sha256": h["review33_sha256"],
             "escalation_rulings_final_sha256": h["escalation_rulings_final_sha256"]}
        if kind != "added":
            e["from"] = copy.deepcopy(before)
        if kind != "removed":
            e["to"] = copy.deepcopy(after)
        change_log.append(e)

    def close_question(text, rid):
        return {"question": text, "status": "closed: " + RULED[rid],
                "closed_by": "%s, ruling %s (%s), INDEPENDENT-REVIEW.md sha256 %s, ESCALATION-RULINGS.final.json "
                             "sha256 %s" % (REVIEW33_NAME, rid, OUTCOME[rid], h["review33_sha256"],
                                            h["escalation_rulings_final_sha256"])}

    # ---- page-field rows (section 4.4 items 1, 2, 4)
    applied_rows = {}
    for spec in PAGE_ROW_SPECS:
        rid = spec["ruling_id"]
        pid, pg, field = _split_row(spec["row"])
        ruling = er[rid]["resulting_rows"][spec["row"]]
        covered = set(spec["apply"]) | set(spec["must_equal"]) | set(spec["null_equals_absent"]) | set(spec["not_applied"])
        if set(ruling) != covered:
            raise ApplyError("%s ruling keys %r are not the enumerated keys %r" % (spec["row"], sorted(ruling),
                                                                                 sorted(covered)))
        if ruling["review_status"] != RULED[rid] or ruling["state"] != "ambiguous":
            raise ApplyError("%s ruling is not '%s' / ambiguous" % (spec["row"], RULED[rid]))
        fld = docs[pid]["pages"][pg][field]
        for k, v in spec["pre"].items():
            if fld.get(k) != v:
                raise ApplyError("%s reviewed-1 %s is %r, Review 33 states %r" % (spec["row"], k, fld.get(k), v))
        for k in spec["must_equal"]:
            if _canon(fld.get(k)) != _canon(ruling[k]):
                raise ApplyError("%s reviewed-1 %s %r differs from the ruling %r (must stay unchanged)"
                                 % (spec["row"], k, fld.get(k), ruling[k]))
        for k in spec["null_equals_absent"]:
            if ruling[k] is not None or fld.get(k) is not None:
                raise ApplyError("%s %s must be null/absent on both sides" % (spec["row"], k))
        if "open_question" not in fld:
            raise ApplyError("%s carries no open question to close" % spec["row"])
        base = _path("documents", pid, "pages", pg, field)
        superseded, added = {}, []
        for k in spec["apply"]:
            if k in fld and _canon(fld[k]) == _canon(ruling[k]):
                continue
            if k in fld:
                superseded[k] = copy.deepcopy(fld[k])
                log(base + "/" + k, "set", fld[k], ruling[k], rid, spec["section"])
            else:
                added.append(k)
                log(base + "/" + k, "added", None, ruling[k], rid, spec["section"])
            fld[k] = copy.deepcopy(ruling[k])
        oq = fld.pop("open_question")
        log(base + "/open_question", "removed", oq, None, rid, spec["section"])
        block = dict(ref, ruling_id=rid, outcome=OUTCOME[rid], review33_section=spec["section"],
                     ruling_text=er[rid]["ruling"], superseded_value=superseded, added_keys=added,
                     open_question_closed=close_question(oq, rid),
                     unchanged_and_confirmed={k: copy.deepcopy(ruling[k]) for k in spec["must_equal"]},
                     owner_alternative_not_applied=er[rid].get("owner_alternative"))
        for k, why in spec["not_applied"].items():
            block["ruling_row_" + k] = ruling[k]
            block["ruling_row_%s_not_applied_because" % k] = why
        fld["review33_ruling"] = block
        log(base + "/review33_ruling", "added", None, block, rid, spec["section"])
        applied_rows[spec["row"]] = {k: copy.deepcopy(fld.get(k, ABSENT)) for k in
                                     ("state", "literal", "candidates", "review_status", "excluded_from_scoring")}

    # ---- document-field rows (section 4.4 items 3, 5), the D-00x questions and unresolved entries
    for spec in DOC_SPECS:
        rid, pid, field = spec["ruling_id"], spec["doc"], spec["field"]
        target = er[rid]["document_level"][spec["row"]]
        e = docs[pid]["review"][field]
        for k, v in spec["pre"].items():
            if e.get(k) != v:
                raise ApplyError("%s reviewed-1 %s is %r, Review 33 states %r" % (spec["row"], k, e.get(k), v))
        if set(target) != {"resolved_for_scoring", "carries_fact"}:
            raise ApplyError("%s document ruling keys %r" % (spec["row"], sorted(target)))
        changed = sorted(k for k in target if e[k] != target[k])
        if tuple(changed) != tuple(sorted(spec["changes"])):
            raise ApplyError("%s would change %r, Review 33 section 4.4 enumerates %r"
                             % (spec["row"], changed, sorted(spec["changes"])))
        base = _path("documents", pid, "review", field)
        superseded = {}
        for k in changed:
            superseded[k] = e[k]
            log(base + "/" + k, "set", e[k], target[k], rid, spec["section"])
            e[k] = target[k]
        if "open_question" not in e:
            raise ApplyError("%s carries no open question to close" % spec["row"])
        oq = e.pop("open_question")
        log(base + "/open_question", "removed", oq, None, rid, spec["section"])
        block = dict(ref, ruling_id=rid, outcome=OUTCOME[rid], review33_section=spec["section"],
                     ruling_text=er[rid]["ruling"], superseded_value=superseded,
                     open_question_closed=close_question(oq, rid),
                     count_impact=er[rid].get("count_impact"),
                     owner_alternative_not_applied=er[rid].get("owner_alternative"))
        e["review33_ruling"] = block
        log(base + "/review33_ruling", "added", None, block, rid, spec["section"])
        applied_rows[spec["row"]] = {"resolved_for_scoring": e["resolved_for_scoring"], "carries_fact": e["carries_fact"]}

        qsec = QUESTION_SECTION[rid]
        for j in _ruled_question_indexes(reviewed1, pid, rid):
            q = docs[pid]["questions"][j]
            if not q["ruling"].startswith("unresolved"):
                raise ApplyError("%s question %d is not unresolved: %r" % (pid, j, q["ruling"]))
            qbase = _path("documents", pid, "questions", j)
            old = q["ruling"]
            log(qbase + "/ruling", "set", old, RULED[rid], rid, qsec)
            q["ruling"] = RULED[rid]
            qblock = dict(ref, ruling_id=rid, outcome=OUTCOME[rid], review33_section=qsec,
                          superseded_value={"ruling": old})
            if "open_question" in q:
                oqq = q.pop("open_question")
                log(qbase + "/open_question", "removed", oqq, None, rid, qsec)
                qblock["open_question_closed"] = close_question(oqq, rid)
            q["review33_ruling"] = qblock
            log(qbase + "/review33_ruling", "added", None, qblock, rid, qsec)
            applied_rows["%s question %d" % (pid, j)] = {"ruling": RULED[rid]}
        marks = [dict(ref, item=s, index=i, status=RULED[rid], ruling_id=rid, question_index=j,
                      note="this 'unresolved' entry (kept verbatim in the unresolved list) is ruled; see questions[%d]" % j)
                 for i, s, j in _marked_unresolved(reviewed1, pid, rid)]
        if marks:
            docs[pid]["unresolved_review33_marks"] = marks
            log(_path("documents", pid, "unresolved_review33_marks"), "added", None, marks, rid, qsec)

    # ---- escalations (section 4.4 item 6)
    esc = r2.get("escalations") or []
    er_rows = {r.replace(" (document)", "") for rid in ("D-004", "D-005") for r in er[rid]["rows"]}
    if {x["row"] for x in esc} != er_rows or len(esc) != 6:
        raise ApplyError("escalations %r are not the six D-004/D-005 rows %r" % ([x["row"] for x in esc], sorted(er_rows)))
    for i, x in enumerate(esc):
        rid = x.get("disposition_id")
        if rid not in RULED:
            raise ApplyError("escalation %s has disposition %r, which Review 33 did not rule" % (x["row"], rid))
        if x["level"] == "question":
            js = _ruled_question_indexes(reviewed1, x["row"].split()[0], rid)
            resulting = {"ruling": RULED[rid], "question_indexes": js}
        else:
            resulting = applied_rows[x["row"]]
        x["status"] = RULED[rid]
        x["ruled_by"] = dict(ref, ruling_id=rid, outcome=OUTCOME[rid], review33_section=ESCALATION_SECTION,
                             resulting_value=copy.deepcopy(resulting))
        log(_path("escalations", i, "status"), "added", None, x["status"], rid, ESCALATION_SECTION)
        log(_path("escalations", i, "ruled_by"), "added", None, x["ruled_by"], rid, ESCALATION_SECTION)

    # ---- count-once alias annotations (section 4.3, 4.4 item 7); count_once_aliases itself is unchanged
    annotations = {}
    for a in ALIAS_SPECS:
        co = _carried(er, a["carried_over"])
        if a["caveat"] and a["caveat"] not in co["final_ruling"]:
            raise ApplyError("caveat for %s not in the final ruling text" % a["alias"])
        ann = dict(ref, of=a["of"], ruling=a["ruling"], basis=a["basis"], review33_section="4.3; 4.4 item 7",
                   review33_verbatim=list(a["review33_verbatim"]), final_ruling_verbatim=co["final_ruling"])
        if a["caveat"]:
            ann["caveat"] = a["caveat"]
        annotations[a["alias"]] = ann
        rid = "(c)(ii)" if a["ruling"].startswith("Review 33") else "section 4.3 (frozen section 1)"
        change_log.append({"path": "count_once_alias_annotations/" + a["alias"], "change": "added", "to": ann,
                           "provenance": "Review 33 %s" % rid, "review33_section": "4.3; 4.4 item 7",
                           "review33_sha256": h["review33_sha256"],
                           "escalation_rulings_final_sha256": h["escalation_rulings_final_sha256"]})
    if {k: v["of"] for k, v in annotations.items()} != EXPECTED_ALIASES:
        raise ApplyError("alias annotations do not cover the four aliases")

    # ---- amendment and interpretation list (condition C-2; section 4.3, 4.4 item 8)
    items = []
    for a in AMENDMENTS:
        topic = _topic(reviewed1, a["label_review_topic"])
        if topic.get("disposition_id") != a["label_review_disposition"]:
            raise ApplyError("%s: label-review topic %s carries disposition %r, expected %r"
                             % (a["id"], topic["topic"], topic.get("disposition_id"), a["label_review_disposition"]))
        co = [_carried(er, p) for p in a["carried_over"]]
        items.append({"id": a["id"], "kind": a["kind"], "scope": a["scope"], "effect": a["effect"],
                      "review33_verbatim": list(a["review33_verbatim"]),
                      "escalation_rulings_final_verbatim": [{"item": c["item"], "ruling": c.get("ruling"),
                                                             "final_ruling": c["final_ruling"]} for c in co],
                      "label_review_convention_topic": topic["topic"],
                      "label_review_disposition_id": topic.get("disposition_id"),
                      "label_review_disposition_note": "ids D-001..D-005 here are the label review's dispositions "
                                                       "(M2-label-review-r32-draft-1/DISPOSITIONS.json e8828bec...), "
                                                       "not Review 33's DISPOSITIONS.json"})
    amend = dict(ref, condition="C-2", condition_c2_verbatim=C2_TEXT, section_4_4_item_8_verbatim=ITEM8_TEXT,
                 status="recorded as Review 33 rulings (amendments and interpretations); NOT owner decisions; the "
                        "owner may reverse them (Review 33 section 7)",
                 items=items)
    for it in items:
        change_log.append({"path": "convention_amendments_and_interpretations/items/" + it["id"], "change": "added",
                           "to": {"id": it["id"], "kind": it["kind"]}, "provenance": "Review 33 C-2",
                           "review33_section": "condition C-2; 4.3; 4.4 item 8",
                           "review33_sha256": h["review33_sha256"],
                           "escalation_rulings_final_sha256": h["escalation_rulings_final_sha256"]})

    # ---- post-conditions: nothing left open
    left = []
    for pid, d in sorted(docs.items()):
        for pg, page in (d.get("pages") or {}).items():
            for f in FIELDS:
                x = page.get(f)
                if x and (x.get("review_status") == "unresolved" or "open_question" in x):
                    left.append("%s/p%s/%s" % (pid, pg, f))
        for f in FIELDS:
            x = d["review"][f]
            if "unresolved" in (x.get("resolved_for_scoring"), x.get("carries_fact")) or "open_question" in x:
                left.append("%s/%s" % (pid, f))
        for j, q in enumerate(d.get("questions") or []):
            if q["ruling"].startswith("unresolved") or "open_question" in q:
                left.append("%s question %d" % (pid, j))
    if left:
        raise ApplyError("still unresolved after application: %r" % left)

    r2.update({
        "version": VERSION,
        "status": STATUS_TEXT,
        "derived_from": {"version": PREV_VERSION, "sha256": meta.get("reviewed1_sha256")},
        "applied": {
            "review": REVIEW33_NAME,
            "review33_sha256": h["review33_sha256"],
            "review33_verdict": REVIEW33_VERDICT,
            "escalation_rulings_final_sha256": h["escalation_rulings_final_sha256"],
            "escalation_rulings_draft_sha256_superseded_for_application":
                (er.get("supersedes_for_application") or {}).get("sha256"),
            "dispositions_sha256": h["dispositions_sha256"],
            "conditions_applied": list(CONDITIONS_APPLIED),
            "rulings_applied": ["D-004 AMBIGUOUS (F069 p1/p3 identity; F069 identity no/no)",
                                "D-005 AMBIGUOUS (F019 p1 revision; F019 revision no/no)",
                                "count-once (c)(ii) ADOPTED (annotation of F031->F001, F059->F046; no row change)",
                                "frozen section 1 (annotation of F052->F038, F070->F067; no row change)",
                                "C-2 amendment and interpretation list"],
            "applied_by": "R32APPLY2-IMPL (ORCH-04.1), Claude Opus 5.5 (claude-opus-5-5), effort High; mechanical "
                          "application; no image read; no ruling re-made",
            "rules": {
                "page rows": "keys state, literal, candidates and review_status are taken from "
                             "ESCALATION-RULINGS.final.json resulting_rows where section 4.4 lists them as changing; "
                             "association, excluded_from_scoring (and for F019 state, candidates, region) must already "
                             "equal the ruling and are left unchanged; open_question is removed and kept, closed, under "
                             "review33_ruling.open_question_closed; every other key is unchanged",
                "document rows": "resolved_for_scoring and carries_fact from document_level where section 4.4 lists "
                                 "them as changing; open_question closed as above",
                "questions": "the D-005 question's ruling becomes 'ruled (Review 33, D-005)'; its open_question is "
                             "closed under review33_ruling; the 'unresolved' list is kept verbatim and its D-005 entry "
                             "is marked ruled in unresolved_review33_marks",
                "escalations": "every entry keeps its keys and gains status and ruled_by (hashes and resulting value)",
                "count_once_aliases": "unchanged as a mapping (the frozen count-once rule reads it); annotations are in "
                                      "count_once_alias_annotations",
                "everything else": "identical to reviewed-1 at field level; replaced metadata kept verbatim under "
                                   "lineage.reviewed_1; asserted by check_only_enumerated_changes",
            },
            "not_applied": [{"row": "F019/p1/revision", "key": "note",
                             "reason": PAGE_ROW_SPECS[2]["not_applied"]["note"]},
                            {"row": "F069/p1/identity, F069/p3/identity",
                             "key": "printed_label, semantic_role, region, value_note, evidence, review_provenance, "
                                    "other_identities",
                             "reason": "not listed as changing in section 4.4 items 1-2; kept as in reviewed-1"}],
            "page_field_status_counts": _status_counts(docs),
            "escalations_ruled": len(esc),
            "escalations_open": 0,
            "change_log_entries": len(change_log),
        },
        "lineage": {"reviewed_1": {k: copy.deepcopy(reviewed1.get(k)) for k in METADATA_KEYS},
                    "note": "reviewed-1 top-level metadata replaced in this version, kept verbatim"},
        "change_log": change_log,
        "count_once_alias_annotations": annotations,
        "convention_amendments_and_interpretations": amend,
        "generated_at_utc": meta.get("generated_at_utc"),
        "generator": {"script": meta.get("generator_script"), "sha256": meta.get("generator_sha256")},
    })

    # ---- nothing else changed: the diff must equal the change log on documents/escalations, inside the enumerated set
    unexpected = check_only_enumerated_changes(reviewed1, r2)
    if unexpected:
        raise ApplyError("keys outside the enumerated Review 33 changes differ: %r" % unexpected)
    diffed = {_path(*p) for p, _ in diff_paths(reviewed1, r2) if p[0] in ("documents", "escalations")}
    logged = {e["path"] for e in change_log if e["path"].split("/")[0] in ("documents", "escalations")}
    if diffed != logged:
        raise ApplyError("change log and diff disagree: only diffed %r, only logged %r"
                         % (sorted(diffed - logged), sorted(logged - diffed)))
    for k in UNCHANGED_TOP_KEYS:
        if _canon(r2[k]) != _canon(reviewed1[k]):
            raise ApplyError("%s changed" % k)
    return r2


# ------------------------------------------------------------------ CLI
PILOT = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot"
R33 = ("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/"
       "master-roadmap/reviews/M2-review-33")
PKG = PILOT + "/fresh-cohort-r32-reviewed-2"
FROZEN = {
    "reviewed1": (PILOT + "/fresh-cohort-r32-reviewed/labels/R32-LABELS-REVIEWED-1.json",
                  "00e53e8253adf86fc5cabbd1659576a2e728f4d0ef20b084f7aaba3157379779"),
    "review33": (R33 + "/INDEPENDENT-REVIEW.md", "8d20baecc8eef24d2047287de77b3c252c1e5641f2dc61c5ffe449f6bbd97804"),
    "escalation_rulings_final": (R33 + "/ESCALATION-RULINGS.final.json",
                                 "e2fe503d96a3bc08c99ce52862d2017a567f6e2a6677744f43750c5ebc7611a0"),
    "dispositions": (R33 + "/DISPOSITIONS.json", "ceb8fdcc6cc3e54219ab22686fc663a66c93ca5ed44316255ddf24745018315b"),
}


def sha256_file(path):
    hh = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            hh.update(chunk)
    return hh.hexdigest()


def dump_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=PKG + "/labels/R32-LABELS-REVIEWED-2.json")
    args = ap.parse_args(argv)
    got = {}
    for name, (path, exp) in FROZEN.items():
        got[name] = sha256_file(path)
        if got[name] != exp:
            print("PACKET MISMATCH", name, path, got[name], "!=", exp)
            return 2
    with open(FROZEN["reviewed1"][0], encoding="utf-8") as f:
        reviewed1 = json.load(f)
    with open(FROZEN["escalation_rulings_final"][0], encoding="utf-8") as f:
        er = json.load(f)
    with open(FROZEN["review33"][0], encoding="utf-8") as f:
        review_text = f.read()
    me = os.path.abspath(__file__).replace("\\", "/")
    hashes = {"review33_sha256": got["review33"], "escalation_rulings_final_sha256": got["escalation_rulings_final"],
              "dispositions_sha256": got["dispositions"]}
    meta = {"reviewed1_sha256": got["reviewed1"],
            "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "generator_script": me, "generator_sha256": sha256_file(me)}
    r2 = build_reviewed2(reviewed1, er, hashes, meta, review33_text=review_text)
    if os.path.exists(args.out):
        print("refusing to overwrite", args.out)
        return 3
    dump_json(r2, args.out)
    print("wrote", args.out, sha256_file(args.out))
    print("change_log entries", len(r2["change_log"]), "status counts",
          json.dumps(r2["applied"]["page_field_status_counts"], sort_keys=True))
    print("unexpected diffs", check_only_enumerated_changes(reviewed1, r2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
