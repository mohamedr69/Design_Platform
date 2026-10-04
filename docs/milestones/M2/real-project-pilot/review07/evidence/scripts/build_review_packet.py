"""Review 07 (G): the human source-review packet. Pages are rendered independently from the staged originals; no
candidate prediction is shown. Proposed labels are the current Golden labels -- AI-drafted, not a human signature.
Scope (the agreed one): every decision label, every critical disagreement / adjudicated case, every ambiguous
identity / revision / part case, and a frozen seeded 20 % sample of the remaining components and BOQ rows."""
import csv
import hashlib
import json
import random
import re
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, r"C:\t\iso\ep-platform\backend")
from scripts import m2_eval4 as ev4  # noqa: E402

P = Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot")
OUT = P / "review07" / "human-review-packet"
PAGES_DIR = OUT / "pages"
PAGES_DIR.mkdir(parents=True, exist_ok=True)
SEED = "m2-review07-packet-2026-09-29"
STAGES = {"pilot": Path(r"C:\t\pilot\stage"), "holdout": Path(r"C:\t\holdout\stage")}

gold = json.load(open(P / "GOLDEN-LABELS.json", encoding="utf-8"))
gpages = json.load(open(P / "review05" / "labels" / "GOLDEN-LABELS-v2-PAGES.json", encoding="utf-8"))
hold = json.load(open(P / "review05" / "holdout" / "HOLDOUT-LABELS.json", encoding="utf-8"))
hpages = json.load(open(P / "review05" / "holdout" / "HOLDOUT-PAGE-LABELS.json", encoding="utf-8"))
adjudicated = json.load(open(r"C:\t\iso\work\r7\ADJUDICATIONS.json", encoding="utf-8"))["cases"]

# critical disagreements from the current re-scores (register / accepted / AI), all runs
critical_docs = set()
for f in Path(r"C:\t\iso\work\r7\eval5").glob("*.json"):
    if f.name == "SUMMARY.json":
        continue
    t = json.load(open(f, encoding="utf-8"))["totals"]
    for c in t["register"]["critical"]:
        critical_docs.add((c["doc"], int(c["page"])))
    for layer in ("evidence", "ai"):
        for c in t[layer]["critical"] + t[layer].get("observed_errors", []):
            critical_docs.add((c["doc"], int(c["page"] or 1)))
for c in adjudicated:
    if "*" not in c["doc"] and "(" not in c["doc"][:3]:
        critical_docs.add((c["doc"], int(c["page"])))

components = []
for cohort, labels, pages in (("pilot", gold, gpages), ("holdout", hold, hpages)):
    plab = {k.replace("\\", "/"): v for k, v in pages["documents"].items()}
    for doc in labels["documents"]:
        key = doc["doc"].replace("\\", "/")
        exp, no_record, _unval, page_labelled = ev4.expected_records(doc, plab.get(key))
        for e in exp:
            components.append({"cohort": cohort, "doc": key, "page": int(e["page"]), "component": e.get("component"),
                               "reference": e.get("reference"), "printed_revision": e.get("printed_revision"), "decision": e.get("decision"),
                               "kind": doc["labels"].get("kind"), "confidence": e.get("confidence") or doc.get("confidence"),
                               "decision_actor": e.get("decision_actor"), "decision_evidence": e.get("decision_evidence")})
        for p in sorted(no_record):
            components.append({"cohort": cohort, "doc": key, "page": int(p), "component": "no-record page", "reference": "absent",
                               "printed_revision": "absent", "decision": "n/a", "kind": doc["labels"].get("kind"),
                               "confidence": doc.get("confidence"), "no_record_page": True})

AMBIGUOUS = re.compile(r"unknown|illegible|ambiguous|unclear|unlabel|\?", re.I)
rng = random.Random(SEED)
items = []
for c in components:
    reasons = []
    dstate, _ = ev4.decision_truth(c["decision"])
    if dstate in ("readable", "conflict") or re.search(r"form|reply|comment|review|transmittal", str(c["kind"] or ""), re.I):
        reasons.append("decision label")
    if (c["doc"], c["page"]) in critical_docs:
        reasons.append("critical disagreement / adjudicated case")
    if str(c["confidence"]) not in ("high",) or any(AMBIGUOUS.search(str(c.get(f) or "")) for f in ("reference", "printed_revision", "decision")):
        reasons.append("ambiguous or low-confidence label")
    c["scope"] = reasons
items_required = [c for c in components if c["scope"]]
remainder = sorted([c for c in components if not c["scope"]], key=lambda c: (c["doc"], c["page"], str(c["component"])))
sample = rng.sample(remainder, k=round(0.2 * len(remainder)))
for c in sample:
    c["scope"] = ["frozen 20 % sample"]
selected = items_required + sorted(sample, key=lambda c: (c["doc"], c["page"]))

