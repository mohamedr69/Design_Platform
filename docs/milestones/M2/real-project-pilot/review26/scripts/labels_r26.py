"""Assemble the R26 reference labels (version r26-labels-2026-10-01.1) from the per-document drafts (drafts/Dnn.json) into
the evaluator's shapes, BESIDE the untouched R21 skeletons (review21/labels-r21) and the earlier label packets:
  labels-r26/R26-REGISTER-LABELS.json         register layer (one entry per planned document, all 27)
  labels-r26/R26-PAGE-LABELS.json             page layer (every in-scope page of every PDF; .doc control register-only)
  labels-r26/R26-UNCERTAINTY-AND-EXPOSURE.json genuine uncertainty (docs excluded from the critical tripwire by the runner's
                                               predeclared rule), labelling conventions, exposure, off-title-block outcome
  labels-r26/R26-LABEL-EVIDENCE.json          per page: source sha256, render sha256, crop hashes, regions, text-layer checks
  labels-r26/R26-REVIEW-PASS.json             the second pass (same assistant, NOT independent) and its outcome
  labels-r26/LABEL-MANIFEST.r26.json          workflow status, provenance, hashes of the files above (written last)
No prediction exists for any of these documents; no model / provider request was made; nothing is filled from file names."""
import datetime
import hashlib
import json
import pathlib
import re

R = pathlib.Path(__file__).resolve().parent
OUT = R / "labels-r26"
OUT.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
R21 = pathlib.Path("C:/t/iso/work/r2x/review21")
skel_reg = {d["doc"]: d for d in json.loads((R21 / "labels-r21/R21-REGISTER-LABELS.json").read_text(encoding="utf-8"))["documents"]}
skel_pg = json.loads((R21 / "labels-r21/R21-PAGE-LABELS.json").read_text(encoding="utf-8"))["documents"]
exposure_r21 = json.loads((R21 / "labels-r21/EXPOSURE.json").read_text(encoding="utf-8"))["documents"]
renders = {d["id"]: d for d in json.loads((R / "renders/RENDERS.json").read_text(encoding="utf-8"))["documents"]}
crops = [json.loads(l) for l in (R / "renders/crops/CROPS.jsonl").read_text(encoding="utf-8").splitlines()]
sample_sha = json.loads((R21 / "labels-r21/R21-REGISTER-LABELS.json").read_text(encoding="utf-8"))["sample_sha256"]
VERSION = "r26-labels-2026-10-01.1"
PROV = {"drafted_by": "AI (Claude Opus 5.5 coding assistant, this session) from local renders and text layers of the hash-checked staged copies",
        "reviewed_by": "the same assistant, second pass (re-inspection of every decision, every rotated / scanned item and a seeded 25 % subset); NOT an independent review",
        "human_signoff": "none", "blind": "no (the labeller saw no prediction; none exists for these documents)", "model_requests": 0}
STATUS = ("AI-DRAFTED AND SAME-ASSISTANT SECOND-PASS CHECKED reference labels, FROZEN before any prediction; not human-signed, not blind, "
          "not independently reviewed (R21 label-manifest step 4 independence NOT met)")
GENUINE = {"D03", "D08", "D11", "D12", "D15", "D21", "D24", "D25", "D26", "D27"}   # truth-relevant uncertainty -> medium confidence

reg_docs, pg_docs, evid, unc, conv, otb = [], {}, {}, [], [], []
for did in sorted(renders):
    d = json.loads((R / "drafts" / f"{did}.json").read_text(encoding="utf-8"))
    meta = renders[did]
    sk = skel_reg[meta["doc"]]
    assert sk["sha256"] == meta["sha256"]
    conf = d["confidence"]
    assert (conf != "high") == (did in GENUINE), (did, conf)
    reg_docs.append({"doc": meta["doc"], "ep": sk["ep"], "cohort": sk["cohort"], "stratum": sk["stratum"], "extension": sk["extension"], "sha256": meta["sha256"],
                     "role": sk["role"], "confidence": conf, "labels": d["register"], "label_source": VERSION, "provenance": PROV, "draft_id": did})
    if not d.get("register_only"):
        records, no_record = [], {}
        for pno, pg in sorted(d["pages"].items(), key=lambda x: int(x[0])):
            if "no_record" in pg:
                no_record[pno] = pg["no_record"]
            for r in pg.get("records") or []:
                records.append({k: v for k, v in r.items() if k != "evidence"})
                evid[f"{meta['doc']}#p{pno}"] = {**r["evidence"], "source_sha256": meta["sha256"],
                                                  "render": next(x for x in meta["rendered"] if x["page"] == int(pno)),
                                                  "crop_hashes": {c["png"]: c["sha256"] for c in crops if c["id"] == did and c["page"] == int(pno)}}
        labelled = sorted(int(p) for p in d["pages"])
        expected = skel_pg[meta["doc"]]["pages_to_label"]
        assert labelled == expected, (did, labelled, expected)
        pg_docs[meta["doc"]] = {"doc": meta["doc"], "sha256": meta["sha256"], "stratum": sk["stratum"], "records": records, "no_record_pages": no_record,
                                "unvalidated_pages": [], "unresolved": [], "pages_labelled": labelled,
                                "pages_beyond_reader_scope": d.get("pages_beyond_reader_scope") or skel_pg[meta["doc"]]["pages_beyond_reader_scope"],
                                "label_source": VERSION}
    for u in d.get("uncertainty") or []:
        (unc if did in GENUINE else conv).append({"doc": meta["doc"], "draft_id": did, **u})
    if did == "D17":
        conv.append({"doc": meta["doc"], "draft_id": did, "field": "decision_actor", "issue": "actor inferred (initials only; ATK RECEIVED stamp)", "effect": "decision value high confidence"})
    o = d["off_title_block"]
    otb.append({"doc": meta["doc"], "draft_id": did, "role": sk["role"], **o})

