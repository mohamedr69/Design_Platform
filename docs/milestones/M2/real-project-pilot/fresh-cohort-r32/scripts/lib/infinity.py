"""Helper for the EP-22349 Infinity Engineering / Al Arabia drawing sheets (SHEET NO. in the title block, no revision cell,
no review stamp unless stated). Every value passed in was read from the page renders / crops by the drafter."""
import json


def sheet(pid, title, sheet_no, crop, status_text=None, id_region=(0.89, 0.955, 0.93, 0.97), rev=None, decision=None, extra_unresolved=(), kind=None):
    p = {"page_role": f"Infinity Engineering Consultants / Al Arabia drawing sheet: {title}" + (f" (printed status '{status_text}')" if status_text else ""),
         "identity": {"state": "present", "literal": sheet_no, "printed_label": "SHEET NO.", "semantic_role": "own sheet number in the title block", "region": list(id_region), "evidence": [crop], "association": "resolved",
                      "value_note": "the title block has no separate drawing-number cell; SHEET NO. is the sheet's own number"},
         "revision": rev or {"state": "absent", "note": "the title block has no revision cell or revision table"},
         "decision": decision or {"state": "absent", "absent_kind": "no_decision_area", "note": "no consultant or authority review stamp on this sheet" + (f"; '{status_text}' is the issuer's drawing status, not a review decision" if status_text else "")},
         "other_identities": [{"literal": "0815", "printed_label": "PLOT NO.", "role": "plot number"}, {"literal": "000", "printed_label": "JOB. NO.", "role": "job number"}]}
    if status_text == "AS BUILT":
        p["other_identities"].append({"literal": "2020 - 4 - 1072822", "printed_label": "OLD APPLICATION NUMBER", "role": "authority application number"})
    json.dump({"pool_id": pid, "kind": kind or f"EP-22349 drawing sheet {sheet_no}", "pages": {"1": p}, "confidence": "high" if not extra_unresolved else "medium", "unresolved": list(extra_unresolved)},
              open(f"C:/t/iso/work/r2x/r32/drafts/{pid}.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
