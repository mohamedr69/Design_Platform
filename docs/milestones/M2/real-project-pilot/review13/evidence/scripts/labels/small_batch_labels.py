"""M2 Round 2 exploration: AI-drafted SOURCE labels for the frozen small batch (SMALL-BATCH.json), written from the
staged renders / text layer / Word text BEFORE any candidate prediction for these documents existed. Proposals only --
not human truth, no reviewer, no sign-off. Shape: page labels v2 (evaluator .9) plus the LABEL-FORMAT.md extensions.
Decision vocabulary as in v2 (approved | ANN | rejected | UR | ambiguous | n/a)."""
import datetime
import hashlib
import json
import pathlib

W = pathlib.Path("C:/t/iso/work/r2x")
SB = W / "SMALL-BATCH.json"
SB_SHA = "7039daa3f04935a35d9a272076be16510d4eb0a8885651f83f07af51f44d7139"
assert hashlib.sha256(SB.read_bytes()).hexdigest() == SB_SHA, "the small batch changed"
sb = json.loads(SB.read_text(encoding="utf-8"))
by_tag = {d["sha256"][:12]: d for d in sb["documents"]}


def ident(literal, label, role, own=False):
    return {"literal": literal, "printed_label": label, "role": role, "own_for_evaluation": own}


def rec(page, component, category, reference, rev, decision="n/a", actor=None, evidence=None, identities=(), states=None, register=True, confidence="high", **kw):
    d = dict(page=page, component=component, category=category, reference=reference, printed_revision=rev, decision=decision,
             decision_actor=actor, decision_evidence=evidence, identities=list(identities),
             states=states or {"identity": "clear", "revision": "clear" if rev else "absent", "decision": "absent" if decision == "n/a" else "clear"},
             register=register, confidence=confidence)
    d.update(kw)
    return d


