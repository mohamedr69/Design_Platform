"""Review 07: source adjudication of the findings that changed under evaluator .5 (AI-introduced errors and wrong raw
observations). Each case was inspected against the staged source (text layer, OCR, or a rendered crop). Categories:
  ai_correct_label_disputed  -- the AI value is printed on the page; the label chose another identity / missed a mark
  literal_ocr_error          -- a real misread of the printed characters (a raw-observation error)
  referenced_as_own          -- a number the page references was taken as its own identity (a raw-observation error)
  two_own_identities         -- the page prints two identities that are both its own; the label chose the other
  label_gap_unlabelled_own   -- the page prints its own identity; the page labels list no component there
Only a human reviewer settles the disputed labels (the Golden truth is not changed here)."""
import json

CASES = [
    # AI-introduced (evaluator .5, policy .1 as run; policy .2 replay noted)
    {"run": "AI-EV1", "doc": "EP-30088/04. Drawings/1. IFC DRAWINGS/03. IFC/Park Medows   -Final Design Revision Arch  - Approved/REQ-2387569  - BP.pdf",
     "page": 1, "field": "identity", "value": "B2312982", "label": "REQ-2387569", "category": "two_own_identities",
     "evidence": "rendered page: Dubai Development Authority BUILDING PERMIT, 'Permit Number B2312982' in the header table; footer 'REQ-2387569-2' (the request reference); the file is named after the request",
     "policy_2": "still validated (the literal is in the read region)", "resolution": "disputed truth -> human review; not counted as an AI false acceptance until settled"},
    {"run": "AI-EV1, AI-EV2", "doc": "EP-29076/06- Drawings/01- FA/03- SD/Fire Alarm/25H-S202-NCC-SD-MEP-ELE-FA-003-R03 - Code B.pdf",
     "page": 3, "field": "decision", "value": "ANN", "label": "n/a (no decision on page 3)", "category": "ai_correct_label_disputed",
     "evidence": "rendered crop of the blind read region: blue consultant stamp 'CODE B APPROVED AS NOTED' ticked and signed on page 3 (sheet 02 of 02); the engineer's-comments block beside it is unmarked",
     "policy_2": "candidate (discovery did not corroborate the mark)", "resolution": "label likely incomplete -> human review"},
    # wrong raw observations, det .8 pilot + holdout
    {"run": "det .8", "doc": "EP-30784/01- EP-30784 Scan/EP-30784 EML Design.pdf", "page": 1, "field": "identity", "value": "TEP-30784", "label": "EP-30784",
     "category": "literal_ocr_error", "evidence": "OCR of the labelled 'Doc No.' line adds a leading T", "resolution": "raw observation error (observed, not accepted)"},
    {"run": "det .8", "doc": "EP-14119/EP-14119 Commercial/EP-14119 LPO.pdf", "page": 1, "field": "identity", "value": "LPOD-1856000229", "label": "LPO/1050000159",
     "category": "literal_ocr_error", "evidence": "OCR of the LPO number: '/' read as 'D' and digits misread", "resolution": "raw observation error"},
    {"run": "det .8", "doc": "EP-19977/EP-19977 Commercial/EP-19977 CBS Quotation.pdf", "page": 1, "field": "identity", "value": "D1902-FC-DWG-EM-B1200", "label": "EP-19977-R1",
     "category": "referenced_as_own", "evidence": "the quotation's 'Ref' line quotes the consultant drawing it prices", "resolution": "raw observation error"},
    {"run": "det .8", "doc": "EP-19977/EP-19977 Commercial/EP-19977 FA Quotation R4.pdf", "page": 1, "field": "identity", "value": "D1902-FC-DWG-EF-B1200 & ...", "label": "EP - 19977 - R4-B0",
     "category": "referenced_as_own", "evidence": "as above", "resolution": "raw observation error"},
    {"run": "det .8", "doc": "EP-13777/*/TAV-TN-009782 (1).pdf, TAV-TN-000731.pdf, TAV-TN-011156 (1).pdf", "page": 1, "field": "identity", "value": "K&A-WTRAN-017671 / -000913 / -020525",
     "label": "TAVC-TRANSMIT-009782 / -000731 / -011156", "category": "two_own_identities",
     "evidence": "text layer prints both 'TAVC-TRANSMIT-009782' and 'K&A-WTRAN-017671' (the consultant's and the contractor's transmittal numbers)", "resolution": "disputed truth -> human review (3 cases)"},
    {"run": "det .8", "doc": "EP-26369/MS FAS/R1/MS FAS SOFTCOPY (TIM AEROSPACE) R1.pdf", "page": 1, "field": "identity+revision", "value": "EP-26369/SS/FA/101, 01",
     "label": "page 1 labelled no component (components on pages 4-5)", "category": "label_gap_unlabelled_own",
     "evidence": "text layer page 1: 'EP-26369/SS/FA/101', 'Revision' (the company's own cover)", "resolution": "label gap -> human review"},
    {"run": "det .8", "doc": "EP-30784/03- MS/03- FRC/03- TIANJIE/BBY006_1.PDF", "page": 3, "field": "identity+revision", "value": "EP-30627/SS/EML/ 1293, 00",
     "label": "page 3 labelled no component", "category": "label_gap_unlabelled_own",
     "evidence": "text layer page 3: 'EP-30627/SS/EML/ 1293', 'Revision' -- a cover of another project number filed in this package", "resolution": "label gap -> human review"},
    {"run": "det .8", "doc": "EP-29076/*/Minutes of Weekly MEP Meeting No. 020 - Final Issuance.pdf", "page": 1, "field": "identity", "value": "10789-CSCEC-OUT-L0",
     "label": "L0749", "category": "two_own_identities", "evidence": "OCR: the minutes carry the contractor's outgoing letter number and the meeting letter number",
     "resolution": "disputed truth -> human review"},
    {"run": "det .8 (parser drawing_sheet observations, also in Candidate C)", "doc": "EP-26082 BELLAGIO / MGM / landscape sheets (9 cases)", "page": 1,
     "field": "identity", "value": "R1029-05-BSB-DWG-ALL-ARC-1282, A-DWG-TYP-GRO-INT-1102-01, ...", "label": "the sheet's own number",
     "category": "referenced_as_own", "evidence": "untracked-discipline sheet observations carry a referenced drawing number from the sheet's reference table / a part number",
     "resolution": "raw observation error (pre-existing since Candidate C)"},
    {"run": "det .8 holdout", "doc": "EP-8430/Approval and Comments/PAVA MS Comments.pdf", "page": 1, "field": "identity", "value": "ICDS-DOC-01943",
     "label": "D15015-0200S-FS-EL-MS-0022", "category": "two_own_identities",
     "evidence": "the Dar review form prints its own document number (OCR 'ICDS-DOC-01943', leading I probably noise) and the MS it reviews; the label keys the component to the reviewed MS",
     "resolution": "role ambiguity (own vs target) -> human review; the literal's leading 'I' also unverified"},
    {"run": "det .8 holdout", "doc": "EP-8430/EP-8430 PAVA MS/Rev. 0/Test Certificates/BOSCH PAVA Letter.pdf", "page": 1, "field": "identity",
     "value": "BSS/AE/ALARABIA/170315-047", "label": "no component", "category": "label_gap_unlabelled_own",
     "evidence": "the Bosch letter's own reference; labelled as a no-record page", "resolution": "label gap -> human review"},
]
json.dump({"cases": CASES}, open(r"C:\t\iso\work\r7\ADJUDICATIONS.json", "w", encoding="utf-8"), indent=1)
import collections
print(collections.Counter(c["category"] for c in CASES))
