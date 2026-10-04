"""Synthetic labels for the r22 dry stage (harness plumbing only; not truth of anything): register / page labels in the
evaluator's shape for the four synthetic PDFs (every page labelled, including the two beyond the reader's scope), and the
Word file as a planned unsupported control. The raster pages are labelled with the literal the scripted provider answers
(X-DRY-1 / 01) so a dry run never trips the critical-acceptance stop by construction. Writes review22/labels-dry-r22/*.json."""
import hashlib
import json
import pathlib

W = pathlib.Path("C:/t/iso/work/r2x/review22")
stage = json.loads(pathlib.Path("C:/t/r2x/dry-runs/r22-stage/R22-DRY-STAGE.json").read_text(encoding="utf-8"))["files"]
by = {f["doc_key"]: f for f in stage}


def rec(page, ref, rev, decision="n/a", actor=None, evidence=None, note="synthetic"):
    return {"page": page, "component": "sheet", "category": "drawings", "reference": ref, "printed_revision": rev, "decision": decision,
            "decision_actor": actor, "decision_evidence": evidence,
            "identities": [{"literal": ref, "printed_label": "DRAWING NO", "role": "own_document", "own_for_evaluation": True}],
            "register": True, "confidence": "high", "note": note}


docs, pages = [], {}
DEC = ("approved as noted", "consultant", "scripted legend B marked (synthetic)")
spec = {"EP-16830/synth/raster-6pages.pdf": ("X-DRY-1", "01", [1, 2, 3, 4, 5, 6], DEC), "EP-16830/synth/raster-1page.pdf": ("X-DRY-1", "01", [1], DEC),
        "EP-17428/synth/raster-2pages.pdf": ("X-DRY-1", "01", [1, 2], DEC), "EP-17428/synth/text-sheet.pdf": ("X-SD-7", "02", [1], ("n/a", None, None))}
for key, (ref, rev, pnos, dec) in spec.items():
    f = by[key]
    ep = key.split("/")[0][3:]
    docs.append({"doc": key, "ep": ep, "cohort": "synthetic", "stratum": "synthetic", "extension": ".pdf", "sha256": f["sha256"], "confidence": "high",
                 "labels": {"kind": "synthetic sheet", "reference": ref, "revision": rev, "decision": dec[0], "system": "other", "register": True}})
    pages[key] = {"doc": key, "sha256": f["sha256"], "stratum": "synthetic", "records": [rec(p, ref, rev, *dec) for p in pnos], "no_record_pages": {}, "unvalidated_pages": [], "unresolved": []}
docx = by["EP-17428/synth/note.docx"]
docs.append({"doc": docx["doc_key"], "ep": "17428", "cohort": "synthetic", "stratum": "synthetic", "extension": ".docx", "sha256": docx["sha256"], "confidence": "high",
             "labels": {"kind": "word note (unsupported input for the evidence reader)", "reference": "TR-002", "revision": "00", "decision": "n/a", "system": "other", "register": False}})
common = {"status": "SYNTHETIC dry-run labels (harness plumbing only)", "labels_version": "r22-dry-labels-2026-09-30.2"}
OUT = W / "labels-dry-r22"
OUT.mkdir(exist_ok=True)
files = {"DRY-REGISTER-LABELS.json": {**common, "documents": docs}, "DRY-PAGE-LABELS.json": {**common, "documents": pages},
         "DRY-UNCERTAINTY-AND-EXPOSURE.json": {**common, "uncertainty": [], "exposure": []}}
for n, obj in files.items():
    (OUT / n).write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
print({n: hashlib.sha256((OUT / n).read_bytes()).hexdigest()[:12] for n in files})
