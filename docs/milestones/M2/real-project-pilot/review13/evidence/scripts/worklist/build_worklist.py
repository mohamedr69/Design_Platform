"""Round 2 human-review worklist (new, linked; packet v2 is preserved unchanged and referenced by hash).

Sections:
  1. the 13 unresolved Review 07 source findings (8 DECIDE, 5 CONFIRM groups) -- the packet v2 question, its page image
     and the new region crops (FINDING-CROPS.json);
  2. H-06 BOQ rows (EP-8430): the three accepted-wrong quantities and the control row, with crops;
  3. the small batch's unresolved label items, with crops (SMALL-BATCH-CROPS.json);
  4. decisions: every labelled decision is mandatory review (the small batch labels none: stated, not hidden);
  5. critical disagreements: filled from the scored runs (--disagreements file), every one mandatory;
  6. the independent 20 % sample: over the label units NOT already mandatory, ranked by
     sha256(seed + unit id) -- a function of the label unit ids only, never of any prediction or score.
No reviewer is named; nothing here is a decision. Usage: build_worklist.py [--disagreements file.json]"""
import argparse
import hashlib
import json
import math
import pathlib

a = argparse.ArgumentParser()
a.add_argument("--disagreements")
args = a.parse_args()
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
PKT = PILOT / "review08/human-review-packet-v2"
W = pathlib.Path("C:/t/iso/work/r2x")
FC = pathlib.Path("C:/t/r2x/worklist/findings/FINDING-CROPS.json")
SC = pathlib.Path("C:/t/r2x/worklist/small-batch/SMALL-BATCH-CROPS.json")
H6 = pathlib.Path("C:/t/r2x/worklist/h06/H06-CROPS.json")
LAB = W / "labels/SMALL-BATCH-LABELS.json"
SEED = "m2-round2-human-sample-2026-09-29"
RATE = 0.20


