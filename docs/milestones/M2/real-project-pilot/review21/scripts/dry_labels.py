"""Synthetic labels for the dry stage (harness plumbing only; not truth of anything): register / page labels in the
evaluator's shape for the four synthetic PDFs (every page of the 6-page file labelled), and the Word file as a planned
unsupported control. Writes labels-dry/*.json."""
import hashlib
import json
import pathlib

W = pathlib.Path("C:/t/iso/work/r2x/review21")
stage = json.loads(pathlib.Path("C:/t/r2x/dry-runs/r21-stage/R21-DRY-STAGE.json").read_text(encoding="utf-8"))["files"]
by = {f["doc_key"]: f for f in stage}


def rec(page, ref, rev, decision="n/a", actor=None, evidence=None, note="synthetic"):
    return {"page": page, "component": "sheet", "category": "drawings", "reference": ref, "printed_revision": rev, "decision": decision,
            "decision_actor": actor, "decision_evidence": evidence,
            "identities": [{"literal": ref, "printed_label": "DRAWING NO", "role": "own_document", "own_for_evaluation": True}],
            "register": True, "confidence": "high", "note": note}


docs, pages = [], {}
spec = {"EP-16830/synth/rot270-sheet.pdf": ("X-SD-1", "02", "approved as noted", "consultant", "legend B marked, in the title block", [1]),
        "EP-16830/synth/long-6pages.pdf": ("X-SD-11", "02", "n/a", None, None, [1, 2, 3, 4, 5, 6]),
        "EP-17428/synth/a4-letter.pdf": ("TR-001", "00", "n/a", None, None, [1]),
        "EP-17428/synth/stamp-outside.pdf": ("X-SD-7", "02", "approved as noted", "consultant", "raster stamp CODE B outside the title block", [1])}
for key, (ref, rev, dec, actor, ev, pnos) in spec.items():
    f = by[key]
    ep = key.split("/")[0][3:]
    docs.append({"doc": key, "ep": ep, "cohort": "synthetic", "stratum": "synthetic", "extension": ".pdf", "sha256": f["sha256"], "confidence": "high",
                 "labels": {"kind": "synthetic sheet", "reference": ref, "revision": rev, "decision": dec, "system": "other", "register": True}})
    recs = [rec(p, ref if p == 1 else f"X-SD-{10 + p}", rev, dec if p == 1 else "n/a", actor if p == 1 else None, ev if p == 1 else None) for p in pnos]
    pages[key] = {"doc": key, "sha256": f["sha256"], "stratum": "synthetic", "records": recs, "no_record_pages": {}, "unvalidated_pages": [], "unresolved": []}
docx = by["EP-17428/synth/note.docx"]
docs.append({"doc": docx["doc_key"], "ep": "17428", "cohort": "synthetic", "stratum": "synthetic", "extension": ".docx", "sha256": docx["sha256"], "confidence": "high",
             "labels": {"kind": "word note (unsupported input for the evidence reader)", "reference": "TR-002", "revision": "00", "decision": "n/a", "system": "other", "register": False}})
common = {"status": "SYNTHETIC dry-run labels (harness plumbing only)", "labels_version": "r21-dry-labels-2026-09-30.1"}
OUT = W / "labels-dry"
OUT.mkdir(exist_ok=True)
files = {"DRY-REGISTER-LABELS.json": {**common, "documents": docs}, "DRY-PAGE-LABELS.json": {**common, "documents": pages},
         "DRY-UNCERTAINTY-AND-EXPOSURE.json": {**common, "uncertainty": [], "exposure": []}}
for n, obj in files.items():
    (OUT / n).write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
print({n: hashlib.sha256((OUT / n).read_bytes()).hexdigest()[:12] for n in files})
