"""Write labels-r26/R26-REVIEW-PASS.json (the second pass over the drafted labels) and labels-r26/LABEL-MANIFEST.r26.json
(workflow status, provenance and the hashes that freeze the label files). Run after labels_r26.py; no model request."""
import datetime
import hashlib
import json
import pathlib

R = pathlib.Path(__file__).resolve().parent
L = R / "labels-r26"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
crops = {json.loads(l)["png"]: json.loads(l)["sha256"] for l in (R / "renders/crops/CROPS.jsonl").read_text(encoding="utf-8").splitlines()}
REVIEW = {
    "labels_version": "r26-labels-2026-10-01.1",
    "reviewer": "the same assistant that drafted the labels (second pass in the same session) - NOT independent, NOT human, NOT blind to the draft",
    "scope": {
        "every_decision_label": ["D04 p1", "D16 p1", "D17 p1", "D18 p1", "D19 p1", "D22 p1", "D22 p2"],
        "every_rotated_or_scanned_item": ["D05", "D06", "D07", "D08", "D09", "D10", "D11", "D12", "D16", "D17", "D18", "D19", "D21", "D22", "D23", "D24"],
        "seeded_25_percent_subset": {"seed": "m2-r26-label-review-2026-10-01", "rule": "first 7 of 27 documents by sha256(seed|doc_key)", "documents": ["D12", "D08", "D25", "D19", "D01", "D20", "D11"]},
        "also_checked": "every 'n/a' / 'UR' label on a page that prints a decision block (D01, D06, D09, D10, D19 p2-p4) was checked for an empty block"},
    "methods": [
        "mechanical: every reference / revision literal of a page with a text layer was searched in that page's text layer - all found (25 records on text pages)",
        "visual: decision marks and image-only literals re-inspected on new zoom crops (hashes below)",
        "rules: off-title-block status, page-level decision convention and no-record continuation pages re-checked against the earlier label sets' conventions"],
    "decision_recheck_crops": {k: crops[k] for k in ("D04-p1-0.08_0.58_0.52_0.70.png", "D19-p1-0.06_0.48_0.92_0.53.png", "D19-p1-0.60_0.09_0.92_0.15.png",
                                                     "D22-p1-0.06_0.33_0.36_0.43.png", "D23-p1-0.25_0.80_0.75_0.85.png",
                                                     "D16-p1-0.72_0.13_1.00_0.36-r270.png", "D17-p1-0.62_0.18_0.80_0.56-r270.png", "D18-p1-0.50_0.16_0.70_0.36-r270.png")},
    "outcome": {"labels_changed": 0, "disagreements": [], "confirmed": "all drafted labels kept; decisions: D04 approved as noted (Approved with Comments ticked), D16 / D18 approved as noted (ATK CODE B stamp + handwritten status), D17 approved as noted (handwritten status only), D19 p1 rejected (C. Revise & Resubmit ticked), D22 p1 / p2 approved as noted (box ticked; REVIEW STATUS)"},
    "limits": ["not independent: R21 label-manifest step 4 asks for an independent owner-delegated AI source review; no other model or instance was allowed in this task",
               "the .doc control (D27) was labelled from text runs of the binary without rendering",
               "regions are approximate display-fraction boxes derived from the crops"],
}
(L / "R26-REVIEW-PASS.json").write_text(json.dumps(REVIEW, indent=1) + "\n", encoding="utf-8")
names = ["R26-REGISTER-LABELS.json", "R26-PAGE-LABELS.json", "R26-UNCERTAINTY-AND-EXPOSURE.json", "R26-LABEL-EVIDENCE.json", "R26-REVIEW-PASS.json"]
R21L = pathlib.Path("C:/t/iso/work/r2x/review21/labels-r21")
MAN = {
    "labels_version": "r26-labels-2026-10-01.1", "frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "frozen_before_any_prediction": True, "predictions_existing_for_these_documents": 0, "model_requests_for_labelling": 0,
    "replaces_nothing": "versioned beside review21/labels-r21 (skeletons, unchanged) and the earlier label packets; nothing overwritten",
    "r21_skeleton_hashes_unchanged": {p.name: sha(p) for p in sorted(R21L.glob("*.json"))},
    "workflow_status": {
        "1 selection rule frozen": "done (R21-SAMPLE.json, unchanged)",
        "2 owner budget decision": "PENDING - this task orders label completion before the funding request (labels must be frozen before predictions)",
        "3 AI-drafted labels": "DONE - 27 documents, 42 in-scope pages, 30 page records, 12 no-record pages, the .doc control register-only",
        "4 independent AI source review": "NOT DONE AS INDEPENDENT - a same-assistant second pass covered every decision, every rotated / scanned item and a seeded 25 % subset (no changes). Independence can be supplied by the independent review of this package; any change it requires is frozen as r26.2 before any prediction",
        "5 off-title-block minimum": "met by count (6 confirmed among the 24 primary documents); a strict reading (screened candidates) gives 1 of 4 - top-up NOT performed because the sample is frozen; disclosed",
        "6 labels frozen": "DONE - hashes below; any change requires a new version",
        "7 prediction": "none"},
    "provenance": {"drafted": "AI-drafted (Claude Opus 5.5 coding assistant)", "reviewed": "AI self-review (same assistant, second pass) - not independent",
                   "human_signoff": "none", "blind": "no"},
    "files": {n: sha(L / n) for n in names},
}
(L / "LABEL-MANIFEST.r26.json").write_text(json.dumps(MAN, indent=1) + "\n", encoding="utf-8")
print(json.dumps(MAN["files"], indent=1))
print("manifest", sha(L / "LABEL-MANIFEST.r26.json"))