def sha(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


findings = json.loads((PKT / "FINDINGS-INDEX.json").read_text(encoding="utf-8"))["groups"]
crops = {(i["group"], i["item"]): i for i in json.loads(FC.read_text(encoding="utf-8"))["items"]}
AI_NOTES = {("F12", "C0282"): "AI observation from the crop (not a decision): the cell reads 'Submitted Reference: CDS-DOC-01943' -- "
                              "no leading 'I' is visible in the crop, and the label names it a submitted reference"}
sec1 = []
for g in findings:
    for it in g["items"]:
        c = crops[(g["group"], it["item"])]
        sec1.append({"id": f"{g['group']}/{it['item']}", "kind": "DECIDE" if g["status"] == "unresolved" else "CONFIRM", "group": g["group"],
                     "category": g["category"], "field": g["field"], "doc": it["doc"], "page": int(it["page"]), "cohort": it["cohort"],
                     "question": g["to_decide"], "value_read": g["value_read"], "label": g["label"],
                     "page_image_packet_v2": it["page_image"], "crops": [x["file"] for x in c["crops"]],
                     "literal_not_located": c["not_located"], "ai_note": AI_NOTES.get((g["group"], it["item"])),
                     "answer": {"decision": None, "own_identity_literal": None, "roles": None, "reviewer": None, "date": None}})
h6 = json.loads(H6.read_text(encoding="utf-8"))
H06_DOC = "EP-8430/EP-8430 Commercial/EP-8430 PAVA Revised Design Sheet - 23.10.2017.pdf"
sec2 = [{"id": f"H06/{r['id']}", "kind": "CONFIRM", "doc": H06_DOC, "row_description": r["description"], "note": r["note"],
         "crops": [r["row_crop"], r["quantity_crop"]], "question": "Confirm the printed quantity and part literal of this row"
         + (" (a known-correct control row)." if "control" in r["id"] else " (the AI-off reader accepted 4; the proposed label says 1)."),
         "answer": {"quantity": None, "part_number": None, "reviewer": None, "date": None}} for r in h6]
sc = json.loads(SC.read_text(encoding="utf-8"))
sec3 = [{"id": f"SB/{i['sha256'][:12]}/u{n + 1}", "kind": "DECIDE" if "DECIDE" in i["question"] else "CONFIRM", "doc": i["doc"], "page": i["page"],
         "question": i["question"], "crops": [c["file"] for c in i["crops"]], "located_by": [c["located_by"] for c in i["crops"]],
         "answer": {"value": None, "reviewer": None, "date": None}} for n, i in enumerate(sc["items"])]
lab = json.loads(LAB.read_text(encoding="utf-8"))
decisions = [{"doc": k, "page": r["page"], "decision": r["decision"]} for k, d in lab["documents"].items() for r in d["records"] if r["decision"] not in (None, "n/a")]
# label units: each record, each no-record page, each BOQ row
units = []
for k, d in lab["documents"].items():
    for r in d["records"]:
        units.append({"unit": f"{d['sha256'][:12]}/p{r['page']}/record/{r['reference']}", "doc": k, "page": r["page"], "type": "record"})
    for p in d["no_record_pages"]:
        units.append({"unit": f"{d['sha256'][:12]}/p{p}/no_record", "doc": k, "page": int(p), "type": "no_record_page"})
    for n, row in enumerate(d.get("boq_rows") or []):
        units.append({"unit": f"{d['sha256'][:12]}/p{row['page']}/boq_row/{n + 1}", "doc": k, "page": row["page"], "type": "boq_row"})
mandatory_pages = {(i["doc"], i["page"]) for i in sec3}
mandatory_units = [u for u in units if (u["doc"], u["page"]) in mandatory_pages]
pool = [u for u in units if (u["doc"], u["page"]) not in mandatory_pages]
n_sample = math.ceil(RATE * len(pool))
ranked = sorted(pool, key=lambda u: hashlib.sha256(f"{SEED}|{u['unit']}".encode()).hexdigest())
sample = [dict(u, rank=i + 1, answer={"label_correct": None, "correction": None, "reviewer": None, "date": None}) for i, u in enumerate(ranked[:n_sample])]
dis = json.loads(pathlib.Path(args.disagreements).read_text(encoding="utf-8")) if args.disagreements else None
out = {"status": "PREPARED BY AI -- NOT REVIEWED. No reviewer is appointed (OWNER-AI-PERMISSION-ROUND2.md: reviewer appointment and sign-off pending). "
                 "Every answer field is empty; nothing here counts as truth until a person fills it.",
       "links": {"packet_v2": {"folder": str(PKT).replace("\\", "/"), "FINDINGS-INDEX.json": sha(PKT / "FINDINGS-INDEX.json"),
                               "PACKET-MANIFEST-v2.json": sha(PKT / "PACKET-MANIFEST-v2.json"), "note": "preserved unchanged"},
                 "finding_crops": {"file": str(FC).replace("\\", "/"), "sha256": sha(FC)}, "h06_crops": {"file": str(H6).replace("\\", "/"), "sha256": sha(H6)},
                 "small_batch_crops": {"file": str(SC).replace("\\", "/"), "sha256": sha(SC)},
                 "small_batch_labels": {"file": str(LAB).replace("\\", "/"), "sha256": sha(LAB)}},
       "rules": {"mandatory": ["every DECIDE / CONFIRM source finding", "every labelled decision", "every critical disagreement (a critical false accept, "
                               "or a critical-field value two profiles assert differently)", "every ambiguous identity / revision / part (the labels' unresolved lists)"],
                 "independent_sample": {"rate": RATE, "seed": SEED, "population": "label units (records, no-record pages, BOQ rows) not on a mandatory page",
                                        "ranking": "sha256(seed | unit id), ascending; depends on label unit ids only, never on predictions or scores",
                                        "declared_when": "written after the profile A / B runs had started; the rule reads no prediction, so the sample is "
                                                         "reproducible from the labels alone (python build_worklist.py)"}},
       "sections": {"1_source_findings": sec1, "2_h06_boq_rows": sec2, "3_small_batch_unresolved": sec3,
                    "4_decisions": {"labelled_decisions": decisions, "note": "the small batch labels no decision; decision accuracy is not measured by it"},
                    "5_critical_disagreements": dis if dis is not None else "to be filled from the scored runs (critical false accepts and cross-profile critical conflicts)",
                    "6_independent_sample": {"units_total": len(units), "units_mandatory": len(mandatory_units), "pool": len(pool), "sample_size": n_sample, "items": sample}},
       "counts": {"source_findings_items": len(sec1), "decide_groups": len({x["group"] for x in sec1 if x["kind"] == "DECIDE"}),
                  "confirm_groups": len({x["group"] for x in sec1 if x["kind"] == "CONFIRM"}), "h06_rows": len(sec2), "small_batch_unresolved": len(sec3),
                  "labelled_decisions": len(decisions), "independent_sample": n_sample}}
p = W / "worklist/HUMAN-REVIEW-WORKLIST.json"
p.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(out["counts"]), "sha256", sha(p))
