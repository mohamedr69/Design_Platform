"""Label version r26-labels-2026-10-01.2 (Review 27, R27-02), written BESIDE the frozen r26.1 labels (unchanged) and the
R21 skeletons (unchanged). It applies only the independent reviewer's specific rulings and provenance; every other source
literal, confidence and document-level uncertainty is carried over byte-for-byte in value.
  * provenance: AI-drafted (Claude assistant) + same-assistant second pass + INDEPENDENT owner-delegated AI source review
    (Codex reviewer, Review 27; not human, not blind to the draft), bound to the reviewer's record by sha256;
  * D17: the readable decision value is kept ('approved as noted'); the ACTOR is marked inferred / unresolved (field-level),
    and the entry moves from 'labelling conventions' to 'field_uncertainty'. The runner's document-level uncertainty list
    (its tripwire exclusion) is NOT changed -- the stop policy is untouched; this schema limit is disclosed;
  * D19: the source literal 'C. Revise & Resubmit' (D. Rejected blank) is recorded beside the evaluator's coarse
    normalized value 'rejected'; enclosed sheets keep their own UR;
  * D05: the printed stage 'ASBUILT' is kept as descriptive metadata (no routing change);
  * D27: marked not visually verified by drafter or reviewer; unsupported control, no extraction-accuracy credit;
  * off-title-block: the reviewer's pre-run interpretation and the ROI-eligible population (ROI-POPULATION.json).
Writes labels-r26.2/*.json and LABEL-MANIFEST.r26.2.json (last). No model request."""
import copy
import datetime
import hashlib
import json
import pathlib

R = pathlib.Path(__file__).resolve().parent
OLD = pathlib.Path("C:/t/iso/work/r2x/r26/labels-r26")
NEW = R / "labels-r26.2"
NEW.mkdir(exist_ok=True)
REV = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-27")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
load = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
old_man = load(OLD / "LABEL-MANIFEST.r26.json")
assert sha(OLD / "LABEL-MANIFEST.r26.json") == "b29d93d162a375ca8d1d2a648c8522af8c3d132a6957c93a2b21e96c63812509"
for n, h in old_man["files"].items():
    assert sha(OLD / n) == h, n
review = load(REV / "INDEPENDENT-LABEL-REVIEW.json")
rulings = {d["id"]: d["ruling"] for d in review["documents"]}
roi = load(R / "ROI-POPULATION.json")
REVIEW_BIND = {n: sha(REV / n) for n in ("INDEPENDENT-LABEL-REVIEW.json", "SOURCE-RENDER-CHECK.json", "REVIEW-27-REPORT.md", "TASK-CLOSE-REVIEW-27.md", "TOKEN-LIMIT-PROBE.json")}
VERSION = "r26-labels-2026-10-01.2"
PROV = {"drafted_by": "AI (Claude Opus 5.5 coding assistant) from local renders and text layers of the hash-checked staged copies",
        "second_pass": "the same assistant (not independent)",
        "independent_review": "owner-delegated independent AI source review (Codex reviewer, Independent M2 Review 27), separate from the drafting assistant; covered all 42 in-scope pages, all decision records, rotated / scanned items and the seeded subset; NOT human, NOT blind to the draft, no predictions consulted, 0 provider requests",
        "independent_review_record": {"file": str(REV / "INDEPENDENT-LABEL-REVIEW.json").replace("\\", "/"), "sha256": REVIEW_BIND["INDEPENDENT-LABEL-REVIEW.json"]},
        "human_signoff": "none", "blind": "no", "model_requests": 0,
        "not_visually_verified": ["D27 (legacy .doc control): drafted from binary text runs; neither the drafter nor the independent reviewer verified it visually"]}
STATUS = ("AI-DRAFTED, SAME-ASSISTANT SECOND PASS AND INDEPENDENT OWNER-DELEGATED AI SOURCE REVIEW (Review 27) reference labels, "
          "FROZEN before any prediction; not human-signed, not blind")
