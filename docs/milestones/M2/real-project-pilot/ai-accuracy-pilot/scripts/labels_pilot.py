"""AI accuracy pilot: SOURCE labels for the frozen pilot sample (PILOT-SAMPLE.json) and the pilot BOQ sheet, written
from the hash-checked staged renders / zooms / text layers BEFORE any prediction for these files existed (no model
request of this pilot had been made when this file was written). AI-drafted by Claude -- proposals, NOT human truth,
not reviewed yet; every metric from them is PROVISIONAL. Page labels v2 shape (evaluator .9) with the 'absent' encoding
for a known-absent revision; document-level (register) labels derived mechanically from page 1.
Uncertainties are listed in the register; nothing uncertain is counted as clear."""
import hashlib
import json
import pathlib

W = pathlib.Path("C:/t/iso/work/r2x/ai-pilot")
S = json.loads((W / "PILOT-SAMPLE.json").read_text(encoding="utf-8"))
SAMPLE_SHA = "3822df9ef792e6c6277e0bec3271dcee06dcdc6a15291a3e03ab0b25b6bf1917"
assert hashlib.sha256((W / "PILOT-SAMPLE.json").read_bytes()).hexdigest() == SAMPLE_SHA
by_tag = {d["sha256"][:12]: d for d in S["documents"]}


def rec(page, component, category, reference, rev, decision="n/a", actor=None, evidence=None, identities=(), register=True, confidence="high", **kw):
    return dict(page=page, component=component, category=category, reference=reference, printed_revision=rev if rev else "absent",
                decision=decision, decision_actor=actor, decision_evidence=evidence, identities=list(identities), register=register,
                confidence=confidence, **kw)


def ident(lit, label, role, own=False):
    return {"literal": lit, "printed_label": label, "role": role, "own_for_evaluation": own}


