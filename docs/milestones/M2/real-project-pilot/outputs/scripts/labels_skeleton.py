"""Pilot step 4: one label record per frozen document, to be filled from the contact sheets (the reader's own output is
never a source of a label). Every scored field starts as "unlabelled" and is set to a literal value, or to one of the
distinct non-values: absent (the page has no such field), illegible, unknown (not established from the crops rendered),
n/a (the field does not apply to this kind of document)."""
import json, sys, pathlib, datetime

S = pathlib.Path(sys.argv[1])
frozen = json.load(open(S / "FROZEN-SAMPLE.json", encoding="utf-8"))
index = {x["doc"]: x for x in json.load(open(S / "crops" / "index.json", encoding="utf-8")) if "doc" in x}
FIELDS = ["kind", "reference", "revision", "date", "title", "system", "floor", "originator", "decision", "decision_candidates", "printed_project", "components"]
labels = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "labeller": "Claude (Fable 5.1), from crops of the staged originals rendered by pymupdf; no parser output consulted",
          "non_values": ["absent", "illegible", "unknown", "n/a", "unlabelled"], "confidence_scale": ["high", "medium", "low"],
          "field_meaning": {"kind": "what page 1 is: shop-drawing cover / drawing sheet / material submittal / reply (CRS) / transmittal / sample approval / spec / calc / datasheet / certificate / design sheet / letter / other",
                            "reference": "the submission or drawing number printed in the header/title block, literal", "revision": "as printed (00, 01, R1, A ...)", "date": "as printed", "title": "the drawing/submittal title, literal",
                            "system": "FAS / VES / ELS / FF / other / none (as the document names it)", "floor": "as printed, or n/a", "originator": "the contractor/consultant named as submitter/originator, literal, or unknown",
                            "decision": "consultant decision as marked: approved / ANN / rejected / UR (no mark) / conflict (marks disagree) -- a contractor reply or a receipt signature is never a decision",
                            "decision_candidates": "every mark seen (method + option) when more than one, else []", "printed_project": "the project code/name printed on the page, or absent",
                            "components": "what the pages hold beyond page 1, when rendered (p2 crop), else unknown"},
          "documents": []}
for d in frozen["documents"]:
    key = f"EP-{d['ep']}/{d['relative_path']}"; ix = index.get(key, {})
    entry = {"doc": key, "sha256": d.get("sha256"), "ep": d["ep"], "cohort": d["cohort"], "stratum": d["stratum"], "extension": d["extension"], "pages": d.get("pages"), "scan_like": d.get("scan_like"),
             "crop_sheet": None, "crops": ix.get("crops", []), "whole": ix.get("whole"),
             "labels": {f: "unlabelled" for f in FIELDS}, "confidence": "unlabelled", "expected_eligibility": "eligible" if d["extension"] == ".pdf" or d["stratum"] == "transmittal_word" else "unsupported",
             "expected_records": "unlabelled", "notes": ""}
    if "read_error" in d or "open_error" in d:
        entry["expected_eligibility"] = "unreadable"; entry["notes"] = d.get("read_error") or d.get("open_error")
    labels["documents"].append(entry)
# which contact sheet holds which document (4 per sheet, in index order)
tiles = [x["doc"] for x in json.load(open(S / "crops" / "index.json", encoding="utf-8")) if "tag" in x]
sheet_of = {doc: f"sheet-{i // 4 + 1:03d}.png" for i, doc in enumerate(tiles)}
for e in labels["documents"]:
    e["crop_sheet"] = sheet_of.get(e["doc"])
json.dump(labels, open(S / "GOLDEN-LABELS-skeleton.json", "w", encoding="utf-8"), indent=1)
print("documents", len(labels["documents"]), "with sheets", sum(1 for e in labels["documents"] if e["crop_sheet"]))
