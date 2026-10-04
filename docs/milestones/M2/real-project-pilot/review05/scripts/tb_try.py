import json, sys, pymupdf
sys.path.insert(0, r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend")
from app.services import title_block as tb
fs = json.load(open(r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\FROZEN-SAMPLE.json", encoding="utf-8"))
staged = {f"EP-{d['ep']}/{d['relative_path']}".replace("\\", "/"): d["staged_path"] for d in fs["documents"]}
for name in sys.argv[1:]:
    doc = next(k for k in staged if k.endswith(name)); pdf = pymupdf.open(staged[doc])
    r = tb.read_page(pdf[0])
    print(name[-48:].ljust(48), None if r is None else (r.number, r.revision, r.history_latest, r.conflict, len(r.history), r.references[:3], r.notes[:3]))