L = {
 "d7ac7576420d": dict(scope_pages=[1], records=[], no_record_pages={
     "1": "PQ table of contents (CONTENTS / Consultant Comments & Reply to Comments on Rev.0 / 1. Introduction ...); no own identity; "
          "Rev.0 names the earlier commented revision, not this document's revision"},
     unresolved=[]),
 "535ffbdabfcf": dict(scope_pages=[1, 2, 3, 4], records=[], no_record_pages={
     "1": "section divider '1) Project Item Specification'; the 'Submittal No.:' field carries only 'Rev.0' (no number printed): identity absent",
     "2": "section divider '2) Compliance Statement' (same header block)", "3": "section divider '3) Approved Vendor List' (same header block)",
     "4": "section divider '4) Proposed Material Details' (same header block)"},
     unvalidated_pages=[5, 6, 7],
     unresolved=["CONFIRM: header 'Submittal No.:' is blank apart from 'Rev.0' -- identity absent; the literal Rev.0 is not attached to any identity (folder says Rev.01)"]),
 "a0db0f066f4e": dict(scope_pages=[1], records=[], no_record_pages={
     "1": "rotated scan of a cost estimation summary (project 'Villanova - Phase 11 (Amaranta 3)'), handwritten notes; no identity, revision or decision; "
          "the file name's EP-18101 is not printed"},
     unresolved=[]),
 "0c9737211762": dict(scope_pages=[1], records=[
     rec(1, "form", "internal request", "3105", None, register=False, confidence="medium",
         identities=[ident("3105", "DRF No.", "own_document", True), ident("EP-22510", "Project Reference", "project_or_contract"),
                     ident("SSD-P-06 B/IQF.17", "Document Reference", "other"), ident("04", "Revision Number", "other")],
         note="Design Request Form ELV Systems (scan), date 28-07-21; DRF No. handwritten; 'Document Reference SSD-P-06 B/IQF.17 / Revision Number 04' "
              "is the form template's own control block, not this request's revision; internal approvals only, no consultant decision")],
     unresolved=["CONFIRM: handwritten DRF No. read as '3105' (medium legibility)",
                 "CONFIRM: 'Revision Number 04' belongs to the form template (SSD-P-06 B/IQF.17), so the request has no own revision"]),
 "bdce7913eb15": dict(scope_pages=[1], records=[
     rec(1, "design sheet", "commercial", "EP-23091 R1", "R1", register=False, confidence="medium",
         identities=[ident("EP-23091 R1", "Qtn. Ref.", "own_document", True), ident("4836", "Enq. No.", "request")],
         note="Design Sheet (scan) dated 25-Oct-2021, to Al Shola Al Modea Safety & Security LLC, consultant Next Engineering Consultant, "
              "Menvier emergency lighting; the revision R1 is embedded in the Qtn. Ref. literal")],
     boq_rows=[
         {"page": 1, "kind": "line", "group": None, "quantity": "15", "part_number": "SL2-65D3D-CGL-M", "description": "Surface Mounted Emergency Light"},
         {"page": 1, "kind": "line", "group": None, "quantity": "13", "part_number": "SL2-42D3D-CGL-M + SL2RBRC",
          "description": "Recess mounted Safelite Emergency Light, IP42", "multiline_part": "two lines (SL2-42D3D-CGL-M + / SL2RBRC)"},
         {"page": 1, "kind": "line", "group": None, "quantity": "10", "part_number": "SL2-42D3D-CGL-M +SL23I",
          "description": "Wall Mounted Exit, 20 metre viewing distance, IP42", "multiline_part": "two lines", "confidence": "medium", "note": "last token read as SL23I"},
         {"page": 1, "kind": "line", "group": None, "quantity": "5", "part_number": "SL2-42D3D-CGL-M +SL2PPLR+SL2RBRC",
          "description": "Exit Directional, Corridor Recessed, 20 metre viewing distance", "multiline_part": "two lines"},
         {"page": 1, "kind": "line", "group": None, "quantity": "1", "part_number": "40071777997-M", "description": "CGLine + Touch Screen Controller"}],
     boq_notes="Qty column literal; no '( n )' counts in descriptions; Unit/Total Price columns empty; the two total-price rows are notes, not items",
     unresolved=["CONFIRM: own identity 'EP-23091 R1' (equal to the project number plus R1) with the revision R1 embedded -- evaluation reference form",
                 "CONFIRM: row 3 part literal '+SL23I' (scan)"]),
 "35bd128789de": dict(scope_pages=[1], records=[
     rec(1, "sheet", "drawings", "DJ-295-O-EN-DST-00-ASS-0157", "01", register=False,
         identities=[ident("DJ-295-O-EN-DST-00-ASS-0157", "AMANA Drawing Number", "own_document", True),
                     ident("00", "Client Drawing Number revision (no number printed)", "other")],
         note="Amana steel approval drawing 'Warehouse - Member Profiles and Load Tables', project AKI Logistics; 'ISSUED FOR APPROVAL' is the issue "
              "purpose, not a decision; another party's structural input (untracked discipline)")],
     unresolved=[]),
 "a7763559b0bc": dict(scope_pages=[1, 2, 3, 4], records=[
     rec(1, "cover", "submittals", "EP-26208/SK/CBS/201", None,
         identities=[ident("EP-26208/SK/CBS/201", "Document No.", "own_document", True)],
         note="lux calculation cover: client Ministry of Presidential Court, consultant Altorath, MEP contractor AKKA, supplier Al Arabia, "
              "manufacturer Teknolux; no revision printed; no decision")],
     no_record_pages={"2": "DIALux project cover (date 17.07.2023), part of the same calculation", "3": "DIALux table of contents",
                      "4": "DIALux table of contents (continued)"},
     unvalidated_pages=list(range(5, 39)), unresolved=[]),
 "79e7e35bd807": dict(scope_pages=[1], records=[
     rec(1, "sheet", "drawings", "FAS-09", "00",
         identities=[ident("FAS-09", "Sheet No.", "own_document", True), ident("P-49354", "PROJECT NO.", "project_or_contract"),
                     ident("6439742", "PLOT NO.", "other")],
         note="Schematic Riser Diagram F.A_[LAYOUT], client IYAD S M ALKOURDI, consultant Eng. Adnan Saffarini, supplier Al Arabia; revision table "
              "single row '00 16-12-2024 ISSUED FOR APPROVAL ARIF' -- ARIF sits in the revision table's APPROVED column (issuer), not a consultant "
              "decision; page rotated 270")],
     unresolved=[]),
 "d8ba80a74660": dict(scope_pages=[1, 2, 3, 4], records=[], no_record_pages={
     "1": "Al Arabia 'PREVIOUS PROJECT REFERENCE LIST' (items 1-8); no own identity; footer 'P06/TRANS/R1' is the letterhead form code",
     "2": "continuation (items 9-23)", "3": "continuation (items 24-38)", "4": "continuation (items 39-41, then a second numbering 31-46)"},
     unvalidated_pages=[5],
     unresolved=["CONFIRM: footer 'P06/TRANS/R1' on every page is a form/letterhead code (role other), not this list's identity or revision R1"]),
 "73a723f42009": dict(scope_pages=[1], records=[
     rec(1, "sheet", "drawings", "DCH-M-BSB-DWG-ZZ-ARC-40075", "E", register=False,
         identities=[ident("DCH-M-BSB-DWG-ZZ-ARC-40075", "CLIENT DRAWING No.", "own_document", True),
                     ident("ARC-40075", "MUNICIPALITY DRAWING No.", "own_document_alternate"),
                     ident("DCH-M-BSB-MOD-04-ARC-40001_PART 4 INT", "vertical model file name", "other"),
                     ident("DCH", "PROJ. No.", "project_or_contract")],
         note="Dubai Square, BSBG architectural sheet 'GF (PARKING 1) - EMERGENCY RESPONSE/ CRISIS MANAGEMENT RM - SHEET 1 OF 2'; revision table "
              "A 50% detailed design 30.04.2025 .. E value engineering 14.11.2025; 'FOR LOCAL AUTHORITY USE ONLY / APPROVAL' box empty -- no decision; "
              "detail tags (40211, 40216 ...) are referenced drawings; the selection stratum 'reply' came from the path rule, the sheet carries no reply")],
     unresolved=[]),
 "2ddc88e23639": dict(scope_pages=[1], records=[
     rec(1, "transmittal", "samples", "TR/1727/24", None,
         identities=[ident("TR/1727/24", "AASS Ref.", "own_document", True), ident("EP-27421", "Project ID", "project_or_contract")],
         note="Word DOCUMENTS TRANSMITTAL dated 13.11.2024 to Jumaira Beach Building Contracting, subject 'Sample Board / Emergency Lighting "
              "System-Menvier'; listed item 1 'Document No ---' (no number), qty 1 no.; no revision; no decision")],
     unresolved=[]),
 "2472d2cc65c3": dict(scope_pages=[1, 2, 3, 4], records=[
     rec(1, "cover", "submittals", "DCH-M-MHT-CAL-IFC-ELE-0001-00", "00", register=False,
         identities=[ident("DCH-M-MHT-CAL-IFC-ELE-0001-00", "REFERENCE:", "own_document", True)],
         note="Meinhardt 'DUBAI SQUARE MALL / ELECTRICAL CALCULATIONS-IFC SUBMISSION' cover; revision 00 printed in the Document History on page 2 "
              "(purpose 'FOR REVIEW AND APPROVAL', 29.01.2026) and as the reference suffix; no decision; consultant design input (not an Al Arabia submittal)")],
     no_record_pages={"2": "Document History / Document Approval of the same calculation (revision 00; prepared/reviewed/approved names = internal sign-off)",
                      "3": "table of contents", "4": "section heading '1. ELECTRICAL LOAD SUMMARY' (image table)"},
     unvalidated_pages=list(range(5, 2837)),
     unresolved=["CONFIRM: evaluation reference keeps the printed suffix ('DCH-M-MHT-CAL-IFC-ELE-0001-00') or is the base "
                 "'DCH-M-MHT-CAL-IFC-ELE-0001' with revision 00"]),
}
assert set(L) == set(by_tag), (set(L) ^ set(by_tag))
docs = {}
for tag, lab in L.items():
    d = by_tag[tag]
    docs[d["doc_key"]] = {"doc": d["doc_key"], "sha256": d["sha256"], "stratum": d.get("stratum"), "no_record_pages": {}, "unvalidated_pages": [], **lab}
out = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "labels_version": "r2x-source-proposals-1",
       "status": "AI-DRAFTED PROPOSALS -- not human truth; no reviewer; no sign-off; any metric from these is PROVISIONAL",
       "labeller": "Claude (Opus 5.5), from staged renders / text layer / Word text, before any prediction for these documents",
       "small_batch_sha256": SB_SHA, "format": "labels/LABEL-FORMAT.md (page labels v2 compatible)",
       "boq_exposed": {"doc_key": sb["boq_exposed"][0]["doc_key"], "labels": "review05/holdout/HOLDOUT-BOQ-LABELS.json (existing, unchanged)",
                       "h06_crops": "C:/t/r2x/worklist/h06/H06-CROPS.json"},
       "documents": docs}
p = W / "labels" / "SMALL-BATCH-LABELS.json"
p.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
n_rec = sum(len(v["records"]) for v in docs.values())
print("documents", len(docs), "records", n_rec, "no_record pages", sum(len(v["no_record_pages"]) for v in docs.values()),
      "boq rows", sum(len(v.get("boq_rows", [])) for v in docs.values()), "unresolved", sum(len(v["unresolved"]) for v in docs.values()))
print("sha256", hashlib.sha256(p.read_bytes()).hexdigest())
