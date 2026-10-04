"""R14-03: the AI source review (M2-review-14/AI-SOURCE-REVIEW.json, 43 units) materialized as a VERSIONED label
amendment, `r14.1`. Nothing earlier is overwritten: the original proposal labels, GOLDEN-LABELS, the v2 page labels,
the holdout labels, HOLDOUT-BOQ-LABELS and packet v2 stay byte-for-byte; amended COPIES are written under
C:/t/iso/work/r2x/labels/r14/ with a change list, and every unit carries:
  original label, reviewer observations, status, disposition, source document + sha256, page, image sha256 + binding
  result (BINDING.json), field role, target / association, reviewer type (AI), uncertainty, and the effect applied.
Provenance: owner-delegated independent AI review (Codex); NOT a human signature, NOT blind to earlier predictions.
Human signature fields stay empty. A unit whose image is not bound to its source page is NOT applied (held as a
binding defect). Holds stay holds: PARTIAL_HELD / ROLE_HELD / ASSOCIATION_HELD / CONFLICT_HELD never become answers.
Usage: build_amendment.py (reads BINDING-REGEN.json, LITERAL-CHECK.json)"""
import copy
import datetime
import hashlib
import json
import pathlib

R = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-14")
P = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
W = pathlib.Path("C:/t/iso/work/r2x")
OUT = W / "labels/r14"
OUT.mkdir(parents=True, exist_ok=True)
VERSION = "r14.1"
sha_b = lambda b: hashlib.sha256(b).hexdigest()
sha = lambda p: sha_b(pathlib.Path(p).read_bytes())

review_path = R / "AI-SOURCE-REVIEW.json"
review = json.loads(review_path.read_text(encoding="utf-8"))
binding = json.loads((W / "r14/BINDING-REGEN.json").read_text(encoding="utf-8"))   # method 2 (regeneration), method 1 for packet pages
bound_by_unit = {}
for b in binding["results"]:
    bound_by_unit.setdefault(b["unit"], []).append(b)

SRC = {"GOLD": P / "GOLDEN-LABELS.json", "PAGES": P / "review05/labels/GOLDEN-LABELS-v2-PAGES.json",
       "HOLD": P / "review05/holdout/HOLDOUT-LABELS.json", "HOLD_PAGES": P / "review05/holdout/HOLDOUT-PAGE-LABELS.json",
       "BOQ": P / "review05/holdout/HOLDOUT-BOQ-LABELS.json", "SMALL": W / "labels/SMALL-BATCH-LABELS.json",
       "SMALL_EVAL": W / "labels/SMALL-BATCH-LABELS.eval.json"}
src_sha = {k: sha(v) for k, v in SRC.items()}
data = {k: json.loads(v.read_text(encoding="utf-8")) for k, v in SRC.items()}
amended = {k: copy.deepcopy(v) for k, v in data.items()}
changes = []

PROV = {"reviewer": "Codex (independent AI reviewer)", "reviewer_type": "AI", "review_id": review["review_id"],
        "review_file_sha256": sha(review_path), "reviewed_at_utc": review["reviewed_at_utc"],
        "not": ["a human signature", "blind to earlier predictions"], "human_signature": None}


def gold_doc(doc):
    for k in ("GOLD", "HOLD"):
        for d in amended[k]["documents"]:
            if d["doc"].replace("\\", "/") == doc:
                return k, d
    return None, None


def page_doc(doc):
    for k in ("PAGES", "HOLD_PAGES"):
        for key, v in amended[k]["documents"].items():
            if key.replace("\\", "/") == doc:
                return k, key, v
    return None, None, None


def set_gold(unit, doc, field, new, why):
    k, d = gold_doc(doc)
    old = d["labels"].get(field)
    d["labels"][field] = new
    d["labels"].setdefault("r14_review", []).append({"unit": unit, "field": field, "old": old, "new": new, **PROV})
    changes.append({"unit": unit, "file": k, "doc": doc, "field": field, "old": old, "new": new, "why": why})


def set_page_record(unit, doc, page, record, why, drop_no_record=True):
    k, key, v = page_doc(doc)
    if v is None:
        k = "HOLD_PAGES" if gold_doc(doc)[0] == "HOLD" else "PAGES"
        key = doc
        v = amended[k]["documents"].setdefault(key, {"records": [], "no_record_pages": {}})
    old = [r for r in v["records"] if r["page"] == page]
    v["records"] = [r for r in v["records"] if r["page"] != page] + [dict(record, r14_review={"unit": unit, **PROV})]
    v["records"].sort(key=lambda r: r["page"])
    old_nr = (v.get("no_record_pages") or {}).pop(str(page), None) if drop_no_record else None
    changes.append({"unit": unit, "file": k, "doc": doc, "page": page, "old_records": old, "old_no_record": old_nr, "new_record": record, "why": why})


