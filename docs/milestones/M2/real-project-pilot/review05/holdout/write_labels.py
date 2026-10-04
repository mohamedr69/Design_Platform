"""Holdout labels (M2 review 05), written from renders of the staged originals and the Word files' own text, BEFORE any
reader output existed for these documents. Labeller: Claude (Fable 5.1). Owner countersignature: none claimed."""
import json, sys, datetime

R = sys.argv[1]
sample = json.load(open(R + "/holdout/HOLDOUT-SAMPLE.json", encoding="utf-8"))
by_suffix = {d["relative_path"].replace("\\", "/"): d for d in sample["documents"]}


def key(ep, rel):
    return f"EP-{ep}/{rel}"


def rec(page, reference, rev, decision, system, register, component="page", confidence="high", **kw):
    return {"page": page, "component": component, "reference": reference, "printed_revision": rev, "decision": decision,
            "system": system, "register": register, "confidence": confidence, **kw}


docs, pages = [], {}


def add(ep, rel, kind, labels, page_records=None, no_record=None, confidence="high", scan_like=False):
    d = by_suffix[rel]
    k = key(ep, rel)
    docs.append({"doc": k, "ep": ep, "cohort": "holdout", "stratum": d["stratum"], "extension": "." + rel.rsplit(".", 1)[-1].lower(),
                 "scan_like": scan_like, "confidence": confidence, "sha256": d["sha256"], "labels": {"kind": kind, **labels}})
    if page_records is not None or no_record is not None:
        pages[k] = {"records": page_records or [], "no_record_pages": {str(p): why for p, why in (no_record or {}).items()}}


NEG = {"reference": "absent", "revision": "absent", "decision": "n/a", "system": "other (not a register document)"}

# EP-28605
add("28605", "EP-28605 Scan/EP-28605 FA&EML MS R0 Ack.pdf", "email thread printed to PDF (RFQ, offer, submittal covering mails)", NEG,
    [], {p: "Outlook email chain: no controlled number, revision or decision" for p in range(1, 7)})
add("28605", "MS/EM/R0/PDF/CS.pdf", "material submittal cover sheet (company's own MS cover)",
    {"reference": "EP-28605 /MA/FA/201", "revision": "00", "decision": "n/a", "system": "ELS", "title": "Monitored Emergency Lighting System Material Submittal"},
    [rec(1, "EP-28605/MA/FA/201", "00", "n/a", "ELS", True, component="MS cover",
         note="the EML cover prints the FA document number EP-28605 /MA/FA/201 (literal); date 20.09.2024")])
add("28605", "MS/FA/R0/PDF/CS.pdf", "material submittal cover sheet (company's own MS cover)",
    {"reference": "EP-28605 /MA/FA/201", "revision": "00", "decision": "n/a", "system": "FAS", "title": "Fire Alarm System Material Submittal"},
    [rec(1, "EP-28605/MA/FA/201", "00", "n/a", "FAS", True, component="MS cover", note="date 20.09.2024")])

# EP-19138
add("19138", "EP-19138 - Scan Documents/EP-19138 T&C Ack.pdf", "internal testing & commissioning request form (scanned)", NEG,
    [], {1: "Al Arabia 'Projects Testing and Commissioning Request Form': internal, no controlled number or decision"}, scan_like=True)
for rel, num, title in (("EP-19138 DWG/a-2 revised  ground floor plan 1537874855099.pdf", "A-01", "GROUND FLOOR"),
                        ("EP-19138 DWG/a-4 revised roof floor plan  1537430734780.pdf", "A-03", "ROOF FLOOR"),
                        ("EP-19138 DWG/a-5 revised elevation 1,2,3_4.  1537874809492.pdf", "A-04", "ELEVATION 1,2,3&4.")):
    add("19138", rel, "architect's drawing given to us (not a shop drawing of ours)",
        {"reference": num + " (architect Al Jethoor; municipality 'Approved Drawings' stamp)", "revision": "absent", "decision": "n/a",
         "system": "other (architecture)", "title": title},
        [], {1: f"architect's sheet {num} ({title}); consultant/municipality stamp is the authority's, not a submittal decision; not a register record"})
