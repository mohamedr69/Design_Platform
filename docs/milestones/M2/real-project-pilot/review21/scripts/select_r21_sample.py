"""R21 sample selection, FROZEN BEFORE LABELLING (no prediction, no model): from the 415-document non-sealed exploration
manifest, every content hash ever predicted or held out is excluded (small batch, pilot, continuation, both BOQ sheets,
review05 holdout files: by sha256 found in those files), duplicates by sha256 collapse to one, staged copies are
hash-checked and EVERY page is classified (size class, rotation, text layer vs scan-like) -- the earlier availability
table described first pages only. A deterministic PRE-LABEL SCREEN of the text layer / cached OCR flags pages whose
decision words lie OUTSIDE the application's title-block strip (candidate off-title-block decisions); it is a selection
aid only, never a label.

Rule (declared here, applied by seed order sha256(seed | doc_key) inside each stratum):
  24 primary documents: rotated text-layer drawing sheets 8; rotation-0 text-layer drawing sheets 4; drawing-sheet scans 3;
  A3/A4 text 5; A3/A4 scans 4 -- each with every page within the reader's 4-page scope; at most 3 per project;
  MINIMUM off-title-block decision stratum: >= 4 of the 24 must carry a screened candidate off-title-block decision on an
  in-scope page (filled first from the screened pool, in seed order, within their strata); if labelling later finds
  fewer than 4 confirmed, the shortfall is topped up from the screened pool in seed order BEFORE any prediction, and the
  final count is reported; a shortfall that cannot be filled is reported, never hidden.
  3 coverage controls (in the planned denominator, outside the 24): 2 PDFs with more than 4 pages (their supported first
  4 pages are read and consume real budget; pages beyond are 'unsupported:beyond_reader_scope'), 1 Word file (unsupported input).
Writes R21-SAMPLE.json and R21-PAGE-CLASSES.json (every page of every candidate, for the workload)."""
import collections
import hashlib
import json
import pathlib
import re

import pymupdf

W = pathlib.Path("C:/t/iso/work/r2x")
R = W / "review21"
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
LONG = "\\\\?\\"
SEED = "m2-r21-four-arm-2026-09-30"
MAN_SHA = "ee9df7b5e3e6f0035beec01643435e46f63d7f59eccfb9102d6633bf2b6f97cd"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert sha(W / "EXPLORATION-MANIFEST.json") == MAN_SHA
man = json.loads((W / "EXPLORATION-MANIFEST.json").read_text(encoding="utf-8"))
exposure_files = [W / "SMALL-BATCH.json", W / "ai-pilot/PILOT-SAMPLE.json", W / "ai-pilot-r18/CONTINUATION-SAMPLE.json"] + sorted((PILOT / "review05/holdout").glob("*.json"))
exposed = set()
for f in exposure_files:
    exposed |= set(re.findall(r"[0-9a-f]{64}", f.read_text(encoding="utf-8", errors="replace")))
exposed |= {"719f8714d2a75673c8ba390a884a2d2889b2438fd587eaa2c42f62d75f344fec"}      # H-06 sheet
boq_pilot = [b for b in man["boq_candidates"] if (b.get("sha256") or "").startswith("6153dfe701f5")]
exposed |= {b["sha256"] for b in boq_pilot}
DECISION = re.compile(r"NO\s+OBJECTION|APPROVED\s+AS\s+NOTED|REVISE\s+(?:AND|&)\s+RESUBMIT|\bREJECTED\b|NOT\s+APPROVED|\bAPPROVED\b(?!\s+(?:BY|FOR))|\bCODE\s+[A-D]\b", re.I)
seen, docs, pages_out = set(), [], []
dups = 0
for d in man["documents"]:
    if not d.get("sha256") or d["sha256"] in exposed:
        continue
    if d["sha256"] in seen:
        dups += 1
        continue
    seen.add(d["sha256"])
    rec = {"doc_key": d["doc_key"], "ep": d["ep"], "sha256": d["sha256"], "staged_path": d["staged_path"], "extension": d["extension"], "stratum_src": d.get("stratum")}
    if d["extension"] != ".pdf":
        rec.update(pages=None, shape="unsupported_input")
        docs.append(rec)
        continue
    try:
        data = open(LONG + d["staged_path"].replace("/", "\\"), "rb").read()
        assert hashlib.sha256(data).hexdigest() == d["sha256"]
        pdf = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:  # noqa: BLE001
        rec.update(pages=None, shape=f"unreadable:{type(exc).__name__}")
        docs.append(rec)
        continue
    pg = []
    for i in range(pdf.page_count):
        p = pdf[i]
        text = p.get_text()
        w, h = p.rect.width, p.rect.height
        strip = pymupdf.Rect(w * 0.72, 0, w, h) if w >= h else pymupdf.Rect(0, h * 0.78, w, h)
        off = False
        for b in p.get_text("blocks"):
            r = pymupdf.Rect(b[:4]) * p.rotation_matrix
            if DECISION.search(b[4] or "") and not strip.contains(r):
                off = True
        pg.append({"page": i + 1, "size": "drawing_sheet" if max(w, h) > 1300 else "a3_a4", "rotation": p.rotation,
                   "text": "text" if len(text.strip()) >= 80 else "scan_like", "screen_off_title_block_decision": off, "in_scope": i < 4})
        pages_out.append({"doc_key": d["doc_key"], **pg[-1]})
    first = pg[0]
    rec.update(pages=pdf.page_count, shape="pdf" if pdf.page_count <= 4 else "pdf_over_4_pages", page_classes=pg,
               stratum=(first["size"], "rotated" if first["rotation"] else "rot0", first["text"]),
               screened_off_title_block=any(x["screen_off_title_block_decision"] for x in pg if x["in_scope"]))
    docs.append(rec)
