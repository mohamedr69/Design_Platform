"""ORCH-05.1 (Review 33 C-5, R33-05): r32-labels-reviewed-2 -> per (pool id, page, field) truth for the r32 harness.

build_truth(reviewed2, renders=..., source_manifest=..., selection=..., verification=...) returns

  {"schema": "r32-truth-1", "documents": {pool_id: {...document attributes...}}, "rows": {"F001|1|identity": {...}}, ...}

Truth of one row (``truth_of(rec)``) is exactly one of three things, never confused with each other:
  * a literal string            -- state present, association resolved, not excluded, document field resolved;
  * ABSENT                      -- state absent and the document field resolved (a verified absence is possible);
  * NOT_SCORABLE                -- anything else: ambiguous, illegible, unsupported, present with association uncertain,
                                   excluded_from_scoring, review_status unresolved, or the document field's
                                   resolved_for_scoring is not "yes" (Review 33 sections 5.1 and 4.1/4.2).
A page-field with no row at all (beyond the reader scope, or an alias without own labels) is ``None`` from ``lookup``.

Document attributes: project (EP-<ep>), contractor (PROJECT-VERIFICATION.json results[ep].contractor), stratum and how
(FROZEN-SELECTION.json pool), doc_key EP-<ep>/<relative_path> and staged sha256 (SOURCE-MANIFEST.json: KEYS only, never
evidence), in_scope_pages (RENDERS.json pages_in_scope), layout_key (LAYOUT_RULES below: deterministic, from the labels'
own kind / page-1 page_role text and the drafting helpers' fixed page_role strings), decision_type (the class(es) of the
document's scorable present decision rows, or "none"), compilation (the (h) ruling's documents), count-once alias data.
Pure: no file is read here (see inputs_r32.load_all), nothing is written, no model is called."""
from __future__ import annotations

import collections
import re

FIELDS = ("identity", "revision", "decision")
SCHEMA = "r32-truth-1"
STATES = ("present", "absent", "illegible", "ambiguous", "unsupported")
SUFFIX_ROLE = "suffix of the printed document number"
LABELLED_TAIL_ROLE = "labelled revision appended to the submittal reference"


class _Sentinel:
    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __bool__(self):          # never truthy: a sentinel is not a value
        return False

    def __reduce__(self):
        return (_sentinel, (self.name,))


def _sentinel(name):
    return {"NOT_SCORABLE": NOT_SCORABLE, "ABSENT": ABSENT}[name]


NOT_SCORABLE = _Sentinel("NOT_SCORABLE")
ABSENT = _Sentinel("ABSENT")

# Layout / template key: the FIRST matching rule, searched (case-insensitive) in "<kind>\n<page-1 page_role>" of the
# document's own labels (alias without pages: the canonical document's key). Rules 1-5 are the fixed page_role / kind
# strings written by the five drafting helpers in fresh-cohort-r32/scripts/lib (emaar.py, dewan.py, arex.py, enco.py,
# infinity.py); rules 6-12 name the other multi-document families visible in the reviewed labels' kind text. A document
# matching no rule is its own family: "single:<pool id>". Label text only -- file and folder names are never used.
LAYOUT_RULES = (
    ("helper:emaar", "emaar-mirage-document-submittal", r"emaar / mirage document submittal"),
    ("helper:dewan", "pivot-al-arabia-shop-drawing-dewan-stamp", r"pivot / al arabia electrical shop drawing"),
    ("helper:arex", "arex-enco-shop-drawing-approval-request", r"shop drawing approval request"),
    ("helper:enco", "enco-shop-drawing", r"(^|\n)enco shop drawing"),
    ("helper:infinity", "infinity-al-arabia-drawing-sheet", r"infinity engineering consultants / al arabia drawing sheet"),
    ("kind", "dewan-design-drawing-civil-defence-stamp", r"civil defence approved dewan design drawing"),
    ("kind", "dewan-material-submittal-form", r"material submittal form, submission sheet"),
    ("kind", "lacasa-shop-drawing-submittal-form", r"shop drawing submittal form"),
    ("kind", "contractor-reply-to-comments-sheet", r"reply to consultant comments"),
    ("kind", "al-arabia-document-transmittal", r"document transmittal"),
    ("kind", "ajman-civil-defence-approval-letter", r"civil defence approval letter"),
)
COMPILATION_TOPIC = "(h) compilation files"
EVALUATOR_DECISION = {"approved": "approved", "approved as noted": "ANN", "revise and resubmit": "rejected", "rejected": "rejected"}


