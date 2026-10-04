"""Helper for drafting the EP-3563 Pivot / Al Arabia shop drawing sheets with a Dewan REVIEW NOTE stamp. Every value passed
in was read from the page renders / crops by the drafter."""
import json

CLASS = {"APPROVED": "approved", "APPROVED AS NOTED": "approved as noted", "APPROVED AS NOTED / RESUBMIT": "approved as noted",
         "REVISE & RE-SUBMIT": "revise and resubmit", "REJECTED": "rejected", "FOR INFORMATION": "other"}


def sheet(pid, title, dwg, rev, id_region, id_crop, stamp_lit, stamp_region, stamp_crop, stamp_note, location="in_title_block", rev_note=None, conf="high", unresolved=(), extra=None):
    dec = {"state": "present", "literal": stamp_lit, "class": CLASS[stamp_lit], "actor": "consultant (Dewan Architects + Engineers REVIEW NOTE stamp, D14-22, The First Avenue Mall & Hotel)",
           "actor_state": "resolved", "location": location, "region": stamp_region, "evidence": [stamp_crop], "association": "resolved", "association_note": stamp_note}
    if stamp_lit == "APPROVED AS NOTED / RESUBMIT":
        dec["value_note"] = "the option also requires resubmission; class kept as approved as noted (as F001); reviewer to rule"
        unresolved = list(unresolved) + ["decision class for 'APPROVED AS NOTED / RESUBMIT' recorded as approved as noted; reviewer to rule"]
        conf = "medium"
    p = {"page_role": f"Pivot / Al Arabia electrical shop drawing sheet (A1, scanned): {title}",
         "identity": {"state": "present", "literal": dwg, "printed_label": "DWG. NO:", "semantic_role": "own drawing number in the title block", "region": id_region, "evidence": [id_crop], "association": "resolved"},
         "revision": {"state": "present", "literal": rev, "printed_label": "Rev. no.", "semantic_role": "current revision cell in the title block", "region": [id_region[2] + 0.005, id_region[1], id_region[2] + 0.03, id_region[3]], "evidence": [id_crop], "association": "resolved"},
         "decision": dec,
         "other_identities": [{"literal": "D14-22", "printed_label": "(Dewan stamp)", "role": "consultant project number"}, {"literal": "6742010", "printed_label": "PLOT NO:", "role": "plot number"}]}
    if rev_note:
        p["revision"]["value_note"] = rev_note
    if extra:
        p.update(extra)
    json.dump({"pool_id": pid, "kind": "Pivot / Al Arabia electrical shop drawing (The First Avenue Mall & Hotel) with Dewan review stamp", "pages": {"1": p},
               "confidence": conf, "unresolved": list(unresolved)}, open(f"C:/t/iso/work/r2x/r32/drafts/{pid}.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
