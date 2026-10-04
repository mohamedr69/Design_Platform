"""Assemble GOLDEN-LABELS.json from the skeleton, the per-tile label parts (labels/part-*.json, keyed by contact-sheet
tile index) and the BOQ row labels (boq_labels/*.json + the EP-30784 golden fixture). Reports what is left unlabelled."""
import json, sys, pathlib, glob, datetime, collections

S = pathlib.Path(sys.argv[1])
skel = json.load(open(S / "GOLDEN-LABELS-skeleton.json", encoding="utf-8"))
tiles = [x for x in json.load(open(S / "crops" / "index.json")) if x.get("whole")]
by_tile = {}
for p in sorted(glob.glob(str(S / "labels" / "part-*.json"))):
    for k, v in json.load(open(p, encoding="utf-8")).items():
        by_tile[int(k)] = v
doc_of_tile = {i: x["doc"] for i, x in enumerate(tiles)}
labelled = {}
for i, v in by_tile.items():
    labelled[doc_of_tile[i]] = v
for p in sorted(glob.glob(str(S / "labels" / "word-*.json"))):
    for k, v in json.load(open(p, encoding="utf-8")).items():
        if not k.startswith("_"): labelled[k] = v
FIELDS = ["kind", "reference", "revision", "date", "title", "system", "floor", "originator", "decision", "decision_candidates", "printed_project", "components"]
missing = []
sha_of = {e["doc"]: e["sha256"] for e in skel["documents"]}
twin_of = {}
for e in skel["documents"]:
    if e["doc"] not in labelled:
        twins = [d for d, v in labelled.items() if sha_of.get(d) == e["sha256"] and d != e["doc"]]
        if twins: twin_of[e["doc"]] = twins[0]
for e in skel["documents"]:
    lab = labelled.get(e["doc"])
    if lab is None and e["doc"] in twin_of:
        lab = dict(labelled[twin_of[e["doc"]]]); lab["notes"] = (lab.get("notes", "") + f" | the same bytes as {twin_of[e['doc']]} (duplicate content): labels copied from that document's render").strip(" |")
    if lab is None:
        if e["extension"] == ".doc" and e["doc"] not in labelled:
            e["labels"]["kind"] = "Word transmittal (not rendered; the reader's transmittal path applies)"; e["confidence"] = "unlabelled"; e["notes"] = (e["notes"] or "") + " Word file: no page render, header fields unlabelled"
        elif e["expected_eligibility"] == "unreadable":
            e["confidence"] = "n/a (unreadable original)"
        else:
            missing.append(e["doc"])
        continue
    for f in FIELDS:
        if f in lab:
            e["labels"][f] = lab[f]
    for extra in ("consultant_date",):
        if extra in lab: e["labels"][extra] = lab[extra]
    e["confidence"] = lab.get("confidence", "unlabelled"); e["notes"] = lab.get("notes", "")
    tile_ids = [i for i, d in doc_of_tile.items() if d == e['doc']] or [i for i, d in doc_of_tile.items() if d == twin_of.get(e['doc'])]
    if e["extension"] == ".doc":
        e["labelled_from"] = "Word document text and tables (Word 16.0 automation)"; continue
    e["labelled_from"] = "contact sheet (page 1 whole + cue bands)" + (" + title-block strip" if tile_ids and (S / "tb" / f"{tile_ids[0]}-strip.png").is_file() else "") + (" (via duplicate-content twin)" if e["doc"] in twin_of else "")
skel["labeller"] = "Claude (Fable 5.1), from renders of the staged originals (contact sheets of page 1 and its cue bands; title-block strips for drawing-sized sheets; full pages for the BOQ set). No reader output was consulted while labelling. Owner to countersign; no countersignature is claimed."
skel["at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
# BOQ rows
boq = {"labeller": skel["labeller"], "sheets": []}
for p in sorted(glob.glob(str(S / "boq_labels" / "*.json"))):
    boq["sheets"].extend(json.load(open(p, encoding="utf-8"))["sheets"])
golden = json.load(open(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend\tests\fixtures\boq_ep30784_golden_v1.json", encoding="utf-8"))
fb = json.load(open(S / "FROZEN-BOQ-SET.json", encoding="utf-8"))
for sheet in fb["sheets"]:
    if sheet["ep"] == "30784":
        code = "FAS" if "FAS" in sheet["relative_path"] else "EML"
        rows = [r for r in golden["rows"] if r["system_code"] == code]
        boq["sheets"].append({"ep": "30784", "sha256_prefix": sheet["sha256"][:12], "relative_path": sheet["relative_path"], "system": code, "pages": sheet.get("pages"),
                              "source": "backend/tests/fixtures/boq_ep30784_golden_v1.json (transcribed 2026-09-27 for the BOQ V2 work; owner countersignature pending)",
                              "rows": [{"page": r["page"], "kind": "line" if r.get("part_number") else "component-or-heading", "group": r.get("group"), "quantity": r.get("quantity"), "part_number": r.get("part_number"), "description": r.get("description")} for r in rows],
                              "confidence": "high", "notes": "reused golden rows; row kinds not re-derived here"})
shas = {s["sha256"][:12]: s for s in fb["sheets"]}
for s in boq["sheets"]:
    src = shas.get(s["sha256_prefix"]); s["sha256"] = src["sha256"] if src else None; s["cohort"] = src["cohort"] if src else None
    s["row_count"] = len(s["rows"]); s["rows_with_quantity"] = sum(1 for r in s["rows"] if r.get("quantity") not in (None, "") and not str(r.get("quantity")).startswith("absent"))
skel["boq_design_sheets"] = boq
json.dump(skel, open(S / "GOLDEN-LABELS.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
docs = skel["documents"]
print("documents", len(docs), "labelled", sum(1 for d in docs if d["confidence"] not in ("unlabelled",)), "missing", len(missing), missing[:10])
print("confidence", collections.Counter(d["confidence"] for d in docs))
print("decisions", collections.Counter(str(d["labels"]["decision"])[:12] for d in docs).most_common(12))
print("boq sheets", len(boq["sheets"]), "rows", sum(s["row_count"] for s in boq["sheets"]), "projects", len({s["ep"] for s in boq["sheets"]}))