add("19138", "EP-19138 MS R0/Battery/ES 12-12.pdf", "datasheet", NEG, [], {1: "battery datasheet", 2: "battery datasheet"})
add("19138", "EP-19138 MS R0/EP-19138 Cataluge/SIGA-AB4G.pdf", "datasheet", NEG, [], {p: "EST datasheet 85001-0581" for p in range(1, 5)})

# EP-28569
add("28569", "EP-28569 ELV/EP-28569 Scan/EP-28569 SCS MS R1 Ack 24.02.25.pdf", "transmittal (scanned document transmittal, signed receipt)",
    {"reference": "TR/1995/25", "revision": "absent", "decision": "n/a", "system": "other (SCS structured cabling; untracked)"},
    [rec(1, "TR/1995/25", "absent", "n/a", "other (SCS; untracked)", False, component="transmittal",
         note="date 24/02/2025; item EP-28569/AW/CCTV&ACS/201 'Material Submittal - SCS-R1'; the signature is a receipt")], scan_like=True)
for rel, num, title in (("EP-28569 ELV/EP-28569 As Built Dwg/CCTV/A01a-Hamriyah/C&MCG42403PH1-01-E-CCTV-2001.pdf", "C&MCG42403PH1-01-E-CCTV-2001", "AL HAMRIYAH GF,FF,SF & RF FLOOR PLAN CCTV SYSTEM"),
                        ("EP-28569 ELV/EP-28569 As Built Dwg/CCTV/A01a-Hamriyah/C&MCG42403PH1-01-E-CCTV-2002.pdf", "C&MCG42403PH1-01-E-CCTV-2002", "AL HAMRIYAH SCHEMATIC DIAGRAM CCTV & ACCESS CONTROL SYSTEM"),
                        ("EP-28569 ELV/EP-28569 As Built Dwg/TELEPHONE/A01b-Zorah/C&MCG42403PH1-01-E-TL-2001.pdf", "C&MCG42403PH1-01-E-TL-2001", "GF,FF,SF & RF FLOOR PLAN TELEPHONE SYSTEM")):
    add("28569", rel, "shop drawing sheet (as built; untracked ELV discipline)",
        {"reference": num, "revision": "00", "decision": "UR", "system": "other (CCTV / telephone; untracked)", "title": title},
        [rec(1, num, "00", "UR", "other (untracked ELV)", False, component="drawing sheet", title=title,
             note="title block DRAWING NO / REV cells; revision history row 00 07.08.2025 ISSUED FOR APPROVAL; 'AS BUILT' stamp is not a decision")])
add("28569", "EP-28569 ELV/Consultant approval/MTS-E-0018-R01-B.pdf", "material submittal (client's MATERIAL SUBMITTAL form, scanned, with the package)",
    {"reference": "MTS-E-0018 (full: NG/LGC/C&M/07/2024/34-MTS-E-0018)", "revision": "01", "decision": "ANN", "system": "other (SCS structured cabling; untracked)"},
    [rec(1, "MTS-E-0018", "01", "ANN", "other (SCS; untracked)", False, component="submittal form", confidence="medium",
         decision_candidates=[["handwritten circle and tick", "B = NO OBJECTION AS NOTED"],
                              ["printed tick in the A box", "the same tick is on the Rev 00 form (page 3) whose decision is C: a template mark, not a decision"]],
         note="date 24-Feb-25; engineer's notes 'Leviton approved for structured cabling...final approval subject to installation, T&C'"),
     rec(2, "EP-27282/MA/TEL/201", "01", "n/a", "other (SCS)", False, component="package cover",
         note="Al Arabia 'SCS Material Submittal' cover prints EP-27282 (another project's number), rev 01, 19/02/2025 -- literal"),
     rec(3, "MTS-E-0018", "00", "rejected", "other (SCS)", False, component="previous revision form carried in the package",
         note="Rev 00, 30-Jan-25; C = REVISE & RESUBMIT circled by hand; printed tick in the A box (template)"),
     rec(4, "NG/LGC/C&M/07/2024/34-MTS-E-0018", "absent", "n/a", "other (SCS)", False, component="contractor's reply table to Rev 00 comments")],
    {5: "content list", 6: "separator sheet", 7: "divider 'COMPANY PROFILE'", 8: "company profile", 9: "company profile", 10: "company profile",
     11: "company profile", 12: "company profile"}, confidence="medium", scan_like=True)