# BOQ rows: every ambiguous / heading-or-component / critical row, plus a frozen 20 % of the rest
boq_items = []
boq_critical = {("30088", "PT-1S+"), ("30088", "4-FWAL4"), ("30088", "SIGA-IB"), ("14119", "SIGA-AA50"), ("26082", "PT-1S+"), ("8430", "PRS-CSNKP")}
for cohort, sheets in (("pilot", gold["boq_design_sheets"]["sheets"]),
                       ("holdout", json.load(open(P / "review05" / "holdout" / "HOLDOUT-BOQ-LABELS.json", encoding="utf-8"))["boq_design_sheets"]["sheets"])):
    for s in sheets:
        for i, r in enumerate(s["rows"]):
            reasons = []
            if (s["ep"], r.get("part_number")) in boq_critical or (s["ep"] == "8430" and r.get("quantity") in ("1", "2")):
                reasons.append("critical disagreement (deterministic reader)")
            if r.get("kind") == "component-or-heading" or AMBIGUOUS.search(str(r.get("note") or "")) or AMBIGUOUS.search(str(r.get("part_number") or "")):
                reasons.append("ambiguous part / row")
            boq_items.append({"cohort": cohort, "ep": s["ep"], "doc": f"EP-{s['ep']}/{s['relative_path']}".replace("\\", "/"), "page": int(r.get("page") or 1),
                              "row": i, "kind": r.get("kind"), "part_number": r.get("part_number"), "quantity": r.get("quantity"),
                              "description": r.get("description"), "note": r.get("note"), "scope": reasons})
boq_required = [b for b in boq_items if b["scope"]]
boq_rest = [b for b in boq_items if not b["scope"] and b["kind"] in ("line", "component")]
for b in random.Random(SEED + ":boq").sample(boq_rest, k=round(0.2 * len(boq_rest))):
    b["scope"] = ["frozen 20 % sample"]
boq_selected = [b for b in boq_items if b["scope"]]

# render every page the selection needs, from the staged originals (never from a candidate output)
rendered = {}
manifest = {}


def render(doc: str, page: int, cohort: str) -> str:
    key = (doc, page)
    if key in rendered:
        return rendered[key]
    src = STAGES[cohort] / doc
    name = hashlib.sha256(f"{doc}|{page}".encode()).hexdigest()[:16] + f"-p{page}.jpg"
    try:
        with pymupdf.open(src) as d:
            if page > d.page_count:
                rendered[key] = "page not in file"
                return rendered[key]
            pg = d[page - 1]
            zoom = min(110 / 72, 2200 / max(pg.rect.width, pg.rect.height))
            pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(PAGES_DIR / name, jpg_quality=72)
        manifest[doc] = hashlib.sha256(src.read_bytes()).hexdigest()
        rendered[key] = f"pages/{name}"
    except Exception as exc:  # noqa: BLE001 -- a Word transmittal or an unreadable original: reviewed from the file
        rendered[key] = f"open the original ({type(exc).__name__})"
        if src.exists():
            manifest[doc] = hashlib.sha256(src.read_bytes()).hexdigest()
    return rendered[key]


FIELDS = ["item", "cohort", "scope", "doc", "page", "page_image", "component", "proposed_reference", "proposed_printed_revision",
          "proposed_decision", "proposed_decision_actor", "proposed_label_confidence", "label_origin",
          "human_reference", "human_printed_revision", "human_decision", "human_decision_actor", "human_uncertainty",
          "human_reviewer", "human_date", "human_notes"]
with open(OUT / "COMPONENT-ITEMS.csv", "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    w.writeheader()
    for n, c in enumerate(selected, 1):
        w.writerow({"item": f"C{n:04d}", "cohort": c["cohort"], "scope": "; ".join(c["scope"]), "doc": c["doc"], "page": c["page"],
                    "page_image": render(c["doc"], c["page"], c["cohort"]), "component": c["component"],
                    "proposed_reference": c["reference"], "proposed_printed_revision": c["printed_revision"], "proposed_decision": c["decision"],
                    "proposed_decision_actor": c.get("decision_actor") or "", "proposed_label_confidence": c["confidence"],
                    "label_origin": "AI-drafted Golden label (v1 / v2 page labels) -- not a human signature"})
BOQ_FIELDS = ["item", "cohort", "scope", "doc", "page", "page_image", "row", "kind", "proposed_part_number", "proposed_quantity",
              "proposed_description", "label_note", "label_origin", "human_part_number", "human_quantity", "human_kind", "human_uncertainty",
              "human_reviewer", "human_date", "human_notes"]
with open(OUT / "BOQ-ITEMS.csv", "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=BOQ_FIELDS)
    w.writeheader()
    for n, b in enumerate(boq_selected, 1):
        w.writerow({"item": f"B{n:04d}", "cohort": b["cohort"], "scope": "; ".join(b["scope"]), "doc": b["doc"], "page": b["page"],
                    "page_image": render(b["doc"], b["page"], b["cohort"]), "row": b["row"], "kind": b["kind"],
                    "proposed_part_number": b["part_number"], "proposed_quantity": b["quantity"], "proposed_description": b["description"],
                    "label_note": b.get("note") or "", "label_origin": "AI-drafted Golden BOQ label -- not a human signature"})
summary = {"seed": SEED, "components_total": len(components), "components_selected": len(selected),
           "components_by_scope": {k: sum(1 for c in selected if k in c["scope"]) for k in
                                   ("decision label", "critical disagreement / adjudicated case", "ambiguous or low-confidence label", "frozen 20 % sample")},
           "boq_rows_total": len(boq_items), "boq_rows_selected": len(boq_selected),
           "boq_by_scope": {k: sum(1 for b in boq_selected if k in b["scope"]) for k in
                            ("critical disagreement (deterministic reader)", "ambiguous part / row", "frozen 20 % sample")},
           "pages_rendered": sum(1 for v in rendered.values() if v.startswith("pages/")),
           "not_rendered": sorted({f"{d} p{p}: {v}" for (d, p), v in rendered.items() if not v.startswith("pages/")}),
           "source_sha256": manifest}
json.dump(summary, open(OUT / "PACKET-MANIFEST.json", "w", encoding="utf-8"), indent=1)
print(json.dumps({k: v for k, v in summary.items() if k != "source_sha256"}, indent=1))
