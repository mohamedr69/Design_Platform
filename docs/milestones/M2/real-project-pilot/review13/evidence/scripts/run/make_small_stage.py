"""The small batch's run stage: byte copies of the 12 frozen small-batch documents, taken from the Round 2 stage
(C:/t/r2x/stage, never the originals), under C:/t/r2x/small-stage/EP-<ep>/<same relative path>. Each copy is hash-checked
against the staging manifest. Nothing else is placed there, so a project's sync sees exactly its batch documents."""
import hashlib
import json
import pathlib
import shutil
import sys

W = pathlib.Path("C:/t/iso/work/r2x")
SB_SHA = "7039daa3f04935a35d9a272076be16510d4eb0a8885651f83f07af51f44d7139"
assert hashlib.sha256((W / "SMALL-BATCH.json").read_bytes()).hexdigest() == SB_SHA
sb = json.loads((W / "SMALL-BATCH.json").read_text(encoding="utf-8"))
man = {d["sha256"]: d for d in json.loads((W / "EXPLORATION-MANIFEST.json").read_text(encoding="utf-8"))["documents"]}
DST = pathlib.Path("C:/t/r2x/small-stage")
PREFIX = "\\\\?\\"
if DST.exists():
    sys.exit("the small stage exists already; it is never rebuilt in place")
out = []
for d in sb["documents"]:
    m = man[d["sha256"]]
    rel = m["doc_key"].split("/", 1)[1]
    src = PREFIX + m["staged_path"].replace("/", "\\")
    dst = pathlib.Path(PREFIX + str(DST / f"EP-{m['ep']}" / pathlib.PurePosixPath(rel)).replace("/", "\\"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    got = hashlib.sha256(dst.read_bytes()).hexdigest()
    assert got == d["sha256"], (rel, got)
    out.append({"doc_key": m["doc_key"], "sha256": got, "path": str(dst)[4:], "path_length": len(str(dst)) - 4})
(DST / "SMALL-STAGE.json").write_text(json.dumps({"small_batch_sha256": SB_SHA, "files": out}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(out), "files; longest path", max(o["path_length"] for o in out))
