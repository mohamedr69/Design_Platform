"""The R21 stage: byte copies of the 27 selected files (from the Round 2 stage, never the originals) under
C:/t/r2x/r21-stage/EP-<ep>/<relative path>, each hash-checked against the frozen sample; page counts re-read from the
copies. Nothing else is placed there. Writes R21-STAGE.json. No prediction, no model."""
import hashlib
import json
import pathlib
import shutil
import sys

import pymupdf

R = pathlib.Path("C:/t/iso/work/r2x/review21")
SAMPLE_SHA = "18b480631547270e9aca26df1d8576ba8924b8e7ec608fd180655a303cd335d9"
assert hashlib.sha256((R / "R21-SAMPLE.json").read_bytes()).hexdigest() == SAMPLE_SHA
sample = json.loads((R / "R21-SAMPLE.json").read_text(encoding="utf-8"))
DST = pathlib.Path("C:/t/r2x/r21-stage")
LONG = "\\\\?\\"
if DST.exists():
    sys.exit("the R21 stage exists already; never rebuilt in place")
out = []
for d in sample["documents"]:
    rel = d["doc_key"].split("/", 1)[1]
    src = LONG + d["staged_path"].replace("/", "\\")
    dst = pathlib.Path(LONG + str(DST / f"EP-{d['ep']}" / pathlib.PurePosixPath(rel)).replace("/", "\\"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    data = dst.read_bytes()
    got = hashlib.sha256(data).hexdigest()
    assert got == d["sha256"], (rel, got)
    pages = pymupdf.open(stream=data, filetype="pdf").page_count if d["extension"] == ".pdf" else None
    assert pages == d["pages"], (rel, pages, d["pages"])
    out.append({"doc_key": d["doc_key"], "sha256": got, "path": str(dst)[4:], "pages": pages, "extension": d["extension"], "role": d["role"]})
(DST / "R21-STAGE.json").write_text(json.dumps({"sample_sha256": SAMPLE_SHA, "files": out}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(out), "files;", sum(1 for o in out if o["pages"]), "pdfs;", sum(o["pages"] or 0 for o in out), "pages total;",
      sum(min(o["pages"] or 0, 4) for o in out), "in scope; manifest", hashlib.sha256((DST / "R21-STAGE.json").read_bytes()).hexdigest())