screened = [x for x in otb if x["screened"] and x["role"].startswith("primary")]      # the stratum concerns the 24 primary documents
confirmed = [x for x in otb if x["confirmed"] and x["role"].startswith("primary")]
off = {"rule": "R21 sample rule: >= 4 of the 24 primary documents must carry a screened candidate off-title-block decision; if labelling finds fewer than 4 confirmed, top up from the screened pool before any prediction",
       "screened_candidates_selected": [x["draft_id"] for x in screened], "screened_confirmed": [x["draft_id"] for x in screened if x["confirmed"]],
       "confirmed_off_title_block_decisions_total": [x["draft_id"] for x in confirmed],
       "projects_of_confirmed": sorted({x["doc"].split("/")[0] for x in confirmed}),
       "reading_by_purpose": f"{len(confirmed)} confirmed off-title-block consultant decisions among the 24 primary documents (>= 4): the stratum's purpose (decisions an ROI / title-block-only reader can miss) is met",
       "reading_strict": f"only {len([x for x in screened if x['confirmed']])} of the {len(screened)} screened candidates is confirmed (the text screen's hits on D01, D02, D03 were note / certificate / marketing text): a strict reading leaves a shortfall of {4 - len([x for x in screened if x['confirmed']])}",
       "top_up_performed": False,
       "why_not": "the task freezes the 27-document sample (no replacement or enlargement); the confirmed total already meets the minimum by count; the strict-reading shortfall is disclosed for the reviewer",
       "clustering": "3 of the confirmed decisions (D16, D17, D18) come from one project (EP-19144) and one consultant (ATK); per-project clustering is kept in the analysis (document-clustered bootstrap)",
       "documents": otb}
common = {"status": STATUS, "sample_sha256": sample_sha, "labels_version": VERSION, "provenance": PROV}
REG = {**common, "documents": reg_docs}
PAGE = {**common, "documents": pg_docs, "page1_corrections": []}
exposure = [{**e, "r26_renders": "full in-scope page renders and zoom crops made for labelling in C:/t/iso/work/r2x/r26/renders (hashes in R26-LABEL-EVIDENCE.json); no prediction"} for e in exposure_r21]
UNC = {**common, "uncertainty": unc, "labelling_conventions": conv, "exposure": exposure, "off_title_block": off,
       "disagreements": [], "disagreements_note": "the second pass changed no label; no draft / review disagreement was recorded",
       "unresolved_documents": "none left blank; documents with truth-relevant uncertainty are labelled with confidence 'medium' and listed under 'uncertainty' (the runner's predeclared rule excludes them from the critical-acceptance stop)"}
EVID = {"labels_version": VERSION, "renders_manifest_sha256": sha(R / "renders/RENDERS.json"), "crops_log_sha256": sha(R / "renders/crops/CROPS.jsonl"), "pages": evid,
        "text_layer_check": "every label literal on a page with a text layer was found in that text layer (review pass); image-only pages were checked visually on zoom crops"}
files = {"R26-REGISTER-LABELS.json": REG, "R26-PAGE-LABELS.json": PAGE, "R26-UNCERTAINTY-AND-EXPOSURE.json": UNC, "R26-LABEL-EVIDENCE.json": EVID}
for n, obj in files.items():
    (OUT / n).write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
n_pages = sum(len(v["pages_labelled"]) for v in pg_docs.values())
n_records = sum(len(v["records"]) for v in pg_docs.values())
print("register docs", len(reg_docs), "| page-labelled docs", len(pg_docs), "| in-scope pages labelled", n_pages, "| records", n_records,
      "| no-record pages", sum(len(v["no_record_pages"]) for v in pg_docs.values()))
print("confidence", {c: sum(1 for d in reg_docs if d["confidence"] == c) for c in ("high", "medium")}, "| decisions", sorted({d["labels"]["decision"] for d in reg_docs}))
print("off-title-block: screened", off["screened_candidates_selected"], "confirmed of screened", off["screened_confirmed"], "| confirmed total", off["confirmed_off_title_block_decisions_total"])