def patch_page_record(unit, doc, page, patch, why):
    k, key, v = page_doc(doc)
    rec = [r for r in v["records"] if r["page"] == page][0]
    old = {f: rec.get(f) for f in patch}
    rec.update(patch)
    rec.setdefault("r14_review", []).append({"unit": unit, **PROV})
    changes.append({"unit": unit, "file": k, "doc": doc, "page": page, "old": old, "new": patch, "why": why})


def small_doc(tag):
    for key, d in amended["SMALL_EVAL"]["documents"].items():
        if d["sha256"].startswith(tag):
            return key, d
    raise KeyError(tag)


def support(unit, tag, page, obs, why):
    key, d = small_doc(tag)
    d.setdefault("supported_observations", {}).setdefault(str(page), []).append(dict(obs, r14_review={"unit": unit, **PROV}))
    changes.append({"unit": unit, "file": "SMALL", "doc": key, "page": page, "supported_observation": obs, "why": why})


# --- the effect of each ruling (source-backed; holds stay holds) --------------------------------------------------------
def apply(a):
    u, doc, o = a["id"], a["worklist_entry"].get("doc", "").replace("\\", "/"), a["observations"]
    if u == "F01/C0073":
        set_gold(u, doc, "reference", "B2312982", "ROLE_SPLIT: the permit number is the permit's own identity; footer REQ-2387569-2 kept as a request reference")
        set_gold(u, doc, "identities", [{"literal": "B2312982", "role": "own_document"}, {"literal": "REQ-2387569-2", "role": "request (footer reference)"}], "typed identities")
        return "applied (role split)"
    if u == "F02/C0083":
        patch_page_record(u, doc, 3, {"decision": "ANN", "decision_actor": "consultant (LACASA)",
                                      "decision_evidence": "Code B 'Approved as Noted' marked and signed on the consultant stamp (AI source review)"},
                          "LABEL_CORRECTION: the printed sheet 25H-AAEM-SD-ELEC-FA-B1-003A rev 03 carries a marked Code B; the decision is not transferred to other numbers")
        return "applied (decision for the printed sheet only)"
    if u == "F04/C0261":
        set_gold(u, doc, "reference", "LPOD-1856000229", "LABEL_CORRECTION: purchase order literal")
        set_gold(u, doc, "identities", [{"literal": "LPOD-1856000229", "role": "own_document (purchase order)"},
                                        {"literal": "LPRR-1856000239", "role": "request (purchase request)"}], "typed identities")
        return "applied"
    if u == "F05/C0191":
        set_gold(u, doc, "reference", "EP-19977-R3", "LABEL_CORRECTION: the quotation's own Reference; drawing numbers in the scope are referenced drawings")
        set_gold(u, doc, "revision", "R3", "the embedded suffix of the printed reference (declared typed normalization, evaluator suffix rule)")
        return "applied"
    if u == "F06/C0193":
        set_gold(u, doc, "reference", "EP-19977-R4-BD", "LABEL_CORRECTION: 'Our Ref.' wraps after R4- and continues BD")
        set_gold(u, doc, "revision", "ambiguous", "the review corrects the reference only; whether R4 alone is the revision is not ruled -> held (unscorable)")
        return "applied (revision held)"
    if u.startswith("F07/"):
        set_gold(u, doc, "reference", o["mail_number"], "ROLE_SPLIT: the mail number identifies this mail")
        set_gold(u, doc, "identities", [{"literal": o["mail_number"], "role": "own_document (mail number)"},
                                        {"literal": o["reference_number"], "role": "linked reference (other workflow / transmittal)"}], "typed identities")
        return "applied (role split)"
    if u == "F08/C0159":
        set_page_record(u, doc, 1, {"page": 1, "component": "cover", "category": "submittals", "reference": "EP-26369/SS/FA/101", "printed_revision": "01",
                                    "decision": "n/a", "decision_actor": None, "decision_evidence": None, "register": False, "confidence": "high",
                                    "note": "own printed document-number and revision fields; a source component, not a second business record"},
                        "LABEL_CORRECTION: the cover's own fields are source observations")
        return "applied (register False)"
    if u == "F09/C0034":
        set_page_record(u, doc, 3, {"page": 3, "component": "cover", "category": "submittals", "reference": "EP-30627/SS/EML/ 1293", "printed_revision": "00",
                                    "decision": "n/a", "decision_actor": None, "decision_evidence": None, "register": False, "confidence": "high",
                                    "association": "HELD: header prints EP-30784 BINGHATTI SKYBLADE, the number prints EP-30627 -- a source conflict; "
                                                   "no project / business association approved"},
                        "CONFLICT_HELD: both literals are printed; the literal is a source fact, its business association is held")
        return "applied (literal as source fact; association held; register False)"
    if u == "F10/C0245":
        set_gold(u, doc, "reference", "ambiguous", "PARTIAL_HELD: candidate 10789-CSCEC-OUT-L0749-O-20250403-KUW with an unclear glyph; not a usable key")
        set_gold(u, doc, "reference_candidate", o["reference_candidate"], "held candidate (not scored)")
        return "applied as HOLD (unscorable)"
    if u == "F12/C0282":
        patch_page_record(u, doc, 1, {"reference": "CRS-DOC-02006",
                                      "identities": [{"literal": "CRS-DOC-02006", "role": "own_document (review form)"},
                                                     {"literal": "CDS-DOC-01943", "role": "submitted reference"},
                                                     {"literal": "D15015-0200S-FS-EL-MS-0022", "role": "reviewed document"}]},
                          "ROLE_SPLIT: the review form's own identity is CRS-DOC-02006; the decision field is not re-ruled by this review")
        set_gold(u, doc, "reference", "CRS-DOC-02006", "ROLE_SPLIT (document-level copy)")
        return "applied (decision unchanged, not re-reviewed)"
    if u == "F13/C0283":
        set_page_record(u, doc, 1, {"page": 1, "component": "letter", "category": "correspondence", "reference": "BSS/AE/ALARABIA/170315-047",
                                    "printed_revision": "absent", "decision": "n/a", "decision_actor": None, "register": False, "confidence": "high",
                                    "note": "manufacturer letter (Bosch, 17 March 2015); a manufacturer statement is not a consultant approval"},
                        "LABEL_CORRECTION: the letter's own reference")
        set_gold(u, doc, "reference", "BSS/AE/ALARABIA/170315-047", "document-level copy")
        return "applied (register False)"
    if u.startswith("F11/") or u == "F03/C0049":
        return "confirmed (no change)"
    if u.startswith("H06/"):
        return "confirmed (BOQ label unchanged; review recorded)"
    if u == "SB/535ffbdabfcf/u1":
        support(u, "535ffbdabfcf", 1, {"field": "revision", "literal": "Rev.0", "normalized": "0", "role": "revision", "target": None,
                                       "association": "HELD: no supported target (Submittal No. prints no identity)"}, "CONFIRMED: identity absent; revision literal real")
        return "applied (supported observation; no target)"
    if u in ("SB/0c9737211762/u2", "SB/0c9737211762/u3", "SB/bdce7913eb15/u4") or u.startswith("SAMPLE/"):
        return "confirmed (no change)"
    if u == "SB/bdce7913eb15/u5":
        key, d = small_doc("bdce7913eb15")
        row = d["boq_rows"][2]
        changes.append({"unit": u, "file": "SMALL", "doc": key, "boq_row": 3, "old": dict(row), "new_state": "part ambiguous (I/1)"})
        row["part_state"] = "ambiguous"
        row["part_candidates"] = ["SL2-42D3D-CGL-M +SL23I", "SL2-42D3D-CGL-M +SL231"]
        row["r14_review"] = {"unit": u, **PROV}
        return "applied as HOLD (part ambiguous; quantity 10 kept)"
    if u in ("SB/d8ba80a74660/u6", "CRIT/5"):
        if u == "SB/d8ba80a74660/u6":
            for pg in (1, 2):
                support(u, "d8ba80a74660", pg, {"field": "identity", "literal": "P06/TRANS/R1", "role": "footer / control-code candidate (HELD)",
                                                "target": None, "association": "HELD: not established as a unique document identity"}, "ROLE_HELD")
        return "applied as HOLD (footer evidence; not an identity)"
    if u in ("SB/2472d2cc65c3/u7", "CRIT/3"):
        if u == "CRIT/3":
            support(u, "2472d2cc65c3", 2, {"field": "revision", "literal": "00", "normalized": "00", "role": "revision (Document History)", "target": None,
                                           "association": "PROPOSAL (not accepted): the page-1 component DCH-M-MHT-CAL-IFC-ELE-0001-00, under the "
                                                          "component-association contract; no register-recovery credit"}, "LABEL_SCOPE_CORRECTION")
        return "applied (supported observation; association proposal)"
    if u in ("CRIT/1", "CRIT/4"):
        support(u, "535ffbdabfcf", {"CRIT/1": 3, "CRIT/4": 2}[u], {"field": "revision", "literal": "Rev.0", "normalized": "0", "role": "revision", "target": None,
                                                                     "association": "HELD: no supported target"}, "ASSOCIATION_HELD")
        return "applied (supported observation; no target)"
    if u == "CRIT/2":
        support(u, "535ffbdabfcf", 4, {"field": "revision", "literal": "Rev.0", "normalized": "0", "role": "revision", "target": None,
                                       "association": "HELD: no supported target", "not_valid_as": "identity"}, "CONFIRMED_READER_ERROR: Rev.0 is not an identity")
        return "applied (reader error confirmed; literal kept as revision evidence)"
    raise KeyError(u)