L = {
 "a092c82bf7fe": dict(records=[rec(1, "sheet", "drawings", "MEP-FA-B01-005", "01", identities=[ident("MEP-FA-B01-005", "DRAWING No.", "own_document", True)],
                                   note="Al Arabia FA & VE shop drawing, Basement-01 plan; revision table 00 issued for approval / 01 revised as per consultant comments; no stamp")]),
 "b8df3dee0bb7": dict(records=[rec(1, "sheet", "drawings", "TES/1343/NTH-END-3B/SD/TEL-02", "1",
                                   identities=[ident("TES/1343/NTH-END-3B/SD/TEL-02", "DRG.No.", "own_document", True)],
                                   note="REV.NO. printed as '1' in a triangle; revision table rows 0 and 1; consultant's drawing reference list = referenced drawings; no stamp")]),
 "7577b344abed": dict(records=[rec(1, "sheet", "drawings", "AR-101", "00", register=False,
                                   identities=[ident("AR-101", "Sheet Identification", "own_document", True), ident("1159", "Project No", "project_or_contract")],
                                   note="consultant architectural IFC input; revision table single row 'REV. 00 03.02.2019 ISSUED FOR CONSTRUCTION'; status FINAL; no decision")]),
 "500833f7db2b": dict(records=[rec(1, "sheet", "drawings", "BH2031-ID-OFF-23-109-00", "H", register=False,
                                   identities=[ident("BH2031-ID-OFF-23-109-00", "DRAWING NO.", "own_document", True)],
                                   note="interior-design tender input (Bluehaus); REVISION H; no decision")]),
 "b713d5e56599": dict(records=[rec(1, "sheet", "drawings", "DJ-295-0-EN-DST-07-ASS-0301", "00", register=False, confidence="medium",
                                   identities=[ident("DJ-295-0-EN-DST-07-ASS-0301", "AMANA Drawing Number", "own_document", True),
                                               ident("00", "Client Drawing Number revision (no number printed)", "other"), ident("DJ-295", "Project No.", "project_or_contract")],
                                   note="page rotated; numbers drawn as vector graphics (no text layer for them); 'ISSUED FOR APPROVAL & NOT FOR CONSTRUCTION' is the issue purpose, not a decision")],
                     uncertain=["identity character 8 printed like the zeros of '0301' and the file name uses '0'; the earlier small-batch sibling label (DJ-295-O-EN-...-0157) used the letter O -- an O/0 question for a person"]),
 "e740af954610": dict(records=[rec(1, "sheet", "drawings", "TES/1343/NTH-END-3B/SD/TEL-00", "1", decision="ANN", actor="consultant (ATK Engineering)",
                                   evidence="ATK 'APPROVAL STATUS' stamp 5189214, CODE B 'Approved As Noted, Resubmit' marked; handwritten '...approved as noted, resubmit'",
                                   identities=[ident("TES/1343/NTH-END-3B/SD/TEL-00", "DRG.No.", "own_document", True)],
                                   note="scan, rotated; contractor 'SHOP DRAWINGS' / 'RECEIVED' stamps are not decisions")]),
 "1b4770e3ca6e": dict(records=[rec(1, "reply", "reply", "Caf6NGC/KA/PQ\u00b7MEP-002", "00", decision="n/a",
                                   identities=[ident("Caf6NGC/KA/PQ\u00b7MEP-002", "Ref. No.:", "own_document", True)],
                                   note="contractor's reply to consultant comments on the PQ; 'Comply' replies are the contractor's, not a consultant decision")],
                     uncertain=["the printed separator after 'PQ' is U+00B7 (middle dot) in the text layer; a reader may give '-' or '.'"]),
 "1e98dc27bfaf": dict(records=[rec(1, "sheet", "drawings", "DCH-M-BSB-DWG-ZZ-ARC-74028", "E", register=False,
                                   identities=[ident("DCH-M-BSB-DWG-ZZ-ARC-74028", "CLIENT DRAWING No.", "own_document", True),
                                               ident("ARC-74028", "MUNICIPALITY DRAWING No.", "own_document_alternate")],
                                   note="Dubai Square BSBG architectural input; revision table A..E; APPROVAL / FOR LOCAL AUTHORITY boxes empty")]),
 "101bbcb94999": dict(records=[], no_record_pages={"1": "COMPLIANCE STATEMENT section divider (Samsung / Al Arabia); no identity, revision or decision"}),
 "f8e0aae242f5": dict(records=[rec(1, "letter", "correspondence", "P10781", None, register=False,
                                   identities=[ident("P10781", "Ref no.", "own_document", True)],
                                   note="scanned Tecon letter of authorization (22.05.2019); a manufacturer's authorization is not a consultant approval")]),
 "02fd23fe6c30": dict(records=[rec(1, "form", "internal request", "2836", None, register=False, confidence="medium",
                                   identities=[ident("2836", "DRF No:", "own_document", True), ident("EP-18101", "Project Reference", "project_or_contract"),
                                               ident("SSD-P-06 B/IQF.17", "Document Reference", "other"), ident("03", "Revision Number", "other")],
                                   note="scanned Design Request Form; DRF No. handwritten; 'Document Reference ... Revision Number 03' is the form template's control block; internal approvals only")],
                     uncertain=["handwritten DRF No. read as '2836' (medium legibility)"]),
 "125e73464eb7": dict(records=[], no_record_pages={"1": "O&M manual system overview page; no identity / revision / decision", "2": "continuation"}),
}
assert set(L) == set(by_tag)
docs, register, uncertainty, exposure = {}, [], [], []
for tag, lab in L.items():
    d = by_tag[tag]
    docs[d["doc_key"]] = {"doc": d["doc_key"], "sha256": d["sha256"], "stratum": d["stratum"], "records": lab["records"],
                          "no_record_pages": lab.get("no_record_pages", {}), "unvalidated_pages": [], "unresolved": lab.get("uncertain", [])}
    p1 = [r for r in lab["records"] if r["page"] == 1]
    r = p1[0] if p1 else None
    register.append({"doc": d["doc_key"], "ep": d["ep"], "cohort": "exploration", "stratum": d["stratum"], "extension": ".pdf", "sha256": d["sha256"],
                     "confidence": (r or {}).get("confidence", "high"),
                     "labels": {"kind": {"cover": "technical submission", "sheet": "shop drawing sheet" if (r or {}).get("register") else "drawing sheet (input, not a register document)",
                                         "reply": "reply", "letter": "letter (not a register document)", "form": "internal form (not a register document)"}.get((r or {}).get("component"), "other"),
                                "reference": (r or {}).get("reference") or "absent", "revision": (r or {}).get("printed_revision") or "absent",
                                "decision": (r or {}).get("decision") or "n/a", "system": "other", "register": bool((r or {}).get("register"))}})
    uncertainty += [{"doc": d["doc_key"], "item": u} for u in lab.get("uncertain", [])]
    exposure.append({"doc": d["doc_key"], "sha256": d["sha256"], "prior_predictions": "none (not in the small batch, the pilot, the holdout or any earlier run)",
                     "prior_renders": "Round 2 renders for labelling only (C:/t/r2x/renders)", "template_exposure":
                     "same template family as earlier exposed files" if tag in ("02fd23fe6c30", "b713d5e56599", "1e98dc27bfaf", "b8df3dee0bb7", "e740af954610") else "none known"})
