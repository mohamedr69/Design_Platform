"""Helper for the EP-26687 AREX / ENCO shop drawing approval requests (SDAR form + drawing with AREX review stamp).
Every value passed in was read from the page renders / crops by the drafter."""
import json


def sdar(ref, dwg_desc, dwg_disp, dwg_cell, pid, title):
    form = {"page_role": "AREX / ENCO SHOP DRAWING APPROVAL REQUEST (SDAR) form",
            "identity": {"state": "present", "literal": ref, "printed_label": "Ref. No.", "semantic_role": "own approval-request reference", "region": [0.653, 0.165, 0.831, 0.176], "evidence": [f"{pid}-p1-0.6_0.14_0.9_0.2.png"], "association": "resolved",
                         "value_note": "printed as 'Ref. No.' immediately followed by the number without a space"},
            "revision": {"state": "present", "literal": "R0", "printed_label": "(none: suffix of the drawing description)", "semantic_role": "suffix of the enclosed drawing's description line", "region": [0.72, 0.292, 0.78, 0.306], "evidence": [f"render {pid}-p1.png"], "association": "uncertain",
                         "association_note": f"the form has no revision cell; '-R0' ends the description '{dwg_desc}' of the enclosed drawing"},
            "decision": {"state": "present", "literal": "B - Approved as noted", "class": "approved as noted", "actor": "consultant (AREX: Arun Menon, Sam Gopinathan, signed 18-09-2023)", "actor_state": "resolved", "location": "outside_title_block",
                         "region": [0.29, 0.775, 0.42, 0.79], "evidence": [f"{pid}-p1-0.1_0.76_0.8_0.8.png"], "association": "resolved", "association_note": "blue tick in the B box; 'Refer attached drawing for comments'"}}
    sheet = {"page_role": f"ENCO shop drawing (A2, drawn rotated on the page): {title}",
             "identity": {"state": "present", "literal": dwg_cell, "printed_label": "DWG-NO:", "semantic_role": "own drawing number in the title block", "region": [0.93, 0.945, 0.972, 0.953], "evidence": [f"{pid}-p2-0.88_0.9_1_0.97.png"], "association": "resolved",
                          "value_note": f"printed as 'DWG-NO:{dwg_disp}' with a space after the hyphen; kept as printed"},
             "revision": {"state": "present", "literal": "0", "printed_label": "REV -", "semantic_role": "current revision cell in the title block", "region": [0.974, 0.945, 0.991, 0.953], "evidence": [f"{pid}-p2-0.88_0.9_1_0.97.png"], "association": "resolved", "value_note": "printed 'REV - 0'; revision table row 0 SUBMITTED FOR APPROVAL 07-09-2023 agrees"},
             "decision": {"state": "present", "literal": "B Approved As Noted", "class": "approved as noted", "actor": "consultant (AREX SHOP DRAWING REVIEW STATUS stamp, signed 18-09-2023; review table codes B by the resident and electrical engineers)", "actor_state": "resolved", "location": "outside_title_block",
                          "region": [0.62, 0.8, 0.67, 0.83], "evidence": [f"{pid}-p2-0.61_0.78_1_0.97.png"], "association": "resolved", "association_note": "blue tick at B in the AREX review status stamp on this sheet; red consultant mark-ups"}}
    json.dump({"pool_id": pid, "kind": f"AREX / ENCO shop drawing approval request {ref} + the enclosed drawing (2 pages)", "pages": {"1": form, "2": sheet}, "confidence": "medium",
               "unresolved": ["p1 revision only as the '-R0' suffix of the enclosed drawing's description (association uncertain)"]},
              open(f"C:/t/iso/work/r2x/r32/drafts/{pid}.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
