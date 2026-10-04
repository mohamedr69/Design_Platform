# DERIVED from ai-accuracy-pilot/make_pilot_stage.py by derive_runners.py -- the continuation stage C:/t/r2x/cont-stage (7 documents)
"""AI accuracy pilot run stage: byte copies of the 12 frozen pilot documents, taken from the Round 2 stage (never the
originals), under C:/t/r2x/pilot-stage/EP-<ep>/<same relative path>. Each copy is hash-checked against the frozen sample.
Nothing else is placed there, so a project's sync sees exactly its pilot documents. The BOQ sheet is read from its
staged copy by the BOQ runner (hash-checked) and is not part of this stage."""
import hashlib
import json
import pathlib
import shutil
import sys

A = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")
SAMPLE_SHA = "ddbceb3f75ee2d44a654a68d6a54b41875cc37f0f26899d4806239cfd3e3c7f3"
assert hashlib.sha256((A / "CONTINUATION-SAMPLE.json").read_bytes()).hexdigest() == SAMPLE_SHA
sample = json.loads((A / "CONTINUATION-SAMPLE.json").read_text(encoding="utf-8"))
DST = pathlib.Path("C:/t/r2x/cont-stage")
LONG = "\\\\?\\"
if DST.exists():
    sys.exit("the pilot stage exists already; it is never rebuilt in place")
out = []
for d in sample["documents"]:
    rel = d["doc_key"].split("/", 1)[1]
    src = LONG + d["staged_path"].replace("/", "\\")
    dst = pathlib.Path(LONG + str(DST / f"EP-{d['ep']}" / pathlib.PurePosixPath(rel)).replace("/", "\\"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    got = hashlib.sha256(dst.read_bytes()).hexdigest()
    assert got == d["sha256"], (rel, got)
    out.append({"doc_key": d["doc_key"], "sha256": got, "path": str(dst)[4:], "path_length": len(str(dst)) - 4})
(DST / "CONT-STAGE.json").write_text(json.dumps({"sample_sha256": SAMPLE_SHA, "files": out}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(out), "files; longest path", max(o["path_length"] for o in out))
print("stage manifest", hashlib.sha256((DST / "CONT-STAGE.json").read_bytes()).hexdigest())
