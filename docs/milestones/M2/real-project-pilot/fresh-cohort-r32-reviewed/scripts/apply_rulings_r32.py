"""ORCH-02.1 (R32APPLY-IMPL) step 2: apply the frozen independent review to the draft labels.

Mechanical application only: no image reading, no re-ruling, no model call.

build_reviewed(draft, final_response, dispositions=None, meta=None, other_identity_additions=None) -> reviewed
    Pure function (no I/O, no clock). Every page-field, document-field and question
    ruling of the final response is consumed exactly once; every draft field receives
    exactly one ruling; anything left over raises ApplyError.

CLI: reads the frozen draft, REVIEWER-RESPONSE.final.json and DISPOSITIONS.json,
verifies their sha256 against the frozen values, and writes
fresh-cohort-r32-reviewed/labels/R32-LABELS-REVIEWED-1.json.
"""
import argparse
import copy
import datetime
import hashlib
import json
import os
import re
import sys

FIELDS = ("identity", "revision", "decision")
# keys a 'correct' / 'reject' ruling replaces; empty values ("" / [] / None) clear the key
REPLACED_KEYS = ("state", "literal", "printed_label", "semantic_role", "class", "actor", "actor_state",
                 "location", "association", "association_note", "absent_kind", "region")
# value-bearing keys a ruling may carry beyond the table above; taken from the ruling when present
RULING_VALUE_EXTRAS = ("candidates", "referenced_revision")
STATUS = {"accept": "accepted", "correct": "corrected", "reject": "rejected", "unresolved": "unresolved"}

# Byte-identical files (frozen conventions section 1, draft duplicate_of, consolidator question rulings).
# Content duplicates (final convention (c)(ii)) come from gate_count_once_with in the final response.
VERSION = "r32-labels-reviewed-1"
STATUS_TEXT = ("AI-reviewed: owner-delegated independent Claude AI review (R32REV-B1..B7, CONSOLIDATE, CRITIC, "
               "DISPOSE; Claude Opus 5.5 High); NOT human-signed; NOT a human review")

# other_identities additions: ONLY values the final response or the dispositions record concretely.
# Each entry names its source; build_reviewed asserts every quoted string occurs verbatim in that source.
OTHER_IDENTITY_ADDITIONS = [
    {
        "pool_id": "F047", "page": "1",
        "entry": {"literal": "2020 - 4 - 1072822", "printed_label": "OLD APPLICATION NUMBER",
                  "role": "value shared verbatim with F038 p1's own letter number (topic h2); not this page's identity"},
        "source": {"kind": "disposition", "id": "D-004", "key": "evidence"},
        "must_quote": ["OLD APPLICATION NUMBER 2020 - 4 - 1072822", "F047-p1.png"],
        "basis": "D-004 evidence records the F047 p1 title-block value; D-009 leaves recording the shared F038 letter "
                 "number as an other identity to the reviewed version",
    },
    {
        "pool_id": "F028", "page": "4",
        "entry": {"literal": "00", "printed_label": "REV", "role": "revision of the commented submission"},
        "source": {"kind": "page_field_ruling", "pool_id": "F028", "page": 4, "field": "revision", "key": "note"},
        "must_quote": ["'REV 00' is printed beside the Reference",
                       "'00' should be kept only as a referenced revision (other_identities-style, role "
                       "'revision of the commented submission')"],
        "basis": "the F028 p4 revision ruling (correct, absent) records the value and its role; convention (g2)",
    },
]
# shared value named by topic (h2) / D-009 on documents whose page and printed form are NOT recorded: not added
NOT_ADDED_NOTE = ("Topic (h2) and D-009 say F038 p1's letter number '2020-4-1072822' also recurs in F048 and F049; "
                  "neither the final response nor the dispositions record the page or printed form there, so no "
                  "other_identities entry was added (never invented). F038 p2-p4 and F042 p1 already carry it in "
                  "the draft.")


