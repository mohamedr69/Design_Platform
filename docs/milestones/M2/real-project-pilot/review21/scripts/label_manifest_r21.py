"""Label manifest and exposure records for the R21 sample (no label is drafted here: labels and their AI review are
drafted AFTER the owner's budget decision and frozen BEFORE any prediction). Writes labels-r21/: skeleton register /
page / uncertainty files (status PENDING, every document and in-scope page listed with the fields to fill, the decision
LOCATION field required), LABEL-MANIFEST.json (workflow, provenance rules, freeze order) and EXPOSURE.json."""
import hashlib
import json
import pathlib

R = pathlib.Path("C:/t/iso/work/r2x/review21")
sample = json.loads((R / "R21-SAMPLE.json").read_text(encoding="utf-8"))
stage = {f["doc_key"]: f for f in json.loads(pathlib.Path("C:/t/r2x/r21-stage/R21-STAGE.json").read_text(encoding="utf-8"))["files"]}
STATUS = "PENDING: not drafted; to be AI-drafted from source renders / text layer and independently AI-reviewed AFTER the budget decision and BEFORE any prediction; never human-signed"
docs, pages, exposure = [], {}, []
for d in sample["documents"]:
    f = stage[d["doc_key"]]
    docs.append({"doc": d["doc_key"], "ep": d["ep"], "cohort": "exploration (non-sealed)", "stratum": d.get("stratum") or "unsupported_input", "extension": d["extension"],
                 "sha256": d["sha256"], "role": d["role"], "confidence": None, "labels": None, "status": STATUS})
    if d["extension"] == ".pdf":
        pages[d["doc_key"]] = {"doc": d["doc_key"], "sha256": d["sha256"], "records": None, "no_record_pages": None, "unvalidated_pages": None, "unresolved": None,
                               "pages_to_label": [p["page"] for p in d["page_classes"] if p["in_scope"]], "pages_beyond_reader_scope": [p["page"] for p in d["page_classes"] if not p["in_scope"]],
                               "required_per_record": ["page", "component", "reference (literal, punctuation kept)", "printed_revision", "decision (marked option / n/a / absent)",
                                                       "decision_actor", "decision_evidence", "decision_location: inside_title_block | outside_title_block | none",
                                                       "identities[] with printed_label, role, own_for_evaluation", "confidence", "note"], "status": STATUS}
    exposure.append({"doc": d["doc_key"], "sha256": d["sha256"], "prior_predictions": "none (excluded by content hash from every earlier predicted / held-out set)",
                     "prior_renders": "Round 2 first-page render for labelling only (C:/t/r2x/renders), no prediction", "screened_off_title_block": d.get("screened_off_title_block")})
OUT = R / "labels-r21"
OUT.mkdir(exist_ok=True)
common = {"status": STATUS, "sample_sha256": hashlib.sha256((R / "R21-SAMPLE.json").read_bytes()).hexdigest(), "labels_version": "r21-labels-PENDING"}
files = {"R21-REGISTER-LABELS.json": {**common, "documents": docs}, "R21-PAGE-LABELS.json": {**common, "documents": pages},
         "R21-UNCERTAINTY-AND-EXPOSURE.json": {**common, "uncertainty": None, "exposure": exposure}}
for n, obj in files.items():
    (OUT / n).write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
manifest = {"workflow": ["1. selection rule frozen (R21-SAMPLE.json, this task)", "2. owner budget decision", "3. AI-drafted labels from renders / text layer, page and region bound, "
            "decision location recorded; ambiguous items stay unresolved", "4. independent owner-delegated AI source review of every decision label, every rotated / scanned item and a "
            "seeded 25 % subset; provenance kept (reviewer, render hashes); no human signature", "5. the off-title-block minimum (>= 4 confirmed) checked; shortfall topped up from the "
            "screened pool in seed order, still before any prediction; the final count reported", "6. labels and review FROZEN (hashes into the final declaration)", "7. only then any prediction"],
            "rules": ["no prediction becomes truth", "AI-drafted / AI-reviewed status stays on every label", "unresolved labels are reported separately and never silently resolved"],
            "files": {n: hashlib.sha256((OUT / n).read_bytes()).hexdigest() for n in files}}
(OUT / "LABEL-MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
(OUT / "EXPOSURE.json").write_text(json.dumps({"documents": exposure}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("label skeletons", len(docs), "documents;", sum(len(p["pages_to_label"]) for p in pages.values()), "pages to label;", manifest["files"])
