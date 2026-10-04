"""Truth v2, part 1: expected record sets for the 25 documents whose readings emitted records beyond page 1, labelled
page by page from renders of the staged originals (scratch r5/pages/pg-NNN.jpg), before comparing with any reader
output. Pages visited by the reader but not rendered here are listed as unvalidated. Writes page_labels.json.

Record fields: page, component (cover | sheet | form | tag | reply | attached_submission | workflow_print | comments),
category (drawings | submittals | samples | reply), reference (literal), printed_revision (literal, as printed in its
own field), decision (approved | ANN | rejected | UR | ambiguous | n/a), decision_actor, decision_evidence, register
(True when the legacy register is expected to hold it; False for an untracked discipline or evidence-only component),
confidence (high | medium | low)."""
import json, pathlib, datetime

R = pathlib.Path(__file__).parent


def rec(page, component, category, reference, printed_revision, decision, actor=None, evidence=None, register=True, confidence="high", **kw):
    d = dict(page=page, component=component, category=category, reference=reference, printed_revision=printed_revision, decision=decision,
             decision_actor=actor, decision_evidence=evidence, register=register, confidence=confidence)
    d.update(kw)
    return d


C = "consultant (Silver Stone)"
DOCS = {
 "EP-30784/03- MS/03- FRC/03- TIANJIE/BBY006_1.PDF": dict(sheets="pg-001..003", records=[
     rec(1, "form", "submittals", "BBY006-GME-MAS-EL-FA-0004", "00", "rejected", C, "Re-Submit (C) box filled + (C) Revise & Resubmit stamp"),
 ], no_record_pages={2: "QA/QC comments sheet quoting the same MAS reference (contractor's internal QA/QC, not a decision)",
                     3: "supplier's own cover, document no. EP-30627/SS/EML/1293 rev 00 (supplier numbering, no register code)",
                     4: "contents", 5: "separator", 6: "proposed material list", 7: "separator", 8: "catalogue", 9: "catalogue", 10: "catalogue", 11: "catalogue", 12: "datasheet R1013"}),
 "EP-30784/04- Drawings/08-Shop Drawing/1.FAVE/R1/rejected/BBY006-GME-SDW-FP-FA-ZZZ-L01-010006 Shop Drawing for L01 Amenities Floor Plan - Fire Alarm Layout.pdf": dict(sheets="pg-004", records=[
     rec(1, "cover", "drawings", "BBY006-GME-SDW-FP-FA-ZZZ-L01-010006", "00", "rejected", C, "Re-Submit (C) filled + (C) stamp"),
     rec(2, "sheet", "drawings", "BBY006-GME-SDW-FP-FA-ZZZ-L01-010006", "00", "rejected", C, "(C) Revise & Resubmit stamp on the title block", floor_raw="L01 - AMENITIES FLOOR PLAN"),
 ]),
 "EP-30784/04- Drawings/08-Shop Drawing/1.FAVE/recieved/BBY006-GME-SDW-FP-FA-ZZZ-L02-010007-01 Shop Drawing for L02 1st Mechanical Floor Plan - Fire Alarm Layout.pdf": dict(sheets="pg-004..005", records=[
     rec(1, "cover", "drawings", "BBY006-GME-SDW-FP-FA-ZZZ-L02-010007", "01", "ANN", C, "Approved as Noted (B) filled + (B) stamp"),
     rec(2, "sheet", "drawings", "BBY006-GME-SDW-FP-FA-ZZZ-L02-010007", "01", "ANN", C, "(B) stamp on the title block; revision table rows 00 and 01", floor_raw="L02- 1ST MECHANICAL FLOOR PLAN"),
     rec(3, "cover", "drawings", "BBY006-GME-SDW-FP-FA-ZZZ-L02-010007", "00", "rejected", C, "Re-Submit (C) filled + (C) stamp (the earlier revision's answered cover, filed behind)"),
     rec(4, "sheet", "drawings", "BBY006-GME-SDW-FP-FA-ZZZ-L02-010007", "00", "rejected", C, "(C) stamp on the title block"),
 ]),
 "EP-30784/04- Drawings/08-Shop Drawing/2.EML/approved/BBY006-GME-SDW-EL-LI-ZZZ-L57-010041 Shop Drawing L57-4th Mechanical Floor Plan Emergency Lighting Layout.pdf": dict(sheets="pg-005", records=[
     rec(1, "cover", "drawings", "BBY006-GME-SDW-EL-LI-ZZZ-L57-010041", "00", "ANN", C, "Approved as Noted (B) filled + (B) stamp"),
     rec(2, "sheet", "drawings", "BBY006-GME-SDW-EL-LI-ZZZ-L57-010041", "00", "ANN", C, "(B) stamp in the title block"),
 ]),
 "EP-30784/04- Drawings/08-Shop Drawing/2.EML/Emergency Lighting Layout/BBY006-GME-SDW-EL-LI-POD-P01-010029 Shop Drawing for Podium-1 Floor Plan Emergency Lighting Layout.pdf": dict(sheets="pg-006..010", records=[
     rec(1, "cover", "drawings", "BBY006-GME-SDW-EL-LI-POD-P01-010029", "00", "rejected", C, "Re-Submit (C) filled + (C) stamp"),
     rec(2, "sheet", "drawings", "BBY006-GME-SDW-EL-LI-POD-P01-010029", "00", "rejected", C, "(C) stamp in the title block"),
 ], no_record_pages={p: "DIALux lux calculation" for p in (3, 4, 5, 6, 7, 8, 17, 18, 19, 20)}, unvalidated_pages=[9, 10, 11, 12, 13, 14, 15, 16]),
 "EP-30784/04- Drawings/08-Shop Drawing/2.EML/Emergency Lighting Layout/BBY006-GME-SDW-EL-LI-POD-P02-010030 Shop Drawing for Podium-2 Floor Plan Emergency Lighting Layout.pdf": dict(sheets="pg-011", records=[
     rec(1, "cover", "drawings", "BBY006-GME-SDW-EL-LI-POD-P02-010030", "00", "rejected", C, "Re-Submit (C) filled + (C) stamp"),
     rec(2, "sheet", "drawings", "BBY006-GME-SDW-EL-LI-POD-P02-010030", "00", "rejected", C, "(C) stamp in the title block"),
 ], no_record_pages={3: "DIALux cover", 4: "DIALux contents"}, unvalidated_pages=list(range(5, 17))),
 "EP-30784/04- Drawings/08-Shop Drawing/2.EML/Emergency Lighting Layout/BBY006-GME-SDW-EL-LI-ZZZ-L41-010050 Shop Drawing L41-3rd Mechanical Floor Plan Emergency Lighting Layout.pdf": dict(sheets="pg-015", records=[
     rec(1, "cover", "drawings", "BBY006-GME-SDW-EL-LI-ZZZ-L41-010050", "00", "ANN", C, "Approved as Noted (B) filled + (B) stamp"),
     rec(2, "sheet", "drawings", "BBY006-GME-SDW-EL-LI-ZZZ-L41-010050", "00", "ANN", C, "(B) stamp in the title block"),
 ]),
 "EP-30784/08- approval/samples/FA/R1/BBY006-GME-SAR-EL-FA-0002 Sample Approval Request for Fire Alarm & Voice Evacuation System.pdf": dict(sheets="pg-015..016", records=[
     rec(1, "form", "samples", "BBY006-GME-SAR-EL-FA-0002", "00", "ANN", C, "(B) Approved As Noted stamp and 'MEP (B)' text in the consultant block; the consultant row's (B) box itself is unfilled; the QA/QC row's (B) box is filled (contractor)", confidence="medium"),
     rec(3, "attached_submission", "submittals", "BBY006-GME-MAS-EL-FA-0001", "00", "ANN", C, "Approved as Noted (B) filled + (B) stamp (the related material submittal, attached)"),
 ], no_record_pages={2: "sample board photo headed with the SAR reference (a component of the same sample request)"}),
 "EP-30088/03. Document/1. SAMANA PARK MEADOWS/3. SHOP DRAWING/FIRE FIGHTING/ICC-DLRC-SPM-SD-MEP-FF-0052-03-COMMENTED-B.pdf": dict(sheets="pg-016", records=[
     rec(1, "cover", "drawings", "ICC-DLRC-SPM-SD-MEP-FF-0052", "03", "ANN", "consultant (York)", "B - Approved With Comments highlighted in the Consultant Recommendation row", register=False, raw_system="FIREFIGHTING"),
     rec(2, "cover", "drawings", "ICC-DLRC-SPM-SD-MEP-FF-0052", "02", "rejected", "consultant (York)", "C - Revise & Re-Submit highlighted (orange)", register=False, raw_system="FIREFIGHTING"),
     rec(3, "sheet", "drawings", "ICC-DLRC-SPM-SD-MEP/FF-105", "02", "UR", None, "no mark readable in the comments-status box", register=False, raw_system="FIREFIGHTING", floor_raw="ROOF FLOOR"),
 ]),
}
YORK42 = dict(sheets="pg-017..018", records=[
    rec(1, "cover", "drawings", "ICC-DLRC-SPM-SD-MEP-FA-0042", "01", "ANN", "consultant (York)", "red frame round B - Approved With Comments (Consultant Recommendation row)"),
    rec(2, "cover", "drawings", "ICC-DLRC-SPM-SD-MEP-0042", "00", "rejected", "consultant (York)", "black frame round D- Rejected (Consultant Recommendation row)"),
    rec(3, "sheet", "drawings", "ICC-DLRC-SPM-SD-MEP/FA-103", "01", "UR", None, "comments-status box on the sheet unmarked", floor_raw="HC FLOOR"),
])
DOCS["EP-30088/10. SD/recieved/Fire alarm layout/Received/R01/ICC-DLRC-SPM-SD-MEP-FA-0042-01-HC FLOOR FIRE ALARM LAYOUT_ICC-DLRC-SPM-SD-MEP-FA-0042-01.pdf"] = YORK42
DOCS["EP-30088/10. SD/FA/recieved/R01/ICC-DLRC-SPM-SD-MEP-FA-0042-01-HC FLOOR FIRE ALARM LAYOUT_ICC-DLRC-SPM-SD-MEP-FA-0042-01.pdf"] = YORK42
L = "consultant (LACASA)"
DOCS.update({
 "EP-29076/06- Drawings/01- FA/03- SD/Fire Alarm/25H-NCC-SD-MEP-ELE-FA-024-R00 - Code C.pdf": dict(sheets="pg-018..019", records=[
     rec(1, "cover", "drawings", "25H-S202-NCC-SD-MEP-ELE-FA-024-R0", "R0 (suffix of the reference)", "rejected", L, "REVISE AND RESUBMIT circled (handwritten) in ACTION (As Marked)", printed_reference_glued="Reference25H-S202-NCC-SD-MEP-ELE-FA-024-R0"),
     rec(2, "sheet", "drawings", "25H-AAEM-SD-ELEC-FA-16F-023", "00", "UR", None, "Approval Status box on the sheet: no mark visible", floor_raw="16TH FLOOR", confidence="medium"),
     rec(3, "sheet", "drawings", "25H-AAEM-SD-ELEC-FA-16F-023A", "00", "UR", None, "no mark visible", floor_raw="16TH FLOOR", confidence="medium"),
     rec(4, "sheet", "drawings", "25H-AAEM-SD-ELEC-FA-16F-023", "00", "UR", None, "rotated scan (commented copy); no mark readable", floor_raw="16TH FLOOR", confidence="low"),
     rec(5, "sheet", "drawings", "25H-AAEM-SD-ELEC-FA-16F-023A", "00", "UR", None, "rotated scan (commented copy); no mark readable", floor_raw="16TH FLOOR", confidence="low"),
 ]),
 "EP-29076/06- Drawings/01- FA/03- SD/Fire Alarm/25H-S202-NCC-SD-MEP-ELE-FA-003-R03 - Code B.pdf": dict(sheets="pg-019..020", records=[
     rec(1, "cover", "drawings", "25H-S202-NCC-SD-MEP-ELE-FA-003-R3", "R3 (suffix of the reference); attachments rev 03", "ANN", L, "APPROVED AS NOTED circled"),
     rec(2, "sheet", "drawings", "25H-AAEM-SD-ELEC-FA-B1-003", "03", "UR", None, "Approval Status box unmarked", floor_raw="1ST BASEMENT FLOOR PLAN", confidence="medium"),
     rec(3, "sheet", "drawings", "25H-AAEM-SD-ELEC-FA-B1-003A", "03", "UR", None, "ENGINEER'S COMMENTS options unmarked at this scale", floor_raw="1ST BASEMENT FLOOR PLAN", confidence="medium"),
 ]),
 "EP-29076/06- Drawings/01- FA/03- SD/25H-AAEM-SD-ELEC-FA-133 - L24/24th Floor Fire Alarm Layout/25H-S202-NCC-SD-MEP-ELE-FA-031-R00 - Code B.pdf": dict(sheets="pg-020..021", records=[
     rec(1, "cover", "drawings", "25H-S202-NCC-SD-MEP-ELE-FA-031-R00", "R00 (suffix of the reference)", "ANN", L, "APPROVED AS NOTED circled (red)", printed_reference_glued="Reference25H-S202-NCC-SD-MEP-ELE-FA-031-R00"),
     rec(2, "sheet", "drawings", "25H-AAEM-SD-ELEC-FA-24F-030", "00", "UR", None, "Approval Status box unmarked", floor_raw="24TH FLOOR", confidence="medium"),
     rec(3, "sheet", "drawings", "25H-AAEM-SD-ELEC-FA-24F-030A", "00", "UR", None, "unmarked", floor_raw="24TH FLOOR", confidence="medium"),
 ]),
 "EP-25091/EP-25091 SD/FAS/SCH/AKA-DCC-ELE-FA-SD-000285-R2-AKA-Shop drawing for Fire Alarm System Schematic Diagram.pdf": dict(sheets="pg-021", records=[
     rec(1, "cover", "drawings", "AKA-DCC-ELE-FA-SD-000285", "2 (REVISION NO.; 'R2' beside the SD SUB. NO.)", "ambiguous", "employer's representative consultant (Arif & Bintoak)", "signed 04.10.2025 with 'Refer to the comments in the drawing'; the NOT APPROVED - RESUBMIT box is drawn in red while the others are black -- a mark or a form colour, not settled from the render", confidence="medium"),
     rec(2, "reply", "reply", "AKA-DCC-ELE-FA-SD-000285", "02", "n/a", "contractor (Dutco)", "Comments Resolution Sheet: reply to consultant comments on Rev-01"),
 ]),
 "EP-26369/SHOP DRAWINGS/AFS Comments.pdf": dict(sheets="pg-021..022", records=[
     rec(1, "sheet", "drawings", "JAM-SD-FA-001", "00", "UR", "reviewer notes (AFS), no code", "yellow review notes, no status code"),
     rec(2, "sheet", "drawings", "JAM-SD-FA-003", "00", "UR"),
     rec(3, "sheet", "drawings", "JAM-SD-FA-004", "00", "UR", floor_raw="FIRST FLOOR"),
     rec(4, "sheet", "drawings", "JAM-SD-FA-005", "00", "UR", floor_raw="SECOND FLOOR & ROOF FLOOR"),
 ]),
 "EP-26369/SHOP DRAWINGS/R1/RDJ183 FA Stamped.pdf": dict(sheets="pg-022..024", records=[
     rec(1, "sheet", "drawings", "JAM-SD-FA-001", "01", "ambiguous", "fire-safety consultancy (Vortex)", "'APPROVED BY: PADMANABHAN KAUSHIK DATE 26/10/2024' box: an FLS consultancy approval, not the lead consultant's A-D code (owner policy)"),
     rec(2, "sheet", "drawings", "JAM-SD-FA-002", "01", "unknown", None, "the strip holds no stamp; the drawing area was not rendered", floor_raw="GROUND FLOOR (office building)"),
     rec(3, "sheet", "drawings", "JAM-SD-FA-003", "01", "unknown", None, "an edge of a Vortex box (24/09/2024) at the strip's left edge", confidence="medium"),
     rec(4, "sheet", "drawings", "JAM-SD-FA-004", "01", "unknown", floor_raw="FIRST FLOOR"),
     rec(5, "sheet", "drawings", "JAM-SD-FA-005", "01", "unknown", floor_raw="SECOND FLOOR & ROOF FLOOR"),
     rec(6, "sheet", "drawings", "JAM-SD-FA-006", "00", "unknown"),
     rec(7, "sheet", "drawings", "JAM-SD-FA-007", "00", "unknown", None, "an edge of a Vortex box (24/09/2024) at the strip's left edge", confidence="medium"),
 ]),
 "EP-19977/EP-19977 Scan Doc/EP-19977 FA MS R0 R&R.pdf": dict(sheets="pg-024..025", records=[
     rec(1, "form", "submittals", "EBF-DCP-6374-VL-MAT-ELV-0003", "00", "rejected", "consultant (Allied) + Emaar", "C -Not Approved, Resubmit ticked in both blocks"),
     rec(2, "workflow_print", "submittals", "EBF-DCP-6374-VL-MAT-ELV-0003", "00", "n/a", None, "Aconex print of the same submission (status Pending_By_Engineer); same identity as page 1", duplicate_of_page=1),
     rec(3, "workflow_print", "submittals", "EBF-DCP-6374-VL-MAT-ELV-0003", "00", "rejected", "consultant (workflow field)", "'Consultant Status: C - Not_Approved_Resubmit' (a workflow status of the same submission)", duplicate_of_page=1),
 ], no_record_pages={4: "task details", 5: "workflow steps", 6: "document log"}),
 "EP-19977/EP-19977 Scan Doc/EP-19977 FA MS R1 App.pdf": dict(sheets="pg-026..027", records=[
     rec(1, "form", "submittals", "EBF-DCP-6374-VL-MAT-ELV-0003", "01", "ANN", "consultant (Allied) + Emaar", "B - Approved as Noted ticked in both blocks"),
     rec(2, "workflow_print", "submittals", "EBF-DCP-6374-VL-MAT-ELV-0003", "01", "n/a", None, "Aconex print, same identity", duplicate_of_page=1),
     rec(3, "workflow_print", "submittals", "EBF-DCP-6374-VL-MAT-ELV-0003", "01", "ANN", "consultant (workflow field)", "'Consultant Status: B - Approved_As_Noted'", duplicate_of_page=1),
 ], no_record_pages={4: "task details", 5: "workflow steps", 6: "document log", 7: "supporting documents"}),
 "EP-26082/EP-26082 INPUTS/OneDrive_2024-08-23 - 2/Vol IV Drawings/GAS APPROVAL FOR BELLAGIO/revised_gas_bellagio_part1xiba1741941453483 (1).pdf": dict(sheets="pg-027..029", note="path key resolved at load time by file name", records=[
     rec(p, "sheet", "drawings", ref, rv, "n/a", "authority (DCD stamp)", "Dubai Civil Defence approval stamp; no consultant code", register=False, raw_system="LPG", confidence="medium", floor_raw=fl)
     for p, ref, rv, fl in [(1, "R1029-05-IBA-DWG-GFL-GAS-1200", "B", "GROUND FLOOR"), (2, "R1029-05-IBA-DWG-L01-GAS-1201", "B", "LEVEL 01"), (3, "R1029-05-IBA-DWG-L05-GAS-1205", "A", "LEVEL 05"),
                            (4, "R1029-05-IBA-DWG-L06-GAS-1206", "A", "LEVEL 06"), (5, "R1029-05-IBA-DWG-L07-GAS-1207", "A", "LEVEL 07"), (6, "R1029-05-IBA-DWG-L08-GAS-1208", "A", "LEVEL 08"),
                            (7, "R1029-05-IBA-DWG-L09-GAS-1209", "A", "LEVEL 09"), (8, "R1029-05-IBA-DWG-L10-GAS-1210", "A", "LEVEL 10"), (9, "R1029-05-IBA-DWG-B01-GAS-1199", "B", "BASEMENT 01")]]),
 "EP-26082/EP-26082 SCAN DOC/R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020-01_CODE C.pdf": dict(sheets="pg-030..032", records=[
     rec(1, "tag", "samples", "R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020", "01", "rejected", "engineer (IBA)", "Revise & Resubmit - (C) ticked", related_reference="R1029-CSM-CO-ELV-EL-MAR-PJW-ZZZ-ZZZ-1009 Rev.01"),
     rec(6, "tag", "samples", "R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020", "00", "ANN", "engineer (IBA)", "Approved as Noted - (B) ticked (the earlier revision's tag, filed inside)", related_reference="R1029-CSM-CO-ELV-EL-MAR-PJW-ZZZ-ZZZ-1009 Rev.01"),
     rec(9, "reply", "reply", "R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1004", "03 ('REV 03' as printed)", "n/a", "contractor (Al Arabia)", "reply to consultant comments; the printed reference is ...-1004 REV 03, as printed"),
 ], no_record_pages={2: "sample photo", 3: "cover", 4: "index", 5: "separator", 7: "sample photos", 8: "separator", 10: "separator", 11: "sample photo"},
     note_footer="pages 1, 2, 5 and 6 carry a form footer 'Document No R1029-CSCEC-FM-MAR-001_R01': a form template number, never a record"),
 "EP-26369/MS FAS/R1/MS FAS SOFTCOPY (TIM AEROSPACE) R1.pdf": dict(sheets="pg-032..035", records=[
     rec(4, "form", "submittals", "RDJ183-RAQ-Naffco-MAT-008", "00", "rejected", "client (TIM engineer Mubasher Ayub, 03.10.2024); consultant approval-status boxes empty", "Code C - Not Approved / Revise & Resubmit filled (red) in the client block"),
     rec(5, "reply", "reply", "RDJ183-RAQ-Naffco-MAT-008", None, "n/a", "contractor (Al Arabia)", "REPLY TO CONSULTANT COMMENTS table, Transmittal No. RDJ183-RAQ-Naffco-MAT-008"),
 ], no_record_pages={1: "supplier cover, document no. EP-26369/SS/FA/101 rev 01 (supplier numbering)", 2: "contents", 3: "separator", 6: "separator", 7: "schedule of equipment", 8: "schedule of equipment",
                     9: "separator", 10: "catalogue index", 11: "separator", 12: "datasheet 85006-0049"}),
 "EP-19977/EP-19977 Scan Doc/EP-19977 CBS MS R1 R&R.pdf": dict(sheets="pg-035..036", records=[
     rec(1, "form", "submittals", "EBF-DCP-6374-VL-MAT-ELE-0023", "01", "rejected", "consultant (Allied) + Emaar", "C -Not Approved, Resubmit ticked in both blocks"),
     rec(2, "comments", "submittals", "EBF-DCP-6374-VL-MAT-ELE-0023", "01", "rejected", "consultant (Allied)", "Submittal Comments Sheet: STATUS C Not Approved, Resubmit; stamp 'REVISE & RESUBMIT AS NOTED'", duplicate_of_page=1),
 ]),
 "EP-13777/Approval Documents/A23-EFE-MAT-E-00033  Fire Alarm System - B.pdf": dict(sheets="pg-036..037", records=[
     rec(1, "form", "submittals", "A23-EFE-MAT-E-00033", "00", "n/a", None, "checklist page of the material submittal (rotated); no decision on it", confidence="medium"),
     rec(2, "form", "submittals", "A23-EFE-MAT-E-00033", "00", "ANN", "engineer (K&A, Musa, 3/6/2018)", "(B) Proceed as Noted ticked (rotated scan)", duplicate_of_page=1, confidence="medium"),
     rec(4, "workflow_print", "submittals", "A23-EFECO-MAT-E-00033", "0", "n/a", None, "Aconex print (rotated): Reference No A23-EFECO-MAT-E-00033, Revision 0", confidence="medium"),
     rec(5, "workflow_print", "submittals", "A23-EFECO-MAT-E-00033", "0", "ANN", "employer's representative (workflow field)", "Employer's Representative's Approval: B- Approved as Noted", duplicate_of_page=4, confidence="medium"),
 ], no_record_pages={3: "employer comments letter quoting 'A23-Effeco-MAT-E-00033 Rev.0'", 6: "workflow", 7: "workflow"}, unvalidated_pages=[8, 9, 10, 11]),
 "EP-13777/Approval Documents/AAR-001 Commented Material Submittal- Fire Alarm System & Voice Evacuation System (1).pdf": dict(sheets="pg-039", note="path key resolved at load time by file name", records=[
     rec(3, "attached_submission", "submittals", "A23-EFE-MAT-E-00033", "01", "ANN", "engineer (K&A, Musa, 24/6/2018)", "(B) Proceed as Noted ticked"),
     rec(4, "form", "submittals", "A23-EFE-MAT-E-00033", "01", "n/a", None, "checklist page of the same submittal", duplicate_of_page=3),
 ], no_record_pages={1: "EFECO facsimile cover (sender ref IM/A2A3/RR/sm/AAR/001) quoting A23-EFE-MAT-E-0033 Rev 1", 2: "blank"}),
})
PAGE1_CORRECTIONS = [
    {"doc_suffix": "EP-19977 CBS MS R1 R&R.pdf", "field": "reference", "old": "EBF-DCP-6374-VL-MAT-ELV-0023 (small print; medium confidence on the last digits)", "new": "EBF-DCP-6374-VL-MAT-ELE-0023",
     "evidence": "page 1 Ref.No. and page 2 Submittal No. both print 'EBF-DCP-6374-VL-MAT-ELE-0023' (r5 pages pg-035 tile 139, pg-036 tile 140); the v1 label misread the discipline infix", "labels_version": "v2"},
    {"doc_suffix": "A23-EFE-MAT-E-00033  Fire Alarm System - B.pdf", "field": "decision", "old": "unknown (rotated page 1 only)", "new": "ANN",
     "evidence": "page 2 (rotated): '(B) Proceed as Noted' ticked, engineer Musa 3/6/2018; page 5 employer's B (pg-036 tile 142, pg-037 tile 145); v1 labelled page 1 only", "labels_version": "v2"},
    {"doc_suffix": "AAR-001 Commented Material Submittal- Fire Alarm System & Voice Evacuation System (1).pdf", "field": "decision", "old": "unknown (cover letter only)", "new": "ANN (package: the attached K&A form on page 3); the cover letter itself carries no code",
     "evidence": "page 3: '(B) Proceed as Noted' ticked, Musa 24/6/2018 (pg-039 tile 154)", "labels_version": "v2"},
    {"doc_suffix": "AKA-DCC-ELE-FA-SD-000285-R2-AKA-Shop drawing for Fire Alarm System Schematic Diagram.pdf", "field": "decision", "old": "UR", "new": "ambiguous",
     "evidence": "the NOT APPROVED - RESUBMIT box is outlined in red, the others in black (pg-021 tile 81); v1 read the status boxes as all empty", "labels_version": "v2"},
]
# resolve each label to the sample's document key by file name (every file name here is unique in the sample except
# the York FA-0042-01 copies, whose two paths hold the same bytes and share one label)
todo = json.load(open(R / "pages_to_label.json"))
resolved = {}
for k, v in DOCS.items():
    name = k.split("/")[-1]
    hits = [t for t in todo if t.split("/")[-1] == name]
    assert hits, k
    for t in hits:
        resolved[t] = v
DOCS = resolved
out = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "labels_version": "v2 (page-level record sets)",
       "labeller": "Claude (Opus 5.5), from renders of the staged originals (r5/pages); reader output not consulted before these records were written; no engineer countersignature",
       "documents": DOCS, "page1_corrections": PAGE1_CORRECTIONS}
json.dump(out, open(R / "page_labels.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("documents", len(DOCS), "records", sum(len(d["records"]) for d in DOCS.values()))