class ApplyError(Exception):
    pass


def _empty(v):
    return v is None or v == "" or v == [] or v == {}


def _parse_row_ref(s):
    """'F001/p2/decision' -> ('F001', '2', 'decision'); anything else -> None."""
    m = re.fullmatch(r"(F\d{3})/p(\d+)/(identity|revision|decision)", s.strip())
    return (m.group(1), m.group(2), m.group(3)) if m else None


def _convention(final, prefix):
    hits = [c for c in final["convention_rulings"] if c["topic"].startswith(prefix)]
    if len(hits) != 1:
        raise ApplyError("convention %s found %d times" % (prefix, len(hits)))
    return hits[0]


def _dispositions_by_id(dispositions):
    if not dispositions:
        return {}
    return {d["id"]: d for d in dispositions["dispositions"]}


def _source_text(final, disp_by_id, src):
    if src["kind"] == "disposition":
        d = disp_by_id.get(src["id"])
        if d is None:
            raise ApplyError("disposition %s not found" % src["id"])
        return d.get(src["key"]) or ""
    if src["kind"] == "page_field_ruling":
        hits = [r for r in final["page_field_rulings"] if r["pool_id"] == src["pool_id"]
                and r["page"] == src["page"] and r["field"] == src["field"]]
        if len(hits) != 1:
            raise ApplyError("source ruling %r not unique" % (src,))
        return hits[0].get(src["key"]) or ""
    raise ApplyError("unknown source kind %r" % (src["kind"],))


def _apply_page_field(draft_field, ruling, disp_by_id):
    kind = ruling["ruling"]
    if kind not in STATUS:
        raise ApplyError("unknown ruling %r for %s/p%s/%s" % (kind, ruling["pool_id"], ruling["page"], ruling["field"]))
    prov = {
        "ruling": kind,
        "provenance": ruling["provenance"],
        "disposition_id": ruling.get("disposition_id"),
        "note": ruling["note"],
        "evidence_checked": list(ruling["evidence_checked"]),
    }
    if "superseded_batch_ruling" in ruling:
        prov["superseded_batch_ruling"] = ruling["superseded_batch_ruling"]
    if "superseded_value" in ruling:
        prov["superseded_value"] = ruling["superseded_value"]

    if kind == "accept":
        out = copy.deepcopy(draft_field)
        out["review_status"] = STATUS[kind]
        out["excluded_from_scoring"] = False
    elif kind in ("correct", "reject"):
        out = copy.deepcopy(draft_field)
        for k in REPLACED_KEYS:
            v = ruling.get(k)
            if _empty(v):
                out.pop(k, None)
            else:
                out[k] = copy.deepcopy(v)
        out["evidence"] = list(ruling["evidence_checked"])
        for k in RULING_VALUE_EXTRAS:
            if k in ruling and not _empty(ruling[k]):
                out[k] = copy.deepcopy(ruling[k])
        out["draft_value"] = copy.deepcopy(draft_field)
        out["review_status"] = STATUS[kind]
        out["excluded_from_scoring"] = False
    else:  # unresolved: keep the draft values, exclude, carry the open question
        out = copy.deepcopy(draft_field)
        did = ruling.get("disposition_id")
        oq_ruling = ruling.get("open_question")
        oq_disp = None
        if did is not None:
            d = disp_by_id.get(did)
            if d is None:
                raise ApplyError("unresolved row %s/p%s/%s cites missing disposition %s"
                                 % (ruling["pool_id"], ruling["page"], ruling["field"], did))
            oq_disp = d.get("open_question")
        if oq_ruling and oq_disp and oq_ruling != oq_disp:
            raise ApplyError("open question of %s/p%s/%s differs between ruling and disposition %s"
                             % (ruling["pool_id"], ruling["page"], ruling["field"], did))
        out["review_status"] = STATUS[kind]
        out["excluded_from_scoring"] = True
        out["open_question"] = oq_disp or oq_ruling or ruling["note"]
        if "state_options" in ruling:
            prov["state_options"] = ruling["state_options"]
        if "candidates" in ruling:
            prov["candidates_proposed"] = ruling["candidates"]
    out["review_provenance"] = prov
    return out


