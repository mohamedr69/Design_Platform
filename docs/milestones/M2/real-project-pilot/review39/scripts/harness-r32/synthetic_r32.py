"""Synthetic documents and truth for the runner's integration tests: generated PDFs of an invented project EP-990001 (no
cohort content), so the application readers' path can be exercised in dry mode without any cohort prediction.
ORCH-08C: a spec may give "pages" (default 1): the same lines are printed on that many pages (page_count = pages,
in_scope_pages = min(pages, 4)), so the visibility drill can show pages the reader leaves unread under its own limits."""
from __future__ import annotations

import hashlib
import pathlib

FIELDS = ("identity", "revision", "decision")
EP = "990001"


def make_pdf(path: pathlib.Path, lines: list[str], pages: int = 1) -> str:
    import pymupdf

    doc = pymupdf.open()
    for _ in range(max(1, int(pages))):
        page = doc.new_page(width=595, height=842)
        y = 72
        for line in lines:
            page.insert_text((72, y), line, fontsize=14)
            y += 28
    doc.save(str(path))
    doc.close()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(stage_files: pathlib.Path, specs: list[dict]) -> dict:
    """specs: [{"pool_id": "SYN001", "lines": [...], "truth": {"identity": ("value", "X") | ("absent", None) | ("not_scorable", None), ...}}]"""
    stage_files.mkdir(parents=True, exist_ok=True)
    docs, rows = {}, {}
    for s in specs:
        pid = s["pool_id"]
        n_pages = max(1, int(s.get("pages") or 1))
        sha = make_pdf(stage_files / f"{pid}.pdf", s["lines"], n_pages)
        rel = f"SYN/{pid.lower()}-synthetic-sheet.pdf"
        has = {}
        for f in FIELDS:
            kind, lit = s["truth"][f]
            has[f] = kind == "value"
            rows[f"{pid}|1|{f}"] = {"pool_id": pid, "page": "1", "field": f, "state": {"value": "present", "absent": "absent", "not_scorable": "ambiguous"}[kind],
                                    "association": "resolved" if kind != "absent" else None, "literal": lit, "class": s.get("class") if f == "decision" else None,
                                    "actor": None, "actor_state": None, "absent_kind": "no_decision_area" if (kind == "absent" and f == "decision") else None,
                                    "location": None, "printed_label": None, "semantic_role": None, "resubmission_required": False,
                                    "excluded_from_scoring": False, "review_status": "accepted", "candidates": [], "doc_resolved_for_scoring": "yes",
                                    "doc_carries_fact": "yes" if kind == "value" else "no", "truth_kind": kind, "scorable": kind != "not_scorable",
                                    "not_scorable_reasons": [] if kind != "not_scorable" else ["ambiguous"], "alternates": [], "alternate_kinds": {},
                                    "count_once_alias_of": None}
        docs[pid] = {"pool_id": pid, "canonical_id": pid, "is_alias": False, "alias_kind": None, "ep": EP, "project": f"EP-{EP}",
                     "contractor": "synthetic", "doc_key": f"EP-{EP}/{rel}", "relative_path": rel, "staged_sha256": sha, "stratum": "other",
                     "how": "other", "selection_order": None, "in_scope_pages": min(n_pages, 4), "page_count": n_pages, "labelled_pages": ["1"], "compilation": False,
                     "layout_key": "synthetic", "layout_rule": "test", "kind": "synthetic test sheet", "independent_review": True,
                     "fields": {f: {"resolved_for_scoring": "yes", "carries_fact": "yes" if has[f] else "no", "primary": True, "has_fact": has[f]} for f in FIELDS},
                     "decision_type": "none", "decision_control": "negative" if not has["decision"] else "positive"}
    return {"schema": "r32-truth-1", "source_version": "synthetic", "aliases": {}, "compilations": [], "layout_rules": [], "documents": docs, "rows": rows}