add("28569", "EP-28569 ELV/EP-28569 MS/SCS/Leviton/Sent/R1/Consultant comments.pdf", "material submittal (client's form, Rev 00, with the engineer's comments)",
    {"reference": "MTS-E-0018", "revision": "00", "decision": "rejected", "system": "other (SCS; untracked)"},
    [rec(1, "MTS-E-0018", "00", "rejected", "other (SCS; untracked)", False, component="submittal form",
         decision_candidates=[["handwritten circle", "C = REVISE & RESUBMIT"], ["printed tick in the A box", "template mark (negative control)"]],
         note="30-Jan-25; the A-box tick is printed on the form: a reader taking it as approval makes a false approval")], scan_like=True)
add("28569", "EP-28569 FAS/MS/EMLSC/R0/PDF/AUTH 010.pdf", "manufacturer's authorization letter", NEG, [], {1: "Cooper/Eaton distributor authorization letter"})
add("28569", "EP-28569 FAS/MS/EMLSC/R0/PDF/Catalogue LATEST.pdf", "company profile brochure", NEG, [], {p: "company profile brochure" for p in range(1, 13)})
add("28569", "EP-28569 ELV/Transmittal/EP-28659 SCS CCTV & ACS MS R0.docx", "Word transmittal (DOCUMENT TRANSMITTAL; company form)",
    {"reference": "TR/1785/24", "revision": "absent", "decision": "n/a", "system": "other (SCS / CCTV; untracked)", "date": "13/12/2024",
     "register": False, "note": "carries a material submittal (EP-28569/AW/CCTV&ACS/201); the platform registers transmittals' sample submissions only"})
add("28569", "EP-28569 FAS/Transmittal/EP-28659 FA & EML MS R0.docx", "Word transmittal (DOCUMENT TRANSMITTAL; company form)",
    {"reference": "TR/1733/24", "revision": "absent", "decision": "n/a", "system": "FAS / ELS", "date": "15/11/2024", "register": False,
     "note": "items EP-28569/MA/FA/201 and EP-28569/MA/ESLC/201 (material submittals, not samples)"})

# EP-8430
add("8430", "EP-8430 Scan Doc/EP-8430 PAVA MS R.0 Ack..pdf", "transmittal (scanned document transmittal, received stamp)",
    {"reference": "TR/0897/17", "revision": "absent", "decision": "n/a", "system": "PAVA"},
    [rec(1, "TR/0897/17", "absent", "n/a", "PAVA", False, component="transmittal",
         note="10/05/2017; item EP-8430/SS/FA/201 material submittal PAVA; RECEIVED stamp + signature are a receipt; heading 'DOCUMENT TRANSMITAL' (one T)")],
    scan_like=True)