literal_check = {(x["unit"], x["literal"]): x["text_layer"] for x in json.loads((W / "r14/LITERAL-CHECK.json").read_text(encoding="utf-8"))}
LITERAL_NOTES = {"F11/C0226": "the reviewer's literal 'R1029-07-W&A-DWG-TYP-GRO-INT9011-01' lacks one hyphen; the PDF text layer carries '-GRO-INT-' + "
                              "'9011-01' (overlapping glyphs in the image). The label literal R1029-07-W&A-DWG-TYP-GRO-INT-9011-01 is kept; noted, not applied."}
units = []
for a in review["answers"]:
    b = bound_by_unit.get(a["id"], [])
    all_bound = bool(b) and all(x["bound"] for x in b)
    any_bound = any(x["bound"] for x in b)
    effect = apply(a) if any_bound else "NOT APPLIED: no evidence image bound to the claimed source page (binding defect)"
    w = a["worklist_entry"]
    units.append({"unit": a["id"], "status": a["status"], "doc": w.get("doc"), "page": w.get("page"), "original_worklist_entry": w,
                  "reviewer_observations": a["observations"], "disposition": a["disposition"], "effect": effect,
                  "binding": [{k: x.get(k) for k in ("image", "image_sha256", "doc_sha256", "page", "method", "byte_identical", "ncc", "bound")} for x in b],
                  "all_images_bound": all_bound, "literal_text_layer_checks": {lit: st for (uu, lit), st in literal_check.items() if uu == a["id"]},
                  "literal_note": LITERAL_NOTES.get(a["id"]),
                  "uncertainty": a["observations"].get("uncertainty") if isinstance(a["observations"], dict) else None,
                  "held": a["status"] in ("PARTIAL_HELD", "ROLE_HELD", "ASSOCIATION_HELD", "CONFLICT_HELD"), **PROV})

