"""AI accuracy pilot run stage: byte copies of the 12 frozen pilot documents, taken from the Round 2 stage (never the
originals), under C:/t/r2x/pilot-stage/EP-<ep>/<same relative path>. Each copy is hash-checked against the frozen sample.
Nothing else is placed there, so a project's sync sees exactly its pilot documents. The BOQ sheet is read from its
staged copy by the BOQ runner (hash-checked) and is not part of this stage."""
import hashlib
import json
import pathlib
import shutil
import sys

A = pathlib.Path("C:/t/iso/work/r2x/ai-pilot")
SAMPLE_SHA = "3822df9ef792e6c6277e0bec3271dcee06dcdc6a15291a3e03ab0b25b6bf1917"
assert hashlib.sha256((A / "PILOT-SAMPLE.json").read_bytes()).hexdigest() == SAMPLE_SHA
sample = json.loads((A / "PILOT-SAMPLE.json").read_text(encoding="utf-8"))
DST = pathlib.Path("C:/t/r2x/pilot-stage")
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
(DST / "PILOT-STAGE.json").write_text(json.dumps({"sample_sha256": SAMPLE_SHA, "files": out}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(out), "files; longest path", max(o["path_length"] for o in out))
print("stage manifest", hashlib.sha256((DST / "PILOT-STAGE.json").read_bytes()).hexdigest())