def _doc_review_entry(r):
    e = {
        "resolved_for_scoring": r["resolved_for_scoring"],
        "carries_fact": r["carries_fact"],
        "note": r["note"],
        "provenance": r["provenance"],
        "disposition_id": r.get("disposition_id"),
    }
    for k in ("open_question", "gate_count_once_with", "consolidator_note", "superseded_value",
              "superseded_batch_ruling"):
        if k in r:
            e[k] = r[k]
    return e


def build_reviewed(draft, final_response, dispositions=None, meta=None,
                   other_identity_additions=None):
    """Return the reviewed label set. Pure: no I/O, no clock; `meta` supplies hashes and timestamps."""
    meta = dict(meta or {})
    final = final_response
    disp_by_id = _dispositions_by_id(dispositions)
    docs_in = draft["documents"]
    docs = {}

    # ---- page-field rulings: index, check uniqueness and draft coverage
    pf_index = {}
    for r in final["page_field_rulings"]:
        key = (r["pool_id"], str(r["page"]), r["field"])
        if key in pf_index:
            raise ApplyError("page-field ruling duplicated: %s/p%s/%s" % key)
        pf_index[key] = r
    df_index = {}
    for r in final["document_field_rulings"]:
        key = (r["pool_id"], r["field"])
        if key in df_index:
            raise ApplyError("document-field ruling duplicated: %s/%s" % key)
        df_index[key] = r
    q_index = {}
    for r in final["document_questions"]:
        key = (r["pool_id"], r["question"])
        if key in q_index:
            raise ApplyError("question ruling duplicated: %s %r" % key)
        q_index[key] = r

    consumed_pf, consumed_df, consumed_q = set(), set(), set()

    for pid in sorted(docs_in):
        d = copy.deepcopy(docs_in[pid])
        pages = d.get("pages") or {}
        for pg in sorted(pages, key=lambda x: int(x)):
            page = pages[pg]
            for field in FIELDS:
                if field not in page:
                    continue
                key = (pid, pg, field)
                if key not in pf_index:
                    raise ApplyError("draft field without a ruling: %s/p%s/%s" % key)
                if key in consumed_pf:
                    raise ApplyError("ruling consumed twice: %s/p%s/%s" % key)
                consumed_pf.add(key)
                page[field] = _apply_page_field(page[field], pf_index[key], disp_by_id)
        # document-field rulings
        review = {}
        for field in FIELDS:
            key = (pid, field)
            if key in df_index:
                consumed_df.add(key)
                review[field] = _doc_review_entry(df_index[key])
        if review and len(review) != len(FIELDS):
            raise ApplyError("document %s has document-field rulings for %s only" % (pid, sorted(review)))
        d["review"] = review if review else None
        # questions: draft unresolved strings must each receive one ruling; worklist extras attach too
        qs = []
        draft_qs = list(d.get("unresolved") or [])
        for q in draft_qs:
            key = (pid, q)
            if key not in q_index:
                raise ApplyError("draft unresolved item without a question ruling: %s %r" % key)
        for key in sorted(k for k in q_index if k[0] == pid):
            if key in consumed_q:
                raise ApplyError("question consumed twice: %s %r" % key)
            consumed_q.add(key)
            r = q_index[key]
            e = {"question": r["question"], "ruling": r["ruling"], "reason": r["reason"],
                 "provenance": r["provenance"],
                 "source": "draft unresolved" if r["question"] in draft_qs else "review worklist"}
            for k in ("disposition_id", "open_question", "superseded_value", "superseded_batch_ruling"):
                if k in r:
                    e[k] = r[k]
            qs.append(e)
        d["questions"] = qs
        docs[pid] = d

    # ---- leftovers
    left_pf = sorted(set(pf_index) - consumed_pf)
    left_df = sorted(set(df_index) - consumed_df)
    left_q = sorted(set(q_index) - consumed_q)
    if left_pf or left_df or left_q:
        raise ApplyError("rulings not consumed: page_field=%r document_field=%r questions=%r"
                         % (left_pf, left_df, left_q))

    # ---- count-once aliases
    aliases = {}
    for pid, d in sorted(docs.items()):
        if d.get("duplicate_of"):
            if d.get("pages"):
                raise ApplyError("byte-identical duplicate %s carries pages" % pid)
            aliases[pid] = {"of": d["duplicate_of"],
                            "basis": "byte-identical staged files (frozen conventions section 1; final convention "
                                     "(c)(i); consolidator question ruling)"}
    for (pid, field), r in sorted(df_index.items()):
        w = r.get("gate_count_once_with")
        if w:
            prev = aliases.get(pid)
            if prev and prev["of"] != w:
                raise ApplyError("conflicting count-once target for %s" % pid)
            aliases[pid] = {"of": w, "basis": "content duplicate (final convention (c)(ii)); "
                                              "document-field rulings carry gate_count_once_with"}
    for pid, a in aliases.items():
        if a["of"] not in docs or a["of"] in aliases:
            raise ApplyError("count-once target %s of %s is missing or itself aliased" % (a["of"], pid))
        if pid < a["of"]:
            raise ApplyError("count-once must fall on the lower pool id: %s -> %s" % (pid, a["of"]))
        docs[pid]["count_once_alias"] = {"of": a["of"], "basis": a["basis"]}
        docs[pid]["counted_under"] = a["of"]
    for pid in docs:
        members = sorted(a for a, v in aliases.items() if v["of"] == pid)
        if members:
            docs[pid]["count_once_members"] = members
    for pid, d in docs.items():
        if d["review"] is None:
            if pid not in aliases or not d.get("duplicate_of"):
                raise ApplyError("document %s has no document-field rulings and is not a byte-identical alias" % pid)
            d["review"] = {f: {"resolved_for_scoring": None, "carries_fact": None,
                               "note": "no document-field ruling of its own (in no batch); byte-identical copy of %s, "
                                       "counted under %s (consolidator question ruling)" % (d["duplicate_of"],
                                                                                           d["duplicate_of"]),
                               "provenance": "consolidator", "disposition_id": None} for f in FIELDS}

    # ---- (d1) resubmission_required on the rows the final convention names
    d1 = _convention(final, "(d1)")
    d1_rows = []
    for s in d1["affected_rows"]:
        ref = _parse_row_ref(s)
        if ref is None:
            raise ApplyError("unparsed (d1) affected row %r" % s)
        pid, pg, field = ref
        fld = docs.get(pid, {}).get("pages", {}).get(pg, {}).get(field)
        if fld is None:
            raise ApplyError("(d1) row %s not in the labels" % s)
        fld["resubmission_required"] = "yes"
        d1_rows.append({"row": s, "class": fld.get("class"), "literal": fld.get("literal")})

    # ---- other_identities additions (recorded values only)
    added = []
    if other_identity_additions is None:
        other_identity_additions = OTHER_IDENTITY_ADDITIONS
    for add in other_identity_additions:
        text = _source_text(final, disp_by_id, add["source"])
        for q in add["must_quote"]:
            if q not in text:
                raise ApplyError("other_identities addition for %s p%s: source does not quote %r"
                                 % (add["pool_id"], add["page"], q))
        page = docs[add["pool_id"]]["pages"][add["page"]]
        existing = [o.get("literal") for o in page.get("other_identities", [])]
        if add["entry"]["literal"] in existing:
            continue
        entry = dict(add["entry"])
        entry["added_by_review"] = {"source": add["source"], "basis": add["basis"]}
        page.setdefault("other_identities", []).append(entry)
        added.append({"pool_id": add["pool_id"], "page": add["page"], "literal": entry["literal"],
                      "source": add["source"]})

    # ---- escalations
    escalations = []
    for pid, d in sorted(docs.items()):
        for pg in sorted(d.get("pages") or {}, key=int):
            for field in FIELDS:
                f = d["pages"][pg].get(field)
                if f and f.get("review_status") == "unresolved":
                    escalations.append({"row": "%s/p%s/%s" % (pid, pg, field), "level": "page_field",
                                        "disposition_id": f["review_provenance"]["disposition_id"],
                                        "open_question": f["open_question"]})
        for field in FIELDS:
            e = d["review"][field]
            if "unresolved" in (e["resolved_for_scoring"], e["carries_fact"]):
                escalations.append({"row": "%s/%s" % (pid, field), "level": "document_field",
                                    "disposition_id": e.get("disposition_id"),
                                    "resolved_for_scoring": e["resolved_for_scoring"],
                                    "carries_fact": e["carries_fact"],
                                    "open_question": e.get("open_question")})
        for q in d["questions"]:
            if q["ruling"].startswith("unresolved"):
                escalations.append({"row": "%s question" % pid, "level": "question",
                                    "disposition_id": q.get("disposition_id"), "question": q["question"],
                                    "open_question": q.get("open_question")})

    # ---- convention (a) check: no uncertain row without a note
    uncertain_without_note = []
    for pid, d in sorted(docs.items()):
        for pg, page in (d.get("pages") or {}).items():
            for field in FIELDS:
                f = page.get(field)
                if f and f.get("association") == "uncertain" and _empty(f.get("association_note")):
                    uncertain_without_note.append("%s/p%s/%s" % (pid, pg, field))

    review_of = final.get("review_of", {})
    if meta.get("draft_sha256") and review_of.get("draft_sha256") and review_of["draft_sha256"] != meta["draft_sha256"]:
        raise ApplyError("final response reviews a different draft")

    counts = {f: {s: 0 for s in STATUS.values()} for f in FIELDS}
    for d in docs.values():
        for page in (d.get("pages") or {}).values():
            for field in FIELDS:
                if field in page:
                    counts[field][page[field]["review_status"]] += 1

    return {
        "version": VERSION,
        "status": STATUS_TEXT,
        "derived_from": {"draft_version": draft.get("version"), "draft_sha256": meta.get("draft_sha256")},
        "applied": {
            "final_response_sha256": meta.get("final_response_sha256"),
            "consolidated_sha256": meta.get("consolidated_sha256"),
            "critique_sha256": meta.get("critique_sha256"),
            "dispositions_sha256": meta.get("dispositions_sha256"),
            "conventions_sha256": meta.get("conventions_sha256"),
            "review_kind": final.get("review_kind"),
            "reviewer": final.get("reviewer"),
            "final_finalised_at_utc": final.get("finalised_at_utc"),
            "rules": {
                "accept": "draft values kept",
                "correct/reject": "state, literal, printed_label, semantic_role, class, actor, actor_state, location, "
                                  "association, association_note, absent_kind, region and evidence (= evidence_checked) "
                                  "replaced by the ruling; empty values clear the key; candidates and "
                                  "referenced_revision taken from the ruling when it records them; other draft keys "
                                  "kept; the full draft field kept under draft_value",
                "unresolved": "draft values kept, review_status unresolved, excluded_from_scoring true, open_question "
                              "from the matching DISPOSITIONS entry (equal to the ruling's open_question)",
            },
            "page_field_rulings_applied": len(consumed_pf),
            "document_field_rulings_applied": len(consumed_df),
            "question_rulings_applied": len(consumed_q),
            "page_field_status_counts": counts,
            "resubmission_required_rows": d1_rows,
            "other_identities_added": added,
            "other_identities_not_added": NOT_ADDED_NOTE,
            "uncertain_without_association_note": uncertain_without_note,
        },
        "convention_rulings": copy.deepcopy(final["convention_rulings"]),
        "agents": copy.deepcopy(final["agents"]),
        "count_once_aliases": {k: v["of"] for k, v in sorted(aliases.items())},
        "escalations": escalations,
        "generated_at_utc": meta.get("generated_at_utc"),
        "generator": {"script": meta.get("generator_script"), "sha256": meta.get("generator_sha256")},
        "documents": docs,
    }


