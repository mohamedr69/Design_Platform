"""Helper for EP-26687 ENCO drawings (AREX project, title block with DWG-NO / REV cells), with or without the AREX review stamp."""
import json


def sheet(pid, title, dwg_disp, crop, rev="0", decision=None, kind=None, conf="high", unresolved=()):
    p = {"page_role": f"ENCO shop drawing (A2, drawn rotated on the page): {title}",
         "identity": {"state": "present", "literal": dwg_disp, "printed_label": "DWG-NO:", "semantic_role": "own drawing number in the title block", "region": [0.93, 0.945, 0.972, 0.953], "evidence": [crop], "association": "resolved",
                      "value_note": f"printed as 'DWG-NO:{dwg_disp}'; kept as printed"},
         "revision": {"state": "present", "literal": rev, "printed_label": "REV -", "semantic_role": "current revision cell in the title block", "region": [0.974, 0.945, 0.991, 0.953], "evidence": [crop], "association": "resolved"},
         "decision": decision or {"state": "absent", "absent_kind": "no_decision_area", "note": "no consultant review stamp or status block on this copy"}}
    json.dump({"pool_id": pid, "kind": kind or f"ENCO shop drawing {dwg_disp}", "pages": {"1": p}, "confidence": conf, "unresolved": list(unresolved)},
              open(f"C:/t/iso/work/r2x/r32/drafts/{pid}.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