def layout_key(kind: str | None, page1_role: str | None, pool_id: str) -> tuple[str, str]:
    text = f"{kind or ''}\n{page1_role or ''}".lower()
    for source, key, pattern in LAYOUT_RULES:
        if re.search(pattern, text):
            return key, source
    return f"single:{pool_id}", "single"


def _truthy_yes(v) -> bool:
    return str(v or "").strip().lower() == "yes"


def _compilations(reviewed2) -> list[str]:
    ids = set()
    for r in reviewed2.get("convention_rulings") or []:
        if r.get("topic") == COMPILATION_TOPIC:
            for row in r.get("affected_rows") or []:
                m = re.match(r"(F\d{3})", str(row))
                if m:
                    ids.add(m.group(1))
    return sorted(ids)


def _either_form(page: dict) -> list[str]:
    """(g)(1): the identity's printed form with its own labelled 'Rev.' tail, from the same page's revision row whose
    printed_label quotes it ("Rev. (in 'B01-ASC-SD-ELE-0102-Rev.00')")."""
    rev = page.get("revision") or {}
    if rev.get("semantic_role") != LABELLED_TAIL_ROLE:
        return []
    m = re.search(r"'([^']+)'", rev.get("printed_label") or "")
    return [m.group(1)] if m else []


def _suffix_base(page: dict, literal: str | None) -> list[str]:
    """The identity without its UNLABELLED revision suffix ('...-0002- R00' -> '...-0002') when the same page's
    revision row records that suffix (frozen conventions section 4 'embedded only'; ruling (g)(2)). Carried from the
    frozen evaluator .10 identity equivalence ('suffix', m2_pilot_eval.same_identity); see ADAPTER-CONTRACT.md."""
    rev = page.get("revision") or {}
    if not literal or rev.get("semantic_role") != SUFFIX_ROLE:
        return []
    m = re.search(r"\s*-\s*R\.?\s*\d+\s*$", literal, re.I) or re.search(r"\s+R\.?\s*\d+\s*$", literal, re.I)
    return [literal[:m.start()].rstrip(" -")] if m else []


def _row(pool_id, page_no, field, x: dict, doc_review: dict, page: dict) -> dict:
    state = x.get("state")
    assoc = x.get("association")
    rs, cf = (doc_review or {}).get("resolved_for_scoring"), (doc_review or {}).get("carries_fact")
    reasons = []
    if state not in STATES:
        reasons.append(f"unknown state {state!r}")
    if state in ("ambiguous", "illegible", "unsupported"):
        reasons.append(state)
    if state == "present" and assoc != "resolved":
        reasons.append("uncertain_association")
    if x.get("excluded_from_scoring") is True:
        reasons.append("excluded_from_scoring")
    if "unresolved" in str(x.get("review_status") or "").lower():
        reasons.append("review_status_unresolved")
    if not _truthy_yes(rs):
        reasons.append(f"document_field_resolved_for_scoring={rs}")
    scorable = not reasons
    if scorable and state == "present":
        kind = "value"
    elif scorable and state == "absent":
        kind = "absent"
    else:
        kind = "not_scorable"
    rec = {"pool_id": pool_id, "page": str(page_no), "field": field, "state": state, "association": assoc,
           "literal": x.get("literal"), "class": x.get("class") if field == "decision" else None,
           "actor": x.get("actor"), "actor_state": x.get("actor_state"), "absent_kind": x.get("absent_kind"),
           "location": x.get("location"), "printed_label": x.get("printed_label"), "semantic_role": x.get("semantic_role"),
           "resubmission_required": _truthy_yes(x.get("resubmission_required")),
           "excluded_from_scoring": bool(x.get("excluded_from_scoring")), "review_status": x.get("review_status"),
           "candidates": [c.get("literal") if isinstance(c, dict) else c for c in x.get("candidates") or []],
           "doc_resolved_for_scoring": rs, "doc_carries_fact": cf,
           "truth_kind": kind, "scorable": scorable, "not_scorable_reasons": reasons,
           "alternates": [], "alternate_kinds": {}}
    if field == "identity" and state == "present":
        for alt in _either_form(page):
            rec["alternates"].append(alt)
            rec["alternate_kinds"][alt] = "(g)(1) labelled tail, either form"
        for alt in _suffix_base(page, x.get("literal")):
            rec["alternates"].append(alt)
            rec["alternate_kinds"][alt] = "unlabelled suffix base form (evaluator .10 'suffix' equivalence)"
    if field == "decision" and x.get("class"):
        rec["evaluator_decision"] = EVALUATOR_DECISION.get(x.get("class"))
    return rec