# ------------------------------------------------------------------ CLI
PACKET = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/fresh-cohort-r32"
REVIEW = ("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/"
          "master-roadmap/reviews/M2-label-review-r32-draft-1")
PKG = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/fresh-cohort-r32-reviewed"
FROZEN = {
    "draft": (PACKET + "/labels/R32-LABELS-DRAFT-1.json",
              "ebd1e24d943b3b7b21e96c1930bdb34a1078e4c5d70e3c4c34a258332688a334"),
    "final": (REVIEW + "/REVIEWER-RESPONSE.final.json",
              "920a21d63871d1618b36deb623e4121d31f3d52949d9c5617536aab7af9d4c5b"),
    "consolidated": (REVIEW + "/REVIEWER-RESPONSE.json",
                     "70f94632884af028f31d66f76557807801cf00fcca37251a2ade25c9de3a3ff8"),
    "critique": (REVIEW + "/CRITIQUE.json", "ad6798dc9aba2b1bd20ec6f4db74fbe353bdad93e01144b3ee1d32ab48387eef"),
    "dispositions": (REVIEW + "/DISPOSITIONS.json",
                     "e8828becdad00cec0ce18eec371fc1aeeb246496eda5e57aae71c5388e4d30a7"),
    "conventions": (PACKET + "/LABEL-CONVENTIONS-R32.md",
                    "5c09d4d2bc0867b8af93c93cd0e67c362f96bfeed5a0c109361931ce7dd5e570"),
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dump_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=PKG + "/labels/R32-LABELS-REVIEWED-1.json")
    args = ap.parse_args(argv)
    hashes = {}
    for name, (path, exp) in FROZEN.items():
        got = sha256_file(path)
        if got != exp:
            print("PACKET MISMATCH", name, path, got, "!=", exp)
            return 2
        hashes[name] = got
    with open(FROZEN["draft"][0], encoding="utf-8") as f:
        draft = json.load(f)
    with open(FROZEN["final"][0], encoding="utf-8") as f:
        final = json.load(f)
    with open(FROZEN["dispositions"][0], encoding="utf-8") as f:
        disp = json.load(f)
    me = os.path.abspath(__file__).replace("\\", "/")
    meta = {
        "draft_sha256": hashes["draft"], "final_response_sha256": hashes["final"],
        "consolidated_sha256": hashes["consolidated"], "critique_sha256": hashes["critique"],
        "dispositions_sha256": hashes["dispositions"], "conventions_sha256": hashes["conventions"],
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator_script": me, "generator_sha256": sha256_file(me),
    }
    reviewed = build_reviewed(draft, final, disp, meta)
    if os.path.exists(args.out):
        print("refusing to overwrite", args.out)
        return 3
    dump_json(reviewed, args.out)
    a = reviewed["applied"]
    print("wrote", args.out, sha256_file(args.out))
    print("page-field", a["page_field_rulings_applied"], "document-field", a["document_field_rulings_applied"],
          "questions", a["question_rulings_applied"], "aliases", reviewed["count_once_aliases"])
    print("status counts", json.dumps(a["page_field_status_counts"], sort_keys=True))
    print("escalations", len(reviewed["escalations"]), "uncertain w/o note", a["uncertain_without_association_note"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