# BOQ amended copy: the reviewed H-06 rows keep their values and gain the review record
sheet = [s for s in amended["BOQ"]["boq_design_sheets"]["sheets"] if s["ep"] == "8430"][0]
H06 = {"H06/H06-1": ("Numeric Keypad", "1", 0), "H06/H06-2": ("CD Changer", "1", 0), "H06/H06-3": ("Printer", "1", 0), "H06/H06-control": ("Numeric Keypad", "2", 1)}
for uid, (desc, qty, occurrence) in H06.items():
    rows = [r for r in sheet["rows"] if r.get("description") == desc and r.get("kind") == "line"]
    r = rows[occurrence]
    assert r["quantity"] == qty, (uid, r)
    r["r14_review"] = {"unit": uid, "confirmed_quantity": qty, **PROV}
boq_out = {"labels_version": f"boq-{VERSION}", "derived_from": {"file": str(SRC["BOQ"]), "sha256": src_sha["BOQ"]}, "sheets": amended["BOQ"]["boq_design_sheets"]["sheets"]}

meta = {"labels_version": VERSION, "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "provenance": PROV,
        "originals_sha256": {k: {"file": str(v), "sha256": src_sha[k]} for k, v in SRC.items()}}
files = {"GOLDEN-LABELS.amended-r14.1.json": amended["GOLD"], "GOLDEN-LABELS-v2-PAGES.amended-r14.1.json": amended["PAGES"],
         "HOLDOUT-LABELS.amended-r14.1.json": amended["HOLD"], "HOLDOUT-PAGE-LABELS.amended-r14.1.json": amended["HOLD_PAGES"],
         "SMALL-BATCH-LABELS.amended-r14.1.json": amended["SMALL_EVAL"], "BOQ-LABELS.amended-r14.1.json": boq_out}
for name, obj in files.items():
    obj = dict(obj)
    obj["r14_amendment"] = meta
    (OUT / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
for k, v in SRC.items():
    assert sha(v) == src_sha[k], f"an original changed: {v}"
(OUT / "AI-REVIEW-AMENDMENT-r14.1.json").write_text(json.dumps({**meta, "units": units, "changes": changes,
                                                                "amended_files_sha256": {n: sha(OUT / n) for n in files}}, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
import collections
print("units", len(units), dict(collections.Counter(u["effect"].split(" (")[0] for u in units)))
print("changes", len(changes), "| not applied", [u["unit"] for u in units if u["effect"].startswith("NOT APPLIED")], "| partly bound", [u["unit"] for u in units if not u["all_images_bound"]])
