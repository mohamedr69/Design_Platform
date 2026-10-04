"""ORCH-08 (A-09 point 4; R34-06, R36-09): the page relationships the frozen labels record, and the EVIDENCED cross-page
identity rule of lane_judge_r32 (rule CP-R38, version cross-page-r38-2026-10-03.1).

Before (review36): an identity asserted on page p that differs from p's own value but equals the resolved identity of
ANY other page of the same non-compilation document was a "cross-page copy" (neither correct nor wrong, never a
critical) -- a fact borrowed another page's identity merely because both pages are in the same staged file.

Now a cross-page association of an asserted identity value X on page p of document D is permitted ONLY when every one
of these is evidenced:
  (S) source       the lane document carries the source sha256 of the bytes it read, and it equals D's staged sha256
                   (a lane document without a source hash, or with another, gets no association: fail closed);
  (D) document     D is not a compilation ((h): its pages are different documents) and D's identity is resolved for
                   scoring (document-level identity resolved: resolved_for_scoring yes);
  (T) target       X equals (literal_compare_r32.compare_row) a SCORABLE, RESOLVED identity value row of another page q
                   of D (truth_kind value; association resolved);
  (P) relationship the reviewed labels record a relationship between p and q, one of
        R1 listed-on-page   X is one of the identities the labels record as printed on page p itself
                            (pages[p].other_identities, any role: e.g. the register page listing an enclosure);
        R2 enclosure-of     page p's own resolved identity is listed with an enclosure role ("listed enclosure",
                            "referenced drawing") on a page r of D whose own resolved identity equals q's identity
                            (r may be q): the labels record p as an enclosure of the package identified on q;
        R3 same-identity    page p's own resolved identity literal equals q's own resolved identity literal (one
                            document identity recorded on both pages); X then matches q only through a form printed
                            on q (an alternate such as the labelled 'Rev.' tail).
Anything else is judged on page p as asserted: a wrong value (value row) or a false positive (ABSENT row); a critical
when it is an automatic acceptance. There is no deterministic document-structure rule beyond R1-R3: file names, file
membership and page order are never evidence.
Credit: a permitted association is neither correct nor wrong for page p and never credits page q. A page whose
asserted identities include a permitted cross-page value besides its own correct value is 'recovered_conflict' (no
recovery credit: "held or conflicting identity earns no recovery credit"); held values never earn credit.

relations(truth): page relationships of the truth's documents --
  * truth["page_relations"] when the truth carries them (synthetic tests);
  * for the frozen r32 truth (schema r32-truth-1, source r32-labels-reviewed-2) they are built from the hash-checked
    reviewed-2 labels (inputs_r32.load, PACKET MISMATCH on any difference) -- the truth file itself is unchanged;
  * otherwise {} (no relationship evidenced: no cross-page association at all).
Pure apart from that one hash-checked read; nothing is written; no model is called."""
from __future__ import annotations

import labels_adapter_r32 as A
import literal_compare_r32 as LC

RULE_VERSION = "cross-page-r38-2026-10-03.1"
REVIEWED2_VERSION = "r32-labels-reviewed-2"
ENCLOSURE_ROLE_WORDS = ("enclosure", "referenced drawing")
_CACHE: dict = {}


def build(reviewed2: dict) -> dict:
    """{pool_id: {page: {"own": literal | None, "own_role": str | None, "related": [{"literal", "role"}]}}} from the labels."""
    out = {}
    for pid, d in (reviewed2.get("documents") or {}).items():
        pages = {}
        for pg, p in (d.get("pages") or {}).items():
            idn = (p or {}).get("identity") or {}
            pages[str(pg)] = {"own": idn.get("literal") if idn.get("state") == "present" else None, "own_role": idn.get("semantic_role"),
                              "related": [{"literal": o.get("literal"), "role": o.get("role")} for o in (p or {}).get("other_identities") or []
                                          if o.get("literal")]}
        out[pid] = pages
    return out


def relations(truth: dict) -> dict:
    if truth.get("page_relations") is not None:
        return truth["page_relations"]
    if truth.get("schema") == A.SCHEMA and truth.get("source_version") == REVIEWED2_VERSION:
        if "r32" not in _CACHE:
            import inputs_r32 as I
            _CACHE["r32"] = build(I.load("reviewed2_labels"))
        return _CACHE["r32"]
    return {}


def _value_rows(truth, pid):
    return [r for r in A.doc_rows(truth, pid, "identity") if r["truth_kind"] == "value" and r.get("association") == "resolved"]


def _same(a, b) -> bool:
    return bool(a) and bool(b) and LC.compare(a, b, "identity")["match"]


def cross_page(truth: dict, pool_id: str, page, value, ldoc) -> dict:
    """{"permitted": bool, "why": str, "target_page": q | None, "relationship": R1 | R2 | R3 | None} for an asserted identity
    `value` on `page` that does not equal the page's own truth."""
    page = str(page)
    doc = truth["documents"].get(pool_id) or {}
    out = {"permitted": False, "target_page": None, "relationship": None, "rule": RULE_VERSION}
    if not doc or doc.get("compilation"):
        return out | {"why": "compilation: pages are different documents" if doc else "unknown document"}
    if not (doc.get("fields") or {}).get("identity", {}).get("primary"):
        return out | {"why": "the document's identity is not resolved for scoring"}
    src = (ldoc or {}).get("source_sha256")
    if not src or src != doc.get("staged_sha256"):
        return out | {"why": "no source hash, or not the declared source bytes"}
    targets = [r for r in _value_rows(truth, pool_id) if r["page"] != page and LC.compare_row(r, value)["match"]]
    if not targets:
        return out | {"why": "no resolved identity of another page of the document equals the value"}
    rel = relations(truth).get(pool_id) or {}
    here = rel.get(page) or {}
    own_rows = [r for r in _value_rows(truth, pool_id) if r["page"] == page]
    own = own_rows[0]["literal"] if own_rows else None
    for q in targets:
        if any(_same(o["literal"], value) for o in here.get("related") or []):
            return out | {"permitted": True, "target_page": q["page"], "relationship": "R1", "why": "listed on this page (other_identities)"}
        if own:
            for r_pg, r_rel in rel.items():
                if r_pg == page or not _same((r_rel or {}).get("own"), q["literal"]):
                    continue
                for o in r_rel.get("related") or []:
                    if any(w in str(o.get("role") or "").lower() for w in ENCLOSURE_ROLE_WORDS) and _same(o["literal"], own):
                        return out | {"permitted": True, "target_page": q["page"], "relationship": "R2",
                                      "why": f"page {page} is a listed enclosure on page {r_pg} of the package identified on page {q['page']}"}
            if _same(own, q["literal"]):
                return out | {"permitted": True, "target_page": q["page"], "relationship": "R3",
                              "why": f"pages {page} and {q['page']} record the same document identity"}
    return out | {"target_page": targets[0]["page"],
                  "why": "no relationship between the pages is recorded in the reviewed labels (same file is not evidence)"}