BOQ = {"doc_key": "EP-22510/EP-22510 Commercial/EP-22510 FA Design.pdf", "sha256_prefix": "6153dfe701f5", "pages": 1,
       "rows": [{"page": 1, "kind": "line", "quantity": "1", "part_number": "IO1000R-2", "description": "IO1000 Fire Alarm Control Panel (FACP, 1 loop std expandable to 4, 230v, red door)",
                 "note": "the quantity is printed on the panel heading line, the catalog number on the '( 1 ) FACP' component line"},
                {"page": 1, "kind": "part_only", "quantity": None, "description_count": "2", "part_number": "12V8A", "description": "( 2 ) Battery 8 AH, 12 volt cells",
                 "note": "quantity column empty; the ( 2 ) count is in the description (recorded separately)"}] +
               [{"page": 1, "kind": "line", "quantity": q, "part_number": p, "description": t} for q, p, t in (
                   ("63", "SIGA-PD", "Intelligent Photoelectric Smoke Detector"), ("12", "SIGA-HRD", "Intelligent Fixed Temperature / Rate-of-Rise Heat Detector"),
                   ("57", "SIGA-SB", "Signature Detector Base"), ("4", "SIGA-IB", "Detector Base with Isolator"), ("14", "SIGA-AB4G", "Audible (Sounder) Base"),
                   ("6", "SIGA-278", "Manual Pull Station - Double Action, 1-stage"), ("6", "757-7A-T", "15/75 cd Temporal Horn/Strobe - 24 Vdc, RED"),
                   ("6", "G1R-HD", "Temporal horn, hi/lo dB output - 24V, RED"), ("1", "SIGA-CT2", "Dual Input Module"), ("2", "SIGA-CR", "Control Relay Module"),
                   ("12", "TP606", "2\"x4\" GI Concealed Back Box Single Gange"), ("14", "TP434", "4\"x4\" GI Concealed Back Box Double Gange"),
                   ("3", "27193-11", "Surface Mount Box - Indoor, RED, 1-gang"), ("6", "757A-WB", "Weatherproof Box, Cast - RED"))],
       "headings": ["IO1000 Fire Alarm Control Panel", "Field Devices"], "note": "scan; Unit Price / Total Price columns empty"}
meta = {"status": "AI-DRAFTED PROPOSALS (Claude) written before any pilot prediction; not human truth; not reviewed; metrics PROVISIONAL",
        "sample_sha256": SAMPLE_SHA, "labels_version": "ai-pilot-labels-2026-09-30.1"}
out = {"page_labels": {**meta, "documents": docs}, "register_labels": {**meta, "documents": register}, "boq_labels": {**meta, "sheets": [BOQ]},
       "uncertainty_register": uncertainty, "exposure": exposure}
for name, obj in (("PILOT-PAGE-LABELS.json", out["page_labels"]), ("PILOT-REGISTER-LABELS.json", out["register_labels"]),
                  ("PILOT-BOQ-LABELS.json", out["boq_labels"]), ("PILOT-UNCERTAINTY-AND-EXPOSURE.json", {"uncertainty": uncertainty, "exposure": exposure})):
    p = W / "labels" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(name, hashlib.sha256(p.read_bytes()).hexdigest())
print("records", sum(len(d["records"]) for d in docs.values()), "| decisions", sum(1 for d in docs.values() for r in d["records"] if r["decision"] != "n/a"),
      "| no-record pages", sum(len(d["no_record_pages"]) for d in docs.values()), "| boq rows", len(BOQ["rows"]), "| uncertain", len(uncertainty))
