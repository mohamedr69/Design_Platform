import json, sys, pymupdf, collections
sys.path.insert(0, r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend")
from app.services import title_block as tb
from scripts import m2_pilot_eval as ev
P = r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot"
fs = json.load(open(P + r"\FROZEN-SAMPLE.json", encoding="utf-8"))
gl = {d["doc"].replace("\\", "/"): d for d in json.load(open(P + r"\GOLDEN-LABELS.json", encoding="utf-8"))["documents"]}
out = []; c = collections.Counter()
for d in fs["documents"]:
    key = f"EP-{d['ep']}/{d['relative_path']}".replace("\\", "/")
    if not key.lower().endswith(".pdf"): continue
    try: pdf = pymupdf.open(d["staged_path"])
    except Exception as e: c["open_fail"] += 1; continue
    for i in range(min(pdf.page_count, 3)):
        pg = pdf[i]
        if not tb.is_drawing_sheet(pg): continue
        c["drawing_pages"] += 1
        r = tb.read_page(pg)
        if r is None: c["no_block"] += 1; continue
        lab = gl.get(key, {}).get("labels", {}) if i == 0 else {}
        exp_ref, exp_rev = lab.get("reference"), lab.get("revision")
        row = {"doc": key, "page": i + 1, "number": r.number, "revision": r.revision, "latest": r.history_latest, "conflict": r.conflict,
               "exp_ref": exp_ref, "exp_rev": exp_rev}
        if exp_ref and r.number:
            row["ref"] = ev.judge_reference(exp_ref, r.number)
            c["ref_" + row["ref"]] += 1
        if exp_rev and r.revision:
            row["rev"] = ev.judge_revision(exp_rev, {"printed_revision": r.revision, "revision_source": "printed"}, exp_ref)
            c["rev_" + row["rev"]] += 1
        c["number" if r.number else "no_number"] += 1; c["revision" if r.revision else "no_revision"] += 1; c["conflict"] += r.conflict
        out.append(row)
json.dump(out, open(sys.argv[1] + "/tb_corpus.json", "w", encoding="utf-8"), indent=1)
print(dict(c))
for row in out:
    if row.get("ref") not in (None, "tp") or row.get("rev") not in (None, "tp") or row["conflict"]:
        print(row)