REG, PAGE, UNC, EVID = (load(OLD / n) for n in ("R26-REGISTER-LABELS.json", "R26-PAGE-LABELS.json", "R26-UNCERTAINTY-AND-EXPOSURE.json", "R26-LABEL-EVIDENCE.json"))
ids = {d["doc"]: d["draft_id"] for d in REG["documents"]}
by_id = {d["draft_id"]: d for d in REG["documents"]}
doc_of = {v: k for k, v in ids.items()}
changes = []


def rec(did, page):
    return next(r for r in PAGE["documents"][doc_of[did]]["records"] if r["page"] == page)


for d in (REG, PAGE, UNC):
    d.update(status=STATUS, labels_version=VERSION, provenance=PROV)
for d in REG["documents"]:
    d["label_source"] = VERSION
    d["provenance"] = PROV
    d["independent_ruling"] = rulings[d["draft_id"]]
for v in PAGE["documents"].values():
    v["label_source"] = VERSION
# D17 - actor uncertainty (field level), value kept
r = rec("D17", 1)
old_actor = r["decision_actor"]
r["decision_actor"] = "unresolved (inferred: ATK Engineering Consultants)"
r["actor_attribution"] = {"state": "inferred_unresolved", "basis": "initials only; inferred from the ATK RECEIVED stamp (a receipt, not an approval stamp) and similarity to the stamped D16 hand", "independently_established": False}
by_id["D17"]["field_uncertainty"] = {"decision_actor": "inferred_unresolved"}
changes.append({"id": "D17", "page": 1, "field": "decision_actor", "old": old_actor, "new": r["decision_actor"], "decision_value": f"unchanged ({r['decision']})", "ruling": rulings["D17"]})
# D19 - literal beside the normalized value
r = rec("D19", 1)
r["decision_literal"] = "C. Revise & Resubmit (option C ticked; D. Rejected not marked)"
r["decision_normalization"] = "the evaluator vocabulary has no 'revise and resubmit' value; the label keeps the earlier label sets' coarse convention 'rejected' for scoring. This is a metric convention, not a reading of the D checkbox and not a business-status change"
by_id["D19"]["labels_literal"] = {"decision": "C. Revise & Resubmit"}
changes.append({"id": "D19", "page": 1, "field": "decision_literal (added)", "old": None, "new": r["decision_literal"], "decision_value": f"unchanged ({r['decision']}, normalized)", "enclosed_sheets": "pages 2-4 stay UR (the cover decision is not inherited)", "ruling": rulings["D19"]})
for p in (2, 3, 4):
    assert rec("D19", p)["decision"] == "UR"
# D05 - printed stage as metadata
r = rec("D05", 1)
r["stage_printed"] = "ASBUILT (red text in the 'Status' cell)"
by_id["D05"]["stage_printed"] = "ASBUILT"
changes.append({"id": "D05", "page": 1, "field": "stage_printed (added, descriptive)", "old": None, "new": "ASBUILT", "decision_value": f"unchanged ({r['decision']})", "ruling": rulings["D05"]})
# D27 - not visually verified, no extraction credit
by_id["D27"]["verification"] = "binary-text draft; not visually verified by the drafter or by the independent reviewer; unsupported input control: it stays in the coverage denominator and earns no extraction-accuracy credit"
changes.append({"id": "D27", "field": "verification (added)", "new": by_id["D27"]["verification"], "ruling": rulings["D27"]})
# uncertainty: document-level list unchanged (runner tripwire semantics); D17 moves from conventions to field_uncertainty
doc_level_before = sorted({u["doc"] for u in UNC["uncertainty"]})
UNC["labelling_conventions"] = [c for c in UNC["labelling_conventions"] if not (c["draft_id"] == "D17" and c["field"] == "decision_actor")]
UNC["field_uncertainty"] = [{"doc": doc_of["D17"], "draft_id": "D17", "page": 1, "field": "decision_actor", "state": "inferred_unresolved",
                             "issue": "the handwritten 'CODE B APPROVED AS NOTED, RESUBMIT' is readable; who wrote it is not established (receipt stamp + handwriting similarity only)",
                             "scoring_effect": "none on the decision value: the frozen evaluator scores the literal decision value and does not score the actor",
                             "tripwire_effect": "none: the runner's predeclared exclusion reads only the document-level 'uncertainty' list, which is unchanged"}]
