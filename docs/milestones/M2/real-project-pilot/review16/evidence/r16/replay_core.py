"""The BOQ replay / reporting path (r16.1), used by replay_boq_r16.py AND by the integration tests.

R16-02: a row the join HOLDS (geometry ambiguity or an equally good fallback alignment) keeps that state all the way
into the per-row outcome ('held_ambiguous_join', with its candidate truth ordinals and the reason) and the summary.
It earns no match, no value-accuracy and no blind-accuracy credit, and it is never relabelled 'extra_row'.
'extra_row' is reserved for an emitted row the join lists in `unmatched_emitted`; a stored row that cannot be linked to
any emitted row is 'unlinked_row'. Accounting: every emitted row is exactly one of matched / held / unmatched; every
truth row is exactly one of matched / held candidate / missed."""
from __future__ import annotations

import collections

REPLAY_CORE_VERSION = "r2x-boq-replay-core-2026-09-30.r16.1"


def build_emitted(extraction: dict) -> list[dict]:
    emitted = []
    for i, l in enumerate(extraction.get("lines") or []):
        emitted.append({"id": f"L{i}", "page": l["page"], "y": l["y_px"], "part_number": l.get("catalog_no"), "quantity": l.get("quantity"),
                        "description": l.get("description"), "accepted": True, "bounds": None})
    for i, s in enumerate(extraction.get("issues") or []):
        if str(s.get("target") or "").startswith("boq_line:"):
            d = s["detail"]
            emitted.append({"id": f"I{i}", "page": s["page"], "y": (s["region"][1] + s["region"][3]) / 2, "part_number": d.get("catalog_no"),
                            "quantity": d.get("quantity"), "description": d.get("description"), "accepted": False, "bounds": [s["region"][1], s["region"][3]]})
    return emitted


def emitted_id(emitted: list[dict], r: dict) -> str | None:
    row = r["row"]
    cands = [e for e in emitted if e["page"] == r["page"] and ((row.get("y_px") is not None and e["accepted"] and e["y"] == row["y_px"])
                                                              or (row.get("row_bounds") and not e["accepted"] and e["bounds"] == list(row["row_bounds"])))]
    return cands[0]["id"] if len(cands) == 1 else None


def classify(r, truth, join_state, reader_right, blind_right):
    """Outcome of one verified row. join_state 'ambiguous' or 'held' -> held (no credit); 'unlinked' -> unlinked_row;
    a truth-less row -> extra_row (only reached for rows the join lists as unmatched)."""
    if join_state in ("ambiguous", "held"):
        return "held_ambiguous_join"
    if join_state == "unlinked":
        return "unlinked_row"
    if truth is None:
        return "extra_row"
    if r.get("accepted_by_reader") and reader_right is False:
        return {"conflict": "caught_wrong_accepted", "validated": "missed_wrong_accepted"}.get(r.get("state"), "wrong_accepted_unverified")
    if r.get("accepted_by_reader"):
        return {"validated": "confirmed_correct", "conflict": "questioned_correct"}.get(r.get("state"), "correct_unverified")
    return "held_blind_right" if blind_right else "held_blind_wrong" if blind_right is False else "held_unread"


def replay_sheet(stored_rows: list[dict], emitted: list[dict], truth_rows: list[dict], bc) -> dict:
    """Join once, then give every stored verification row its outcome through the same states the join produced."""
    j = bc.join_rows(emitted, truth_rows)
    t_by = {t["ordinal"]: t for t in truth_rows}
    by_id = {e["id"]: e for e in emitted}
    pair_of = {e: (t, st) for e, t, st in j["pairs"]}
    rows = []
    for n, r in enumerate(stored_rows):
        eid = emitted_id(emitted, r)
        e = by_id.get(eid) or {}
        if eid is None:
            state, t_ord = "unlinked", None
        elif eid in j["held"]:
            state, t_ord = "held", None
        elif eid in pair_of:
            t_ord, state = pair_of[eid]
        else:
            state, t_ord = "unmatched", None
        truth_row = t_by.get(t_ord) if state in ("matched", "matched_geometry") else None
        reader_right = (bc.parts_equal(e.get("part_number"), truth_row.get("part_number")) and bc.quantities_equal(e.get("quantity"), truth_row.get("quantity"))) if truth_row else None
        blind = r.get("blind") or {}
        blind_right = (bc.parts_equal(blind.get("part_number"), truth_row.get("part_number")) and bc.quantities_equal(blind.get("quantity"), truth_row.get("quantity"))) \
            if (truth_row and blind) else None
        rows.append({"request_order": n + 1, "emitted_id": eid, "y": e.get("y"), "accepted_by_reader": r.get("accepted_by_reader"),
                     "emitted": {"part_number": e.get("part_number"), "quantity": e.get("quantity"), "description": e.get("description")},
                     "blind": blind or None, "verifier_state": r.get("state"),
                     "join": state, "truth_ordinal": t_ord, "held_candidates": j["held"].get(eid), "held_reason": j.get("held_reasons", {}).get(eid),
                     "truth": {k: truth_row.get(k) for k in ("part_number", "quantity", "description")} if truth_row else None,
                     "reader_right": reader_right, "blind_right": blind_right, "outcome": classify(r, truth_row, state, reader_right, blind_right)})
    emitted_ids = {e["id"] for e in emitted}
    matched_e = {p[0] for p in j["pairs"] if p[2] in ("matched", "matched_geometry") and p[0] not in j["held"]}
    held_e = set(j["held"])
    unmatched_e = set(j["unmatched_emitted"])
    held_t = {o for c in j["held"].values() for o in c}
    matched_t = {p[1] for p in j["pairs"] if p[2] in ("matched", "matched_geometry") and p[0] not in j["held"]}
    missed_t = set(j["unmatched_truth"])
    all_t = {t["ordinal"] for t in truth_rows}
    accounting = {"emitted": {"total": len(emitted_ids), "matched": len(matched_e), "held": len(held_e), "unmatched": len(unmatched_e),
                              "complete_and_disjoint": matched_e | held_e | unmatched_e == emitted_ids and not (matched_e & held_e) and not (matched_e & unmatched_e) and not (held_e & unmatched_e)},
                  "truth": {"total": len(all_t), "matched": len(matched_t), "held_candidate": len(held_t - matched_t), "missed": len(missed_t),
                            "complete": matched_t | held_t | missed_t == all_t}}
    return {"join": j, "rows": rows, "outcomes": dict(collections.Counter(r["outcome"] for r in rows)), "accounting": accounting,
            "version": REPLAY_CORE_VERSION}
