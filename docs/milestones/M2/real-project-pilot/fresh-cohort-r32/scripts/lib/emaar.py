"""Helpers for drafting the EMAAR / Mirage Document Submittal packages (EP-27331): a cover form, a contractor circulation
sheet, a drawing register and a drawing. Every value passed in was read from the page renders / crops by the drafter."""
import json


def cover(sub, rev, code_lit, actor, id_crop, dec_crop, dec_region, extra_note=""):
    return {"page_role": "Document Submittal form (cover of the package)",
            "identity": {"state": "present", "literal": sub, "printed_label": "Submittal Ref.No.", "semantic_role": "own submittal reference of the package", "region": [0.25, 0.167, 0.45, 0.178], "evidence": [id_crop], "association": "resolved"},
            "revision": {"state": "present", "literal": rev, "printed_label": "Rev. No.", "semantic_role": "revision of this submittal", "region": [0.59, 0.167, 0.61, 0.178], "evidence": [id_crop], "association": "resolved"},
            "decision": {"state": "present", "literal": code_lit, "class": {"Code A": "approved", "Code B": "approved as noted", "Code C": "revise and resubmit", "Code D": "revise and resubmit"}.get(code_lit, "other"),
                         "actor": actor, "actor_state": "resolved", "location": "outside_title_block", "region": dec_region, "evidence": [dec_crop], "association": "resolved",
                         "association_note": ("the code box is marked; the printed legend on the same page reads 'A-Approved, B-Approved with comments, C-Not Approved (Re-submit within 14 days), D-Incomplete, Resubmit, E-Submitted for Information' " + extra_note).strip()}}


def circulation(note):
    return {"page_role": "contractor (Al Sahel) J269 CIRCULATION stamp sheet",
            "identity": {"state": "absent", "note": f"handwritten contractor note '{note}' only"}, "revision": {"state": "absent"},
            "decision": {"state": "absent", "absent_kind": "no_decision_area", "note": "contractor circulation ticks and the handwritten code note are not the reviewing party's decision"},
            "other_identities": [{"literal": note, "printed_label": "(handwritten)", "role": "contractor file annotation"}]}


def register(sub, rev, crop, status=None, rows=1, first_dwg=None, region=(0.03, 0.155, 0.3, 0.167)):
    p = {"page_role": f"DRAWING REGISTER of the submittal ({rows} listed item(s))",
         "identity": {"state": "present", "literal": sub, "printed_label": "Submittal Ref:", "semantic_role": "submittal reference of the package this register belongs to", "region": list(region), "evidence": [crop], "association": "resolved", "value_note": f"printed as '{sub}-Rev.{rev}'"},
         "revision": {"state": "present", "literal": rev, "printed_label": f"Rev. (in '{sub}-Rev.{rev}')", "semantic_role": "labelled revision appended to the submittal reference", "region": [region[2] - 0.04, region[1], region[2], region[3]], "evidence": [crop], "association": "resolved"}}
    if status:
        p["decision"] = {"state": "present", "literal": status, "class": {"A": "approved", "B": "approved as noted", "C": "revise and resubmit", "D": "revise and resubmit"}.get(status, "other"),
                         "actor": "consultant (Status entries in a different typeface from the register)", "actor_state": "inferred", "location": "outside_title_block", "region": [0.7, 0.29, 0.77, 0.33], "evidence": [crop], "association": "uncertain",
                         "association_note": f"status letter(s) written per listed drawing in the Status column ({rows} row(s)), not a single decision printed for the register page; who wrote them is not printed"}
    else:
        p["decision"] = {"state": "absent", "absent_kind": "blank_decision_area", "note": "the Status column of the register is empty"}
    if first_dwg:
        p["other_identities"] = [{"literal": first_dwg, "printed_label": "Drawing No. (row 1)", "role": "listed enclosure"}]
    return p


def drawing(title, dwg, rev, letter, reviewer, id_crop, dec_crop, highlighted="green", id_region=(0.864, 0.963, 0.964, 0.97), rev_region=(0.976, 0.973, 0.984, 0.982), dec_region=(0.885, 0.215, 0.91, 0.24)):
    words = {"A": "Approved", "B": "Approved with comments", "C": "Not Approved (Re-submit with in 14 days)", "D": "Incomplete, Resubmit", "E": "Submitted for information (No approval required)"}
    p = {"page_role": f"shop drawing sheet: {title}",
         "identity": {"state": "present", "literal": dwg, "printed_label": "DRAWING NO.", "semantic_role": "own drawing number in the title block", "region": list(id_region), "evidence": [id_crop], "association": "resolved"},
         "revision": {"state": "present", "literal": rev, "printed_label": "REVISION", "semantic_role": "current revision cell in the title block", "region": list(rev_region), "evidence": [id_crop], "association": "resolved"}}
    if letter:
        p["decision"] = {"state": "present", "literal": f"{letter} {words[letter]}", "class": {"A": "approved", "B": "approved as noted", "C": "revise and resubmit", "D": "revise and resubmit", "E": "other"}[letter],
                         "actor": f"consultant (Mirage Leisure And Development review block{', Reviewed By ' + reviewer if reviewer else ''})", "actor_state": "resolved" if reviewer else "inferred",
                         "location": "in_title_block", "region": list(dec_region), "evidence": [dec_crop], "association": "resolved",
                         "association_note": f"the {letter} cell of the A-E review block in the right-hand title strip is highlighted ({highlighted})" + ("" if reviewer else "; Date Reviewed and Reviewed By are blank")}
    else:
        p["decision"] = {"state": "absent", "absent_kind": "blank_decision_area", "note": "the A-E review block is unmarked"}
    return p


def save(pid, kind, pages, confidence, unresolved):
    json.dump({"pool_id": pid, "kind": kind, "pages": pages, "confidence": confidence, "unresolved": unresolved},
              open(f"C:/t/iso/work/r2x/r32/drafts/{pid}.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