UNC["schema_limitation"] = ("the frozen runner / evaluator know only document-level uncertainty (the 'uncertainty' list, which also excludes a document from the critical-acceptance stop). "
                            "A field-level actor uncertainty cannot be expressed there without changing the stop population; it is therefore recorded in 'field_uncertainty', "
                            "the decision value stays scored, and the stop policy is unchanged (as the task requires)")
assert sorted({u["doc"] for u in UNC["uncertainty"]}) == doc_level_before
off = UNC["off_title_block"]
off["reviewer_interpretation_pre_run"] = {
    "source": "Independent M2 Review 27, recorded before any prediction",
    "rule_reading": "the minimum of 4 confirmed decisions is counted over the frozen 24 primary documents; the text screen was a selection aid",
    "readable_decision_documents": ["D04", "D16", "D17", "D18", "D19", "D22"], "decision_page_records": 7,
    "source_supported_attribution": ["D04", "D16", "D18", "D19", "D22"], "attribution_inferred": ["D17"],
    "minimum_met": "yes: 5 documents with source-supported consultant / engineer attribution (>= 4) even without D17",
    "screen_result_kept": "1 of the 4 screened candidates (D04) is a real decision", "top_up": "none requested or performed"}
off["roi_population"] = {"source": "ROI-POPULATION.json (frozen title_block.is_drawing_sheet on every in-scope page)",
                         "crop_eligible_decision_pages": roi["decision_pages_crop_eligible"], "whole_page_discovery_decision_pages": roi["decision_pages_whole_page_discovery"],
                         "crop_eligible_projects": ["EP-19144"], "explicit_approval_stamps_among_crop_eligible": ["D16", "D18"],
                         "limitation": "only 3 crop-eligible decision sheets, one project, two with explicit stamps: a small diagnostic for ROI decision coverage, not evidence of general decision safety; eligibility does not prove what a runtime crop contains"}
files = {"R26.2-REGISTER-LABELS.json": REG, "R26.2-PAGE-LABELS.json": PAGE, "R26.2-UNCERTAINTY-AND-EXPOSURE.json": UNC, "R26.2-LABEL-EVIDENCE.json": EVID}
for n, obj in files.items():
    (NEW / n).write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
(NEW / "R26.2-CHANGES.json").write_text(json.dumps({"from": "r26-labels-2026-10-01.1", "to": VERSION, "changes": changes,
                                                     "unchanged": "every other identity / revision / decision / confidence / no-record page / document-level uncertainty value",
                                                     "independent_review_bindings": REVIEW_BIND}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
names = list(files) + ["R26.2-CHANGES.json"]
MAN = {"labels_version": VERSION, "frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "frozen_before_any_prediction": True,
       "predictions_existing_for_these_documents": 0, "model_requests_for_labelling": 0,
       "supersedes_for_the_declaration": {"version": "r26-labels-2026-10-01.1", "manifest_sha256": "b29d93d162a375ca8d1d2a648c8522af8c3d132a6957c93a2b21e96c63812509", "kept_unchanged": True},
       "r21_skeleton_hashes_unchanged": old_man["r21_skeleton_hashes_unchanged"],
       "workflow_status": {**old_man["workflow_status"],
                           "4 independent AI source review": "DONE: owner-delegated independent AI source review (Review 27; not human, not blind to the draft); rulings applied in this version",
                           "5 off-title-block minimum": "met under the reviewer's pre-run interpretation (5 source-attributed decision documents among the 24 primary); screen result 1 / 4 kept; no top-up",
                           "6 labels frozen": "DONE (r26.2) - hashes below"},
       "provenance": PROV, "independent_review_bindings": REVIEW_BIND, "files": {n: sha(NEW / n) for n in names}}
(NEW / "LABEL-MANIFEST.r26.2.json").write_text(json.dumps(MAN, indent=1) + "\n", encoding="utf-8")
print("changes", [(c["id"], c["field"]) for c in changes])
print("doc-level uncertainty unchanged", doc_level_before == sorted({u["doc"] for u in UNC["uncertainty"]}), "| manifest", sha(NEW / "LABEL-MANIFEST.r26.2.json"))