for rel, num, date, title, floor in (("Shop Drawings/AGC-DF-MEP-SD-PAS-02-D.pdf", "AGC-DF-MEP-SD-PAS-02-D", "28/10/2017", "GROUND FLOOR AND GROUND MEZZANINE PUBLIC ADDRESS SYSTEM PART PLAN - D", "GROUND FLOOR (and ground mezzanine)"),
                                     ("Shop Drawings/AGC-DF-MEP-SD-PAS-02-A.pdf", "AGC-DF-MEP-SD-PAS-02-A", "28/10/2017", "GROUND FLOOR AND GROUND MEZZANINE PUBLIC ADDRESS SYSTEM PART PLAN - A", "GROUND FLOOR (and ground mezzanine)"),
                                     ("Shop Drawings/AGC-DF-MEP-SD-PAS-03-D.pdf", "AGC-DF-MEP-SD-PAS-03-D", "29/10/2017", "FIRST FLOOR AND SECOND FLOOR PUBLIC ADDRESS SYSTEM PART PLAN - D", "FIRST FLOOR (and second)")):
    add("8430", rel, "shop drawing sheet (contractor shop drawing, PAVA)",
        {"reference": num, "revision": "00", "decision": "UR", "system": "PAVA", "title": title, "floor": floor},
        [rec(1, num, "00", "UR", "PAVA", True, component="drawing sheet", title=title, floor=floor,
             note=f"title block 'Drg. no.' and 'REV.' cells; date {date}; history row 00 ISSUED FOR CONSULTANT APPROVAL; no stamp")])
add("8430", "Approval and Comments/PAVA MS Comments.pdf", "consultant construction review form (method statement comments)",
    {"reference": "D15015-0200S-FS-EL-MS-0022 (review CRS-DOC-02006, submitted CDS-DOC-01943)", "revision": "00", "decision": "rejected",
     "system": "PAVA"},
    [rec(1, "D15015-0200S-FS-EL-MS-0022", "00", "rejected", "PAVA", False, component="review form (method statement)", confidence="medium",
         note="Code3 on the deliverable; comments: 'proposed system (praesideo) is not accepted'; a method statement, not a MAS/SD register record")],
    confidence="medium", scan_like=True)
add("8430", "EP-8430 PAVA MS/Rev. 0/Test Certificates/BOSCH PAVA Letter.pdf", "manufacturer letter", NEG, [], {1: "Bosch letter (letter ref BSS/AE/ALARABIA/170315-047)", 2: "Bosch letter"}, scan_like=True)
add("8430", "EP-8430 PAVA MS/Rev. 0/Test Certificates/CE Certification.pdf", "certificate", NEG, [], {p: "CE certificate and annexes" for p in range(1, 10)})
add("8430", "EP-8430 Transmittal/EP-8430 PAVA MS R0 08.11.2017.doc", "Word transmittal (DOCUMENT TRANSMITAL; company form)",
    {"reference": "TR/2001/17", "revision": "absent", "decision": "n/a", "system": "PAVA", "date": "08/11/2017", "register": False,
     "note": "item EP-8430/SS/FA/201 (material submittal)"})
add("8430", "EP-8430 Transmittal/EP-8430 PAVA MS R0.doc", "Word transmittal (DOCUMENT TRANSMITAL; company form)",
    {"reference": "TR/0897/17", "revision": "absent", "decision": "n/a", "system": "PAVA", "date": "10/05/2017", "register": False,
     "note": "the Word original of the scanned 'PAVA MS R.0 Ack' (same TR number)"})

meta = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "labels_version": "holdout-v1",
        "labeller": "Claude (Fable 5.1), from renders of the staged originals and the Word files' text; no reader output existed. Owner countersignature: none claimed.",
        "documents": docs}
json.dump(meta, open(R + "/holdout/HOLDOUT-LABELS.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
json.dump({"at_utc": meta["at_utc"], "labels_version": "holdout-v1", "documents": pages, "page1_corrections": []},
          open(R + "/holdout/HOLDOUT-PAGE-LABELS.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(docs), "documents;", len(pages), "page-labelled;", sum(len(v["records"]) for v in pages.values()), "records;",
      sum(len(v["no_record_pages"]) for v in pages.values()), "no-record pages")
