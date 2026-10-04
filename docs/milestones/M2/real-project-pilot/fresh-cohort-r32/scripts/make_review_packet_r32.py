"""Step 9/10: the reviewer packet for the independent (owner-delegated Codex) label review, generated from the FROZEN draft
labels/R32-LABELS-DRAFT-1.json. Reviewer columns are blank by construction. Writes review/PAGE-FIELD-WORKLIST.csv,
review/DOCUMENT-FIELD-WORKLIST.csv, review/DOCUMENT-QUESTIONS.json, review/REVIEWER-RESPONSE-TEMPLATE.json and
EVIDENCE-INDEX.json (every render and crop with absolute path, sha256, binding and recipe)."""
import csv
import hashlib
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
D = json.loads((HERE / "labels" / "R32-LABELS-DRAFT-1.json").read_text(encoding="utf-8"))
DRAFT_SHA = hashlib.sha256((HERE / "labels" / "R32-LABELS-DRAFT-1.json").read_bytes()).hexdigest()
SEL = {p["pool_id"]: p for p in json.loads((HERE / "FROZEN-SELECTION.json").read_text(encoding="utf-8"))["pool"]}
R = {d["pool_id"]: d for d in json.loads((HERE / "RENDERS.json").read_text(encoding="utf-8"))["documents"]}
RD, CD = "C:/t/r2x/r32-stage/renders", "C:/t/r2x/r32-stage/crops"
(HERE / "review").mkdir(exist_ok=True)


def ev_paths(ev):
    return "; ".join(f"{RD}/{e[7:]}" if e.startswith("render ") else f"{CD}/{e}" for e in ev or [])


rows, drows, questions = [], [], []
for pid, d in D["documents"].items():
    if d.get("duplicate_of"):
        questions.append({"pool_id": pid, "question": f"byte-identical copy of {d['duplicate_of']} (convention 1): confirm it counts once", "draft": "counts once with " + d["duplicate_of"]})
        continue
    for pn, p in sorted(d["pages"].items(), key=lambda x: int(x[0])):
        for f in ("identity", "revision", "decision"):
            x = p[f]
            rows.append({"pool_id": pid, "ep": d["ep"], "page": pn, "page_render": f"{RD}/{pid}-p{pn}.png", "page_role": p.get("page_role", ""), "field": f,
                         "draft_state": x["state"], "draft_literal": x.get("literal", "") if f != "revision" or x["state"] != "ambiguous" else "",
                         "draft_candidates": json.dumps(x.get("candidates"), ensure_ascii=False) if x.get("candidates") else "",
                         "draft_class": x.get("class", ""), "draft_absent_kind": x.get("absent_kind", ""), "draft_printed_label": x.get("printed_label", ""),
                         "draft_semantic_role": x.get("semantic_role", ""), "draft_association": x.get("association", ""), "draft_actor": x.get("actor", ""),
                         "draft_region_display_fraction": json.dumps(x.get("region")) if x.get("region") else "", "evidence": ev_paths(x.get("evidence")),
                         "draft_notes": " | ".join(str(x.get(k)) for k in ("value_note", "association_note", "note") if x.get(k)),
                         "reviewer_ruling": "", "reviewer_state": "", "reviewer_literal": "", "reviewer_class": "", "reviewer_association": "", "reviewer_note": ""})
    for f in ("identity", "revision", "decision"):
        pages = [pn for pn, p in d["pages"].items() if p[f]["state"] == "present" and p[f].get("association") == "resolved"]
        drows.append({"pool_id": pid, "ep": d["ep"], "stratum": SEL[pid]["stratum"], "field": f, "draft_carries_fact": "yes" if pages else "no",
                      "draft_pages_present_resolved": " ".join(pages), "draft_document_confidence": d.get("confidence"),
                      "draft_unresolved": " | ".join(d.get("unresolved") or []),
                      "reviewer_field_resolved_for_scoring": "", "reviewer_carries_fact": "", "reviewer_note": ""})
    for u in d.get("unresolved") or []:
        questions.append({"pool_id": pid, "question": u, "draft": "see the draft fields"})
    if d.get("content_duplicate_of"):
        questions.append({"pool_id": pid, "question": f"content duplicate of {d['content_duplicate_of']['pool_id']} (not byte-identical): count once or twice?", "draft": "flagged only"})
with open(HERE / "review" / "PAGE-FIELD-WORKLIST.csv", "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
with open(HERE / "review" / "DOCUMENT-FIELD-WORKLIST.csv", "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=list(drows[0]))
    w.writeheader()
    w.writerows(drows)
(HERE / "review" / "DOCUMENT-QUESTIONS.json").write_text(json.dumps({"draft_sha256": DRAFT_SHA, "questions": questions}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
template = {"review_of": {"draft_version": D["version"], "draft_sha256": DRAFT_SHA}, "reviewer": "", "review_kind": "owner-delegated independent AI review (Codex reviewer); NOT human sign-off unless a named human signs",
            "independent_of_drafter": True, "predictions_consulted": False, "completed_at_utc": "",
            "page_field_rulings": [{"pool_id": "", "page": "", "field": "", "ruling": "accept | correct | reject", "state": "", "literal": "", "class": "", "association": "", "note": ""}],
            "document_field_rulings": [{"pool_id": "", "field": "", "resolved_for_scoring": "yes | no", "carries_fact": "yes | no", "note": ""}],
            "document_questions": [{"pool_id": "", "question": "", "ruling": ""}],
            "convention_rulings": [{"topic": "e.g. class of 'Approved as noted / Resubmit', authority approvals, compilation files", "ruling": ""}]}
(HERE / "review" / "REVIEWER-RESPONSE-TEMPLATE.json").write_text(json.dumps(template, indent=1) + "\n", encoding="utf-8")
crops = [json.loads(l) for l in (HERE / "CROPS.jsonl").read_text(encoding="utf-8").splitlines()]
idx = {"recipes": {"render": json.loads((HERE / "RENDERS.json").read_text(encoding="utf-8"))["recipe"], "crop": "CROP-R32-1 (crop_r32.py): region in fractions of the displayed page, rendered from the hash-checked staged bytes, long side px, optional rotation of the PNG only"},
       "renders": [{"pool_id": pid, "page": r["page"], "path": f"{RD}/{r['png']}", "sha256": r["png_sha256"], "staged_sha256": R[pid]["staged_sha256"], "text_layer": f"{RD}/{pid}-p{r['page']}.txt", "text_sha256": r["txt_sha256"]}
                   for pid in sorted(R) for r in R[pid]["rendered"]],
       "crops": [{**c, "path": f"{CD}/{c['png']}"} for c in crops],
       "staged_files": "C:/t/r2x/r32-stage/files/<pool id>.pdf (SOURCE-MANIFEST.json)",
       "note": "images are kept in the isolated staging area (about 143 MB) and bound by sha256; the package checker re-hashes every one"}
(HERE / "EVIDENCE-INDEX.json").write_text(json.dumps(idx, indent=1) + "\n", encoding="utf-8")
print(len(rows), "page-field rows;", len(drows), "document-field rows;", len(questions), "questions;", len(idx["renders"]), "renders;", len(idx["crops"]), "crops")