def build_truth(reviewed2: dict, *, renders: dict, source_manifest: dict, selection: dict, verification: dict) -> dict:
    docs_in = reviewed2["documents"]
    aliases = dict(reviewed2.get("count_once_aliases") or {})
    src = {f["pool_id"]: f for f in source_manifest["files"]}
    rnd = {d["pool_id"]: d for d in renders["documents"]}
    sel = {p["pool_id"]: p for p in selection["pool"]}
    contractors = {ep: (r or {}).get("contractor") for ep, r in (verification.get("results") or {}).items()}
    compilations = set(_compilations(reviewed2))
    rows, documents = {}, {}
    for pid in sorted(docs_in):
        d = docs_in[pid]
        ep = str(d.get("ep") or src[pid]["ep"])
        pages = d.get("pages") or {}
        review = d.get("review") or {}
        for pg in sorted(pages, key=lambda s: int(s)):
            for f in FIELDS:
                x = (pages[pg] or {}).get(f)
                if x is None:
                    continue
                rec = _row(pid, pg, f, x, review.get(f) or {}, pages[pg])
                rec["count_once_alias_of"] = aliases.get(pid)
                rows[f"{pid}|{pg}|{f}"] = rec
        fields = {}
        for f in FIELDS:
            r = review.get(f) or {}
            fields[f] = {"resolved_for_scoring": r.get("resolved_for_scoring"), "carries_fact": r.get("carries_fact"),
                         "primary": _truthy_yes(r.get("resolved_for_scoring")),
                         "has_fact": _truthy_yes(r.get("resolved_for_scoring")) and _truthy_yes(r.get("carries_fact"))}
        p1 = (pages.get("1") or {}).get("page_role")
        lk, lsrc = layout_key(d.get("kind"), p1, pid)
        documents[pid] = {
            "pool_id": pid, "canonical_id": aliases.get(pid, pid), "is_alias": pid in aliases,
            "alias_kind": (None if pid not in aliases else
                           "byte-identical (frozen section 1)" if src[pid]["staged_sha256"] == src[aliases[pid]]["staged_sha256"]
                           else "content duplicate (Review 33 (c)(ii))"),
            "ep": ep, "project": f"EP-{ep}", "contractor": contractors.get(ep),
            "doc_key": f"EP-{ep}/{src[pid]['relative_path']}".replace("\\", "/"), "relative_path": src[pid]["relative_path"],
            "staged_sha256": src[pid]["staged_sha256"], "stratum": sel[pid]["stratum"], "how": sel[pid]["how"],
            "selection_order": sel[pid].get("selection_order"),
            "in_scope_pages": int(rnd[pid]["pages_in_scope"]), "page_count": int(rnd[pid]["page_count"]),
            "labelled_pages": sorted(pages, key=lambda s: int(s)), "compilation": pid in compilations,
            "layout_key": lk, "layout_rule": lsrc, "kind": d.get("kind"), "independent_review": True,
            "fields": fields}
    # an alias with no pages of its own (byte-identical F052, F070) takes its canonical document's layout key
    for pid, doc in documents.items():
        if doc["is_alias"] and not doc["labelled_pages"]:
            doc["layout_key"], doc["layout_rule"] = documents[doc["canonical_id"]]["layout_key"], "canonical (alias without pages)"
    for pid, doc in documents.items():
        classes = sorted({r["class"] for r in rows.values() if r["pool_id"] == pid and r["field"] == "decision"
                          and r["truth_kind"] == "value" and r["class"]})
        doc["decision_type"] = "+".join(classes) if classes else "none"
        doc["decision_control"] = _decision_control(pid, rows, doc)
    return {"schema": SCHEMA, "source_version": reviewed2.get("version"), "aliases": aliases,
            "compilations": sorted(compilations), "layout_rules": [list(r) for r in LAYOUT_RULES],
            "documents": documents, "rows": rows}