rank = lambda d: hashlib.sha256(f"{SEED}|{d['doc_key']}".encode()).hexdigest()
QUOTA = {("drawing_sheet", "rotated", "text"): 8, ("drawing_sheet", "rot0", "text"): 4, ("drawing_sheet", "*", "scan_like"): 3,
         ("a3_a4", "*", "text"): 5, ("a3_a4", "*", "scan_like"): 4}
MIN_OFF = 4
in_scope = [d for d in docs if d.get("shape") == "pdf"]


def stratum_of(d):
    s, r, t = d["stratum"]
    for q in QUOTA:
        if q[0] == s and (q[1] == "*" or q[1] == r) and q[2] == t:
            return q
    return None


per_project, chosen = collections.Counter(), []


def take(pool, n, tag):
    got = 0
    for d in sorted(pool, key=rank):
        if got == n:
            break
        if d in chosen or per_project[d["ep"]] >= 3:
            continue
        chosen.append(dict(d, role=tag))
        per_project[d["ep"]] += 1
        got += 1
    return got


# the off-title-block minimum first (within strata), then the rest of each stratum
off_pool = [d for d in in_scope if d["screened_off_title_block"] and stratum_of(d)]
off_got = take(off_pool, MIN_OFF, "primary:screened_off_title_block")
shortfall = []
for q, n in QUOTA.items():
    already = sum(1 for c in chosen if stratum_of(c) == q)
    pool = [d for d in in_scope if stratum_of(d) == q]
    got = take(pool, max(0, n - already), "primary")
    if already + got < n:
        shortfall.append({"stratum": q, "wanted": n, "got": already + got})
long_pdfs = take([d for d in docs if d.get("shape") == "pdf_over_4_pages"], 2, "control:pdf_over_4_pages")
word = take([d for d in docs if d.get("shape") == "unsupported_input" and d["extension"] in (".doc", ".docx")], 1, "control:unsupported_input")
strata_avail = collections.Counter(stratum_of(d) for d in in_scope if stratum_of(d))
out = {"seed": SEED, "rule": __doc__, "manifest_sha256": MAN_SHA, "exposure_files": {posix: sha(f) for posix, f in ((str(f).replace("\\", "/"), f) for f in exposure_files)},
       "excluded_exposed_hashes": len(exposed), "duplicates_collapsed": dups, "candidates": len(docs), "in_scope_pdfs": len(in_scope),
       "strata_available": {" / ".join(k): v for k, v in sorted(strata_avail.items())}, "screened_off_title_block_available": len(off_pool),
       "min_off_title_block": MIN_OFF, "off_title_block_selected": off_got, "shortfall": shortfall, "per_project": dict(per_project),
       "documents": [{k: c[k] for k in ("doc_key", "ep", "sha256", "staged_path", "extension", "pages", "shape", "role", "stratum_src")}
                     | {"stratum": " / ".join(c["stratum"]) if c.get("stratum") else None, "page_classes": c.get("page_classes"),
                        "screened_off_title_block": c.get("screened_off_title_block")} for c in chosen]}
(R / "R21-SAMPLE.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
(R / "R21-PAGE-CLASSES.json").write_text(json.dumps({"seed": SEED, "pages": pages_out}, indent=1) + "\n", encoding="utf-8")
print("candidates", len(docs), "in-scope", len(in_scope), "dups", dups, "| strata", out["strata_available"], "| off-tb pool", len(off_pool))
print("chosen", len(chosen), "off-tb", off_got, "shortfall", shortfall, "per project", dict(per_project))
for c in chosen:
    print(" ", c["role"][:22], c["sha256"][:12], c["ep"], c.get("pages"), c.get("stratum"), "OFF" if c.get("screened_off_title_block") else "", c["doc_key"][-55:])
print("sha256", sha(R / "R21-SAMPLE.json"))
