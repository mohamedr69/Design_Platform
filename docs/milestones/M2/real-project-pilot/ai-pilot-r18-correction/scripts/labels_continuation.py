"""Continuation labels (ai-pilot-r18-continuation-labels-2026-09-30.1), written BEFORE any prediction for the three new
documents (Claude-drafted from the hash-checked staged copies' text layer and renders: label-renders/*.png; not human
truth; PROVISIONAL). The four controls carry their v2 labels unchanged (exposed documents). Writes
labels-continuation/{CONT-REGISTER-LABELS.json, CONT-PAGE-LABELS.json, CONT-UNCERTAINTY-AND-EXPOSURE.json}."""
import copy
import hashlib
import json
import pathlib

W = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
S = json.loads((W / "CONTINUATION-SAMPLE.json").read_text(encoding="utf-8"))
assert sha(W / "CONTINUATION-SAMPLE.json").startswith("ddbceb3f75ee")
reg2 = json.loads((W / "labels-v2/PILOT-REGISTER-LABELS.v2.json").read_text(encoding="utf-8"))
page2 = json.loads((W / "labels-v2/PILOT-PAGE-LABELS.v2.json").read_text(encoding="utf-8"))
unc2 = json.loads((W / "labels-v2/PILOT-UNCERTAINTY-AND-EXPOSURE.v2.json").read_text(encoding="utf-8"))
VERSION = "ai-pilot-r18-continuation-labels-2026-09-30.1"
STATUS = "AI-DRAFTED PROPOSALS (Claude) written before any prediction for the new documents; controls carry v2; not human truth; PROVISIONAL"
renders = {p.name: sha(p) for p in sorted((W / "label-renders").glob("*.png"))}


def rec(ref, rev, label, note, refs=(), confidence="high"):
    ids = [{"literal": ref, "printed_label": label, "role": "own_document", "own_for_evaluation": True}]
    ids += [{"literal": r, "printed_label": pl, "role": role, "own_for_evaluation": False} for r, pl, role in refs]
    return {"page": 1, "component": "sheet", "category": "drawings", "reference": ref, "printed_revision": rev, "decision": "n/a",
            "decision_actor": None, "decision_evidence": None, "identities": ids, "register": True, "confidence": confidence, "note": note}


NEW = {
    "87c43a7d1395": ("EML-09", "00", "Sheet No.", "medium",
                     "Al Arabia emergency-lighting schematic riser (A1, rotated 270); no 'Drawing No' label: the title block prints "
                     "'Sheet No.' EML-09 (and a code box 'EML'); revision table one row: 00 16-12-2024 ISSUED FOR APPROVAL; project "
                     "no P-49354; a supplier's company seal, no consultant decision", [("P-49354", "PROJECT NO.", "project_or_contract")]),
    "2253a7db7b41": ("ELEC-B16-EM-101", "0", "DRAWING NUMBER", "high",
                     "Al Arabia shop drawing, emergency light layout B16 (A1, rotated 270); REV. 0; submissions table: 0 ISSUED FOR "
                     "APPROVAL 26-07-2023; the DRAWING REFERENCES table lists B16-EM-101 (rev 00) and B16-A102 (rev 00) -- referenced "
                     "drawings, not this sheet; status SHOP DRAWING; no consultant decision",
                     [("B16-EM-101", "DRAWING REFERENCES / DRG. NO", "referenced_drawing"), ("B16-A102", "DRAWING REFERENCES / DRG. NO", "referenced_drawing"),
                      ("P56", "JOB No.", "project_or_contract")]),
    "273f8052cef3": ("819-TL-101", "01", "DRAWING No:", "high",
                     "structure cabling shop drawing, cafe ground floor (A0 page, A1 sheet size printed; rotated 270); REVISION 01; "
                     "revision rows 01 REVISED AS PER COMMENTS 22.06.2019, 00 Issued For Approval 02.04.2019; the Al Arabia 'SHOP "
                     "DRAWINGS' stamp (6/7/19) is the supplier's, not a consultant decision", []),
}
docs, pages, unc, exposure = [], {}, [], []
for d in S["documents"]:
    k = d["sha256"][:12]
    if d["role"] == "control_exposed":
        r = copy.deepcopy([x for x in reg2["documents"] if x["sha256"] == d["sha256"]][0])
        docs.append({**r, "label_source": "ai-pilot-labels-2026-09-30.2 (unchanged)"})
        pages[r["doc"]] = {**copy.deepcopy(page2["documents"][r["doc"]]), "label_source": "ai-pilot-labels-2026-09-30.2 (unchanged)"}
        unc += [u for u in unc2["uncertainty"] if u["doc"] == r["doc"]]
        exposure.append({"doc": r["doc"], "sha256": d["sha256"], "exposure": "EXPOSED: predicted by ai-accuracy-pilot A/S/G/T (2026-09-30)"})
        continue
    ref, rev, label, conf, note, refs = NEW[k]
    kind = "shop drawing sheet"
    docs.append({"doc": d["doc_key"], "ep": d["ep"], "cohort": "exploration", "stratum": d["stratum"], "extension": ".pdf", "sha256": d["sha256"],
                 "confidence": conf, "labels": {"kind": kind, "reference": ref, "revision": rev, "decision": "n/a", "system": "other", "register": True},
                 "label_source": VERSION})
    pages[d["doc_key"]] = {"doc": d["doc_key"], "sha256": d["sha256"], "stratum": d["stratum"], "records": [rec(ref, rev, label, note, refs, conf)],
                           "no_record_pages": {}, "unvalidated_pages": [], "unresolved": [], "label_source": VERSION,
                           "renders": {n: h for n, h in renders.items() if n.startswith(k)}}
    exposure.append({"doc": d["doc_key"], "sha256": d["sha256"], "exposure": "NEW: never predicted before this continuation (not in the small batch or the pilot)",
                     "prior_renders": "labelling renders only (label-renders/)"})
    if k == "87c43a7d1395":
        unc.append({"doc": d["doc_key"], "item": "no 'Drawing No' label: the own identity is taken from 'Sheet No.' (EML-09); the code box 'EML' "
                                                 "and the file name 'EML-09-SCH' are not used; a person may name another own identity"})
OUT = W / "labels-continuation"
OUT.mkdir(exist_ok=True)
common = {"status": STATUS, "sample_sha256": sha(W / "CONTINUATION-SAMPLE.json"), "labels_version": VERSION}
files = {"CONT-REGISTER-LABELS.json": {**common, "documents": docs}, "CONT-PAGE-LABELS.json": {**common, "documents": pages},
         "CONT-UNCERTAINTY-AND-EXPOSURE.json": {**common, "uncertainty": unc, "exposure": exposure}}
for n, obj in files.items():
    (OUT / n).write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print({n: sha(OUT / n)[:12] for n in files}, "| docs", len(docs), "| uncertainty", len(unc))