def _decision_control(pid, rows, doc) -> str:
    """positive: decision truth present and resolved (document carries the fact); negative: every in-scope decision row
    is a scorable ABSENT (blank_decision_area / no_decision_area) and the document field is resolved; otherwise none."""
    if doc["fields"]["decision"]["has_fact"]:
        return "positive"
    drows = [r for r in rows.values() if r["pool_id"] == pid and r["field"] == "decision" and int(r["page"]) <= doc["in_scope_pages"]]
    if drows and doc["fields"]["decision"]["primary"] and all(r["truth_kind"] == "absent" for r in drows):
        return "negative"
    return "none"


# --- access ------------------------------------------------------------------------------------------------------------


def lookup(truth: dict, pool_id: str, page, field: str):
    """The row for (pool id, page, field), or None when no such row exists (never labelled)."""
    return truth["rows"].get(f"{pool_id}|{page}|{field}")


def truth_of(rec):
    """literal | ABSENT | NOT_SCORABLE (rec must be a row; a missing row is the caller's None)."""
    if rec is None:
        return None
    if rec["truth_kind"] == "value":
        return rec["literal"]
    if rec["truth_kind"] == "absent":
        return ABSENT
    return NOT_SCORABLE


def canonical(truth: dict, pool_id: str) -> str:
    return truth["aliases"].get(pool_id, pool_id)


def primary(truth: dict, pool_id: str, field: str) -> bool:
    d = truth["documents"].get(pool_id)
    return bool(d) and not d["is_alias"] and d["fields"][field]["primary"] and d["independent_review"]


def has_fact(truth: dict, pool_id: str, field: str) -> bool:
    d = truth["documents"].get(pool_id)
    return bool(d) and not d["is_alias"] and d["fields"][field]["has_fact"]


def doc_rows(truth: dict, pool_id: str, field: str | None = None) -> list[dict]:
    return [r for r in truth["rows"].values() if r["pool_id"] == pool_id and (field is None or r["field"] == field)]


def population(truth: dict) -> dict:
    """Counted documents per field (canonical ids only; resolved_for_scoring yes AND carries_fact yes)."""
    return {f: sorted(pid for pid in truth["documents"] if has_fact(truth, pid, f)) for f in FIELDS}


def not_scorable_summary(truth: dict) -> dict:
    rows = [r for r in truth["rows"].values() if r["truth_kind"] == "not_scorable"]
    by_reason = collections.Counter(reason for r in rows for reason in r["not_scorable_reasons"])
    pages = {(r["pool_id"], r["page"]) for r in rows}
    return {"rows": len(rows), "pages": len(pages), "documents": len({r["pool_id"] for r in rows}),
            "by_reason": dict(sorted(by_reason.items())),
            "by_field": dict(collections.Counter(r["field"] for r in rows)),
            "rows_list": sorted(f"{r['pool_id']}|{r['page']}|{r['field']}" for r in rows)}


def serialisable(truth: dict) -> dict:
    """The truth as plain JSON (sentinels are carried by truth_kind; nothing else needs converting)."""
    return truth
